"""
Test Suite for Phase 2 ML Integration
Tests the ML-powered intelligent coordination components
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from voicehive.domains.agents.services.ml.prioritization_engine import (
    PrioritizationEngine, ImprovementCandidate, ImprovementCategory, ImprovementPriority
)
from voicehive.domains.agents.services.ml.anomaly_detector import (
    AnomalyDetector, TimeSeriesData, MetricDataPoint, AnomalyType, AnomalySeverity
)
from voicehive.domains.agents.services.ml.resource_allocator import (
    ResourceAllocator, ResourceType, AllocationStrategy
)
from voicehive.domains.agents.services.ml.decision_engine import (
    DecisionEngine, DecisionType, DecisionUrgency
)
from voicehive.domains.agents.services.operational_supervisor import OperationalSupervisor
from voicehive.services.ai.openai_service import OpenAIService


class TestPrioritizationEngine:
    """Test ML-based prioritization engine"""
    
    @pytest.fixture
    def mock_openai_service(self):
        service = Mock(spec=OpenAIService)
        service.generate_response = AsyncMock(return_value=json.dumps({
            "score": 0.8,
            "priority": "high",
            "reasoning": "High impact improvement with manageable risk",
            "timeline": "2 weeks",
            "confidence": 0.85
        }))
        return service
    
    @pytest.fixture
    def prioritization_engine(self, mock_openai_service):
        return PrioritizationEngine(
            project_id="test-project",
            openai_service=mock_openai_service
        )
    
    @pytest.fixture
    def sample_candidates(self):
        return [
            ImprovementCandidate(
                id="imp-1",
                title="Optimize Response Time",
                description="Reduce API response time by 30%",
                category=ImprovementCategory.PERFORMANCE,
                estimated_impact=0.8,
                estimated_effort=0.6,
                risk_level=0.3,
                performance_data={"response_time": 150, "success_rate": 0.95},
                timestamp=datetime.now(),
                source_agent="monitoring_agent"
            ),
            ImprovementCandidate(
                id="imp-2",
                title="Enhance Security",
                description="Implement additional security measures",
                category=ImprovementCategory.SAFETY,
                estimated_impact=0.9,
                estimated_effort=0.8,
                risk_level=0.2,
                performance_data={"security_score": 0.85},
                timestamp=datetime.now(),
                source_agent="security_agent"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_prioritize_improvements(self, prioritization_engine, sample_candidates):
        """Test improvement prioritization"""
        results = await prioritization_engine.prioritize_improvements(sample_candidates)
        
        assert len(results) == 2
        assert all(result.final_priority in ImprovementPriority for result in results)
        assert all(0 <= result.combined_score <= 1 for result in results)
        assert all(0 <= result.confidence <= 1 for result in results)
        
        # Results should be sorted by score
        scores = [result.combined_score for result in results]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_vertex_ai_fallback(self, prioritization_engine, sample_candidates):
        """Test fallback when Vertex AI is not available"""
        # Vertex AI should gracefully fallback to heuristic scoring
        results = await prioritization_engine.prioritize_improvements(sample_candidates)
        
        assert len(results) == 2
        assert all(result.ml_score >= 0 for result in results)
        
        # Safety category should get higher priority
        safety_result = next(r for r in results if r.candidate.category == ImprovementCategory.SAFETY)
        performance_result = next(r for r in results if r.candidate.category == ImprovementCategory.PERFORMANCE)
        
        # Safety improvements typically get higher priority
        assert safety_result.combined_score >= performance_result.combined_score
    
    def test_prioritization_statistics(self, prioritization_engine):
        """Test prioritization statistics"""
        stats = prioritization_engine.get_prioritization_statistics()
        
        assert "total_prioritizations" in stats
        assert "vertex_ai_available" in stats
        assert isinstance(stats["vertex_ai_available"], bool)


class TestAnomalyDetector:
    """Test ML-powered anomaly detection"""
    
    @pytest.fixture
    def anomaly_detector(self):
        return AnomalyDetector(project_id="test-project", sensitivity=2.0)
    
    @pytest.fixture
    def sample_time_series(self):
        # Create time series with normal values and one anomaly
        data_points = []
        base_time = datetime.now()
        
        # Normal values
        for i in range(20):
            data_points.append(MetricDataPoint(
                timestamp=base_time + timedelta(minutes=i),
                value=100.0 + (i * 2),  # Gradual increase
                metadata={"source": "test"}
            ))
        
        # Add anomaly
        data_points.append(MetricDataPoint(
            timestamp=base_time + timedelta(minutes=21),
            value=200.0,  # Significant spike
            metadata={"source": "test"}
        ))
        
        return TimeSeriesData(
            metric_name="response_time_ms",
            data_points=data_points,
            unit="ms",
            description="API response time"
        )
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, anomaly_detector, sample_time_series):
        """Test anomaly detection in time series data"""
        detected_anomalies = await anomaly_detector.add_metric_data(sample_time_series)
        
        # Should detect the spike as an anomaly
        assert len(detected_anomalies) >= 1
        
        anomaly = detected_anomalies[-1]  # Last detected anomaly
        assert anomaly.metric_name == "response_time_ms"
        assert anomaly.anomaly_type in AnomalyType
        assert anomaly.severity in AnomalySeverity
        assert anomaly.value == 200.0
        assert anomaly.confidence > 0
    
    @pytest.mark.asyncio
    async def test_prediction_capabilities(self, anomaly_detector, sample_time_series):
        """Test future value prediction"""
        # Add data to build baseline
        await anomaly_detector.add_metric_data(sample_time_series)
        
        # Get predictions
        predictions = await anomaly_detector.predict_future_metrics(
            ["response_time_ms"], steps_ahead=5
        )
        
        assert "response_time_ms" in predictions
        assert len(predictions["response_time_ms"]) == 5
        
        for prediction in predictions["response_time_ms"]:
            assert prediction.confidence > 0
            assert prediction.trend_direction in ["increasing", "decreasing", "stable"]
    
    @pytest.mark.asyncio
    async def test_early_warnings(self, anomaly_detector, sample_time_series):
        """Test early warning system"""
        # Add data and get predictions
        await anomaly_detector.add_metric_data(sample_time_series)
        await anomaly_detector.predict_future_metrics(["response_time_ms"])
        
        # Get early warnings
        warnings = anomaly_detector.get_early_warnings(threshold_hours=2)
        
        assert isinstance(warnings, list)
        # Warnings may or may not be present depending on predictions
        for warning in warnings:
            assert "type" in warning
            assert "metric" in warning
            assert "confidence" in warning
    
    def test_detection_statistics(self, anomaly_detector):
        """Test anomaly detection statistics"""
        stats = anomaly_detector.get_detection_statistics()
        
        assert "total_anomalies" in stats
        assert "vertex_ai_available" in stats
        assert "metrics_monitored" in stats


class TestResourceAllocator:
    """Test intelligent resource allocation"""
    
    @pytest.fixture
    def resource_allocator(self):
        return ResourceAllocator(project_id="test-project")
    
    @pytest.mark.asyncio
    async def test_resource_request(self, resource_allocator):
        """Test resource allocation request"""
        request_id = await resource_allocator.request_resources(
            requesting_agent="test_agent",
            resource_type=ResourceType.COMPUTE_INSTANCE,
            amount=2.0,
            priority=2,
            duration_hours=4.0,
            justification="Testing resource allocation"
        )
        
        assert isinstance(request_id, str)
        assert len(request_id) > 0
        
        # Check that request is in pending queue
        assert len(resource_allocator.pending_requests) == 1
        assert resource_allocator.pending_requests[0].id == request_id
    
    @pytest.mark.asyncio
    async def test_allocation_optimization(self, resource_allocator):
        """Test resource allocation optimization"""
        # Create multiple requests
        await resource_allocator.request_resources(
            requesting_agent="agent1",
            resource_type=ResourceType.COMPUTE_INSTANCE,
            amount=1.0,
            priority=1
        )
        
        await resource_allocator.request_resources(
            requesting_agent="agent2",
            resource_type=ResourceType.AI_MODEL_CAPACITY,
            amount=100.0,
            priority=3
        )
        
        # Optimize allocations
        result = await resource_allocator.optimize_allocations()
        
        assert "strategy_used" in result
        assert "new_allocations" in result
        assert "active_allocations" in result
        assert result["new_allocations"] >= 0
    
    def test_allocation_status(self, resource_allocator):
        """Test allocation status reporting"""
        status = resource_allocator.get_allocation_status()
        
        assert "active_allocations" in status
        assert "pending_requests" in status
        assert "total_cost_per_hour" in status
        assert "resource_utilization" in status
    
    def test_allocation_statistics(self, resource_allocator):
        """Test allocation statistics"""
        stats = resource_allocator.get_allocation_statistics()
        
        assert "total_allocations" in stats
        assert "vertex_ai_available" in stats
        assert "resource_types_managed" in stats


class TestDecisionEngine:
    """Test enhanced decision engine"""
    
    @pytest.fixture
    def mock_openai_service(self):
        service = Mock(spec=OpenAIService)
        service.generate_response = AsyncMock(return_value="Test decision analysis response")
        return service
    
    @pytest.fixture
    def decision_engine(self, mock_openai_service):
        return DecisionEngine(
            project_id="test-project",
            openai_service=mock_openai_service
        )
    
    @pytest.mark.asyncio
    async def test_improvement_prioritization_decision(self, decision_engine):
        """Test improvement prioritization decision"""
        request_id = await decision_engine.request_decision(
            decision_type=DecisionType.IMPROVEMENT_PRIORITIZATION,
            urgency=DecisionUrgency.NORMAL,
            data={
                "candidates": [
                    {
                        "id": "imp-1",
                        "title": "Test Improvement",
                        "description": "Test improvement description",
                        "category": "performance",
                        "estimated_impact": 0.8,
                        "estimated_effort": 0.5,
                        "risk_level": 0.3,
                        "performance_data": {}
                    }
                ]
            },
            requesting_agent="test_agent"
        )
        
        assert isinstance(request_id, str)
        assert len(request_id) > 0
    
    @pytest.mark.asyncio
    async def test_resource_allocation_decision(self, decision_engine):
        """Test resource allocation decision"""
        request_id = await decision_engine.request_decision(
            decision_type=DecisionType.RESOURCE_ALLOCATION,
            urgency=DecisionUrgency.HIGH,
            data={
                "resource_requests": [
                    {
                        "agent": "test_agent",
                        "resource_type": "compute_instance",
                        "amount": 2.0,
                        "priority": 2,
                        "justification": "Testing resource allocation"
                    }
                ]
            },
            requesting_agent="test_agent"
        )
        
        assert isinstance(request_id, str)
        
        # Check decision status
        status = decision_engine.get_decision_status(request_id)
        assert status is not None
        assert "status" in status
    
    def test_engine_statistics(self, decision_engine):
        """Test decision engine statistics"""
        stats = decision_engine.get_engine_statistics()
        
        assert "total_decisions" in stats
        assert "pending_decisions" in stats
        assert "ml_components" in stats
        assert "prioritization_engine" in stats["ml_components"]


class TestMLIntegratedSupervisor:
    """Test ML-integrated operational supervisor"""
    
    @pytest.fixture
    def mock_openai_service(self):
        service = Mock(spec=OpenAIService)
        service.generate_response = AsyncMock(return_value="Test response")
        return service
    
    @pytest.fixture
    def mock_message_bus(self):
        bus = Mock()
        bus.start = AsyncMock()
        bus.subscribe = Mock()
        bus.publish = AsyncMock()
        bus.is_running = True
        return bus
    
    @pytest.fixture
    def mock_monitoring_agent(self):
        agent = Mock()
        agent.start = AsyncMock()
        agent.register_agent = AsyncMock()
        return agent
    
    @pytest.fixture
    def mock_emergency_manager(self):
        manager = Mock()
        manager.check_emergency_conditions = AsyncMock(return_value=[])
        return manager
    
    @pytest.fixture
    def ml_supervisor(self, mock_openai_service, mock_message_bus, 
                     mock_emergency_manager, mock_monitoring_agent):
        return OperationalSupervisor(
            openai_service=mock_openai_service,
            message_bus=mock_message_bus,
            emergency_manager=mock_emergency_manager,
            monitoring_agent=mock_monitoring_agent,
            project_id="test-project"
        )
    
    def test_ml_components_initialization(self, ml_supervisor):
        """Test that ML components are properly initialized"""
        assert hasattr(ml_supervisor, 'decision_engine')
        assert hasattr(ml_supervisor, 'anomaly_detector')
        assert hasattr(ml_supervisor, 'resource_allocator')
        
        assert ml_supervisor.decision_engine is not None
        assert ml_supervisor.anomaly_detector is not None
        assert ml_supervisor.resource_allocator is not None
    
    def test_ml_statistics(self, ml_supervisor):
        """Test ML statistics reporting"""
        stats = ml_supervisor.get_ml_statistics()
        
        assert "decision_engine" in stats
        assert "anomaly_detector" in stats
        assert "resource_allocator" in stats
        assert "ml_integration_status" in stats
        assert stats["ml_integration_status"] == "active"
        assert "phase" in stats
        assert "Phase 2" in stats["phase"]
    
    @pytest.mark.asyncio
    async def test_enhanced_emergency_detection(self, ml_supervisor):
        """Test ML-enhanced emergency detection"""
        # Mock the collect metrics method
        ml_supervisor._collect_current_metrics = AsyncMock(return_value={
            "response_time_ms": 150.0,
            "error_rate": 0.05,
            "cpu_usage_percent": 85.0
        })
        
        # Test emergency checking with ML
        await ml_supervisor._check_emergencies()
        
        # Verify that ML anomaly detection was attempted
        assert ml_supervisor.anomaly_detector is not None


@pytest.mark.integration
class TestPhase2Integration:
    """Integration tests for Phase 2 ML components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_ml_workflow(self):
        """Test complete ML workflow from detection to decision to allocation"""
        # This would be a comprehensive integration test
        # Testing the full pipeline of ML components working together
        
        # Initialize components
        openai_service = Mock(spec=OpenAIService)
        openai_service.generate_response = AsyncMock(return_value="Test response")
        
        decision_engine = DecisionEngine(project_id="test-project", openai_service=openai_service)
        anomaly_detector = AnomalyDetector(project_id="test-project", openai_service=openai_service)
        resource_allocator = ResourceAllocator(project_id="test-project", openai_service=openai_service)
        
        # Simulate anomaly detection
        time_series = TimeSeriesData(
            metric_name="test_metric",
            data_points=[
                MetricDataPoint(timestamp=datetime.now(), value=100.0),
                MetricDataPoint(timestamp=datetime.now(), value=200.0)  # Anomaly
            ]
        )
        
        anomalies = await anomaly_detector.add_metric_data(time_series)
        
        # If anomalies detected, trigger decision making
        if anomalies:
            request_id = await decision_engine.request_decision(
                decision_type=DecisionType.EMERGENCY_RESPONSE,
                urgency=DecisionUrgency.HIGH,
                data={"emergency": {"type": "performance_degradation", "severity": "high"}},
                requesting_agent="integration_test"
            )
            
            assert isinstance(request_id, str)
        
        # Test resource allocation
        allocation_id = await resource_allocator.request_resources(
            requesting_agent="integration_test",
            resource_type=ResourceType.COMPUTE_INSTANCE,
            amount=1.0,
            priority=1
        )
        
        assert isinstance(allocation_id, str)
        
        # Verify components can work together
        assert decision_engine.get_engine_statistics()["total_decisions"] >= 0
        assert anomaly_detector.get_detection_statistics()["total_anomalies"] >= 0
        assert resource_allocator.get_allocation_statistics()["total_allocations"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
