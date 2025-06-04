# Memory System API Documentation

## Overview

The VoiceHive Memory System provides intelligent conversation memory and context management using Mem0 cloud integration with local fallback storage. This system enables personalized interactions, conversation history tracking, and comprehensive lead data storage.

## Architecture

```
Memory System Architecture
├── Mem0 Cloud Integration (Primary)
│   ├── Real-time memory storage
│   ├── Advanced search capabilities
│   └── Scalable cloud infrastructure
├── Local Fallback Storage (Secondary)
│   ├── In-memory storage
│   ├── Session-based organization
│   └── Automatic failover
└── Cache Layer (Performance)
    ├── Frequently accessed memories
    ├── TTL-based expiration
    └── LRU eviction
```

## Core Components

### 1. Mem0Integration Class

The main interface for memory operations.

```python
from memory.mem0 import memory_system

# Store conversation memory
result = memory_system.store_conversation_memory(
    session_id="call_123",
    call_id="vapi_456",
    user_name="John Doe",
    user_phone="+1234567890",
    query="I need to book an appointment",
    answer="I'd be happy to help you book an appointment. What date works for you?",
    tags=["appointment", "booking"],
    metadata={"intent": "booking", "urgency": "normal"}
)
```

### 2. Memory Storage Methods

#### `store_conversation_memory()`

Store conversation interactions with comprehensive metadata.

**Parameters:**
- `session_id` (str): Unique session identifier
- `call_id` (str): Call-specific identifier
- `user_name` (str, optional): Customer name
- `user_phone` (str, optional): Customer phone number
- `query` (str): User's message/question
- `answer` (str): Agent's response
- `tags` (List[str], optional): Categorization tags
- `metadata` (Dict[str, Any], optional): Additional context data

**Returns:**
```python
{
    "success": True,
    "memory_id": "mem_20241201_143022_123456",
    "mem0_id": "mem0_cloud_id_789",
    "message": "Memory stored successfully in Mem0",
    "storage": "mem0"  # or "fallback"
}
```

**Example:**
```python
result = await memory_system.store_conversation_memory(
    session_id="session_abc123",
    call_id="call_def456",
    user_name="Sarah Johnson",
    user_phone="+1555123456",
    query="Can I reschedule my appointment for next week?",
    answer="Of course! Let me check available slots for next week.",
    tags=["appointment", "reschedule", "customer_service"],
    metadata={
        "intent": "reschedule",
        "original_date": "2024-12-15",
        "customer_sentiment": "neutral"
    }
)
```

### 3. Memory Retrieval Methods

#### `retrieve_user_memories()`

Retrieve memories for a specific user using various identifiers.

**Parameters:**
- `user_identifier` (str): User identifier (phone, name, or session)
- `identifier_type` (str): Type of identifier ("phone", "name", "session_id")
- `limit` (int, optional): Maximum number of memories to retrieve (default: 10)

**Returns:**
```python
{
    "success": True,
    "memories": [
        {
            "id": "mem_20241201_143022_123456",
            "content": "User: Can I book an appointment?\nAgent: I'd be happy to help...",
            "metadata": {"intent": "booking", "timestamp": "2024-12-01T14:30:22Z"},
            "created_at": "2024-12-01T14:30:22Z",
            "source": "mem0"
        }
    ],
    "count": 1,
    "user_identifier": "+1555123456",
    "source": "mem0"
}
```

**Example:**
```python
# Retrieve by phone number
memories = await memory_system.retrieve_user_memories(
    user_identifier="+1555123456",
    identifier_type="phone",
    limit=5
)

# Retrieve by name
memories = await memory_system.retrieve_user_memories(
    user_identifier="Sarah Johnson",
    identifier_type="name",
    limit=3
)
```

#### `search_memories()`

Search memories by content with optional user filtering.

**Parameters:**
- `query` (str): Search query string
- `user_id` (str, optional): Filter by specific user
- `limit` (int, optional): Maximum results (default: 10)

**Returns:**
```python
{
    "success": True,
    "memories": [
        {
            "id": "mem_20241201_143022_123456",
            "content": "User: appointment booking\nAgent: available slots...",
            "score": 0.95,
            "metadata": {"intent": "booking"},
            "source": "mem0"
        }
    ],
    "count": 1,
    "query": "appointment",
    "source": "mem0"
}
```

**Example:**
```python
# Search for appointment-related conversations
results = await memory_system.search_memories(
    query="appointment booking",
    limit=10
)

# Search within specific user's memories
results = await memory_system.search_memories(
    query="reschedule",
    user_id="session_abc123",
    limit=5
)
```

### 4. Specialized Storage Methods

#### `store_lead_summary()`

Store comprehensive lead data and call summaries.

**Parameters:**
- `session_id` (str): Session identifier
- `call_id` (str): Call identifier
- `lead_data` (Dict[str, Any]): Lead information
- `transcript_summary` (str, optional): Call transcript summary

**Example:**
```python
lead_data = {
    "id": "lead_789",
    "name": "John Smith",
    "phone": "+1555987654",
    "email": "john@example.com",
    "company": "Tech Corp",
    "interest_level": "high",
    "budget": "$50,000",
    "timeline": "Q1 2024"
}

result = await memory_system.store_lead_summary(
    session_id="session_xyz789",
    call_id="call_abc123",
    lead_data=lead_data,
    transcript_summary="Customer interested in enterprise solution, budget confirmed, ready to proceed with demo."
)
```

#### `get_session_context()`

Get comprehensive context for a session including recent memories and user insights.

**Parameters:**
- `session_id` (str): Session identifier

**Returns:**
```python
{
    "session_id": "session_abc123",
    "recent_memories": [...],
    "user_context": {
        "total_interactions": 5,
        "last_interaction": "2024-12-01T14:30:22Z",
        "common_topics": ["appointments", "billing"],
        "sentiment_trend": "positive"
    },
    "recommendations": [
        "Customer has shown interest in premium features",
        "Previous appointment was rescheduled twice"
    ]
}
```

## Convenience Functions

The memory system provides simplified functions for common operations:

### Basic Operations

```python
from memory.mem0 import store_memory, get_user_memories, search_memories

# Store a memory
await store_memory(
    session_id="session_123",
    call_id="call_456",
    user_phone="+1555123456",
    query="User question",
    answer="Agent response"
)

# Get user memories
memories = get_user_memories("+1555123456", "phone", limit=5)

# Search memories
results = search_memories("appointment", limit=10)
```

### Specialized Functions

```python
from memory.mem0 import store_lead_memory, get_session_context

# Store lead data
await store_lead_memory(
    session_id="session_123",
    call_id="call_456",
    lead_data={"name": "John", "phone": "+1555123456"},
    transcript_summary="Interested in product demo"
)

# Get session context
context = get_session_context("session_123")
```

## Integration with Agent

### Automatic Memory Storage

The Roxy agent automatically stores conversation memories:

```python
class RoxyAgent:
    async def handle_message(self, call_id: str, user_message: str) -> str:
        # ... process message ...
        
        # Store conversation in memory
        await self._store_conversation_memory(
            call_id, customer_number, user_message, response
        )
        
        return response
```

### Memory-Aware Responses

The agent uses memory for personalized interactions:

```python
async def _generate_response_with_memory(self, history: list, call_id: str, customer_number: str) -> str:
    if customer_number:
        # Retrieve previous interactions
        memory_result = mem0.get_user_memories(customer_number, "phone", limit=3)
        
        if memory_result["success"] and memory_result["memories"]:
            # Add memory context to conversation
            context_messages.append({
                "role": "system",
                "content": f"Previous interactions: {memory_result['memories']}"
            })
```

## Error Handling

The memory system includes comprehensive error handling:

### Exception Types

```python
from app.utils.exceptions import (
    MemoryError,
    MemoryConnectionError,
    MemoryStorageError,
    MemoryRetrievalError
)

try:
    result = await memory_system.store_conversation_memory(...)
except MemoryConnectionError:
    # Handle connection issues
    logger.warning("Memory service unavailable, using fallback")
except MemoryStorageError:
    # Handle storage failures
    logger.error("Failed to store memory")
```

### Fallback Behavior

When Mem0 is unavailable, the system automatically falls back to local storage:

```python
# Automatic fallback
if self.mem0_client:
    try:
        # Try Mem0 first
        result = self.mem0_client.add(...)
    except Exception:
        # Fall back to local storage
        return self._store_fallback_memory(...)
else:
    # Use local storage directly
    return self._store_fallback_memory(...)
```

## Performance Optimization

### Caching

Memory results are cached for improved performance:

```python
from app.utils.cache import cache_memory_results

@cache_memory_results(ttl=300)  # Cache for 5 minutes
async def get_user_memories(user_id: str, identifier_type: str, limit: int = 10):
    return await memory_system.retrieve_user_memories(user_id, identifier_type, limit)
```

### Batching

For bulk operations, use batching to improve efficiency:

```python
# Batch memory storage
batch_memories = []
for conversation in conversations:
    batch_memories.append({
        "session_id": conversation.session_id,
        "query": conversation.query,
        "answer": conversation.answer
    })

# Process batch (implementation depends on Mem0 capabilities)
await memory_system.store_batch_memories(batch_memories)
```

## Configuration

Memory system configuration is managed through settings:

```python
# In app/config/settings.py
class Settings(BaseSettings):
    # Mem0 Configuration
    mem0_api_key: Optional[str] = Field(default=None, env="MEM0_API_KEY")
    mem0_timeout: int = Field(default=30, env="MEM0_TIMEOUT")
    mem0_max_retries: int = Field(default=3, env="MEM0_MAX_RETRIES")
    mem0_batch_size: int = Field(default=10, env="MEM0_BATCH_SIZE")
```

### Environment Variables

```bash
# Required for Mem0 integration
MEM0_API_KEY=your_mem0_api_key_here

# Optional configuration
MEM0_TIMEOUT=30
MEM0_MAX_RETRIES=3
MEM0_BATCH_SIZE=10
```

## Monitoring and Analytics

### Memory Statistics

```python
# Get memory system statistics
stats = memory_system.get_statistics()
print(f"Total memories stored: {stats['total_memories']}")
print(f"Mem0 success rate: {stats['mem0_success_rate']}%")
print(f"Fallback usage: {stats['fallback_usage']}%")
```

### Health Checks

```python
# Check memory system health
health = await memory_system.health_check()
if health["status"] == "healthy":
    print("Memory system is operational")
else:
    print(f"Memory system issues: {health['issues']}")
```

## Best Practices

### 1. Memory Organization

- Use consistent session IDs for related conversations
- Include relevant tags for easy categorization
- Store meaningful metadata for context

### 2. Performance

- Cache frequently accessed memories
- Use appropriate TTL values for different data types
- Implement batching for bulk operations

### 3. Error Handling

- Always handle memory service failures gracefully
- Implement retry logic for transient failures
- Use fallback storage when cloud service is unavailable

### 4. Privacy and Security

- Sanitize sensitive information before storage
- Implement data retention policies
- Use encryption for sensitive memory data

## Examples

### Complete Conversation Flow

```python
async def handle_customer_call():
    session_id = "session_" + generate_uuid()
    call_id = "call_" + generate_uuid()
    customer_phone = "+1555123456"
    
    # Check for existing customer context
    context = get_session_context(session_id)
    memories = get_user_memories(customer_phone, "phone", limit=3)
    
    if memories["success"] and memories["memories"]:
        print("Returning customer detected")
        # Use memory context for personalized greeting
    
    # Process conversation
    user_message = "I need to reschedule my appointment"
    agent_response = await generate_response_with_context(user_message, memories)
    
    # Store conversation
    await store_memory(
        session_id=session_id,
        call_id=call_id,
        user_phone=customer_phone,
        query=user_message,
        answer=agent_response,
        tags=["appointment", "reschedule"],
        metadata={"intent": "reschedule", "urgency": "normal"}
    )
    
    # If lead captured, store lead summary
    if lead_captured:
        await store_lead_memory(
            session_id=session_id,
            call_id=call_id,
            lead_data=lead_info,
            transcript_summary="Customer rescheduled appointment, showed interest in premium features"
        )
```

This comprehensive API documentation provides developers with all the information needed to effectively use the VoiceHive Memory System for building intelligent, context-aware voice applications.
