"""
Message Bus - Event-driven communication system for agents
"""
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict
import uuid

from voicehive.utils.exceptions import VoiceHiveError, ErrorHandler
from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class MessageType(Enum):
    """Types of messages in the system"""
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_STATUS_UPDATE = "agent_status_update"
    EMERGENCY_ALERT = "emergency_alert"
    IMPROVEMENT_TRIGGER = "improvement_trigger"
    DEPLOYMENT_NOTIFICATION = "deployment_notification"
    PERFORMANCE_METRIC = "performance_metric"
    SYSTEM_COMMAND = "system_command"
    HEALTH_CHECK = "health_check"


@dataclass
class Message:
    """Message structure for inter-agent communication"""
    id: str
    type: MessageType
    sender_id: str
    recipient_id: Optional[str]  # None for broadcast messages
    data: Dict[str, Any]
    priority: MessagePriority
    timestamp: datetime
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    correlation_id: Optional[str] = None


@dataclass
class Subscription:
    """Subscription to message types"""
    subscriber_id: str
    message_types: Set[MessageType]
    handler: Callable
    filter_func: Optional[Callable] = None
    active: bool = True


class MessageBus:
    """
    Event-driven communication system for agents
    
    Features:
    - Publish/Subscribe pattern
    - Message routing and filtering
    - Priority-based delivery
    - Message persistence and replay
    - Dead letter queue for failed messages
    - Circuit breaker for failed subscribers
    """
    
    def __init__(self):
        # Message storage
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_history: List[Message] = []
        self.dead_letter_queue: List[Message] = []
        
        # Subscriptions
        self.subscriptions: Dict[str, Subscription] = {}
        self.type_subscribers: Dict[MessageType, List[str]] = defaultdict(list)
        
        # Processing state
        self.is_running = False
        self.processing_task: Optional[asyncio.Task] = None
        
        # Circuit breaker for failed subscribers
        self.failed_subscribers: Dict[str, datetime] = {}
        self.circuit_breaker_timeout = timedelta(minutes=5)
        
        # Message retention
        self.max_history_size = 1000
        self.message_ttl = timedelta(hours=24)
        
        logger.info("Message Bus initialized with pub/sub communication system")
    
    async def start(self):
        """Start the message bus processing"""
        if self.is_running:
            logger.warning("Message bus is already running")
            return
        
        self.is_running = True
        self.processing_task = asyncio.create_task(self._process_messages())
        logger.info("Message Bus started and processing messages")
    
    async def stop(self):
        """Stop the message bus processing"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Message Bus stopped")
    
    async def publish(self, 
                     message_type: MessageType,
                     data: Dict[str, Any],
                     sender_id: str,
                     recipient_id: Optional[str] = None,
                     priority: MessagePriority = MessagePriority.NORMAL,
                     expires_in_seconds: Optional[int] = None,
                     correlation_id: Optional[str] = None) -> str:
        """
        Publish a message to the bus
        
        Args:
            message_type: Type of message
            data: Message payload
            sender_id: ID of the sending agent
            recipient_id: ID of specific recipient (None for broadcast)
            priority: Message priority
            expires_in_seconds: Message expiration time
            correlation_id: Correlation ID for message tracking
            
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        expires_at = None
        if expires_in_seconds:
            expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
        
        message = Message(
            id=message_id,
            type=message_type,
            sender_id=sender_id,
            recipient_id=recipient_id,
            data=data,
            priority=priority,
            timestamp=datetime.now(),
            expires_at=expires_at,
            correlation_id=correlation_id
        )
        
        # Add to queue for processing
        await self.message_queue.put(message)
        
        logger.debug(f"Message published: {message_type.value} from {sender_id} (ID: {message_id})")
        return message_id
    
    def subscribe(self, 
                 subscriber_id: str,
                 message_types: List[MessageType],
                 handler: Callable,
                 filter_func: Optional[Callable] = None) -> str:
        """
        Subscribe to message types
        
        Args:
            subscriber_id: Unique subscriber identifier
            message_types: List of message types to subscribe to
            handler: Async function to handle messages
            filter_func: Optional filter function for messages
            
        Returns:
            Subscription ID
        """
        subscription_id = f"{subscriber_id}_{uuid.uuid4().hex[:8]}"
        
        subscription = Subscription(
            subscriber_id=subscriber_id,
            message_types=set(message_types),
            handler=handler,
            filter_func=filter_func
        )
        
        self.subscriptions[subscription_id] = subscription
        
        # Update type-based subscriber mapping
        for msg_type in message_types:
            if subscription_id not in self.type_subscribers[msg_type]:
                self.type_subscribers[msg_type].append(subscription_id)
        
        logger.info(f"Subscriber {subscriber_id} subscribed to {len(message_types)} message types")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from messages"""
        if subscription_id not in self.subscriptions:
            return False
        
        subscription = self.subscriptions[subscription_id]
        
        # Remove from type-based mapping
        for msg_type in subscription.message_types:
            if subscription_id in self.type_subscribers[msg_type]:
                self.type_subscribers[msg_type].remove(subscription_id)
        
        # Remove subscription
        del self.subscriptions[subscription_id]
        
        logger.info(f"Subscription {subscription_id} removed")
        return True
    
    async def _process_messages(self):
        """Main message processing loop"""
        while self.is_running:
            try:
                # Get message with timeout to allow for graceful shutdown
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Check if message has expired
                if message.expires_at and datetime.now() > message.expires_at:
                    logger.warning(f"Message {message.id} expired, moving to dead letter queue")
                    self.dead_letter_queue.append(message)
                    continue
                
                # Process the message
                await self._deliver_message(message)
                
                # Add to history
                self._add_to_history(message)
                
            except asyncio.TimeoutError:
                # Timeout is expected for graceful shutdown
                continue
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
    
    async def _deliver_message(self, message: Message):
        """Deliver message to subscribers"""
        # Get subscribers for this message type
        subscriber_ids = self.type_subscribers.get(message.type, [])
        
        if not subscriber_ids:
            logger.debug(f"No subscribers for message type: {message.type.value}")
            return
        
        delivery_tasks = []
        
        for subscription_id in subscriber_ids:
            if subscription_id not in self.subscriptions:
                continue
            
            subscription = self.subscriptions[subscription_id]
            
            # Check if subscriber is in circuit breaker
            if self._is_subscriber_circuit_broken(subscription.subscriber_id):
                continue
            
            # Check recipient filter
            if message.recipient_id and message.recipient_id != subscription.subscriber_id:
                continue
            
            # Apply custom filter if provided
            if subscription.filter_func and not subscription.filter_func(message):
                continue
            
            # Create delivery task
            task = asyncio.create_task(
                self._deliver_to_subscriber(message, subscription)
            )
            delivery_tasks.append(task)
        
        # Wait for all deliveries to complete
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)
    
    async def _deliver_to_subscriber(self, message: Message, subscription: Subscription):
        """Deliver message to a specific subscriber"""
        try:
            await subscription.handler(message)
            logger.debug(f"Message {message.id} delivered to {subscription.subscriber_id}")
            
            # Reset circuit breaker on successful delivery
            if subscription.subscriber_id in self.failed_subscribers:
                del self.failed_subscribers[subscription.subscriber_id]
                
        except Exception as e:
            logger.error(f"Failed to deliver message {message.id} to {subscription.subscriber_id}: {str(e)}")
            
            # Increment retry count
            message.retry_count += 1
            
            if message.retry_count < message.max_retries:
                # Retry delivery
                await asyncio.sleep(2 ** message.retry_count)  # Exponential backoff
                await self.message_queue.put(message)
            else:
                # Move to dead letter queue and activate circuit breaker
                self.dead_letter_queue.append(message)
                self.failed_subscribers[subscription.subscriber_id] = datetime.now()
                logger.warning(f"Message {message.id} moved to dead letter queue after {message.max_retries} retries")
    
    def _is_subscriber_circuit_broken(self, subscriber_id: str) -> bool:
        """Check if subscriber circuit breaker is active"""
        if subscriber_id not in self.failed_subscribers:
            return False
        
        failure_time = self.failed_subscribers[subscriber_id]
        if datetime.now() - failure_time > self.circuit_breaker_timeout:
            # Circuit breaker timeout expired, remove from failed list
            del self.failed_subscribers[subscriber_id]
            return False
        
        return True
    
    def _add_to_history(self, message: Message):
        """Add message to history with size and TTL management"""
        self.message_history.append(message)
        
        # Trim history by size
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
        
        # Remove expired messages
        current_time = datetime.now()
        self.message_history = [
            msg for msg in self.message_history
            if current_time - msg.timestamp < self.message_ttl
        ]
    
    def get_message_history(self, 
                           message_type: Optional[MessageType] = None,
                           sender_id: Optional[str] = None,
                           limit: int = 100) -> List[Message]:
        """Get message history with optional filtering"""
        filtered_messages = self.message_history
        
        if message_type:
            filtered_messages = [msg for msg in filtered_messages if msg.type == message_type]
        
        if sender_id:
            filtered_messages = [msg for msg in filtered_messages if msg.sender_id == sender_id]
        
        return filtered_messages[-limit:]
    
    def get_dead_letter_messages(self, limit: int = 100) -> List[Message]:
        """Get messages from dead letter queue"""
        return self.dead_letter_queue[-limit:]
    
    def get_bus_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        return {
            "total_subscriptions": len(self.subscriptions),
            "active_subscribers": len(set(sub.subscriber_id for sub in self.subscriptions.values())),
            "message_history_size": len(self.message_history),
            "dead_letter_queue_size": len(self.dead_letter_queue),
            "failed_subscribers": len(self.failed_subscribers),
            "queue_size": self.message_queue.qsize(),
            "is_running": self.is_running
        }
