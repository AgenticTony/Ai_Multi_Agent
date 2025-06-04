"""
Integration tests for VAPI webhook endpoints
Tests the complete flow from webhook to response
"""

import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from hypothesis import given, strategies as st
from hypothesis.strategies import text, integers, composite

from voicehive.main import app
from voicehive.models.vapi import VapiWebhookRequest, VapiWebhookResponse


@composite
def vapi_webhook_data(draw):
    """Generate valid VAPI webhook data using Hypothesis"""
    call_id = draw(text(min_size=10, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"))
    message_types = ["function-call", "transcript", "hang", "conversation"]
    message_type = draw(st.sampled_from(message_types))
    
    base_data = {
        "call": {"id": call_id},
        "message": {"type": message_type}
    }
    
    if message_type == "function-call":
        function_names = ["book_appointment", "capture_lead", "send_confirmation", "transfer_call"]
        base_data["message"]["functionCall"] = {
            "name": draw(st.sampled_from(function_names)),
            "parameters": {
                "name": draw(text(min_size=2, max_size=50)),
                "phone": draw(text(min_size=10, max_size=15, alphabet="0123456789")),
            }
        }
    elif message_type == "transcript":
        base_data["message"]["transcript"] = draw(text(min_size=1, max_size=500))
    elif message_type == "conversation":
        base_data["message"]["content"] = draw(text(min_size=1, max_size=200))
    
    return base_data


class TestVapiIntegration:
    """Integration tests for VAPI webhook handling"""
    
    @pytest.fixture
    async def client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    def mock_roxy_agent(self):
        """Mock Roxy agent for testing"""
        with patch('voicehive.api.v1.endpoints.vapi.roxy') as mock:
            mock.handle_message = AsyncMock(return_value="Hello! How can I help you?")
            mock.handle_function_call = AsyncMock()
            mock.handle_transcript_update = AsyncMock()
            mock.handle_call_end = AsyncMock()
            yield mock
    
    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "voicehive-api"
    
    async def test_vapi_webhook_conversation_message(self, client, mock_roxy_agent):
        """Test handling conversation messages"""
        webhook_data = {
            "call": {"id": "test-call-123"},
            "message": {
                "type": "conversation",
                "content": "Hello, I need help"
            }
        }
        
        response = await client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        mock_roxy_agent.handle_message.assert_called_once_with("test-call-123", "Hello, I need help")
    
    async def test_vapi_webhook_function_call(self, client, mock_roxy_agent):
        """Test handling function calls"""
        from voicehive.models.vapi import FunctionCallResponse
        
        mock_roxy_agent.handle_function_call.return_value = FunctionCallResponse(
            success=True,
            message="Appointment booked successfully",
            data={"appointment_id": "apt-123"}
        )
        
        webhook_data = {
            "call": {"id": "test-call-456"},
            "message": {
                "type": "function-call",
                "functionCall": {
                    "name": "book_appointment",
                    "parameters": {
                        "name": "John Doe",
                        "phone": "1234567890",
                        "date": "2024-01-15",
                        "time": "10:00"
                    }
                }
            }
        }
        
        response = await client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "result" in data
        mock_roxy_agent.handle_function_call.assert_called_once()
    
    async def test_vapi_webhook_transcript_update(self, client, mock_roxy_agent):
        """Test handling transcript updates"""
        webhook_data = {
            "call": {"id": "test-call-789"},
            "message": {
                "type": "transcript",
                "transcript": "Customer said: I want to book an appointment"
            }
        }
        
        response = await client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "transcript_received"
        mock_roxy_agent.handle_transcript_update.assert_called_once_with(
            "test-call-789", 
            "Customer said: I want to book an appointment"
        )
    
    async def test_vapi_webhook_call_end(self, client, mock_roxy_agent):
        """Test handling call end"""
        webhook_data = {
            "call": {"id": "test-call-end"},
            "message": {"type": "hang"}
        }
        
        response = await client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "call_ended"
        mock_roxy_agent.handle_call_end.assert_called_once_with("test-call-end")
    
    @given(vapi_webhook_data())
    async def test_vapi_webhook_property_based(self, client, mock_roxy_agent, webhook_data):
        """Property-based test for VAPI webhook handling"""
        # Ensure mock returns appropriate responses
        mock_roxy_agent.handle_message.return_value = "Test response"
        
        from voicehive.models.vapi import FunctionCallResponse
        mock_roxy_agent.handle_function_call.return_value = FunctionCallResponse(
            success=True,
            message="Function executed",
            data={}
        )
        
        response = await client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
        
        # Should always return 200 for valid webhook data
        assert response.status_code == 200
        
        # Response should always be valid JSON
        data = response.json()
        assert isinstance(data, dict)
        
        # Should have appropriate response fields based on message type
        message_type = webhook_data["message"]["type"]
        if message_type == "function-call":
            assert "result" in data
        elif message_type == "transcript":
            assert data.get("status") == "transcript_received"
        elif message_type == "hang":
            assert data.get("status") == "call_ended"
        else:
            assert "message" in data
    
    async def test_vapi_webhook_invalid_data(self, client):
        """Test handling invalid webhook data"""
        invalid_data = {"invalid": "data"}
        
        response = await client.post("/api/v1/vapi/webhook/vapi", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    async def test_vapi_webhook_missing_function_call_data(self, client, mock_roxy_agent):
        """Test handling function call without function data"""
        webhook_data = {
            "call": {"id": "test-call-error"},
            "message": {
                "type": "function-call"
                # Missing functionCall data
            }
        }
        
        response = await client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
        assert response.status_code == 400
    
    async def test_vapi_webhook_agent_error(self, client, mock_roxy_agent):
        """Test handling agent errors"""
        from voicehive.utils.exceptions import AgentError
        
        mock_roxy_agent.handle_message.side_effect = AgentError("Test agent error")
        
        webhook_data = {
            "call": {"id": "test-call-error"},
            "message": {
                "type": "conversation",
                "content": "Test message"
            }
        }
        
        response = await client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "transfer" in data["message"].lower() or "human agent" in data["message"].lower()
    
    async def test_concurrent_webhook_requests(self, client, mock_roxy_agent):
        """Test handling concurrent webhook requests"""
        webhook_data = {
            "call": {"id": "concurrent-test"},
            "message": {
                "type": "conversation",
                "content": "Concurrent test"
            }
        }
        
        # Simulate concurrent requests
        tasks = []
        for i in range(10):
            task = client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Agent should be called for each request
        assert mock_roxy_agent.handle_message.call_count == 10


class TestVapiPerformance:
    """Performance tests for VAPI endpoints"""
    
    @pytest.fixture
    async def client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    def mock_roxy_agent(self):
        """Mock Roxy agent for performance testing"""
        with patch('voicehive.api.v1.endpoints.vapi.roxy') as mock:
            mock.handle_message = AsyncMock(return_value="Quick response")
            yield mock
    
    @pytest.mark.performance
    async def test_webhook_response_time(self, client, mock_roxy_agent):
        """Test webhook response time is under 200ms"""
        import time
        
        webhook_data = {
            "call": {"id": "perf-test"},
            "message": {
                "type": "conversation",
                "content": "Performance test message"
            }
        }
        
        start_time = time.time()
        response = await client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert response_time < 200, f"Response time {response_time}ms exceeds 200ms threshold"
    
    @pytest.mark.performance
    async def test_webhook_throughput(self, client, mock_roxy_agent):
        """Test webhook can handle multiple requests per second"""
        import time
        
        webhook_data = {
            "call": {"id": "throughput-test"},
            "message": {
                "type": "conversation",
                "content": "Throughput test"
            }
        }
        
        # Send 50 requests and measure time
        start_time = time.time()
        tasks = []
        for i in range(50):
            task = client.post("/api/v1/vapi/webhook/vapi", json=webhook_data)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Should handle at least 25 requests per second
        total_time = end_time - start_time
        throughput = 50 / total_time
        assert throughput >= 25, f"Throughput {throughput} req/s is below 25 req/s threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
