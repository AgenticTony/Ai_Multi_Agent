"""
Notification Tool - Enhanced SMS/email functionality with Twilio and SMTP integration
"""
import logging
import smtplib
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

# Twilio imports
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None
    TwilioException = Exception

logger = logging.getLogger(__name__)


@dataclass
class NotificationRecord:
    """Notification record data structure"""
    id: str
    recipient_phone: Optional[str] = None
    recipient_email: Optional[str] = None
    message: str = ""
    channels: List[str] = None
    status: str = "pending"
    sent_at: Optional[str] = None
    error_message: Optional[str] = None
    notification_type: str = "general"
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = []


class NotificationTool:
    """Enhanced notification functionality with real integrations"""
    
    def __init__(self):
        # Initialize Twilio client
        self.twilio_client = None
        if TWILIO_AVAILABLE:
            try:
                account_sid = os.getenv('TWILIO_ACCOUNT_SID')
                auth_token = os.getenv('TWILIO_AUTH_TOKEN')
                if account_sid and auth_token:
                    self.twilio_client = TwilioClient(account_sid, auth_token)
                    self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
                    logger.info("Twilio client initialized successfully")
                else:
                    logger.warning("Twilio credentials not found in environment")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
        
        # SMTP configuration
        self.smtp_config = {
            'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('SMTP_FROM_EMAIL'),
            'from_name': os.getenv('SMTP_FROM_NAME', 'VoiceHive')
        }
        
        # Notification history
        self.notifications: Dict[str, NotificationRecord] = {}
        
        # Message templates
        self.templates = {
            'appointment_confirmation': {
                'sms': "Hi {name}! Your appointment is confirmed for {date} at {time}. Reply STOP to opt out.",
                'email_subject': "Appointment Confirmation - {date} at {time}",
                'email_body': """
Dear {name},

Your appointment has been confirmed for:
Date: {date}
Time: {time}
Service: {service}

If you need to reschedule or cancel, please call us at {business_phone}.

Best regards,
{business_name}
"""
            },
            'appointment_reminder': {
                'sms': "Reminder: You have an appointment tomorrow at {time}. Reply STOP to opt out.",
                'email_subject': "Appointment Reminder - Tomorrow at {time}",
                'email_body': """
Dear {name},

This is a reminder that you have an appointment scheduled for:
Date: {date}
Time: {time}
Service: {service}

We look forward to seeing you!

Best regards,
{business_name}
"""
            },
            'appointment_cancelled': {
                'sms': "Your appointment for {date} at {time} has been cancelled. Call us to reschedule.",
                'email_subject': "Appointment Cancelled - {date} at {time}",
                'email_body': """
Dear {name},

Your appointment scheduled for {date} at {time} has been cancelled.

To reschedule, please call us at {business_phone} or visit our website.

Best regards,
{business_name}
"""
            }
        }
    
    def send_notification(self, phone: str = None, email: str = None, 
                         message: str = "", notification_type: str = "general",
                         template_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send notification via SMS and/or email
        
        Args:
            phone: Phone number for SMS
            email: Email address
            message: Message content (if not using template)
            notification_type: Type of notification for template selection
            template_data: Data for template rendering
            
        Returns:
            Notification sending result
        """
        try:
            if not phone and not email:
                return {
                    "success": False,
                    "message": "No valid contact method provided"
                }
            
            # Generate notification ID
            notification_id = f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Create notification record
            notification = NotificationRecord(
                id=notification_id,
                recipient_phone=phone,
                recipient_email=email,
                message=message,
                notification_type=notification_type
            )
            
            results = []
            
            # Send SMS if phone provided
            if phone:
                sms_result = self._send_sms(phone, message, notification_type, template_data)
                results.append(sms_result)
                if sms_result["success"]:
                    notification.channels.append("sms")
            
            # Send email if email provided
            if email:
                email_result = self._send_email(email, message, notification_type, template_data)
                results.append(email_result)
                if email_result["success"]:
                    notification.channels.append("email")
            
            # Update notification status
            if any(result["success"] for result in results):
                notification.status = "sent"
                notification.sent_at = datetime.utcnow().isoformat()
            else:
                notification.status = "failed"
                notification.error_message = "; ".join([r.get("error", "") for r in results if not r["success"]])
            
            # Store notification record
            self.notifications[notification_id] = notification
            
            success_count = sum(1 for result in results if result["success"])
            
            return {
                "success": success_count > 0,
                "notification_id": notification_id,
                "channels_sent": notification.channels,
                "total_channels": len(results),
                "successful_channels": success_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send notification: {str(e)}"
            }
    
    def _send_sms(self, phone: str, message: str, notification_type: str = "general",
                  template_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send SMS using Twilio"""
        try:
            if not self.twilio_client:
                logger.warning("Twilio client not available, simulating SMS send")
                return {
                    "success": True,
                    "channel": "sms",
                    "message": "SMS simulated (Twilio not configured)",
                    "recipient": phone
                }
            
            # Use template if available
            if notification_type in self.templates and template_data:
                template = self.templates[notification_type]
                if 'sms' in template:
                    message = template['sms'].format(**template_data)
            
            # Send SMS via Twilio
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=phone
            )
            
            logger.info(f"SMS sent successfully to {phone}, SID: {message_obj.sid}")
            
            return {
                "success": True,
                "channel": "sms",
                "message": "SMS sent successfully",
                "recipient": phone,
                "message_sid": message_obj.sid
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {phone}: {str(e)}")
            return {
                "success": False,
                "channel": "sms",
                "error": f"Twilio error: {str(e)}",
                "recipient": phone
            }
        except Exception as e:
            logger.error(f"Error sending SMS to {phone}: {str(e)}")
            return {
                "success": False,
                "channel": "sms",
                "error": str(e),
                "recipient": phone
            }
    
    def _send_email(self, email: str, message: str, notification_type: str = "general",
                    template_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send email using SMTP"""
        try:
            if not self.smtp_config['username'] or not self.smtp_config['password']:
                logger.warning("SMTP credentials not configured, simulating email send")
                return {
                    "success": True,
                    "channel": "email",
                    "message": "Email simulated (SMTP not configured)",
                    "recipient": email
                }
            
            # Prepare email content
            subject = "Notification from VoiceHive"
            body = message
            
            # Use template if available
            if notification_type in self.templates and template_data:
                template = self.templates[notification_type]
                if 'email_subject' in template:
                    subject = template['email_subject'].format(**template_data)
                if 'email_body' in template:
                    body = template['email_body'].format(**template_data)
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
            msg['To'] = email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {email}")
            
            return {
                "success": True,
                "channel": "email",
                "message": "Email sent successfully",
                "recipient": email,
                "subject": subject
            }
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {email}: {str(e)}")
            return {
                "success": False,
                "channel": "email",
                "error": f"SMTP error: {str(e)}",
                "recipient": email
            }
        except Exception as e:
            logger.error(f"Error sending email to {email}: {str(e)}")
            return {
                "success": False,
                "channel": "email",
                "error": str(e),
                "recipient": email
            }
    
    def send_appointment_confirmation(self, name: str, phone: str = None, 
                                    email: str = None, date: str = "", 
                                    time: str = "", service: str = "") -> Dict[str, Any]:
        """
        Send appointment confirmation notification
        
        Args:
            name: Customer name
            phone: Phone number
            email: Email address
            date: Appointment date
            time: Appointment time
            service: Service type
            
        Returns:
            Notification result
        """
        template_data = {
            'name': name,
            'date': date,
            'time': time,
            'service': service or 'Consultation',
            'business_phone': os.getenv('BUSINESS_PHONE', '(555) 123-4567'),
            'business_name': os.getenv('BUSINESS_NAME', 'VoiceHive')
        }
        
        return self.send_notification(
            phone=phone,
            email=email,
            notification_type='appointment_confirmation',
            template_data=template_data
        )
    
    def send_appointment_reminder(self, name: str, phone: str = None, 
                                email: str = None, date: str = "", 
                                time: str = "", service: str = "") -> Dict[str, Any]:
        """Send appointment reminder notification"""
        template_data = {
            'name': name,
            'date': date,
            'time': time,
            'service': service or 'Consultation',
            'business_phone': os.getenv('BUSINESS_PHONE', '(555) 123-4567'),
            'business_name': os.getenv('BUSINESS_NAME', 'VoiceHive')
        }
        
        return self.send_notification(
            phone=phone,
            email=email,
            notification_type='appointment_reminder',
            template_data=template_data
        )
    
    def send_cancellation_notice(self, name: str, phone: str = None, 
                               email: str = None, date: str = "", 
                               time: str = "", reason: str = "") -> Dict[str, Any]:
        """Send appointment cancellation notice"""
        template_data = {
            'name': name,
            'date': date,
            'time': time,
            'reason': reason,
            'business_phone': os.getenv('BUSINESS_PHONE', '(555) 123-4567'),
            'business_name': os.getenv('BUSINESS_NAME', 'VoiceHive')
        }
        
        return self.send_notification(
            phone=phone,
            email=email,
            notification_type='appointment_cancelled',
            template_data=template_data
        )
    
    def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Get notification status and details
        
        Args:
            notification_id: Unique notification identifier
            
        Returns:
            Notification status and details
        """
        try:
            if notification_id not in self.notifications:
                return {
                    "success": False,
                    "message": f"Notification {notification_id} not found"
                }
            
            notification = self.notifications[notification_id]
            
            return {
                "success": True,
                "notification": {
                    "id": notification.id,
                    "recipient_phone": notification.recipient_phone,
                    "recipient_email": notification.recipient_email,
                    "message": notification.message,
                    "channels": notification.channels,
                    "status": notification.status,
                    "sent_at": notification.sent_at,
                    "error_message": notification.error_message,
                    "notification_type": notification.notification_type
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting notification status: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get notification status: {str(e)}"
            }
    
    def get_notification_history(self, phone: str = None, email: str = None,
                               limit: int = 50) -> Dict[str, Any]:
        """
        Get notification history for a contact
        
        Args:
            phone: Filter by phone number
            email: Filter by email address
            limit: Maximum number of records to return
            
        Returns:
            Notification history
        """
        try:
            notifications = []
            
            for notification in self.notifications.values():
                # Filter by contact info if provided
                if phone and notification.recipient_phone != phone:
                    continue
                if email and notification.recipient_email != email:
                    continue
                
                notifications.append({
                    "id": notification.id,
                    "recipient_phone": notification.recipient_phone,
                    "recipient_email": notification.recipient_email,
                    "channels": notification.channels,
                    "status": notification.status,
                    "sent_at": notification.sent_at,
                    "notification_type": notification.notification_type
                })
            
            # Sort by sent_at (most recent first)
            notifications.sort(key=lambda x: x["sent_at"] or "", reverse=True)
            
            # Apply limit
            notifications = notifications[:limit]
            
            return {
                "success": True,
                "notifications": notifications,
                "count": len(notifications),
                "phone_filter": phone,
                "email_filter": email
            }
            
        except Exception as e:
            logger.error(f"Error getting notification history: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get notification history: {str(e)}"
            }


# Global notification instance
notification_tool = NotificationTool()


# Convenience functions for agent integration
def send_sms(phone: str, message: str) -> Dict[str, Any]:
    """Send SMS notification"""
    return notification_tool.send_notification(phone=phone, message=message)


def send_email(email: str, message: str, subject: str = None) -> Dict[str, Any]:
    """Send email notification"""
    return notification_tool.send_notification(email=email, message=message)


def send_confirmation(phone: str = None, email: str = None, name: str = "",
                     date: str = "", time: str = "", service: str = "") -> Dict[str, Any]:
    """Send appointment confirmation"""
    return notification_tool.send_appointment_confirmation(name, phone, email, date, time, service)


def send_reminder(phone: str = None, email: str = None, name: str = "",
                 date: str = "", time: str = "", service: str = "") -> Dict[str, Any]:
    """Send appointment reminder"""
    return notification_tool.send_appointment_reminder(name, phone, email, date, time, service)


def send_cancellation(phone: str = None, email: str = None, name: str = "",
                     date: str = "", time: str = "", reason: str = "") -> Dict[str, Any]:
    """Send cancellation notice"""
    return notification_tool.send_cancellation_notice(name, phone, email, date, time, reason)


def get_notification_status(notification_id: str) -> Dict[str, Any]:
    """Get notification status"""
    return notification_tool.get_notification_status(notification_id)
