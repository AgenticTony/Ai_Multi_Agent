# ADR-002: AI Service Architecture

## Status
Accepted

## Context
VoiceHive requires sophisticated AI capabilities for voice conversation handling, function calling, and memory management. We need to decide on the architecture for AI services that can support multiple AI providers, conversation management, and future enhancements like multi-agent systems.

## Decision
We will implement a layered AI service architecture with the following components:

```
voicehive/services/ai/
├── openai_service.py          # OpenAI integration
├── conversation_manager.py    # Conversation state management
├── function_registry.py       # Function calling registry
├── memory_service.py          # Memory persistence (Mem0)
└── agents/
    ├── base_agent.py          # Abstract base agent
    ├── roxy_agent.py          # Customer service agent
    └── supervisor_agent.py    # Multi-agent coordination (future)
```

### Key Architectural Decisions:

1. **Provider Abstraction**: Abstract AI provider interface to support multiple LLM providers
2. **Conversation Management**: Centralized conversation state and history management
3. **Function Registry**: Dynamic function registration and validation system
4. **Memory Integration**: Persistent memory using Mem0 for context retention
5. **Agent Framework**: Extensible agent system for specialized behaviors

## Consequences

### Positive
- **Provider Flexibility**: Easy to switch or add AI providers
- **Conversation Continuity**: Robust conversation state management
- **Function Extensibility**: Easy to add new function calling capabilities
- **Memory Persistence**: Long-term context retention across sessions
- **Agent Specialization**: Different agents for different use cases
- **Testing**: Mockable AI services for reliable testing

### Negative
- **Complexity**: More complex than direct API calls
- **Latency**: Additional abstraction layers may add latency
- **Memory Overhead**: Conversation and memory management requires storage

## Implementation Details

### AI Provider Interface
```python
class AIProvider(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[Message]) -> str:
        pass
    
    @abstractmethod
    async def function_call(self, messages: List[Message], functions: List[Function]) -> FunctionCall:
        pass
```

### Conversation Manager
- Manages conversation history per session
- Implements conversation memory limits
- Handles context window management
- Integrates with persistent memory service

### Function Registry
- Dynamic function registration
- Function validation and schema checking
- Permission-based function access
- Function call result handling

## Alternatives Considered

1. **Direct API Integration**: Simple but not scalable
2. **LangChain Framework**: Feature-rich but heavyweight for our needs
3. **Custom Agent Framework**: More control but higher development cost

## Migration Strategy
1. Create AI service abstractions
2. Migrate existing OpenAI integration
3. Implement conversation manager
4. Add function registry
5. Integrate memory service
6. Refactor agents to use new architecture

## References
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Mem0 Documentation](https://docs.mem0.ai/)
- [LangChain Agent Architecture](https://python.langchain.com/docs/modules/agents/)
