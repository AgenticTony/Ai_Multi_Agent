"""
Test Suite for Sprint 6 Supervisor Implementation
Tests the core supervisor components and their integration
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from voicehive.domains.agents.services.emergency_manager import (
    EmergencyManager, Emergency, EmergencyType, EmergencySeverity
)
from voicehive.domains.agents.services.monitoring_agent import (
    MonitoringAgent, AgentStatus, AgentMetrics
)
from voicehive.domains.agents.services.operational_supervisor import (
    OperationalSupervisor, AgentRegistration
)
from voicehive.domains.agents.services.supervisor_integration_bridge import (
    SupervisorIntegrationBridge, BridgeStatus, CircuitBreaker, CircuitBreakerConfig
)
from voicehive.domains.communication.services.message_bus import (
    MessageBus, MessageType, MessagePriority, Message
)


class TestEmergencyManager:
    """Test Emergency Manager functionality"""
    
    @pytest.fixture
    def emergency_manager(self):
        """Create emergency manager for testing"""
        return EmergencyManager()
    
    @pytest.mark.asyncio
    async def test_emergency_detection(self, emergency_manager):
        """Test emergency condition detection"""
        # Test metrics that should trigger emergencies
        high_failure_metrics = {
            "call_failure_rate": 0.5,  # 50% failure rate (threshold: 30%)
            "avg_response_time_ms": 10000,  # 10 seconds (threshold: 8 seconds)
            "memory_usage_percent": 95  # 95% memory (threshold: 90%)
        }
        
        emergencies = await emergency_manager.check_emergency_conditions(high_failure_metrics)
        
        assert len(emergencies) >= 2  # Should detect multiple emergencies
        assert any(e.type == EmergencyType.CALL_FAILURE_RATE for e in emergencies)
        assert any(e.severity == EmergencySeverity.HIGH for e in emergencies)
    
    @pytest.mark.asyncio
    async def test_emergency_handling(self, emergency_manager):
        """Test emergency intervention execution"""
        emergency = Emergency(
            id="test-emergency-1",
            type=EmergencyType.CALL_FAILURE_RATE,
            severity=EmergencySeverity.HIGH,
            message="Test emergency",
            timestamp=datetime.now(),
            affected_agents=["roxy_agent"],
            metrics={"call_failure_rate": 0.5}
        )
        
        result = await emergency_manager.handle_emergency(emergency)
        
        assert result["success"] is True
        assert len(result["actions_taken"]) > 0
        assert emergency.id in emergency_manager.active_emergencies
    
    def test_emergency_statistics(self, emergency_manager):
        """Test emergency statistics collection"""
        # Add some test emergencies to history
        test_emergency = Emergency(
            id="test-emergency-2",
            type=EmergencyType.MEMORY_EXHAUSTION,
            severity=EmergencySeverity.MEDIUM,
            message="Test emergency",
            timestamp=datetime.now(),
            affected_agents=["test_agent"],
            metrics={}
        )
        emergency_manager.emergency_history.append(test_emergency)
        
        stats = emergency_manager.get_emergency_statistics()
        
        assert stats["total_emergencies"] >= 1
        assert "severity_distribution" in stats
        assert "type_distribution" in stats


class TestMonitoringAgent:
    """Test Monitoring Agent functionality"""
    
    @pytest.fixture
    def message_bus(self):
        """Create mock message bus"""
        return Mock(spec=MessageBus)
    
    @pytest.fixture
    def monitoring_agent(self, message_bus):
        """Create monitoring agent for testing"""
        message_bus.is_running = False
        message_bus.start = AsyncMock()
        message_bus.subscribe = Mock()
        message_bus.publish = AsyncMock()
        return MonitoringAgent(message_bus=message_bus)
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, monitoring_agent):
        """Test agent registration"""
        result = await monitoring_agent.register_agent(
            agent_id="test_agent",
            agent_type="voice_agent",
            capabilities=["voice_processing", "nlp"]
        )
        
        assert result is True
        assert "test_agent" in monitoring_agent.registered_agents
        assert monitoring_agent.registered_agents["test_agent"].status == AgentStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_heartbeat_processing(self, monitoring_agent):
        """Test agent heartbeat processing"""
        # Register agent first
        await monitoring_agent.register_agent("test_agent", "voice_agent", [])
        
        # Create heartbeat message
        heartbeat_message = Mock()
        heartbeat_message.type = MessageType.AGENT_HEARTBEAT
        heartbeat_message.data = {
            "agent_id": "test_agent",
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
        await monitoring_agent._process_heartbeat("test_agent", heartbeat_message.data)
        
        assert "test_agent" in monitoring_agent.agent_heartbeats
        assert monitoring_agent.registered_agents["test_agent"].status == AgentStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_system_metrics_collection(self, monitoring_agent):
        """Test system metrics collection"""
        # Register some test agents
        await monitoring_agent.register_agent("agent1", "voice_agent", [])
        await monitoring_agent.register_agent("agent2", "monitoring_agent", [])
        
        metrics = await monitoring_agent._collect_system_metrics()
        
        assert metrics.total_agents == 2
        assert metrics.healthy_agents >= 0
        assert metrics.timestamp is not None
        assert metrics.system_cpu_percent >= 0
        assert metrics.system_memory_percent >= 0


class TestOperationalSupervisor:
    """Test Operational Supervisor functionality"""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing"""
        openai_service = Mock()
        message_bus = Mock(spec=MessageBus)
        message_bus.is_running = False
        message_bus.start = AsyncMock()
        message_bus.subscribe = Mock()
        message_bus.publish = AsyncMock()
        
        emergency_manager = Mock()
        emergency_manager.check_emergency_conditions = AsyncMock(return_value=[])
        
        monitoring_agent = Mock()
        monitoring_agent.start = AsyncMock()
        monitoring_agent.stop = AsyncMock()
        monitoring_agent.register_agent = AsyncMock(return_value=True)
        
        return {
            "openai_service": openai_service,
            "message_bus": message_bus,
            "emergency_manager": emergency_manager,
            "monitoring_agent": monitoring_agent
        }
    
    @pytest.fixture
    def operational_supervisor(self, mock_services):
        """Create operational supervisor for testing"""
        return OperationalSupervisor(
            openai_service=mock_services["openai_service"],
            message_bus=mock_services["message_bus"],
            emergency_manager=mock_services["emergency_manager"],
            monitoring_agent=mock_services["monitoring_agent"]
        )
    
    @pytest.mark.asyncio
    async def test_supervisor_startup(self, operational_supervisor, mock_services):
        """Test supervisor startup process"""
        await operational_supervisor.start()
        
        assert operational_supervisor.is_running is True
        mock_services["message_bus"].start.assert_called_once()
        mock_services["monitoring_agent"].start.assert_called_once()
        mock_services["message_bus"].subscribe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, operational_supervisor):
        """Test agent registration with supervisor"""
        result = await operational_supervisor.register_agent(
            agent_id="test_agent",
            agent_type="voice_agent",
            capabilities=["voice_processing"],
            priority_level=1
        )
        
        assert result is True
        assert "test_agent" in operational_supervisor.registered_agents
        registration = operational_supervisor.registered_agents["test_agent"]
        assert registration.agent_type == "voice_agent"
        assert registration.priority_level == 1
    
    @pytest.mark.asyncio
    async def test_message_handling(self, operational_supervisor):
        """Test message handling"""
        # Create test message
        test_message = Mock()
        test_message.type = MessageType.EMERGENCY_ALERT
        test_message.data = {
            "alert_type": "test_alert",
            "severity": "high"
        }
        
        # Should not raise exception
        await operational_supervisor._handle_message(test_message)


class TestSupervisorIntegrationBridge:
    """Test Supervisor Integration Bridge functionality"""
    
    @pytest.fixture
    def message_bus(self):
        """Create mock message bus"""
        message_bus = Mock(spec=MessageBus)
        message_bus.is_running = False
        message_bus.start = AsyncMock()
        message_bus.subscribe = Mock()
        message_bus.publish = AsyncMock()
        return message_bus
    
    @pytest.fixture
    def integration_bridge(self, message_bus):
        """Create integration bridge for testing"""
        return SupervisorIntegrationBridge(message_bus=message_bus)
    
    @pytest.mark.asyncio
    async def test_bridge_startup(self, integration_bridge, message_bus):
        """Test bridge startup process"""
        await integration_bridge.start()
        
        assert integration_bridge.is_running is True
        assert integration_bridge.status == BridgeStatus.HEALTHY
        message_bus.start.assert_called_once()
        message_bus.subscribe.assert_called_once()
    
    def test_message_validation(self, integration_bridge):
        """Test message contract validation"""
        # Valid improvement trigger message
        valid_message = {
            "trigger_type": "performance_degradation",
            "performance_data": {"response_time": 5000},
            "timestamp": datetime.now().isoformat(),
            "affected_agents": ["roxy_agent"],
            "severity": "medium"
        }
        
        result = integration_bridge.message_validator.validate_message(
            "improvement_trigger", valid_message
        )
        assert result is True
        
        # Invalid message (missing required field)
        invalid_message = {
            "trigger_type": "performance_degradation",
            # Missing required fields
        }
        
        result = integration_bridge.message_validator.validate_message(
            "improvement_trigger", invalid_message
        )
        assert result is False
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout_seconds=1)
        circuit_breaker = CircuitBreaker(config)
        
        # Initially healthy
        assert circuit_breaker.state == BridgeStatus.HEALTHY
        
        # Simulate failures
        asyncio.run(circuit_breaker._on_failure())
        assert circuit_breaker.state == BridgeStatus.HEALTHY  # Still healthy
        
        asyncio.run(circuit_breaker._on_failure())
        assert circuit_breaker.state == BridgeStatus.CIRCUIT_OPEN  # Now open
    
    def test_dead_letter_queue(self, integration_bridge):
        """Test dead letter queue functionality"""
        test_message = {
            "id": "test-message-1",
            "type": "test_type",
            "data": {"test": "data"}
        }
        
        integration_bridge.dead_letter_queue.add_message(test_message, "Test error")
        
        messages = integration_bridge.dead_letter_queue.get_messages()
        assert len(messages) == 1
        assert messages[0]["message"]["id"] == "test-message-1"
        assert messages[0]["error"] == "Test error"
    
    def test_bridge_health_status(self, integration_bridge):
        """Test bridge health status reporting"""
        health = integration_bridge.get_bridge_health()
        
        assert "bridge_id" in health
        assert "status" in health
        assert "circuit_breaker_state" in health
        assert "metrics" in health
        assert health["is_running"] is False  # Not started yet


class TestMessageBus:
    """Test Message Bus functionality"""
    
    @pytest.fixture
    def message_bus(self):
        """Create message bus for testing"""
        return MessageBus()
    
    @pytest.mark.asyncio
    async def test_message_publishing(self, message_bus):
        """Test message publishing"""
        message_id = await message_bus.publish(
            message_type=MessageType.AGENT_HEARTBEAT,
            data={"agent_id": "test_agent", "status": "healthy"},
            sender_id="test_sender"
        )
        
        assert message_id is not None
        assert message_bus.message_queue.qsize() == 1
    
    def test_subscription(self, message_bus):
        """Test message subscription"""
        handler = AsyncMock()
        
        subscription_id = message_bus.subscribe(
            subscriber_id="test_subscriber",
            message_types=[MessageType.AGENT_HEARTBEAT],
            handler=handler
        )
        
        assert subscription_id is not None
        assert subscription_id in message_bus.subscriptions
        assert MessageType.AGENT_HEARTBEAT in message_bus.type_subscribers
    
    def test_unsubscription(self, message_bus):
        """Test message unsubscription"""
        handler = AsyncMock()
        
        subscription_id = message_bus.subscribe(
            subscriber_id="test_subscriber",
            message_types=[MessageType.AGENT_HEARTBEAT],
            handler=handler
        )
        
        result = message_bus.unsubscribe(subscription_id)
        
        assert result is True
        assert subscription_id not in message_bus.subscriptions
    
    def test_bus_statistics(self, message_bus):
        """Test message bus statistics"""
        stats = message_bus.get_bus_statistics()
        
        assert "total_subscriptions" in stats
        assert "active_subscribers" in stats
        assert "message_history_size" in stats
        assert "queue_size" in stats
        assert "is_running" in stats


@pytest.mark.integration
class TestSupervisorIntegration:
    """Integration tests for supervisor components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_emergency_flow(self):
        """Test complete emergency detection and handling flow"""
        # Create integrated system
        message_bus = MessageBus()
        emergency_manager = EmergencyManager()
        monitoring_agent = MonitoringAgent(message_bus)
        operational_supervisor = OperationalSupervisor(
            message_bus=message_bus,
            emergency_manager=emergency_manager,
            monitoring_agent=monitoring_agent
        )
        
        try:
            # Start all components
            await message_bus.start()
            await monitoring_agent.start()
            await operational_supervisor.start()
            
            # Register an agent
            await operational_supervisor.register_agent(
                "test_agent", "voice_agent", ["voice_processing"]
            )
            
            # Simulate emergency conditions
            emergency_metrics = {
                "call_failure_rate": 0.6,  # High failure rate
                "avg_response_time_ms": 12000  # High response time
            }
            
            emergencies = await emergency_manager.check_emergency_conditions(emergency_metrics)
            
            # Verify emergency detection
            assert len(emergencies) > 0
            
            # Handle emergencies
            for emergency in emergencies:
                result = await emergency_manager.handle_emergency(emergency)
                assert result["success"] is True
            
        finally:
            # Cleanup
            await operational_supervisor.stop()
            await monitoring_agent.stop()
            await message_bus.stop()
    
    @pytest.mark.asyncio
    async def test_supervisor_bridge_communication(self):
        """Test communication through supervisor integration bridge"""
        message_bus = MessageBus()
        bridge = SupervisorIntegrationBridge(message_bus)
        
        try:
            await message_bus.start()
            await bridge.start()
            
            # Test improvement trigger message
            await message_bus.publish(
                message_type=MessageType.IMPROVEMENT_TRIGGER,
                data={
                    "trigger_type": "performance_degradation",
                    "performance_data": {"response_time": 5000},
                    "timestamp": datetime.now().isoformat(),
                    "affected_agents": ["roxy_agent"],
                    "severity": "medium"
                },
                sender_id="operational_supervisor"
            )
            
            # Allow message processing
            await asyncio.sleep(0.1)
            
            # Verify bridge health
            health = bridge.get_bridge_health()
            assert health["status"] == BridgeStatus.HEALTHY.value
            
        finally:
            await bridge.stop()
            await message_bus.stop()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
