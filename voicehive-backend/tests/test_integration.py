import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import asyncio

from app.main import app

client = TestClient(app)


class TestCriticalPaths:
    """Integration tests for critical application paths"""

    @pytest.mark.integration
    def test_complete_appointment_booking_flow(self, sample_function_call_data, mock_roxy_agent):
        """Test complete appointment booking flow from webhook to confirmation"""
        # Mock successful appointment booking
        mock_response = MagicMock()
        mock_response.dict.return_value = {
            "success": True,
            "message": "Appointment booked for John Doe on 2024-01-15 at 10:00 AM",
            "data": {
                "appointment_id": "apt_20240115_100000",
                "status": "confirmed"
            }
        }
        mock_roxy_agent.handle_function_call.return_value = mock_response
        
        # Send webhook request
        response = client.post("/webhook/vapi", json=sample_function_call_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert data["result"]["success"] is True
        assert "John Doe" in data["result"]["message"]
        
        # Verify agent was called correctly
        mock_roxy_agent.handle_function_call.assert_called_once()
        call_args = mock_roxy_agent.handle_function_call.call_args
        assert call_args[0][1] == "book_appointment"  # function name
        assert call_args[0][2]["name"] == "John Doe"  # parameters

    @pytest.mark.integration
    def test_conversation_flow_with_context(self, sample_vapi_webhook_data, mock_roxy_agent):
        """Test conversation flow maintains context across multiple messages"""
        call_id = sample_vapi_webhook_data["call"]["id"]
        
        # First message
        mock_roxy_agent.handle_message.return_value = "Hello! How can I help you today?"
        response1 = client.post("/webhook/vapi", json=sample_vapi_webhook_data)
        assert response1.status_code == 200
        
        # Second message in same conversation
        sample_vapi_webhook_data["message"]["content"] = "I need to book an appointment"
        mock_roxy_agent.handle_message.return_value = "I'd be happy to help you book an appointment. What date works for you?"
        response2 = client.post("/webhook/vapi", json=sample_vapi_webhook_data)
        assert response2.status_code == 200
        
        # Verify both calls used same call_id
        assert mock_roxy_agent.handle_message.call_count == 2
        call_args_1 = mock_roxy_agent.handle_message.call_args_list[0]
        call_args_2 = mock_roxy_agent.handle_message.call_args_list[1]
        assert call_args_1[0][0] == call_args_2[0][0] == call_id

    @pytest.mark.integration
    def test_error_handling_and_recovery(self, sample_vapi_webhook_data, mock_roxy_agent):
        """Test error handling and graceful recovery"""
        # Simulate agent error
        mock_roxy_agent.handle_message.side_effect = Exception("OpenAI API error")
        
        response = client.post("/webhook/vapi", json=sample_vapi_webhook_data)
        
        # Should still return 200 with error message
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "trouble processing" in data["message"].lower()
        assert "human agent" in data["message"].lower()

    @pytest.mark.integration
    def test_call_lifecycle_management(self, mock_roxy_agent):
        """Test complete call lifecycle from start to end"""
        call_id = "test-call-lifecycle"
        
        # 1. Initial message
        webhook_data = {
            "message": {"type": "message", "content": "Hello"},
            "call": {"id": call_id}
        }
        mock_roxy_agent.handle_message.return_value = "Hello! How can I help?"
        response = client.post("/webhook/vapi", json=webhook_data)
        assert response.status_code == 200
        
        # 2. Function call
        webhook_data["message"] = {
            "type": "function-call",
            "functionCall": {
                "name": "capture_lead",
                "parameters": {"name": "Test User", "phone": "+1234567890"}
            }
        }
        mock_response = MagicMock()
        mock_response.dict.return_value = {"success": True, "message": "Lead captured"}
        mock_roxy_agent.handle_function_call.return_value = mock_response
        response = client.post("/webhook/vapi", json=webhook_data)
        assert response.status_code == 200
        
        # 3. Transcript update
        webhook_data["message"] = {
            "type": "transcript",
            "transcript": "Complete conversation transcript"
        }
        mock_roxy_agent.handle_transcript_update.return_value = None
        response = client.post("/webhook/vapi", json=webhook_data)
        assert response.status_code == 200
        
        # 4. Call end
        webhook_data["message"] = {"type": "hang"}
        mock_roxy_agent.handle_call_end.return_value = None
        response = client.post("/webhook/vapi", json=webhook_data)
        assert response.status_code == 200
        
        # Verify all lifecycle methods were called
        mock_roxy_agent.handle_message.assert_called()
        mock_roxy_agent.handle_function_call.assert_called()
        mock_roxy_agent.handle_transcript_update.assert_called_with(call_id, "Complete conversation transcript")
        mock_roxy_agent.handle_call_end.assert_called_with(call_id)

    @pytest.mark.integration
    def test_concurrent_calls_handling(self, mock_roxy_agent):
        """Test handling multiple concurrent calls"""
        import threading
        import time
        
        results = []
        
        def make_request(call_id):
            webhook_data = {
                "message": {"type": "message", "content": f"Hello from {call_id}"},
                "call": {"id": call_id}
            }
            mock_roxy_agent.handle_message.return_value = f"Response to {call_id}"
            response = client.post("/webhook/vapi", json=webhook_data)
            results.append((call_id, response.status_code))
        
        # Create multiple threads for concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=[f"call-{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(results) == 5
        for call_id, status_code in results:
            assert status_code == 200

    @pytest.mark.integration
    def test_api_documentation_accessibility(self):
        """Test that API documentation is accessible"""
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.headers.get("content-type", "").lower() or "html" in response.headers.get("content-type", "").lower()
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()
        
        # Test OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
        
        # Verify OpenAPI structure
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data
        assert "/webhook/vapi" in openapi_data["paths"]

    @pytest.mark.integration
    def test_health_endpoints_monitoring(self):
        """Test health endpoints for monitoring systems"""
        # Root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "docs_url" in data
        
        # Health check endpoint
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        
        # Documentation info endpoint
        response = client.get("/docs-info")
        assert response.status_code == 200
        data = response.json()
        assert "swagger_ui" in data
        assert "redoc" in data
        assert "openapi_json" in data

    @pytest.mark.integration
    @pytest.mark.slow
    def test_webhook_payload_validation(self):
        """Test webhook payload validation with various invalid inputs"""
        invalid_payloads = [
            # Missing required fields
            {"message": {"type": "message"}},  # Missing call
            {"call": {"id": "test"}},  # Missing message
            
            # Invalid data types
            {"message": "invalid", "call": {"id": "test"}},
            {"message": {"type": "message"}, "call": "invalid"},
            
            # Empty payload
            {},
            
            # Invalid function call structure
            {
                "message": {
                    "type": "function-call",
                    "functionCall": "invalid"
                },
                "call": {"id": "test"}
            }
        ]
        
        for payload in invalid_payloads:
            response = client.post("/webhook/vapi", json=payload)
            # Should return 422 for validation errors
            assert response.status_code == 422, f"Failed for payload: {payload}"
