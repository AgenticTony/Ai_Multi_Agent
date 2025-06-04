"""
Calendar Tool - Enhanced appointment booking and scheduling functionality
"""
import logging
from datetime import datetime, timedelta, time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class Appointment:
    """Appointment data structure"""
    id: str
    name: str
    phone: str
    date: str  # YYYY-MM-DD format
    time: str  # HH:MM AM/PM format
    email: Optional[str] = None
    service: Optional[str] = None
    duration: int = 60  # minutes
    status: str = "confirmed"
    notes: List[str] = None
    created_at: str = None
    updated_at: str = None
    reminder_sent: bool = False

    def __post_init__(self):
        if self.notes is None:
            self.notes = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


class CalendarTool:
    """Enhanced calendar functionality for appointment management"""

    def __init__(self):
        # In production, this would integrate with calendar systems
        # (Google Calendar, Outlook, Calendly, etc.)
        self.appointments: Dict[str, Appointment] = {}
        self.business_hours = {
            "monday": {"start": "09:00", "end": "17:00"},
            "tuesday": {"start": "09:00", "end": "17:00"},
            "wednesday": {"start": "09:00", "end": "17:00"},
            "thursday": {"start": "09:00", "end": "17:00"},
            "friday": {"start": "09:00", "end": "17:00"},
            "saturday": {"start": "10:00", "end": "14:00"},
            "sunday": {"closed": True}
        }
        self.slot_duration = 60  # minutes
        self.buffer_time = 15  # minutes between appointments

    def book_appointment(self, name: str, phone: str, date: str, time: str,
                        service: str = None, email: str = None,
                        duration: int = 60) -> Dict[str, Any]:
        """
        Book a new appointment

        Args:
            name: Customer name
            phone: Phone number
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM AM/PM format
            service: Type of service/appointment
            email: Email address (optional)
            duration: Appointment duration in minutes

        Returns:
            Booking result with appointment ID
        """
        try:
            # Validate date and time format
            validation_result = self._validate_datetime(date, time)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": validation_result["message"]
                }

            # Check availability
            if not self.check_availability(date, time, duration):
                return {
                    "success": False,
                    "message": f"Time slot {date} at {time} is not available"
                }

            # Check business hours
            if not self._is_within_business_hours(date, time):
                return {
                    "success": False,
                    "message": f"Requested time is outside business hours"
                }

            # Generate appointment ID
            appointment_id = f"apt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            # Create appointment
            appointment = Appointment(
                id=appointment_id,
                name=name,
                phone=phone,
                email=email,
                date=date,
                time=time,
                service=service,
                duration=duration
            )

            # Store appointment
            self.appointments[appointment_id] = appointment

            logger.info(f"Appointment booked: {appointment_id} - {name} on {date} at {time}")

            return {
                "success": True,
                "appointment_id": appointment_id,
                "message": f"Appointment booked for {name} on {date} at {time}",
                "details": {
                    "name": name,
                    "phone": phone,
                    "date": date,
                    "time": time,
                    "service": service,
                    "duration": duration
                }
            }

        except Exception as e:
            logger.error(f"Error booking appointment: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to book appointment: {str(e)}"
            }

    def check_availability(self, date: str, time: str, duration: int = 60) -> bool:
        """
        Check if a time slot is available

        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM AM/PM format
            duration: Required duration in minutes

        Returns:
            True if available, False otherwise
        """
        try:
            # Parse requested datetime
            requested_dt = self._parse_datetime(date, time)
            if not requested_dt:
                return False

            requested_end = requested_dt + timedelta(minutes=duration)

            # Check against existing appointments
            for appointment in self.appointments.values():
                if appointment.status == "cancelled":
                    continue

                # Parse existing appointment datetime
                existing_dt = self._parse_datetime(appointment.date, appointment.time)
                if not existing_dt:
                    continue

                existing_end = existing_dt + timedelta(minutes=appointment.duration)

                # Check for overlap (including buffer time)
                buffer = timedelta(minutes=self.buffer_time)
                if (requested_dt < existing_end + buffer and
                    requested_end + buffer > existing_dt):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return False

    def get_available_slots(self, date: str, duration: int = 60) -> Dict[str, Any]:
        """
        Get all available time slots for a given date

        Args:
            date: Date in YYYY-MM-DD format
            duration: Required duration in minutes

        Returns:
            List of available time slots
        """
        try:
            # Validate date
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid date format. Use YYYY-MM-DD"
                }

            # Check if date is in the past
            if target_date < datetime.now().date():
                return {
                    "success": False,
                    "message": "Cannot book appointments in the past"
                }

            # Get business hours for the day
            day_name = target_date.strftime("%A").lower()
            if day_name not in self.business_hours:
                return {
                    "success": False,
                    "message": f"No business hours defined for {day_name}"
                }

            day_hours = self.business_hours[day_name]
            if day_hours.get("closed"):
                return {
                    "success": True,
                    "available_slots": [],
                    "message": f"Closed on {day_name.title()}"
                }

            # Generate time slots
            available_slots = []
            start_time = datetime.strptime(day_hours["start"], "%H:%M").time()
            end_time = datetime.strptime(day_hours["end"], "%H:%M").time()

            current_time = datetime.combine(target_date, start_time)
            end_datetime = datetime.combine(target_date, end_time)

            while current_time + timedelta(minutes=duration) <= end_datetime:
                time_str = current_time.strftime("%I:%M %p")

                if self.check_availability(date, time_str, duration):
                    available_slots.append({
                        "time": time_str,
                        "datetime": current_time.isoformat(),
                        "duration": duration
                    })

                current_time += timedelta(minutes=self.slot_duration)

            return {
                "success": True,
                "date": date,
                "available_slots": available_slots,
                "total_slots": len(available_slots)
            }

        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get available slots: {str(e)}"
            }

    def reschedule_appointment(self, appointment_id: str, new_date: str,
                             new_time: str) -> Dict[str, Any]:
        """
        Reschedule an existing appointment

        Args:
            appointment_id: Unique appointment identifier
            new_date: New date in YYYY-MM-DD format
            new_time: New time in HH:MM AM/PM format

        Returns:
            Reschedule result
        """
        try:
            if appointment_id not in self.appointments:
                return {
                    "success": False,
                    "message": f"Appointment {appointment_id} not found"
                }

            appointment = self.appointments[appointment_id]

            # Store old details
            old_date = appointment.date
            old_time = appointment.time

            # Check new slot availability
            if not self.check_availability(new_date, new_time, appointment.duration):
                return {
                    "success": False,
                    "message": f"New time slot {new_date} at {new_time} is not available"
                }

            # Update appointment
            appointment.date = new_date
            appointment.time = new_time
            appointment.updated_at = datetime.utcnow().isoformat()
            appointment.reminder_sent = False  # Reset reminder flag

            logger.info(f"Appointment rescheduled: {appointment_id} from {old_date} {old_time} to {new_date} {new_time}")

            return {
                "success": True,
                "appointment_id": appointment_id,
                "message": f"Appointment rescheduled from {old_date} {old_time} to {new_date} {new_time}",
                "old_datetime": f"{old_date} {old_time}",
                "new_datetime": f"{new_date} {new_time}"
            }

        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to reschedule appointment: {str(e)}"
            }

    def cancel_appointment(self, appointment_id: str, reason: str = None) -> Dict[str, Any]:
        """
        Cancel an appointment

        Args:
            appointment_id: Unique appointment identifier
            reason: Cancellation reason (optional)

        Returns:
            Cancellation result
        """
        try:
            if appointment_id not in self.appointments:
                return {
                    "success": False,
                    "message": f"Appointment {appointment_id} not found"
                }

            appointment = self.appointments[appointment_id]
            appointment.status = "cancelled"
            appointment.updated_at = datetime.utcnow().isoformat()

            if reason:
                appointment.notes.append(f"Cancelled: {reason}")

            logger.info(f"Appointment cancelled: {appointment_id} - {reason or 'No reason provided'}")

            return {
                "success": True,
                "appointment_id": appointment_id,
                "message": f"Appointment cancelled for {appointment.name} on {appointment.date} at {appointment.time}",
                "reason": reason
            }

        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to cancel appointment: {str(e)}"
            }

    def get_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Get appointment details

        Args:
            appointment_id: Unique appointment identifier

        Returns:
            Appointment details or error
        """
        try:
            if appointment_id not in self.appointments:
                return {
                    "success": False,
                    "message": f"Appointment {appointment_id} not found"
                }

            appointment = self.appointments[appointment_id]

            return {
                "success": True,
                "appointment": {
                    "id": appointment.id,
                    "name": appointment.name,
                    "phone": appointment.phone,
                    "email": appointment.email,
                    "date": appointment.date,
                    "time": appointment.time,
                    "service": appointment.service,
                    "duration": appointment.duration,
                    "status": appointment.status,
                    "notes": appointment.notes,
                    "created_at": appointment.created_at,
                    "updated_at": appointment.updated_at,
                    "reminder_sent": appointment.reminder_sent
                }
            }

        except Exception as e:
            logger.error(f"Error getting appointment: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get appointment: {str(e)}"
            }

    def get_appointments_by_date(self, date: str) -> Dict[str, Any]:
        """
        Get all appointments for a specific date

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            List of appointments for the date
        """
        try:
            appointments = []

            for appointment in self.appointments.values():
                if appointment.date == date and appointment.status != "cancelled":
                    appointments.append({
                        "id": appointment.id,
                        "name": appointment.name,
                        "phone": appointment.phone,
                        "time": appointment.time,
                        "service": appointment.service,
                        "duration": appointment.duration,
                        "status": appointment.status
                    })

            # Sort by time
            appointments.sort(key=lambda x: datetime.strptime(x["time"], "%I:%M %p"))

            return {
                "success": True,
                "date": date,
                "appointments": appointments,
                "count": len(appointments)
            }

        except Exception as e:
            logger.error(f"Error getting appointments by date: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get appointments: {str(e)}"
            }

    def _validate_datetime(self, date: str, time: str) -> Dict[str, Any]:
        """Validate date and time format"""
        try:
            # Validate date format
            target_date = datetime.strptime(date, "%Y-%m-%d").date()

            # Check if date is in the past
            if target_date < datetime.now().date():
                return {
                    "valid": False,
                    "message": "Cannot book appointments in the past"
                }

            # Validate time format
            try:
                datetime.strptime(time, "%I:%M %p")
            except ValueError:
                return {
                    "valid": False,
                    "message": "Invalid time format. Use HH:MM AM/PM (e.g., 02:30 PM)"
                }

            return {"valid": True}

        except ValueError:
            return {
                "valid": False,
                "message": "Invalid date format. Use YYYY-MM-DD"
            }

    def _parse_datetime(self, date: str, time: str) -> Optional[datetime]:
        """Parse date and time strings into datetime object"""
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            time_obj = datetime.strptime(time, "%I:%M %p").time()
            return datetime.combine(date_obj, time_obj)
        except ValueError:
            return None

    def _is_within_business_hours(self, date: str, time: str) -> bool:
        """Check if the requested time is within business hours"""
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            day_name = target_date.strftime("%A").lower()

            if day_name not in self.business_hours:
                return False

            day_hours = self.business_hours[day_name]
            if day_hours.get("closed"):
                return False

            requested_time = datetime.strptime(time, "%I:%M %p").time()
            start_time = datetime.strptime(day_hours["start"], "%H:%M").time()
            end_time = datetime.strptime(day_hours["end"], "%H:%M").time()

            return start_time <= requested_time <= end_time

        except (ValueError, KeyError):
            return False


# Global calendar instance
calendar_tool = CalendarTool()


# Convenience functions for agent integration
def book_appointment(name: str, phone: str, date: str, time: str,
                    service: str = None, email: str = None,
                    duration: int = 60) -> Dict[str, Any]:
    """Book a new appointment"""
    return calendar_tool.book_appointment(name, phone, date, time, service, email, duration)


def check_availability(date: str, time: str, duration: int = 60) -> bool:
    """Check if time slot is available"""
    return calendar_tool.check_availability(date, time, duration)


def get_available_slots(date: str, duration: int = 60) -> Dict[str, Any]:
    """Get available time slots for a date"""
    return calendar_tool.get_available_slots(date, duration)


def reschedule_appointment(appointment_id: str, new_date: str, new_time: str) -> Dict[str, Any]:
    """Reschedule an appointment"""
    return calendar_tool.reschedule_appointment(appointment_id, new_date, new_time)


def cancel_appointment(appointment_id: str, reason: str = None) -> Dict[str, Any]:
    """Cancel an appointment"""
    return calendar_tool.cancel_appointment(appointment_id, reason)


def get_appointment(appointment_id: str) -> Dict[str, Any]:
    """Get appointment details"""
    return calendar_tool.get_appointment(appointment_id)


def get_daily_schedule(date: str) -> Dict[str, Any]:
    """Get all appointments for a date"""
    return calendar_tool.get_appointments_by_date(date)
