"""
SupervisorIntegrationBridge - Critical linchpin connecting Operational and Gatekeeper Supervisors

⚠️ CRITICAL COMPONENT WARNING ⚠️
This bridge is the LINCHPIN of VoiceHive's unified supervisor architecture.
An error here could decouple the feedback loops, undermining the self-healing system.
"""
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

from voicehive.domains.communication.services.message_bus import MessageBus, MessageType, MessagePriority
from voicehive.utils.exceptions import VoiceHiveError, ErrorHandler, RetryableError
from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BridgeStatus(Enum):
    """Bridge operational status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CIRCUIT_OPEN = "circuit_open"
    FAILED = "failed"


class MessageContractVersion(Enum):
    """Message contract versions for backward compatibility"""
    V1_0 = "1.0"
    V1_1 = "1.1"


@dataclass
class MessageContract:
    """Versioned message contract definition"""
    version: MessageContractVersion
    schema: Dict[str, Any]
    backward_compatible_versions: List[MessageContractVersion]


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 30
    half_open_max_calls: int = 3
    success_threshold: int = 2


@dataclass
class RetryConfig:
    """Retry policy configuration"""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_factor: float = 2.0


class CircuitBreaker:
    """Circuit breaker implementation for resilient communication"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = BridgeStatus.HEALTHY
        self.half_open_calls = 0
        self.success_count = 0
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == BridgeStatus.CIRCUIT_OPEN:
            if self._should_attempt_reset():
                self.state = BridgeStatus.DEGRADED
                self.half_open_calls = 0
                self.success_count = 0
            else:
                raise VoiceHiveError("Circuit breaker is open")
        
        if self.state == BridgeStatus.DEGRADED:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise VoiceHiveError("Circuit breaker half-open limit reached")
            self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout_seconds
    
    async def _on_success(self):
        """Handle successful call"""
        if self.state == BridgeStatus.DEGRADED:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = BridgeStatus.HEALTHY
                self.failure_count = 0
                self.half_open_calls = 0
                self.success_count = 0
                logger.info("Circuit breaker reset to healthy state")
        else:
            self.failure_count = 0
    
    async def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = BridgeStatus.CIRCUIT_OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class DeadLetterQueue:
    """Dead letter queue for failed messages"""
    
    def __init__(self, max_size: int = 1000):
        self.messages: List[Dict[str, Any]] = []
        self.max_size = max_size
    
    def add_message(self, message: Dict[str, Any], error: str):
        """Add failed message to dead letter queue"""
        dead_letter_entry = {
            "message": message,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "retry_count": message.get("retry_count", 0)
        }
        
        self.messages.append(dead_letter_entry)
        
        # Trim queue if too large
        if len(self.messages) > self.max_size:
            self.messages = self.messages[-self.max_size:]
        
        logger.warning(f"Message added to dead letter queue: {error}")
    
    def get_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages from dead letter queue"""
        return self.messages[-limit:]
    
    def clear(self):
        """Clear dead letter queue"""
        cleared_count = len(self.messages)
        self.messages.clear()
        logger.info(f"Dead letter queue cleared: {cleared_count} messages removed")


class MessageValidator:
    """Message contract validator"""
    
    def __init__(self):
        self.contracts = self._initialize_contracts()
    
    def _initialize_contracts(self) -> Dict[str, MessageContract]:
        """Initialize message contracts"""
        return {
            "improvement_trigger": MessageContract(
                version=MessageContractVersion.V1_0,
                schema={
                    "type": "object",
                    "required": ["trigger_type", "performance_data", "timestamp"],
                    "properties": {
                        "trigger_type": {"type": "string"},
                        "performance_data": {"type": "object"},
                        "timestamp": {"type": "string"},
                        "affected_agents": {"type": "array"},
                        "severity": {"type": "string"}
                    }
                },
                backward_compatible_versions=[MessageContractVersion.V1_0]
            ),
            "deployment_notification": MessageContract(
                version=MessageContractVersion.V1_0,
                schema={
                    "type": "object",
                    "required": ["deployment_id", "status", "timestamp"],
                    "properties": {
                        "deployment_id": {"type": "string"},
                        "status": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "prompt_version": {"type": "string"},
                        "rollback_available": {"type": "boolean"}
                    }
                },
                backward_compatible_versions=[MessageContractVersion.V1_0]
            )
        }
    
    def validate_message(self, message_type: str, message_data: Dict[str, Any]) -> bool:
        """Validate message against contract"""
        if message_type not in self.contracts:
            logger.warning(f"No contract found for message type: {message_type}")
            return False
        
        contract = self.contracts[message_type]
        
        # Simplified validation (in production, use jsonschema library)
        schema = contract.schema
        required_fields = schema.get("required", [])
        
        for field in required_fields:
            if field not in message_data:
                logger.error(f"Missing required field '{field}' in message type '{message_type}'")
                return False
        
        return True


class SupervisorIntegrationBridge:
    """
    Critical integration bridge connecting Operational and Gatekeeper Supervisors
    
    Features:
    - Resilient message handling with circuit breakers
    - Retry logic with exponential backoff
    - Dead letter queue for failed messages
    - Versioned message contracts
    - Comprehensive monitoring and alerting
    """
    
    def __init__(self, 
                 message_bus: Optional[MessageBus] = None,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
                 retry_config: Optional[RetryConfig] = None):
        
        self.message_bus = message_bus or MessageBus()
        
        # Resilience components
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config or CircuitBreakerConfig())
        self.retry_config = retry_config or RetryConfig()
        self.dead_letter_queue = DeadLetterQueue()
        self.message_validator = MessageValidator()
        
        # Bridge state
        self.is_running = False
        self.bridge_id = str(uuid.uuid4())
        self.status = BridgeStatus.HEALTHY
        
        # Performance metrics
        self.metrics = {
            "messages_processed": 0,
            "messages_failed": 0,
            "circuit_breaker_trips": 0,
            "avg_processing_time_ms": 0,
            "dead_letter_queue_size": 0
        }
        
        # Message routing
        self.message_handlers = {
            "improvement_trigger": self._handle_improvement_trigger,
            "deployment_notification": self._handle_deployment_notification
        }
        
        logger.info(f"SupervisorIntegrationBridge initialized (ID: {self.bridge_id})")
    
    async def start(self):
        """Start the integration bridge"""
        if self.is_running:
            logger.warning("SupervisorIntegrationBridge is already running")
            return
        
        # Start message bus if not running
        if not self.message_bus.is_running:
            await self.message_bus.start()
        
        # Subscribe to bridge messages
        self.message_bus.subscribe(
            subscriber_id=f"integration_bridge_{self.bridge_id}",
            message_types=[
                MessageType.IMPROVEMENT_TRIGGER,
                MessageType.DEPLOYMENT_NOTIFICATION
            ],
            handler=self._handle_bridge_message
        )
        
        self.is_running = True
        self.status = BridgeStatus.HEALTHY
        
        logger.info("SupervisorIntegrationBridge started and processing messages")
    
    async def stop(self):
        """Stop the integration bridge"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.status = BridgeStatus.FAILED
        
        logger.info("SupervisorIntegrationBridge stopped")
    
    async def _handle_bridge_message(self, message):
        """Handle incoming bridge messages with resilience patterns"""
        processing_start = datetime.now()
        
        try:
            # Validate message contract
            message_type = message.type.value
            if not self.message_validator.validate_message(message_type, message.data):
                raise VoiceHiveError(f"Message contract validation failed for {message_type}")
            
            # Route message to appropriate handler
            handler = self.message_handlers.get(message_type)
            if not handler:
                raise VoiceHiveError(f"No handler found for message type: {message_type}")
            
            # Execute with circuit breaker protection
            result = await self.circuit_breaker.call(handler, message)
            
            # Update metrics
            self.metrics["messages_processed"] += 1
            processing_time = (datetime.now() - processing_start).total_seconds() * 1000
            self.metrics["avg_processing_time_ms"] = (
                (self.metrics["avg_processing_time_ms"] + processing_time) / 2
            )
            
            logger.debug(f"Bridge message processed successfully: {message_type}")
            return result
            
        except Exception as e:
            # Handle failure with retry logic
            await self._handle_message_failure(message, str(e))
            raise
    
    async def _handle_message_failure(self, message, error: str):
        """Handle message processing failure"""
        self.metrics["messages_failed"] += 1
        
        # Increment retry count
        message.data["retry_count"] = message.data.get("retry_count", 0) + 1
        
        if message.data["retry_count"] < self.retry_config.max_retries:
            # Calculate retry delay with exponential backoff
            delay = min(
                self.retry_config.base_delay_seconds * (
                    self.retry_config.backoff_factor ** (message.data["retry_count"] - 1)
                ),
                self.retry_config.max_delay_seconds
            )
            
            logger.warning(f"Retrying message in {delay} seconds (attempt {message.data['retry_count']})")
            
            # Schedule retry
            await asyncio.sleep(delay)
            await self.message_bus.publish(
                message_type=message.type,
                data=message.data,
                sender_id=message.sender_id,
                priority=message.priority
            )
        else:
            # Move to dead letter queue
            self.dead_letter_queue.add_message(asdict(message), error)
            self.metrics["dead_letter_queue_size"] = len(self.dead_letter_queue.messages)
            
            logger.error(f"Message moved to dead letter queue after {self.retry_config.max_retries} retries")
    
    async def _handle_improvement_trigger(self, message) -> Dict[str, Any]:
        """Handle improvement trigger from Operational Supervisor to Gatekeeper"""
        trigger_data = message.data
        
        logger.info(f"Processing improvement trigger: {trigger_data.get('trigger_type')}")
        
        # Forward to Gatekeeper Supervisor (simplified implementation)
        # In a real system, this would route to the actual Gatekeeper Supervisor
        
        return {
            "status": "forwarded_to_gatekeeper",
            "trigger_id": trigger_data.get("trigger_id"),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_deployment_notification(self, message) -> Dict[str, Any]:
        """Handle deployment notification from Gatekeeper to Operational Supervisor"""
        deployment_data = message.data
        
        logger.info(f"Processing deployment notification: {deployment_data.get('deployment_id')}")
        
        # Forward to Operational Supervisor (simplified implementation)
        # In a real system, this would route to the actual Operational Supervisor
        
        return {
            "status": "forwarded_to_operational",
            "deployment_id": deployment_data.get("deployment_id"),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_bridge_health(self) -> Dict[str, Any]:
        """Get bridge health status"""
        return {
            "bridge_id": self.bridge_id,
            "status": self.status.value,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "is_running": self.is_running,
            "metrics": self.metrics,
            "dead_letter_queue_size": len(self.dead_letter_queue.messages),
            "last_health_check": datetime.now().isoformat()
        }
    
    def get_dead_letter_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages from dead letter queue"""
        return self.dead_letter_queue.get_messages(limit)
    
    async def replay_dead_letter_messages(self, message_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Replay messages from dead letter queue"""
        messages_to_replay = self.dead_letter_queue.get_messages()
        
        if message_ids:
            # Filter by specific message IDs (simplified implementation)
            pass
        
        replayed_count = 0
        failed_count = 0
        
        for dead_letter_entry in messages_to_replay:
            try:
                message_data = dead_letter_entry["message"]
                message_data["retry_count"] = 0  # Reset retry count
                
                # Republish message
                await self.message_bus.publish(
                    message_type=MessageType(message_data["type"]),
                    data=message_data["data"],
                    sender_id=message_data["sender_id"],
                    priority=MessagePriority(message_data["priority"])
                )
                
                replayed_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to replay dead letter message: {str(e)}")
        
        # Clear successfully replayed messages
        if replayed_count > 0:
            self.dead_letter_queue.clear()
        
        return {
            "replayed_count": replayed_count,
            "failed_count": failed_count,
            "timestamp": datetime.now().isoformat()
        }
