import logging
from typing import Dict, Any, List
from datetime import datetime

from voicehive.core.settings import get_settings
from voicehive.models.vapi import (
    ConversationMessage, 
    FunctionCallResponse,
    AppointmentRequest,
    LeadCaptureRequest,
    ConfirmationRequest,
    TransferRequest
)
from voicehive.services.ai.openai_service import OpenAIService
from voicehive.domains.appointments.services.appointment_service import AppointmentService
from voicehive.domains.leads.services.lead_service import LeadService
from voicehive.domains.notifications.services.notification_service import NotificationService
from voicehive.utils.exceptions import AgentError, FunctionCallError

logger = logging.getLogger(__name__)
settings = get_settings()


class RoxyAgent:
    """
    Roxy AI Agent - Handles voice conversations and function calls
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.appointment_service = AppointmentService()
        self.lead_service = LeadService()
        self.notification_service = NotificationService()
        self.conversation_history: Dict[str, List[ConversationMessage]] = {}
        self.system_prompt = self._load_system_prompt()
        
    def _load_system_prompt(self) -> str:
        """Load the system prompt for Roxy"""
        return """
You are Roxy, a professional AI voice assistant for VoiceHive. You help businesses handle inbound calls efficiently.

Your personality:
- Professional but friendly
- Confident and helpful
- Clear and concise in communication
- Patient with customers

Your main functions:
1. Greet callers warmly
2. Understand their needs (appointments, questions, complaints)
3. Book appointments when requested
4. Capture lead information
5. Handle basic objections
6. Transfer to human agents when needed

Guidelines:
- Keep responses under 50 words for natural conversation flow
- Always confirm important details (names, phone numbers, appointment times)
- If you can't help, offer to transfer to a human agent
- Be empathetic to customer concerns
- Ask clarifying questions when needed

Available tools:
- book_appointment: Schedule appointments in the calendar
- capture_lead: Store customer contact information
- send_confirmation: Send SMS/email confirmations
- transfer_call: Transfer to human agent
"""

    async def handle_message(self, call_id: str, user_message: str) -> str:
        """
        Handle a general message from the user
        
        Args:
            call_id: Unique identifier for the call
            user_message: The user's message content
            
        Returns:
            Agent's response message
        """
        try:
            if not user_message.strip():
                return "Hello! I'm Roxy, your VoiceHive assistant. How can I help you today?"
            
            # Get or create conversation history
            history = self._get_conversation_history(call_id)
            
            # Add user message to history
            user_msg = ConversationMessage(role="user", content=user_message)
            history.append(user_msg)
            
            # Generate response using OpenAI
            response = await self.openai_service.generate_response(
                self.system_prompt, 
                history
            )
            
            # Add assistant response to history
            assistant_msg = ConversationMessage(role="assistant", content=response)
            history.append(assistant_msg)
            
            # Update conversation history (keep only recent messages)
            self._update_conversation_history(call_id, history)
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling message for call {call_id}: {str(e)}")
            raise AgentError(f"Failed to process message: {str(e)}")

    async def handle_function_call(self, call_id: str, function_name: str, parameters: Dict[str, Any]) -> FunctionCallResponse:
        """
        Handle function calls from the assistant
        
        Args:
            call_id: Unique identifier for the call
            function_name: Name of the function to call
            parameters: Function parameters
            
        Returns:
            Function call response
        """
        try:
            logger.info(f"Function call for call {call_id}: {function_name} with parameters: {parameters}")
            
            if function_name == "book_appointment":
                return await self._handle_book_appointment(parameters)
            elif function_name == "capture_lead":
                return await self._handle_capture_lead(parameters)
            elif function_name == "send_confirmation":
                return await self._handle_send_confirmation(parameters)
            elif function_name == "transfer_call":
                return await self._handle_transfer_call(parameters)
            else:
                raise FunctionCallError(f"Unknown function: {function_name}")
                
        except Exception as e:
            logger.error(f"Error handling function call {function_name} for call {call_id}: {str(e)}")
            return FunctionCallResponse(
                success=False,
                message=f"Function call failed: {str(e)}"
            )

    async def handle_transcript_update(self, call_id: str, transcript: str) -> None:
        """
        Handle transcript updates for analysis
        
        Args:
            call_id: Unique identifier for the call
            transcript: Updated transcript content
        """
        try:
            logger.info(f"Transcript update for call {call_id}: {transcript}")
            # Store transcript for later analysis (Sprint 3)
            # This would typically go to a database or memory system
            
        except Exception as e:
            logger.error(f"Error handling transcript update for call {call_id}: {str(e)}")

    async def handle_call_end(self, call_id: str) -> None:
        """
        Handle call end cleanup
        
        Args:
            call_id: Unique identifier for the call
        """
        try:
            logger.info(f"Call ended: {call_id}")
            
            # Clean up conversation history
            if call_id in self.conversation_history:
                del self.conversation_history[call_id]
            
            # Store final call data for analysis
            # This would typically go to a database
            
        except Exception as e:
            logger.error(f"Error handling call end for call {call_id}: {str(e)}")

    def _get_conversation_history(self, call_id: str) -> List[ConversationMessage]:
        """Get conversation history for a call"""
        return self.conversation_history.get(call_id, [])

    def _update_conversation_history(self, call_id: str, history: List[ConversationMessage]) -> None:
        """Update conversation history, keeping only recent messages"""
        # Keep only the last N messages to prevent memory bloat
        limit = settings.conversation_history_limit
        self.conversation_history[call_id] = history[-limit:] if len(history) > limit else history

    async def _handle_book_appointment(self, parameters: Dict[str, Any]) -> FunctionCallResponse:
        """Handle appointment booking"""
        try:
            # Validate parameters
            appointment_request = AppointmentRequest(**parameters)
            
            # Book the appointment
            result = await self.appointment_service.book_appointment(appointment_request)
            
            return FunctionCallResponse(
                success=True,
                message=f"Appointment booked for {appointment_request.name} on {appointment_request.date} at {appointment_request.time}",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error booking appointment: {str(e)}")
            return FunctionCallResponse(
                success=False,
                message="Failed to book appointment. Please try again or speak with a human agent."
            )

    async def _handle_capture_lead(self, parameters: Dict[str, Any]) -> FunctionCallResponse:
        """Handle lead capture"""
        try:
            # Validate parameters
            lead_request = LeadCaptureRequest(**parameters)
            
            # Capture the lead
            result = await self.lead_service.capture_lead(lead_request)
            
            return FunctionCallResponse(
                success=True,
                message=f"Thank you {lead_request.name}! I've captured your information and someone will follow up with you soon.",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error capturing lead: {str(e)}")
            return FunctionCallResponse(
                success=False,
                message="Failed to capture your information. Please try again."
            )

    async def _handle_send_confirmation(self, parameters: Dict[str, Any]) -> FunctionCallResponse:
        """Handle sending confirmations"""
        try:
            # Validate parameters
            confirmation_request = ConfirmationRequest(**parameters)
            
            # Send confirmation
            result = await self.notification_service.send_confirmation(confirmation_request)
            
            return FunctionCallResponse(
                success=True,
                message="Confirmation sent successfully!",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Error sending confirmation: {str(e)}")
            return FunctionCallResponse(
                success=False,
                message="Failed to send confirmation. Please check your contact information."
            )

    async def _handle_transfer_call(self, parameters: Dict[str, Any]) -> FunctionCallResponse:
        """Handle call transfer"""
        try:
            # Validate parameters
            transfer_request = TransferRequest(**parameters)
            
            logger.info(f"Transferring call to {transfer_request.department}: {transfer_request.reason}")
            
            return FunctionCallResponse(
                success=True,
                message="I'm transferring you to a human agent now. Please hold for a moment.",
                data={
                    "transfer_type": "human_agent",
                    "department": transfer_request.department,
                    "reason": transfer_request.reason
                }
            )
            
        except Exception as e:
            logger.error(f"Error transferring call: {str(e)}")
            return FunctionCallResponse(
                success=False,
                message="Failed to transfer call. Let me try to help you directly."
            )
