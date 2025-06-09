# Project Reorganization Summary

This document summarizes the successful reorganization of the VoiceHive project to a Domain-Driven Design (DDD) architecture. This effort was undertaken to improve scalability, maintainability, and clarity of the codebase.

## 🏛️ Core Architectural Changes

The project's structure was refactored from a feature-based layout to a domain-centric one. The core business logic is now located in `src/voicehive/domains/`.

### Key Domains

- **`/domains/agents`**: Contains the logic for all autonomous agents, including the `PromptAgent` (the writer) and the `SupervisorAgent` (the gatekeeper).
- **`/domains/prompts`**: Manages the lifecycle of prompts, including versioning and storage, via the `PromptManager`.
- **`/domains/feedback`**: Orchestrates the complete autonomous feedback loop. It now contains the `CompleteFeedbackPipeline` and all related `VertexFeedbackService` logic.
- **`/domains/calls`**: Manages the core call-handling logic, including the main `RoxyAgent`.
- **`/domains/appointments`**: Handles appointment scheduling and management.
- **`/domains/leads`**: Manages lead data and qualification.
- **`/domains/notifications`**: Handles sending notifications (e.g., SMS, email).

### Other Key Directories

- **`/api`**: Contains all API endpoint definitions, separating the presentation layer from business logic.
- **`/services`**: Holds generic, cross-domain services like the `OpenAIService`.
- **`/data`**: External data, such as prompt versions, is stored here, completely separate from the application code.

## ✅ Summary of Changes

- **File Relocation**: All key service files were moved into their respective domain directories (e.g., `prompt_manager.py` → `domains/prompts/services/`).
- **Standardized Imports**: All import paths have been updated to the consistent `voicehive.*` format, improving code navigation.
- **Data Separation**: Prompt data has been moved to the `data/` directory.
- **Vertex Service Integration**: The `vertex` services were moved into the `domains/feedback/services/vertex/` directory to create a fully consistent DDD structure.
- **Cleanup**: The legacy `improvements/` and top-level `vertex/` directories have been removed.

## 🎯 Benefits

- **Clear Separation of Concerns**: Each business domain is self-contained.
- **Improved Scalability**: New features or domains can be added with minimal impact on existing code.
- **Enhanced Testability**: Domains can be tested independently.
- **Consistent Architecture**: The entire backend now follows a single, predictable design pattern.
