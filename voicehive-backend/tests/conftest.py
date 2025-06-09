import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os

from voicehive.main import app
from voicehive.core.settings import Settings


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return Settings(
        secret_key="test-secret-key",
        openai_api_key="test-openai-key",
        vapi_api_key="test-vapi-key",
        environment="test",
        log_level="DEBUG"
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch('app.services.openai_service.OpenAI') as mock:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_vapi_webhook_data():
    """Sample Vapi webhook data for testing"""
    return {
        "message": {
            "type": "message",
            "content": "Hello, I need help"
        },
        "call": {
            "id": "test-call-123",
            "phoneNumber": "+1234567890",
            "status": "active"
        }
    }


@pytest.fixture
def sample_function_call_data():
    """Sample function call data for testing"""
    return {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "book_appointment",
                "parameters": {
                    "name": "John Doe",
                    "phone": "+1234567890",
                    "date": "2024-01-15",
                    "time": "10:00 AM",
                    "service": "consultation"
                }
            }
        },
        "call": {
            "id": "test-call-456",
            "phoneNumber": "+1234567890",
            "status": "active"
        }
    }


@pytest.fixture
def sample_appointment_request():
    """Sample appointment request for testing"""
    return {
        "name": "Jane Smith",
        "phone": "+1987654321",
        "date": "2024-02-01",
        "time": "2:00 PM",
        "service": "consultation"
    }


@pytest.fixture
def sample_lead_request():
    """Sample lead capture request for testing"""
    return {
        "name": "Bob Johnson",
        "phone": "+1555123456",
        "email": "bob@example.com",
        "interest": "Enterprise solution for our company"
    }


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    test_env = {
        "SECRET_KEY": "test-secret-key",
        "OPENAI_API_KEY": "test-openai-key",
        "VAPI_API_KEY": "test-vapi-key",
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG"
    }
    
    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def mock_roxy_agent():
    """Mock Roxy agent for testing"""
    with patch('app.routers.vapi.roxy') as mock:
        mock.handle_message.return_value = "Hello! How can I help you?"
        mock.handle_function_call.return_value = MagicMock(
            success=True,
            message="Function executed successfully",
            data={"result": "success"}
        )
        mock.handle_transcript_update.return_value = None
        mock.handle_call_end.return_value = None
        yield mock


@pytest.fixture
def mock_appointment_service():
    """Mock appointment service for testing"""
    with patch('app.services.integrations.appointment_service.AppointmentService') as mock:
        mock_instance = MagicMock()
        mock_instance.book_appointment.return_value = {
            "appointment_id": "apt_20240115_100000",
            "status": "confirmed",
            "message": "Appointment confirmed"
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_lead_service():
    """Mock lead service for testing"""
    with patch('app.services.integrations.lead_service.LeadService') as mock:
        mock_instance = MagicMock()
        mock_instance.capture_lead.return_value = {
            "lead_id": "lead_20240115_100000",
            "status": "captured",
            "score": 70,
            "message": "Lead captured successfully"
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_notification_service():
    """Mock notification service for testing"""
    with patch('app.services.integrations.notification_service.NotificationService') as mock:
        mock_instance = MagicMock()
        mock_instance.send_confirmation.return_value = {
            "notification_id": "notif_20240115_100000",
            "status": "sent",
            "channels": ["sms", "email"],
            "message": "Confirmation sent successfully"
        }
        mock.return_value = mock_instance
        yield mock_instance
