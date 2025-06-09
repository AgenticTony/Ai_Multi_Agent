"""
VoiceHive Appointment Service
Handles appointment booking, cancellation, and availability checking
Uses dependency injection for memory and repository services
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from voicehive.models.vapi import AppointmentRequest
from voicehive.utils.exceptions import AppointmentServiceError
from voicehive.repositories.base_repository import AppointmentRepository
from voicehive.services.memory.memory_service import MemoryServiceInterface

logger = logging.getLogger(__name__)


class AppointmentService:
    """Service for handling appointment bookings with dependency injection"""

    def __init__(
        self,
        repository: Optional[AppointmentRepository] = None,
        memory_service: Optional[MemoryServiceInterface] = None
    ):
        """
        Initialize appointment service with injected dependencies

        Args:
            repository: Repository for appointment data persistence
            memory_service: Memory service for conversation storage
        """
        # Use dependency injection or fallback to default implementations
        from voicehive.repositories.base_repository import get_repository_factory
        from voicehive.services.memory.memory_service import UnifiedMemoryService

        self.repository = repository or get_repository_factory().get_appointment_repository()
        self.memory_service = memory_service or UnifiedMemoryService()

        logger.info("AppointmentService initialized with dependency injection")
        
    async def book_appointment(
        self,
        appointment_request: AppointmentRequest,
        call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Book an appointment
        
        Args:
            appointment_request: Validated appointment request
            
        Returns:
            Appointment booking result
        """
        try:
            # Generate appointment ID
            appointment_id = f"apt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # In a real implementation, this would:
            # 1. Check calendar availability
            # 2. Validate date/time format
            # 3. Store in calendar system (Google Calendar, Calendly, etc.)
            # 4. Send calendar invites
            
            appointment_data = {
                "id": appointment_id,
                "name": appointment_request.name,
                "phone": appointment_request.phone,
                "date": appointment_request.date,
                "time": appointment_request.time,
                "service": appointment_request.service,
                "status": "confirmed",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store appointment using repository
            stored_appointment = await self.repository.create(appointment_data)

            # Store conversation memory
            await self.memory_service.store_conversation_memory(
                session_id=call_id,
                call_id=call_id,
                user_name=appointment_request.name,
                user_phone=appointment_request.phone,
                query=f"Book appointment for {appointment_request.date} at {appointment_request.time}",
                answer=f"Appointment confirmed for {appointment_request.name}",
                tags=["appointment", "booking"],
                metadata={"appointment_id": appointment_id}
            )

            logger.info(f"Appointment booked: {appointment_id} for {appointment_request.name}")

            return {
                "appointment_id": appointment_id,
                "status": "confirmed",
                "message": f"Appointment confirmed for {appointment_request.date} at {appointment_request.time}"
            }
            
        except Exception as e:
            logger.error(f"Error booking appointment: {str(e)}")
            raise AppointmentServiceError(
                message=f"Failed to book appointment: {str(e)}",
                user_message=f"I couldn't book your appointment for {appointment_request.date}. Please try again or let me transfer you to someone who can help.",
                details={"appointment_request": appointment_request.dict()}
            ) from e
    
    async def check_availability(self, date: str, time: str) -> bool:
        """
        Check if a time slot is available
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM AM/PM format
            
        Returns:
            True if available, False otherwise
        """
        try:
            # Placeholder implementation
            # In a real system, this would check against the actual calendar
            
            # For now, assume all slots are available except for demonstration
            unavailable_slots = [
                ("2024-01-15", "10:00 AM"),
                ("2024-01-15", "2:00 PM")
            ]
            
            return (date, time) not in unavailable_slots
            
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return False
    
    async def get_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Get appointment details
        
        Args:
            appointment_id: Unique appointment identifier
            
        Returns:
            Appointment details
        """
        try:
            appointment = self.appointments.get(appointment_id)
            if not appointment:
                raise AppointmentServiceError(f"Appointment {appointment_id} not found")
            
            return appointment
            
        except Exception as e:
            logger.error(f"Error getting appointment {appointment_id}: {str(e)}")
            raise AppointmentServiceError(f"Failed to get appointment: {str(e)}")
    
    async def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Cancel an appointment
        
        Args:
            appointment_id: Unique appointment identifier
            
        Returns:
            Cancellation result
        """
        try:
            if appointment_id not in self.appointments:
                raise AppointmentServiceError(f"Appointment {appointment_id} not found")
            
            # Update appointment status
            self.appointments[appointment_id]["status"] = "cancelled"
            cancelled_at = datetime.now(timezone.utc).isoformat()
            self.appointments[appointment_id]["cancelled_at"] = cancelled_at
            
            logger.info(f"Appointment cancelled: {appointment_id}")
            
            return {
                "appointment_id": appointment_id,
                "status": "cancelled",
                "message": "Appointment has been cancelled successfully"
            }
            
        except Exception as e:
            logger.error(f"Error cancelling appointment {appointment_id}: {str(e)}")
            raise AppointmentServiceError(f"Failed to cancel appointment: {str(e)}")
