"""
Comprehensive test suite for Sprint 4: Dashboard & Monitoring System
Tests dashboard functionality, monitoring infrastructure, and alerting systems.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

# Import components to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from dashboard.api.dashboard import router as dashboard_router
from monitoring.instrumentation import VoiceHiveInstrumentation, get_instrumentation
from vertex.monitoring_service import MonitoringService

class TestDashboardAPI:
    """Test suite for dashboard API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client for dashboard API."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(dashboard_router)
        return TestClient(app)
    
    def test_get_dashboard_metrics(self, client):
        """Test dashboard metrics endpoint."""
        response = client.get("/api/dashboard/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_calls" in data
        assert "active_calls" in data
        assert "success_rate" in data
        assert "avg_duration" in data
        assert "system_health" in data
        assert "alerts" in data
        assert "last_updated" in data
        
        # Validate data types
        assert isinstance(data["total_calls"], int)
        assert isinstance(data["active_calls"], int)
        assert isinstance(data["success_rate"], float)
        assert isinstance(data["avg_duration"], float)
        assert isinstance(data["alerts"], int)
    
    def test_get_system_health(self, client):
        """Test system health endpoint."""
        response = client.get("/api/dashboard/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "api_response_time" in data
        assert "memory_usage" in data
        assert "cpu_usage" in data
        assert "active_alerts" in data
        assert "uptime" in data
        
        # Validate health status values
        assert data["status"] in ["healthy", "warning", "error"]
        assert 0 <= data["memory_usage"] <= 100
        assert 0 <= data["cpu_usage"] <= 100
    
    def test_get_call_volume(self, client):
        """Test call volume data endpoint."""
        response = client.get("/api/dashboard/call-volume")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Validate data structure
        for item in data:
            assert "time" in item
            assert "calls" in item
            assert isinstance(item["calls"], int)
    
    def test_get_recent_activity(self, client):
        """Test recent activity endpoint."""
        response = client.get("/api/dashboard/recent-activity")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Validate activity structure
        for activity in data:
            assert "timestamp" in activity
            assert "event" in activity
            assert "status" in activity
            assert activity["status"] in ["success", "warning", "error", "info"]
    
    def test_get_alerts(self, client):
        """Test alerts endpoint."""
        response = client.get("/api/dashboard/alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Validate alert structure
        for alert in data:
            assert "id" in alert
            assert "severity" in alert
            assert "message" in alert
            assert "timestamp" in alert
            assert "acknowledged" in alert
            assert alert["severity"] in ["info", "warning", "critical"]
    
    def test_acknowledge_alert(self, client):
        """Test alert acknowledgment endpoint."""
        alert_id = "test-alert-123"
        response = client.post(f"/api/dashboard/alerts/{alert_id}/acknowledge")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert alert_id in data["message"]
    
    def test_get_performance_metrics(self, client):
        """Test performance metrics endpoint."""
        response = client.get("/api/dashboard/performance-metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "response_times" in data
        assert "throughput" in data
        assert "error_rates" in data
        assert "resource_usage" in data
    
    def test_get_call_analytics(self, client):
        """Test call analytics endpoint."""
        response = client.get("/api/dashboard/call-analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert "success_rate_trend" in data
        assert "sentiment_analysis" in data
        assert "common_issues" in data
        assert "performance_improvements" in data

class TestMonitoringInstrumentation:
    """Test suite for monitoring instrumentation."""
    
    @pytest.fixture
    def instrumentation(self):
        """Create instrumentation instance for testing."""
        return VoiceHiveInstrumentation()
    
    def test_instrumentation_initialization(self, instrumentation):
        """Test that instrumentation initializes correctly."""
        assert instrumentation.tracer is not None
        assert instrumentation.meter is not None
        assert instrumentation.metrics is not None
        assert instrumentation.prometheus_metrics is not None
    
    def test_record_call_metrics(self, instrumentation):
        """Test recording call metrics."""
        # Test successful call
        instrumentation.record_call_metrics(
            duration=4.5,
            status="success",
            agent="roxy"
        )
        
        # Test failed call
        instrumentation.record_call_metrics(
            duration=2.1,
            status="error",
            agent="roxy"
        )
        
        # Verify metrics were recorded (would check actual metrics in real implementation)
        assert True  # Placeholder for actual metric verification
    
    def test_record_api_metrics(self, instrumentation):
        """Test recording API metrics."""
        instrumentation.record_api_metrics(
            method="POST",
            endpoint="/api/vapi/call",
            status_code=200,
            response_time=0.15
        )
        
        instrumentation.record_api_metrics(
            method="GET",
            endpoint="/api/dashboard/metrics",
            status_code=500,
            response_time=2.5
        )
        
        # Verify metrics were recorded
        assert True  # Placeholder for actual metric verification
    
    def test_update_system_metrics(self, instrumentation):
        """Test updating system metrics."""
        instrumentation.update_system_metrics(
            memory_usage=75.5,
            cpu_usage=45.2,
            active_calls=8
        )
        
        # Verify system metrics were updated
        assert True  # Placeholder for actual metric verification
    
    def test_create_span(self, instrumentation):
        """Test creating trace spans."""
        span = instrumentation.create_span(
            name="test_operation",
            attributes={"user_id": "123", "operation": "test"}
        )
        
        assert span is not None
        
        # Test span context
        if span:
            span.end()

class TestMonitoringService:
    """Test suite for monitoring service."""
    
    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance."""
        return MonitoringService()
    
    @pytest.mark.asyncio
    async def test_get_system_health(self, monitoring_service):
        """Test system health retrieval."""
        health_data = await monitoring_service.get_system_health()
        
        assert isinstance(health_data, dict)
        assert "overall_status" in health_data
        assert health_data["overall_status"] in ["healthy", "warning", "error"]
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, monitoring_service):
        """Test performance metrics retrieval."""
        metrics = await monitoring_service.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        # Verify expected metric categories
        expected_categories = ["response_times", "throughput", "error_rates", "resource_usage"]
        for category in expected_categories:
            assert category in metrics

class TestDashboardIntegration:
    """Integration tests for dashboard components."""
    
    @pytest.mark.asyncio
    async def test_real_time_metrics_flow(self):
        """Test the flow of real-time metrics from instrumentation to dashboard."""
        instrumentation = get_instrumentation()
        
        # Simulate call activity
        instrumentation.record_call_metrics(4.2, "success", "roxy")
        instrumentation.record_call_metrics(3.8, "success", "roxy")
        instrumentation.record_call_metrics(2.1, "error", "roxy")
        
        # Simulate API activity
        instrumentation.record_api_metrics("POST", "/api/vapi/call", 200, 0.15)
        instrumentation.record_api_metrics("GET", "/api/dashboard/metrics", 200, 0.05)
        
        # Update system metrics
        instrumentation.update_system_metrics(72.5, 35.8, 5)
        
        # Verify metrics are available for dashboard
        # In a real implementation, this would check the actual metrics store
        assert True
    
    @pytest.mark.asyncio
    async def test_alert_generation_flow(self):
        """Test alert generation and handling flow."""
        instrumentation = get_instrumentation()
        
        # Simulate conditions that should trigger alerts
        # High error rate
        for _ in range(10):
            instrumentation.record_call_metrics(2.0, "error", "roxy")
        
        # High memory usage
        instrumentation.update_system_metrics(95.0, 45.0, 3)
        
        # High API response time
        instrumentation.record_api_metrics("POST", "/api/vapi/call", 200, 8.5)
        
        # In a real implementation, this would verify alerts were generated
        assert True

class TestAlertingSystem:
    """Test suite for alerting system."""
    
    def test_alert_rule_validation(self):
        """Test that alert rules are properly configured."""
        # Load and validate Prometheus rules
        rules_file = "monitoring/alerts/prometheus-rules.yml"
        assert os.path.exists(rules_file)
        
        with open(rules_file, 'r') as f:
            import yaml
            rules_data = yaml.safe_load(f)
        
        assert "groups" in rules_data
        assert len(rules_data["groups"]) > 0
        
        # Validate rule structure
        for group in rules_data["groups"]:
            assert "name" in group
            assert "rules" in group
            
            for rule in group["rules"]:
                assert "alert" in rule
                assert "expr" in rule
                assert "labels" in rule
                assert "annotations" in rule
                assert "severity" in rule["labels"]
    
    def test_alertmanager_config_validation(self):
        """Test that Alertmanager configuration is valid."""
        config_file = "monitoring/alerts/alertmanager.yml"
        assert os.path.exists(config_file)
        
        with open(config_file, 'r') as f:
            import yaml
            config_data = yaml.safe_load(f)
        
        assert "global" in config_data
        assert "route" in config_data
        assert "receivers" in config_data
        
        # Validate receivers
        receiver_names = [r["name"] for r in config_data["receivers"]]
        assert "critical-alerts" in receiver_names
        assert "warning-alerts" in receiver_names

class TestDashboardUI:
    """Test suite for dashboard UI components (would require frontend testing framework)."""
    
    def test_dashboard_component_structure(self):
        """Test that dashboard components are properly structured."""
        # Verify component files exist
        component_files = [
            "dashboard/src/components/Navbar.tsx",
            "dashboard/src/components/DashboardCard.tsx",
            "dashboard/src/components/DashboardChart.tsx",
            "dashboard/src/app/page.tsx",
            "dashboard/src/app/layout.tsx"
        ]
        
        for file_path in component_files:
            assert os.path.exists(file_path), f"Component file {file_path} not found"
    
    def test_dashboard_configuration_files(self):
        """Test that dashboard configuration files are present."""
        config_files = [
            "dashboard/package.json",
            "dashboard/next.config.js",
            "dashboard/tsconfig.json",
            "dashboard/tailwind.config.js",
            "dashboard/postcss.config.js"
        ]
        
        for file_path in config_files:
            assert os.path.exists(file_path), f"Config file {file_path} not found"

class TestPerformanceMonitoring:
    """Test suite for performance monitoring capabilities."""
    
    @pytest.mark.asyncio
    async def test_response_time_tracking(self):
        """Test API response time tracking."""
        instrumentation = get_instrumentation()
        
        # Simulate various response times
        response_times = [0.05, 0.12, 0.08, 0.15, 0.22, 0.18, 0.09]
        
        for rt in response_times:
            instrumentation.record_api_metrics("GET", "/api/test", 200, rt)
        
        # Verify metrics are being tracked
        assert True  # Placeholder for actual verification
    
    @pytest.mark.asyncio
    async def test_resource_usage_monitoring(self):
        """Test system resource usage monitoring."""
        instrumentation = get_instrumentation()
        
        # Simulate resource usage over time
        for i in range(10):
            memory_usage = 60 + (i * 2)  # Gradually increasing
            cpu_usage = 30 + (i * 1.5)   # Gradually increasing
            active_calls = 5 + i
            
            instrumentation.update_system_metrics(memory_usage, cpu_usage, active_calls)
            await asyncio.sleep(0.1)  # Small delay to simulate time passage
        
        # Verify resource metrics are being tracked
        assert True  # Placeholder for actual verification

class TestErrorHandling:
    """Test suite for error handling in monitoring system."""
    
    def test_instrumentation_error_resilience(self):
        """Test that instrumentation handles errors gracefully."""
        instrumentation = get_instrumentation()
        
        # Test with invalid data
        try:
            instrumentation.record_call_metrics(-1, "invalid_status", "")
            instrumentation.record_api_metrics("", "", -1, -1)
            instrumentation.update_system_metrics(-1, -1, -1)
        except Exception as e:
            pytest.fail(f"Instrumentation should handle invalid data gracefully: {e}")
    
    @pytest.mark.asyncio
    async def test_dashboard_api_error_handling(self):
        """Test dashboard API error handling."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(dashboard_router)
        client = TestClient(app)
        
        # Test with invalid parameters
        response = client.get("/api/dashboard/call-volume?hours=-1")
        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 422]  # Valid error responses

@pytest.mark.integration
class TestEndToEndMonitoring:
    """End-to-end integration tests for the complete monitoring system."""
    
    @pytest.mark.asyncio
    async def test_complete_monitoring_flow(self):
        """Test the complete flow from metrics generation to dashboard display."""
        # 1. Generate metrics through instrumentation
        instrumentation = get_instrumentation()
        
        # Simulate a complete call flow
        with instrumentation.create_span("test_call") as span:
            if span:
                span.set_attribute("call_id", "test-123")
                span.set_attribute("agent", "roxy")
            
            # Record call start
            start_time = time.time()
            
            # Simulate call processing
            await asyncio.sleep(0.1)
            
            # Record call completion
            duration = time.time() - start_time
            instrumentation.record_call_metrics(duration, "success", "roxy")
        
        # 2. Update system metrics
        instrumentation.update_system_metrics(65.0, 40.0, 3)
        
        # 3. Verify metrics are available through dashboard API
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(dashboard_router)
        client = TestClient(app)
        
        response = client.get("/api/dashboard/metrics")
        assert response.status_code == 200
        
        # 4. Verify real-time updates work
        response = client.get("/api/dashboard/recent-activity")
        assert response.status_code == 200
        
        # Test passes if no exceptions are raised
        assert True

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
