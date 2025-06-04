import logging
from datetime import datetime
from typing import Dict, Any

from app.models.vapi import ConfirmationRequest
from app.config.settings import settings
from app.utils.exceptions import NotificationServiceError

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling notifications (SMS, email, etc.)"""
    
    def __init__(self):
        # In Sprint 2, this would integrate with actual notification services
        # For now, we'll simulate sending notifications
        self.sent_notifications = {}
        
    async def send_confirmation(self, confirmation_request: ConfirmationRequest) -> Dict[str, Any]:
        """
        Send confirmation via SMS and/or email
        
        Args:
            confirmation_request: Validated confirmation request
            
        Returns:
            Confirmation sending result
        """
        try:
            notification_id = f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            results = []
            
            # Send SMS if phone number provided
            if confirmation_request.phone:
                sms_result = await self._send_sms(
                    confirmation_request.phone, 
                    confirmation_request.message
                )
                results.append(sms_result)
            
            # Send email if email address provided
            if confirmation_request.email:
                email_result = await self._send_email(
                    confirmation_request.email, 
                    confirmation_request.message
                )
                results.append(email_result)
            
            if not results:
                raise NotificationServiceError("No valid contact method provided")
            
            # Store notification record
            notification_data = {
                "id": notification_id,
                "phone": confirmation_request.phone,
                "email": confirmation_request.email,
                "message": confirmation_request.message,
                "results": results,
                "sent_at": datetime.utcnow().isoformat()
            }
            
            self.sent_notifications[notification_id] = notification_data
            
            logger.info(f"Confirmation sent: {notification_id}")
            
            return {
                "notification_id": notification_id,
                "status": "sent",
                "channels": [r["channel"] for r in results if r["success"]],
                "message": "Confirmation sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Error sending confirmation: {str(e)}")
            raise NotificationServiceError(f"Failed to send confirmation: {str(e)}")
    
    async def _send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """
        Send SMS notification
        
        Args:
            phone: Phone number
            message: Message content
            
        Returns:
            SMS sending result
        """
        try:
            # In a real implementation, this would use Twilio or similar service
            # For now, we'll simulate the SMS sending
            
            logger.info(f"Simulating SMS to {phone}: {message}")
            
            # Simulate success/failure based on phone number format
            success = phone.startswith('+') and len(phone) >= 10
            
            return {
                "channel": "sms",
                "recipient": phone,
                "success": success,
                "message_id": f"sms_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if success else None,
                "error": None if success else "Invalid phone number format"
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS to {phone}: {str(e)}")
            return {
                "channel": "sms",
                "recipient": phone,
                "success": False,
                "message_id": None,
                "error": str(e)
            }
    
    async def _send_email(self, email: str, message: str) -> Dict[str, Any]:
        """
        Send email notification
        
        Args:
            email: Email address
            message: Message content
            
        Returns:
            Email sending result
        """
        try:
            # In a real implementation, this would use SendGrid, AWS SES, or SMTP
            # For now, we'll simulate the email sending
            
            logger.info(f"Simulating email to {email}: {message}")
            
            # Simulate success/failure based on email format
            success = '@' in email and '.' in email.split('@')[1]
            
            return {
                "channel": "email",
                "recipient": email,
                "success": success,
                "message_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if success else None,
                "error": None if success else "Invalid email address format"
            }
            
        except Exception as e:
            logger.error(f"Error sending email to {email}: {str(e)}")
            return {
                "channel": "email",
                "recipient": email,
                "success": False,
                "message_id": None,
                "error": str(e)
            }
    
    async def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Get notification status
        
        Args:
            notification_id: Unique notification identifier
            
        Returns:
            Notification status
        """
        try:
            notification = self.sent_notifications.get(notification_id)
            if not notification:
                raise NotificationServiceError(f"Notification {notification_id} not found")
            
            return notification
            
        except Exception as e:
            logger.error(f"Error getting notification status {notification_id}: {str(e)}")
            raise NotificationServiceError(f"Failed to get notification status: {str(e)}")
    
    async def send_appointment_reminder(self, phone: str, email: str, appointment_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send appointment reminder
        
        Args:
            phone: Phone number
            email: Email address
            appointment_details: Appointment information
            
        Returns:
            Reminder sending result
        """
        try:
            message = f"Reminder: You have an appointment scheduled for {appointment_details['date']} at {appointment_details['time']}. Please call if you need to reschedule."
            
            confirmation_request = ConfirmationRequest(
                phone=phone,
                email=email,
                message=message
            )
            
            return await self.send_confirmation(confirmation_request)
            
        except Exception as e:
            logger.error(f"Error sending appointment reminder: {str(e)}")
            raise NotificationServiceError(f"Failed to send appointment reminder: {str(e)}")
