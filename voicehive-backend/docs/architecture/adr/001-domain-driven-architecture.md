# ADR-001: Domain-Driven Architecture Migration

## Status
Accepted

## Context
The VoiceHive backend was initially built with a flat application structure (`app/`) which worked well for the MVP phase. However, as the system grows to include multiple business domains (calls, appointments, leads, notifications) and integrates with various external services, we need a more scalable and maintainable architecture.

## Decision
We will migrate to a Domain-Driven Design (DDD) architecture with the following structure:

```
src/voicehive/
├── api/                    # API layer (controllers)
├── core/                   # Core application settings and config
├── domains/                # Business domains
│   ├── calls/             # Call handling domain
│   ├── appointments/      # Appointment management domain
│   ├── leads/             # Lead capture domain
│   └── notifications/     # Notification domain
├── models/                # Shared data models
├── services/              # Shared services
│   ├── ai/               # AI-related services
│   └── external/         # External service integrations
├── utils/                 # Utility functions
└── main.py               # Application entry point
```

## Consequences

### Positive
- **Clear Separation of Concerns**: Each domain encapsulates its own business logic
- **Scalability**: Easy to add new domains without affecting existing ones
- **Maintainability**: Developers can work on specific domains independently
- **Testing**: Domain-specific testing strategies
- **Team Organization**: Teams can own specific domains
- **Enterprise Readiness**: Follows industry best practices for large-scale applications

### Negative
- **Migration Complexity**: Requires careful migration of existing code
- **Learning Curve**: Team needs to understand DDD principles
- **Initial Overhead**: More complex structure for simple operations

## Implementation Plan
1. Create new package structure
2. Migrate core infrastructure (settings, main app)
3. Migrate API layer
4. Migrate domain services one by one
5. Update all imports and dependencies
6. Migrate tests to match new structure
7. Update documentation and deployment scripts

## Alternatives Considered
1. **Keep Flat Structure**: Simple but doesn't scale
2. **Microservices**: Too complex for current team size and requirements
3. **Layered Architecture**: Less flexible than DDD for business-focused development

## References
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Python Application Layout Best Practices](https://realpython.com/python-application-layouts/)
