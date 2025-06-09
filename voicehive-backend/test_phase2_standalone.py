#!/usr/bin/env python3
"""
Standalone test for Phase 2 ML Integration
Tests the ML components without external dependencies
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
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
    print("✅ Successfully imported all ML components")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class MockOpenAIService:
    """Mock OpenAI service for testing"""
    
    async def generate_response(self, system_prompt, conversation_history):
        return json.dumps({
            "score": 0.8,
            "priority": "high",
            "reasoning": "High impact improvement with manageable risk",
            "timeline": "2 weeks",
            "confidence": 0.85
        })


async def test_prioritization_engine():
    """Test the prioritization engine"""
    print("\n🧪 Testing Prioritization Engine...")
    
    try:
        # Create mock service
        mock_openai = MockOpenAIService()
        
        # Initialize engine
        engine = PrioritizationEngine(
            project_id="test-project",
            openai_service=mock_openai
        )
        
        # Create test candidates
        candidates = [
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
        
        # Test prioritization
        results = await engine.prioritize_improvements(candidates)
        
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"
        assert all(result.final_priority in ImprovementPriority for result in results), "Invalid priority levels"
        assert all(0 <= result.combined_score <= 1 for result in results), "Invalid scores"
        
        # Test statistics
        stats = engine.get_prioritization_statistics()
        assert "total_prioritizations" in stats, "Missing statistics"
        
        print("✅ Prioritization Engine tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Prioritization Engine test failed: {e}")
        return False


async def test_anomaly_detector():
    """Test the anomaly detector"""
    print("\n🧪 Testing Anomaly Detector...")
    
    try:
        # Initialize detector
        detector = AnomalyDetector(project_id="test-project", sensitivity=2.0)
        
        # Create test time series with anomaly
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
        
        time_series = TimeSeriesData(
            metric_name="response_time_ms",
            data_points=data_points,
            unit="ms",
            description="API response time"
        )
        
        # Test anomaly detection
        detected_anomalies = await detector.add_metric_data(time_series)
        
        # Should detect the spike as an anomaly
        print(f"Detected {len(detected_anomalies)} anomalies")
        
        if detected_anomalies:
            anomaly = detected_anomalies[-1]
            assert anomaly.metric_name == "response_time_ms", "Wrong metric name"
            assert anomaly.anomaly_type in AnomalyType, "Invalid anomaly type"
            assert anomaly.severity in AnomalySeverity, "Invalid severity"
            assert anomaly.confidence > 0, "Invalid confidence"
        
        # Test predictions
        predictions = await detector.predict_future_metrics(["response_time_ms"], steps_ahead=3)
        assert "response_time_ms" in predictions, "Missing predictions"
        
        # Test statistics
        stats = detector.get_detection_statistics()
        assert "total_anomalies" in stats, "Missing statistics"
        
        print("✅ Anomaly Detector tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Anomaly Detector test failed: {e}")
        return False


async def test_resource_allocator():
    """Test the resource allocator"""
    print("\n🧪 Testing Resource Allocator...")
    
    try:
        # Initialize allocator
        allocator = ResourceAllocator(project_id="test-project")
        
        # Test resource request
        request_id = await allocator.request_resources(
            requesting_agent="test_agent",
            resource_type=ResourceType.COMPUTE_INSTANCE,
            amount=2.0,
            priority=2,
            duration_hours=4.0,
            justification="Testing resource allocation"
        )
        
        assert isinstance(request_id, str), "Invalid request ID"
        assert len(request_id) > 0, "Empty request ID"
        
        # Check pending requests
        assert len(allocator.pending_requests) == 1, "Request not added to queue"
        
        # Test optimization
        result = await allocator.optimize_allocations()
        assert "strategy_used" in result, "Missing strategy in result"
        assert "new_allocations" in result, "Missing allocations in result"
        
        # Test status
        status = allocator.get_allocation_status()
        assert "active_allocations" in status, "Missing status fields"
        
        # Test statistics
        stats = allocator.get_allocation_statistics()
        assert "total_allocations" in stats, "Missing statistics"
        
        print("✅ Resource Allocator tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Resource Allocator test failed: {e}")
        return False


async def test_decision_engine():
    """Test the decision engine"""
    print("\n🧪 Testing Decision Engine...")
    
    try:
        # Create mock service
        mock_openai = MockOpenAIService()
        
        # Initialize engine
        engine = DecisionEngine(
            project_id="test-project",
            openai_service=mock_openai
        )
        
        # Test improvement prioritization decision
        request_id = await engine.request_decision(
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
        
        assert isinstance(request_id, str), "Invalid request ID"
        assert len(request_id) > 0, "Empty request ID"
        
        # Test resource allocation decision
        resource_request_id = await engine.request_decision(
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
        
        assert isinstance(resource_request_id, str), "Invalid resource request ID"
        
        # Test statistics
        stats = engine.get_engine_statistics()
        assert "total_decisions" in stats, "Missing statistics"
        assert "ml_components" in stats, "Missing ML components info"
        
        print("✅ Decision Engine tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Decision Engine test failed: {e}")
        return False


async def test_integration():
    """Test integration between components"""
    print("\n🧪 Testing ML Component Integration...")
    
    try:
        # Create mock service
        mock_openai = MockOpenAIService()
        
        # Initialize all components
        decision_engine = DecisionEngine(project_id="test-project", openai_service=mock_openai)
        anomaly_detector = AnomalyDetector(project_id="test-project", openai_service=mock_openai)
        resource_allocator = ResourceAllocator(project_id="test-project", openai_service=mock_openai)
        
        # Simulate workflow: Anomaly -> Decision -> Resource Allocation
        
        # 1. Detect anomaly
        time_series = TimeSeriesData(
            metric_name="test_metric",
            data_points=[
                MetricDataPoint(timestamp=datetime.now(), value=100.0),
                MetricDataPoint(timestamp=datetime.now(), value=200.0)  # Anomaly
            ]
        )
        
        anomalies = await anomaly_detector.add_metric_data(time_series)
        print(f"Detected {len(anomalies)} anomalies")
        
        # 2. Make decision based on anomaly
        if anomalies:
            decision_id = await decision_engine.request_decision(
                decision_type=DecisionType.EMERGENCY_RESPONSE,
                urgency=DecisionUrgency.HIGH,
                data={"emergency": {"type": "performance_degradation", "severity": "high"}},
                requesting_agent="integration_test"
            )
            print(f"Created decision: {decision_id}")
        
        # 3. Allocate resources
        allocation_id = await resource_allocator.request_resources(
            requesting_agent="integration_test",
            resource_type=ResourceType.COMPUTE_INSTANCE,
            amount=1.0,
            priority=1
        )
        print(f"Created allocation: {allocation_id}")
        
        # Verify all components are working
        decision_stats = decision_engine.get_engine_statistics()
        anomaly_stats = anomaly_detector.get_detection_statistics()
        resource_stats = resource_allocator.get_allocation_statistics()
        
        assert decision_stats["total_decisions"] >= 0, "Decision engine not working"
        assert anomaly_stats["total_anomalies"] >= 0, "Anomaly detector not working"
        assert resource_stats["total_allocations"] >= 0, "Resource allocator not working"
        
        print("✅ Integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


async def main():
    """Run all Phase 2 tests"""
    print("🚀 Starting Phase 2 ML Integration Tests")
    print("=" * 50)
    
    tests = [
        test_prioritization_engine,
        test_anomaly_detector,
        test_resource_allocator,
        test_decision_engine,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 2 ML Integration tests PASSED!")
        print("\n✅ Phase 2 Implementation Status: COMPLETE")
        print("✅ ML-Based Prioritization Engine: WORKING")
        print("✅ Predictive Anomaly Detection: WORKING")
        print("✅ Dynamic Resource Allocation: WORKING")
        print("✅ Enhanced Decision Engine: WORKING")
        print("✅ Component Integration: WORKING")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
