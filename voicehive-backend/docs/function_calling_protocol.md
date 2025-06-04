# Function Calling Protocol Documentation

## Overview

The VoiceHive Function Calling Protocol enables the Roxy AI agent to execute specific actions during voice conversations. This system provides a standardized interface for tool integration, allowing the agent to perform tasks like booking appointments, capturing leads, sending notifications, and transferring calls.

## Architecture

```
Function Calling Flow
├── Vapi.ai Webhook
│   ├── Receives function call requests
│   ├── Validates parameters
│   └── Routes to appropriate handler
├── Roxy Agent
│   ├── Processes function calls
│   ├── Validates business logic
│   └── Coordinates tool execution
├── Integration Services
│   ├── Appointment Service
│   ├── Lead Service
│   ├── Notification Service
│   └── Transfer Service
└── Response Generation
    ├── Success responses
    ├── Error handling
    └── User feedback
```

## Function Call Structure

### Request Format

Function calls follow a standardized JSON structure:

```json
{
  "type": "function_call",
  "function_call": {
    "name": "book_appointment",
    "parameters": {
      "name": "John Doe",
      "phone": "+1555123456",
      "email": "john@example.com",
      "date": "2024-12-15",
      "time": "14:00",
      "service": "consultation"
    }
  },
  "call_id": "call_abc123",
  "session_id": "session_xyz789"
}
```

### Response Format

Function call responses include execution status and user feedback:

```json
{
  "success": true,
  "message": "Appointment booked successfully for John Doe on December 15th at 2:00 PM",
  "data": {
    "appointment_id": "apt_456789",
    "confirmation_code": "CONF123",
    "calendar_link": "https://calendar.example.com/event/456789"
  },
  "next_action": "send_confirmation"
}
```

## Available Functions

### 1. Appointment Booking

#### `book_appointment`

Books appointments in the calendar system.

**Parameters:**
- `name` (string, required): Customer name
- `phone` (string, required): Customer phone number
- `email` (string, optional): Customer email address
- `date` (string, required): Appointment date (YYYY-MM-DD)
- `time` (string, required): Appointment time (HH:MM)
- `service` (string, optional): Type of service requested
- `notes` (string, optional): Additional notes

**Example:**
```json
{
  "name": "book_appointment",
  "parameters": {
    "name": "Sarah Johnson",
    "phone": "+1555987654",
    "email": "sarah@example.com",
    "date": "2024-12-20",
    "time": "10:30",
    "service": "consultation",
    "notes": "First-time customer, interested in premium package"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Appointment booked for Sarah Johnson on December 20th at 10:30 AM",
  "data": {
    "appointment_id": "apt_789012",
    "confirmation_code": "CONF456",
    "calendar_link": "https://calendar.example.com/event/789012",
    "reminder_scheduled": true
  }
}
```

### 2. Lead Capture

#### `capture_lead`

Captures and stores lead information.

**Parameters:**
- `name` (string, required): Lead name
- `phone` (string, required): Lead phone number
- `email` (string, optional): Lead email address
- `company` (string, optional): Company name
- `interest` (string, optional): Area of interest
- `budget` (string, optional): Budget range
- `timeline` (string, optional): Decision timeline
- `source` (string, optional): Lead source

**Example:**
```json
{
  "name": "capture_lead",
  "parameters": {
    "name": "Michael Chen",
    "phone": "+1555456789",
    "email": "michael@techcorp.com",
    "company": "TechCorp Solutions",
    "interest": "enterprise_solution",
    "budget": "$50000-100000",
    "timeline": "Q1_2024",
    "source": "voice_call"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Thank you Michael! I've captured your information and someone will follow up with you soon.",
  "data": {
    "lead_id": "lead_345678",
    "lead_score": 85,
    "priority": "high",
    "assigned_to": "sales_team_1",
    "follow_up_scheduled": "2024-12-02T09:00:00Z"
  }
}
```

### 3. Notification Services

#### `send_confirmation`

Sends confirmation messages via SMS or email.

**Parameters:**
- `type` (string, required): "sms", "email", or "both"
- `phone` (string, optional): Phone number for SMS
- `email` (string, optional): Email address
- `message` (string, required): Confirmation message
- `template` (string, optional): Message template to use

**Example:**
```json
{
  "name": "send_confirmation",
  "parameters": {
    "type": "both",
    "phone": "+1555123456",
    "email": "customer@example.com",
    "message": "Your appointment is confirmed for December 15th at 2:00 PM",
    "template": "appointment_confirmation"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Confirmation sent successfully!",
  "data": {
    "sms_status": "delivered",
    "email_status": "sent",
    "delivery_id": "notif_567890"
  }
}
```

### 4. Call Transfer

#### `transfer_call`

Transfers the call to a human agent or department.

**Parameters:**
- `department` (string, required): Target department
- `reason` (string, required): Reason for transfer
- `priority` (string, optional): Transfer priority
- `context` (string, optional): Additional context

**Example:**
```json
{
  "name": "transfer_call",
  "parameters": {
    "department": "sales",
    "reason": "complex_pricing_inquiry",
    "priority": "high",
    "context": "Customer interested in enterprise package, needs custom pricing"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "I'm transferring you to a human agent now. Please hold for a moment.",
  "data": {
    "transfer_type": "human_agent",
    "department": "sales",
    "estimated_wait": "2-3 minutes",
    "queue_position": 2
  }
}
```

## Implementation Details

### Function Call Handler

The main function call handler in the Roxy agent:

```python
async def handle_function_call(self, call_id: str, function_name: str, parameters: Dict[str, Any]) -> FunctionCallResponse:
    """Handle function calls from the assistant"""
    try:
        logger.info(f"Function call for call {call_id}: {function_name} with parameters: {parameters}")
        
        # Route to appropriate handler
        if function_name == "book_appointment":
            return await self._handle_book_appointment(parameters)
        elif function_name == "capture_lead":
            return await self._handle_capture_lead(parameters)
        elif function_name == "send_confirmation":
            return await self._handle_send_confirmation(parameters)
        elif function_name == "transfer_call":
            return await self._handle_transfer_call(parameters)
        else:
            raise FunctionCallError(f"Unknown function: {function_name}")
            
    except Exception as e:
        logger.error(f"Error handling function call {function_name} for call {call_id}: {str(e)}")
        return FunctionCallResponse(
            success=False,
            message=f"Function call failed: {str(e)}"
        )
```

### Parameter Validation

Each function handler includes parameter validation:

```python
async def _handle_book_appointment(self, parameters: Dict[str, Any]) -> FunctionCallResponse:
    """Handle appointment booking"""
    try:
        # Validate parameters using Pydantic model
        appointment_request = AppointmentRequest(**parameters)
        
        # Additional business logic validation
        if not self._is_valid_appointment_time(appointment_request.date, appointment_request.time):
            return FunctionCallResponse(
                success=False,
                message="Sorry, that time slot is not available. Please choose a different time."
            )
        
        # Execute the booking
        result = await self.appointment_service.book_appointment(appointment_request)
        
        return FunctionCallResponse(
            success=True,
            message=f"Appointment booked for {appointment_request.name} on {appointment_request.date} at {appointment_request.time}",
            data=result
        )
        
    except ValidationError as e:
        return FunctionCallResponse(
            success=False,
            message="Please provide all required information for booking."
        )
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        return FunctionCallResponse(
            success=False,
            message="Failed to book appointment. Please try again or speak with a human agent."
        )
```

## Error Handling

### Error Types

The system handles various error scenarios:

1. **Validation Errors**: Invalid or missing parameters
2. **Business Logic Errors**: Conflicts or rule violations
3. **Service Errors**: External service failures
4. **Network Errors**: Connectivity issues

### Error Response Format

```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Please provide a valid phone number",
  "details": {
    "field": "phone",
    "provided_value": "invalid_phone",
    "expected_format": "+1XXXXXXXXXX"
  }
}
```

### Retry Logic

For transient failures, the system implements automatic retry:

```python
from app.utils.retry import retry_on_failure

@retry_on_failure(max_attempts=3, base_delay=1.0)
async def execute_function_call(self, function_name: str, parameters: Dict[str, Any]):
    """Execute function call with retry logic"""
    return await self._execute_function(function_name, parameters)
```

## Integration with OpenAI

### Function Definitions

Functions are defined for OpenAI's function calling:

```python
FUNCTION_DEFINITIONS = [
    {
        "name": "book_appointment",
        "description": "Book an appointment for the customer",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Customer's full name"
                },
                "phone": {
                    "type": "string",
                    "description": "Customer's phone number in format +1XXXXXXXXXX"
                },
                "date": {
                    "type": "string",
                    "description": "Appointment date in YYYY-MM-DD format"
                },
                "time": {
                    "type": "string",
                    "description": "Appointment time in HH:MM format (24-hour)"
                }
            },
            "required": ["name", "phone", "date", "time"]
        }
    }
]
```

### Function Call Detection

The agent detects when to call functions based on conversation context:

```python
async def generate_response(self, system_prompt: str, messages: List[ConversationMessage]) -> str:
    """Generate response with function calling capability"""
    
    response = await self.client.chat.completions.create(
        model=self.model,
        messages=formatted_messages,
        functions=FUNCTION_DEFINITIONS,
        function_call="auto",  # Let OpenAI decide when to call functions
        max_tokens=self.max_tokens,
        temperature=self.temperature
    )
    
    # Check if a function was called
    if response.choices[0].message.function_call:
        function_call = response.choices[0].message.function_call
        
        # Execute the function
        result = await self.agent.handle_function_call(
            call_id=self.current_call_id,
            function_name=function_call.name,
            parameters=json.loads(function_call.arguments)
        )
        
        return result.message
    
    return response.choices[0].message.content
```

## Testing Function Calls

### Unit Tests

```python
import pytest
from app.services.agents.roxy_agent import RoxyAgent

@pytest.mark.asyncio
async def test_book_appointment_success():
    agent = RoxyAgent()
    
    parameters = {
        "name": "Test User",
        "phone": "+1555123456",
        "date": "2024-12-15",
        "time": "14:00"
    }
    
    result = await agent.handle_function_call("test_call", "book_appointment", parameters)
    
    assert result.success is True
    assert "appointment booked" in result.message.lower()
    assert "appointment_id" in result.data

@pytest.mark.asyncio
async def test_invalid_parameters():
    agent = RoxyAgent()
    
    parameters = {
        "name": "Test User"
        # Missing required parameters
    }
    
    result = await agent.handle_function_call("test_call", "book_appointment", parameters)
    
    assert result.success is False
    assert "required information" in result.message.lower()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_appointment_booking():
    """Test complete appointment booking workflow"""
    
    # Simulate Vapi webhook call
    webhook_data = {
        "type": "function_call",
        "function_call": {
            "name": "book_appointment",
            "parameters": {
                "name": "Integration Test User",
                "phone": "+1555999888",
                "date": "2024-12-20",
                "time": "10:00"
            }
        },
        "call_id": "test_call_123"
    }
    
    # Process through webhook handler
    response = await process_vapi_webhook(webhook_data)
    
    # Verify response
    assert response["success"] is True
    assert "appointment booked" in response["message"].lower()
    
    # Verify appointment was actually created
    appointment = await get_appointment(response["data"]["appointment_id"])
    assert appointment is not None
    assert appointment["customer_name"] == "Integration Test User"
```

## Performance Optimization

### Caching Function Results

```python
from app.utils.cache import cached

@cached(ttl=300, cache_name="appointments")
async def check_appointment_availability(date: str, time: str) -> bool:
    """Check if appointment slot is available (cached for 5 minutes)"""
    return await self.calendar_service.check_availability(date, time)
```

### Batching Operations

For multiple function calls, implement batching:

```python
async def handle_batch_function_calls(self, calls: List[Dict[str, Any]]) -> List[FunctionCallResponse]:
    """Handle multiple function calls efficiently"""
    
    # Group calls by type for batch processing
    grouped_calls = self._group_calls_by_type(calls)
    
    results = []
    for call_type, call_list in grouped_calls.items():
        if call_type == "book_appointment":
            batch_results = await self._batch_book_appointments(call_list)
            results.extend(batch_results)
        # Handle other call types...
    
    return results
```

## Security Considerations

### Parameter Sanitization

```python
def sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize function call parameters"""
    
    sanitized = {}
    for key, value in parameters.items():
        if isinstance(value, str):
            # Remove potentially harmful characters
            sanitized[key] = re.sub(r'[<>"\']', '', value).strip()
        else:
            sanitized[key] = value
    
    return sanitized
```

### Rate Limiting

```python
from app.utils.rate_limiter import RateLimiter

rate_limiter = RateLimiter(max_calls=10, window=60)  # 10 calls per minute

async def handle_function_call(self, call_id: str, function_name: str, parameters: Dict[str, Any]):
    """Handle function call with rate limiting"""
    
    if not await rate_limiter.allow_request(call_id):
        return FunctionCallResponse(
            success=False,
            message="Too many requests. Please wait a moment before trying again."
        )
    
    return await self._execute_function_call(function_name, parameters)
```

## Monitoring and Analytics

### Function Call Metrics

```python
from app.utils.metrics import track_function_call

async def handle_function_call(self, call_id: str, function_name: str, parameters: Dict[str, Any]):
    """Handle function call with metrics tracking"""
    
    start_time = time.time()
    
    try:
        result = await self._execute_function_call(function_name, parameters)
        
        # Track successful call
        track_function_call(
            function_name=function_name,
            success=result.success,
            duration=time.time() - start_time,
            call_id=call_id
        )
        
        return result
        
    except Exception as e:
        # Track failed call
        track_function_call(
            function_name=function_name,
            success=False,
            duration=time.time() - start_time,
            error=str(e),
            call_id=call_id
        )
        raise
```

## Best Practices

### 1. Function Design

- Keep functions focused on single responsibilities
- Use clear, descriptive parameter names
- Provide comprehensive parameter validation
- Include helpful error messages

### 2. Error Handling

- Implement graceful degradation for service failures
- Provide user-friendly error messages
- Log detailed error information for debugging
- Use retry logic for transient failures

### 3. Performance

- Cache frequently accessed data
- Implement batching for bulk operations
- Use async/await for non-blocking operations
- Monitor function call performance

### 4. Security

- Validate and sanitize all input parameters
- Implement rate limiting to prevent abuse
- Use proper authentication for external services
- Log security-relevant events

This comprehensive documentation provides developers with everything needed to understand, implement, and extend the VoiceHive Function Calling Protocol.
