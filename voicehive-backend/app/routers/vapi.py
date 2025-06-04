from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.models.vapi import VapiWebhookRequest, VapiWebhookResponse
from app.services.agents.roxy_agent import RoxyAgent
from app.utils.exceptions import AgentError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])

# Initialize Roxy agent
roxy = RoxyAgent()


@router.post("/vapi", response_model=VapiWebhookResponse)
async def vapi_webhook(request: Request):
    """
    Webhook endpoint for Vapi.ai to send call events
    """
    try:
        # Get the raw request body
        body = await request.json()
        
        # Log the incoming request
        logger.info(f"Received Vapi webhook: {body}")
        
        # Validate the request using Pydantic model
        webhook_request = VapiWebhookRequest(**body)
        
        # Extract call and message information
        call_id = webhook_request.call.id
        message = webhook_request.message
        message_type = message.type
        
        if message_type == "function-call":
            # Handle function calls from the assistant
            function_call = message.functionCall
            if not function_call:
                raise HTTPException(status_code=400, detail="Missing function call data")
            
            function_name = function_call.get("name")
            parameters = function_call.get("parameters", {})
            
            response = await roxy.handle_function_call(call_id, function_name, parameters)
            
            return VapiWebhookResponse(result=response.dict())
        
        elif message_type == "transcript":
            # Handle transcript updates
            transcript = message.transcript or ""
            await roxy.handle_transcript_update(call_id, transcript)
            
            return VapiWebhookResponse(status="transcript_received")
        
        elif message_type == "hang":
            # Handle call end
            await roxy.handle_call_end(call_id)
            
            return VapiWebhookResponse(status="call_ended")
        
        else:
            # Handle other message types or general conversation
            user_message = message.content or ""
            response_message = await roxy.handle_message(call_id, user_message)
            
            return VapiWebhookResponse(message=response_message)
            
    except AgentError as e:
        logger.error(f"Agent error processing Vapi webhook: {str(e)}")
        return VapiWebhookResponse(
            message="I apologize, but I'm having trouble processing your request. Let me transfer you to a human agent."
        )
    
    except Exception as e:
        logger.error(f"Error processing Vapi webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
