import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data
    assert data["status"] == "healthy"


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


@patch('app.routers.vapi.roxy')
def test_vapi_webhook_message(mock_roxy):
    """Test Vapi webhook with a message"""
    # Mock the agent response
    mock_roxy.handle_message.return_value = "Hello! How can I help you?"
    
    # Test data
    webhook_data = {
        "message": {
            "type": "message",
            "content": "Hello"
        },
        "call": {
            "id": "test-call-123"
        }
    }
    
    response = client.post("/webhook/vapi", json=webhook_data)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@patch('app.routers.vapi.roxy')
def test_vapi_webhook_function_call(mock_roxy):
    """Test Vapi webhook with a function call"""
    # Mock the agent response
    mock_response = MagicMock()
    mock_response.dict.return_value = {
        "success": True,
        "message": "Appointment booked"
    }
    mock_roxy.handle_function_call.return_value = mock_response
    
    # Test data
    webhook_data = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "book_appointment",
                "parameters": {
                    "name": "John Doe",
                    "phone": "+1234567890",
                    "date": "2024-01-15",
                    "time": "10:00 AM"
                }
            }
        },
        "call": {
            "id": "test-call-123"
        }
    }
    
    response = client.post("/webhook/vapi", json=webhook_data)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data


def test_vapi_webhook_invalid_data():
    """Test Vapi webhook with invalid data"""
    # Missing required fields
    webhook_data = {
        "message": {
            "type": "message"
        }
        # Missing call field
    }
    
    response = client.post("/webhook/vapi", json=webhook_data)
    assert response.status_code == 422  # Validation error
