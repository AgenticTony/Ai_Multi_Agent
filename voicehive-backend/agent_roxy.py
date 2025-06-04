import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from datetime import datetime
import asyncio

# Import new tools and memory
from tools import crm, calendar, notify
from memory import mem0

# Import prompt management
from improvements.prompt_manager import get_system_prompt, get_current_prompt

logger = logging.getLogger(__name__)

class RoxyAgent:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_prompt = self._load_system_prompt()
        self.conversation_history = {}

    def _load_system_prompt(self) -> str:
        """Load the system prompt for Roxy from versioned prompt system"""
        try:
            # Get current prompt from prompt manager
            versioned_prompt = get_system_prompt()
            
            if versioned_prompt:
                logger.info("Loaded versioned system prompt")
                return versioned_prompt
            else:
                logger.warning("No versioned prompt found, using fallback")
                return self._get_fallback_prompt()
                
        except Exception as e:
            logger.error(f"Error loading versioned prompt: {str(e)}")
            return self._get_fallback_prompt()
    
    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if versioned system fails"""
        return """
You are Roxy, a professional AI voice assistant for VoiceHive. You help businesses handle inbound calls efficiently.

Your personality:
- Professional but friendly
- Confident and helpful
- Clear and concise in communication
- Patient with customers
- Remember previous interactions

Your main functions:
1. Greet callers warmly and check if they're a returning customer
2. Understand their needs (appointments, questions, complaints)
3. Book, reschedule, or cancel appointments
4. Capture detailed lead information
5. Handle objections professionally
6. Send confirmations and reminders
7. Transfer to human agents when needed

Guidelines:
- Keep responses under 50 words for natural conversation flow
- Always confirm important details (names, phone numbers, appointment times)
- Use memory to personalize interactions with returning customers
- If you can't help, offer to transfer to a human agent
- Be empathetic to customer concerns
- Ask clarifying questions when needed
- Store important conversation details for future reference

Enhanced tools available:
- CRM tools: create_lead, update_lead, search_leads, add_lead_note
- Calendar tools: book_appointment, check_availability, reschedule_appointment, cancel_appointment
- Notification tools: send_confirmation, send_reminder, send_cancellation
- Memory tools: store_memory, get_user_memories, search_memories
- transfer_call: Transfer to human agent
"""

    async def handle_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general messages from Vapi with memory integration"""
        try:
            message = webhook_data.get("message", {})
            call_id = webhook_data.get("call", {}).get("id", "unknown")
            customer_number = webhook_data.get("call", {}).get("customer", {}).get("number", "")

            # Extract user message if available
            user_message = message.get("content", "")

            if not user_message:
                # Check for returning customer
                context_response = await self._get_customer_context(call_id, customer_number)
                return {"message": context_response}

            # Get conversation history for this call
            history = self.conversation_history.get(call_id, [])

            # Add user message to history
            history.append({"role": "user", "content": user_message})

            # Generate response using OpenAI with memory context
            response = await self._generate_response_with_memory(history, call_id, customer_number)

            # Add assistant response to history
            history.append({"role": "assistant", "content": response})

            # Store updated history
            self.conversation_history[call_id] = history[-10:]  # Keep last 10 messages

            # Store conversation in memory
            await self._store_conversation_memory(call_id, customer_number, user_message, response)

            return {"message": response}

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return {"message": "I apologize, but I'm having trouble processing your request. Let me transfer you to a human agent."}

    async def handle_function_call(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle function calls from the assistant"""
        try:
            function_call = webhook_data.get("message", {}).get("functionCall", {})
            function_name = function_call.get("name")
            parameters = function_call.get("parameters", {})

            logger.info(f"Function call: {function_name} with parameters: {parameters}")

            # Enhanced function routing with new tools
            if function_name == "book_appointment":
                result = await self._book_appointment(parameters)
            elif function_name == "check_availability":
                result = await self._check_availability(parameters)
            elif function_name == "reschedule_appointment":
                result = await self._reschedule_appointment(parameters)
            elif function_name == "cancel_appointment":
                result = await self._cancel_appointment(parameters)
            elif function_name == "create_lead":
                result = await self._create_lead(parameters)
            elif function_name == "capture_lead":
                result = await self._capture_lead(parameters)
            elif function_name == "update_lead":
                result = await self._update_lead(parameters)
            elif function_name == "search_leads":
                result = await self._search_leads(parameters)
            elif function_name == "send_confirmation":
                result = await self._send_confirmation(parameters)
            elif function_name == "send_reminder":
                result = await self._send_reminder(parameters)
            elif function_name == "send_cancellation":
                result = await self._send_cancellation(parameters)
            elif function_name == "transfer_call":
                result = await self._transfer_call(parameters)
            else:
                result = {"success": False, "message": f"Unknown function: {function_name}"}

            return {"result": result}

        except Exception as e:
            logger.error(f"Error handling function call: {str(e)}")
            return {"result": {"success": False, "message": "Function call failed"}}

    async def handle_transcript(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transcript updates"""
        try:
            transcript = webhook_data.get("message", {}).get("transcript", "")
            call_id = webhook_data.get("call", {}).get("id", "unknown")

            logger.info(f"Transcript update for call {call_id}: {transcript}")

            # Store transcript for later analysis
            # This would typically go to a database or memory system

            return {"status": "transcript_received"}

        except Exception as e:
            logger.error(f"Error handling transcript: {str(e)}")
            return {"status": "error"}

    async def handle_call_end(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call end events"""
        try:
            call_id = webhook_data.get("call", {}).get("id", "unknown")

            logger.info(f"Call ended: {call_id}")

            # Clean up conversation history
            if call_id in self.conversation_history:
                del self.conversation_history[call_id]

            # Store final call data for analysis
            # This would typically go to a database

            return {"status": "call_ended"}

        except Exception as e:
            logger.error(f"Error handling call end: {str(e)}")
            return {"status": "error"}

    async def _generate_response(self, conversation_history: list) -> str:
        """Generate response using OpenAI"""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(conversation_history)

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble right now. Let me transfer you to a human agent."

    async def _book_appointment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Book an appointment using enhanced calendar tool"""
        try:
            name = parameters.get("name")
            phone = parameters.get("phone")
            email = parameters.get("email")
            date = parameters.get("date")
            time = parameters.get("time")
            service = parameters.get("service", "consultation")
            duration = parameters.get("duration", 60)

            # Book appointment using calendar tool
            result = calendar.book_appointment(name, phone, date, time, service, email, duration)

            # Send confirmation if successful
            if result["success"]:
                notify.send_confirmation(
                    phone=phone,
                    email=email,
                    name=name,
                    date=date,
                    time=time,
                    service=service
                )

                # Create or update lead
                crm.create_lead(name, phone, email, interest=service)

            return result

        except Exception as e:
            logger.error(f"Error booking appointment: {str(e)}")
            return {"success": False, "message": "Failed to book appointment"}

    async def _capture_lead(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Capture lead information using enhanced CRM tool"""
        try:
            name = parameters.get("name")
            phone = parameters.get("phone")
            email = parameters.get("email")
            interest = parameters.get("interest")
            issue = parameters.get("issue")

            # Create lead using CRM tool
            result = crm.create_lead(name, phone, email, issue, interest)

            # Add note about the call
            if result["success"]:
                lead_id = result["lead_id"]
                crm.add_lead_note(lead_id, "Lead captured during voice call", "call")

            return result

        except Exception as e:
            logger.error(f"Error capturing lead: {str(e)}")
            return {"success": False, "message": "Failed to capture lead information"}

    async def _send_confirmation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send confirmation using enhanced notification tool"""
        try:
            phone = parameters.get("phone")
            email = parameters.get("email")
            name = parameters.get("name", "")
            date = parameters.get("date", "")
            time = parameters.get("time", "")
            service = parameters.get("service", "")
            message = parameters.get("message")

            # Use notification tool for confirmation
            if date and time:  # Appointment confirmation
                result = notify.send_confirmation(phone, email, name, date, time, service)
            else:  # General confirmation
                result = notify.send_notification(phone, email, message or "Confirmation from VoiceHive")

            return result

        except Exception as e:
            logger.error(f"Error sending confirmation: {str(e)}")
            return {"success": False, "message": "Failed to send confirmation"}

    async def _transfer_call(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Transfer call to human agent (placeholder implementation)"""
        try:
            reason = parameters.get("reason", "Customer request")
            department = parameters.get("department", "general")

            # Placeholder - would integrate with call transfer system
            logger.info(f"Transferring call to {department}: {reason}")

            return {
                "success": True,
                "message": "Transferring you to a human agent now",
                "transfer_type": "human_agent"
            }

        except Exception as e:
            logger.error(f"Error transferring call: {str(e)}")
            return {"success": False, "message": "Failed to transfer call"}

    # New enhanced tool integration methods

    async def _get_customer_context(self, call_id: str, customer_number: str) -> str:
        """Get customer context for personalized greeting"""
        try:
            if customer_number:
                # Search for existing customer by phone
                search_result = crm.search_leads(phone=customer_number)
                if search_result["success"] and search_result["leads"]:
                    customer = search_result["leads"][0]
                    name = customer.get("name", "")
                    return f"Hello {name}! Welcome back to VoiceHive. How can I help you today?"

                # Check memory for previous interactions
                memory_result = mem0.get_user_memories(customer_number, "phone", limit=1)
                if memory_result["success"] and memory_result["memories"]:
                    return "Welcome back to VoiceHive! I see we've spoken before. How can I help you today?"

            return "Hello! I'm Roxy, your VoiceHive assistant. How can I help you today?"

        except Exception as e:
            logger.error(f"Error getting customer context: {str(e)}")
            return "Hello! I'm Roxy, your VoiceHive assistant. How can I help you today?"

    async def _generate_response_with_memory(self, history: list, call_id: str, customer_number: str) -> str:
        """Generate response with memory context"""
        try:
            # Get recent memories for context
            context_messages = []
            if customer_number:
                memory_result = mem0.get_user_memories(customer_number, "phone", limit=3)
                if memory_result["success"] and memory_result["memories"]:
                    context_messages.append({
                        "role": "system",
                        "content": f"Previous interactions with this customer: {memory_result['memories']}"
                    })

            # Prepare messages for OpenAI
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(context_messages)
            messages.extend(history)

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating response with memory: {str(e)}")
            return "I apologize, but I'm having trouble right now. Let me transfer you to a human agent."

    async def _store_conversation_memory(self, call_id: str, customer_number: str, query: str, response: str):
        """Store conversation in memory system"""
        try:
            # Extract customer info if available
            customer_name = None
            if customer_number:
                search_result = crm.search_leads(phone=customer_number)
                if search_result["success"] and search_result["leads"]:
                    customer_name = search_result["leads"][0].get("name")

            # Store in memory
            mem0.store_memory(
                session_id=call_id,
                call_id=call_id,
                user_name=customer_name,
                user_phone=customer_number,
                query=query,
                answer=response,
                tags=["conversation", "voice_call"]
            )

        except Exception as e:
            logger.error(f"Error storing conversation memory: {str(e)}")

    # Enhanced tool methods

    async def _check_availability(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check appointment availability"""
        try:
            date = parameters.get("date")
            time = parameters.get("time")
            duration = parameters.get("duration", 60)

            if not date:
                return calendar.get_available_slots(datetime.now().strftime("%Y-%m-%d"), duration)

            if time:
                available = calendar.check_availability(date, time, duration)
                return {
                    "success": True,
                    "available": available,
                    "date": date,
                    "time": time,
                    "message": f"Time slot is {'available' if available else 'not available'}"
                }
            else:
                return calendar.get_available_slots(date, duration)

        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return {"success": False, "message": "Failed to check availability"}

    async def _reschedule_appointment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Reschedule an existing appointment"""
        try:
            appointment_id = parameters.get("appointment_id")
            new_date = parameters.get("new_date")
            new_time = parameters.get("new_time")

            result = calendar.reschedule_appointment(appointment_id, new_date, new_time)

            # Send notification if successful
            if result["success"]:
                appointment = calendar.get_appointment(appointment_id)
                if appointment["success"]:
                    apt_data = appointment["appointment"]
                    notify.send_confirmation(
                        phone=apt_data.get("phone"),
                        email=apt_data.get("email"),
                        name=apt_data.get("name"),
                        date=new_date,
                        time=new_time,
                        service=apt_data.get("service")
                    )

            return result

        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            return {"success": False, "message": "Failed to reschedule appointment"}

    async def _cancel_appointment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel an appointment"""
        try:
            appointment_id = parameters.get("appointment_id")
            reason = parameters.get("reason", "Customer request")

            # Get appointment details before cancelling
            appointment = calendar.get_appointment(appointment_id)

            result = calendar.cancel_appointment(appointment_id, reason)

            # Send cancellation notice if successful
            if result["success"] and appointment["success"]:
                apt_data = appointment["appointment"]
                notify.send_cancellation(
                    phone=apt_data.get("phone"),
                    email=apt_data.get("email"),
                    name=apt_data.get("name"),
                    date=apt_data.get("date"),
                    time=apt_data.get("time"),
                    reason=reason
                )

            return result

        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return {"success": False, "message": "Failed to cancel appointment"}

    async def _create_lead(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lead"""
        try:
            name = parameters.get("name")
            phone = parameters.get("phone")
            email = parameters.get("email")
            issue = parameters.get("issue")
            interest = parameters.get("interest")

            result = crm.create_lead(name, phone, email, issue, interest)

            # Add note about the call
            if result["success"]:
                lead_id = result["lead_id"]
                crm.add_lead_note(lead_id, "Lead created during voice call", "call")

            return result

        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            return {"success": False, "message": "Failed to create lead"}

    async def _update_lead(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing lead"""
        try:
            lead_id = parameters.get("lead_id")
            updates = {k: v for k, v in parameters.items() if k != "lead_id"}

            return crm.update_lead(lead_id, **updates)

        except Exception as e:
            logger.error(f"Error updating lead: {str(e)}")
            return {"success": False, "message": "Failed to update lead"}

    async def _search_leads(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for leads"""
        try:
            query = parameters.get("query")
            status = parameters.get("status")
            phone = parameters.get("phone")

            return crm.search_leads(query, status, phone)

        except Exception as e:
            logger.error(f"Error searching leads: {str(e)}")
            return {"success": False, "message": "Failed to search leads"}

    async def _send_reminder(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send appointment reminder"""
        try:
            phone = parameters.get("phone")
            email = parameters.get("email")
            name = parameters.get("name")
            date = parameters.get("date")
            time = parameters.get("time")
            service = parameters.get("service")

            return notify.send_reminder(phone, email, name, date, time, service)

        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
            return {"success": False, "message": "Failed to send reminder"}

    async def _send_cancellation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send cancellation notice"""
        try:
            phone = parameters.get("phone")
            email = parameters.get("email")
            name = parameters.get("name")
            date = parameters.get("date")
            time = parameters.get("time")
            reason = parameters.get("reason", "")

            return notify.send_cancellation(phone, email, name, date, time, reason)

        except Exception as e:
            logger.error(f"Error sending cancellation: {str(e)}")
            return {"success": False, "message": "Failed to send cancellation"}
