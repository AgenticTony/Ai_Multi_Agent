import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.agents.roxy_agent import RoxyAgent
from app.services.integrations.appointment_service import AppointmentService
from app.services.integrations.lead_service import LeadService
from app.services.integrations.notification_service import NotificationService
from app.models.vapi import (
    AppointmentRequest,
    LeadCaptureRequest,
    ConfirmationRequest,
    ConversationMessage
)


class TestRoxyAgent:
    """Test cases for RoxyAgent"""

    @pytest.fixture
    def roxy_agent(self, mock_openai_client):
        """Create RoxyAgent instance with mocked dependencies"""
        with patch('app.services.agents.roxy_agent.OpenAIService'), \
             patch('app.services.agents.roxy_agent.AppointmentService'), \
             patch('app.services.agents.roxy_agent.LeadService'), \
             patch('app.services.agents.roxy_agent.NotificationService'):
            return RoxyAgent()

    @pytest.mark.asyncio
    async def test_handle_message_empty(self, roxy_agent):
        """Test handling empty message"""
        response = await roxy_agent.handle_message("test-call", "")
        assert "Hello! I'm Roxy" in response

    @pytest.mark.asyncio
    async def test_handle_message_with_content(self, roxy_agent):
        """Test handling message with content"""
        with patch.object(roxy_agent.openai_service, 'generate_response', 
                         return_value="I can help you with that!"):
            response = await roxy_agent.handle_message("test-call", "I need help")
            assert response == "I can help you with that!"

    @pytest.mark.asyncio
    async def test_handle_function_call_book_appointment(self, roxy_agent):
        """Test booking appointment function call"""
        mock_result = {
            "appointment_id": "apt_123",
            "status": "confirmed"
        }
        roxy_agent.appointment_service.book_appointment = AsyncMock(return_value=mock_result)
        
        parameters = {
            "name": "John Doe",
            "phone": "+1234567890",
            "date": "2024-01-15",
            "time": "10:00 AM"
        }
        
        response = await roxy_agent.handle_function_call("test-call", "book_appointment", parameters)
        assert response.success is True
        assert "John Doe" in response.message

    @pytest.mark.asyncio
    async def test_handle_function_call_unknown(self, roxy_agent):
        """Test unknown function call"""
        response = await roxy_agent.handle_function_call("test-call", "unknown_function", {})
        assert response.success is False
        assert "Unknown function" in response.message

    def test_conversation_history_management(self, roxy_agent):
        """Test conversation history is properly managed"""
        call_id = "test-call"
        
        # Initially empty
        history = roxy_agent._get_conversation_history(call_id)
        assert len(history) == 0
        
        # Add messages
        messages = [
            ConversationMessage(role="user", content="Hello"),
            ConversationMessage(role="assistant", content="Hi there!")
        ]
        roxy_agent._update_conversation_history(call_id, messages)
        
        # Check history
        history = roxy_agent._get_conversation_history(call_id)
        assert len(history) == 2
        assert history[0].content == "Hello"


class TestAppointmentService:
    """Test cases for AppointmentService"""

    @pytest.fixture
    def appointment_service(self):
        """Create AppointmentService instance"""
        return AppointmentService()

    @pytest.mark.asyncio
    async def test_book_appointment_success(self, appointment_service):
        """Test successful appointment booking"""
        request = AppointmentRequest(
            name="John Doe",
            phone="+1234567890",
            date="2024-01-15",
            time="10:00 AM"
        )
        
        result = await appointment_service.book_appointment(request)
        
        assert result["status"] == "confirmed"
        assert "appointment_id" in result
        assert "John Doe" in result["message"]

    @pytest.mark.asyncio
    async def test_check_availability(self, appointment_service):
        """Test availability checking"""
        # Available slot
        available = await appointment_service.check_availability("2024-01-20", "3:00 PM")
        assert available is True
        
        # Unavailable slot (from demo data)
        unavailable = await appointment_service.check_availability("2024-01-15", "10:00 AM")
        assert unavailable is False

    @pytest.mark.asyncio
    async def test_get_appointment(self, appointment_service):
        """Test getting appointment details"""
        # First book an appointment
        request = AppointmentRequest(
            name="Jane Smith",
            phone="+1987654321",
            date="2024-02-01",
            time="2:00 PM"
        )
        
        booking_result = await appointment_service.book_appointment(request)
        appointment_id = booking_result["appointment_id"]
        
        # Then retrieve it
        appointment = await appointment_service.get_appointment(appointment_id)
        assert appointment["name"] == "Jane Smith"
        assert appointment["status"] == "confirmed"


class TestLeadService:
    """Test cases for LeadService"""

    @pytest.fixture
    def lead_service(self):
        """Create LeadService instance"""
        return LeadService()

    @pytest.mark.asyncio
    async def test_capture_lead_success(self, lead_service):
        """Test successful lead capture"""
        request = LeadCaptureRequest(
            name="Bob Johnson",
            phone="+1555123456",
            email="bob@example.com",
            interest="Enterprise solution"
        )
        
        result = await lead_service.capture_lead(request)
        
        assert result["status"] == "captured"
        assert "lead_id" in result
        assert result["score"] > 0

    def test_lead_score_calculation(self, lead_service):
        """Test lead scoring algorithm"""
        # Lead with email and high-value keywords
        request_high = LeadCaptureRequest(
            name="Enterprise Client",
            phone="+1234567890",
            email="client@enterprise.com",
            interest="Urgent enterprise business solution needed ASAP"
        )
        score_high = lead_service._calculate_lead_score(request_high)
        
        # Lead with just phone
        request_low = LeadCaptureRequest(
            name="Basic User",
            phone="+1234567890"
        )
        score_low = lead_service._calculate_lead_score(request_low)
        
        assert score_high > score_low
        assert score_high <= 100
        assert score_low >= 0

    @pytest.mark.asyncio
    async def test_search_leads(self, lead_service):
        """Test lead search functionality"""
        # Capture some test leads
        leads = [
            LeadCaptureRequest(name="Alice Smith", phone="+1111111111", email="alice@test.com"),
            LeadCaptureRequest(name="Bob Jones", phone="+2222222222", email="bob@test.com"),
            LeadCaptureRequest(name="Charlie Brown", phone="+3333333333")
        ]
        
        for lead in leads:
            await lead_service.capture_lead(lead)
        
        # Search by name
        results = await lead_service.search_leads(query="Alice")
        assert results["count"] == 1
        assert results["leads"][0]["name"] == "Alice Smith"
        
        # Search by status
        results = await lead_service.search_leads(status="new")
        assert results["count"] == 3


class TestNotificationService:
    """Test cases for NotificationService"""

    @pytest.fixture
    def notification_service(self):
        """Create NotificationService instance"""
        return NotificationService()

    @pytest.mark.asyncio
    async def test_send_confirmation_sms_and_email(self, notification_service):
        """Test sending confirmation via SMS and email"""
        request = ConfirmationRequest(
            phone="+1234567890",
            email="test@example.com",
            message="Your appointment is confirmed"
        )
        
        result = await notification_service.send_confirmation(request)
        
        assert result["status"] == "sent"
        assert "notification_id" in result
        assert len(result["channels"]) == 2
        assert "sms" in result["channels"]
        assert "email" in result["channels"]

    @pytest.mark.asyncio
    async def test_send_confirmation_phone_only(self, notification_service):
        """Test sending confirmation via SMS only"""
        request = ConfirmationRequest(
            phone="+1234567890",
            message="Your appointment is confirmed"
        )
        
        result = await notification_service.send_confirmation(request)
        
        assert result["status"] == "sent"
        assert len(result["channels"]) == 1
        assert "sms" in result["channels"]

    @pytest.mark.asyncio
    async def test_send_confirmation_invalid_phone(self, notification_service):
        """Test sending confirmation with invalid phone"""
        request = ConfirmationRequest(
            phone="invalid-phone",
            message="Test message"
        )
        
        result = await notification_service.send_confirmation(request)
        
        # Should still return success but with no successful channels
        assert result["status"] == "sent"
        assert len(result["channels"]) == 0

    @pytest.mark.asyncio
    async def test_send_appointment_reminder(self, notification_service):
        """Test sending appointment reminder"""
        appointment_details = {
            "date": "2024-01-15",
            "time": "10:00 AM"
        }
        
        result = await notification_service.send_appointment_reminder(
            phone="+1234567890",
            email="test@example.com",
            appointment_details=appointment_details
        )
        
        assert result["status"] == "sent"
        assert "notification_id" in result
