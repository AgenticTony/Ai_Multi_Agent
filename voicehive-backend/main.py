from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
import logging
from agent_roxy import RoxyAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VoiceHive Backend", version="1.0.0")

# Initialize Roxy agent
roxy = RoxyAgent()

@app.get("/")
async def root():
    return {"message": "VoiceHive Backend is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "voicehive-backend"}

@app.post("/webhook/vapi")
async def vapi_webhook(request: Request):
    """
    Webhook endpoint for Vapi.ai to send call events
    """
    try:
        # Get the raw request body
        body = await request.json()
        
        # Log the incoming request
        logger.info(f"Received Vapi webhook: {body}")
        
        # Extract message type and content
        message_type = body.get("message", {}).get("type")
        
        if message_type == "function-call":
            # Handle function calls from the assistant
            response = await roxy.handle_function_call(body)
            return JSONResponse(content=response)
        
        elif message_type == "transcript":
            # Handle transcript updates
            response = await roxy.handle_transcript(body)
            return JSONResponse(content=response)
        
        elif message_type == "hang":
            # Handle call end
            response = await roxy.handle_call_end(body)
            return JSONResponse(content=response)
        
        else:
            # Handle other message types or general conversation
            response = await roxy.handle_message(body)
            return JSONResponse(content=response)
            
    except Exception as e:
        logger.error(f"Error processing Vapi webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
