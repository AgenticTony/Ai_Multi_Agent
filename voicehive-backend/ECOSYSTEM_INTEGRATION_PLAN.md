# VoiceHive Ecosystem Integration Plan

## 🔍 Current Architecture Analysis

### Core Application (✅ Migrated)
- **Location**: `src/voicehive/`
- **Status**: Successfully migrated to domain-driven architecture
- **Import Pattern**: `voicehive.*`

### Ecosystem Components (🔄 Needs Integration)

#### 1. Function Calling Tools
- **Location**: `tools/`
- **Components**: `calendar.py`, `crm.py`, `notify.py`
- **Status**: Standalone, no imports from core
- **Integration**: Can remain standalone or integrate

#### 2. Memory Systems (⚠️ DUPLICATE)
- **New**: `src/voicehive/utils/memory_manager.py` (our creation)
- **Existing**: `memory/mem0.py` (production Mem0 integration)
- **Issue**: Two different memory systems
- **Solution**: Integrate both systems

#### 3. Monitoring & Observability
- **Location**: `monitoring/`
- **Components**: Prometheus, Grafana, alerts
- **Status**: Production-ready monitoring stack
- **Integration**: Keep as-is, add core app metrics

#### 4. Vertex AI Integration
- **Location**: `vertex/`
- **Components**: Feedback pipeline, monitoring, health checks
- **Status**: Advanced AI/ML pipeline
- **Integration**: Keep as-is, integrate with core

#### 5. Dashboard
- **Location**: `dashboard/`
- **Technology**: Next.js
- **Status**: Frontend monitoring dashboard
- **Integration**: Keep as-is, update API endpoints

#### 6. Improvements & Prompts
- **Location**: `improvements/`
- **Components**: Prompt management system
- **Status**: Standalone prompt optimization
- **Integration**: Integrate with core services

## 🎯 Integration Strategy

### Phase 1: Memory System Consolidation (Priority 1)

**Problem**: We have two memory systems:
1. `memory_manager.py` - Local caching and conversation management
2. `mem0.py` - Production Mem0 integration for persistent memory

**Solution**: Hybrid approach
- Use `memory_manager.py` for local caching and conversation cleanup
- Use `mem0.py` for persistent memory storage and retrieval
- Create unified interface in core application

### Phase 2: Tools Integration (Priority 2)

**Current**: Tools are standalone in `tools/` directory
**Recommendation**: Keep tools standalone but create service adapters

```python
# In src/voicehive/services/external/
from tools.calendar import CalendarTool
from tools.crm import CRMTool
from tools.notify import NotificationTool

class ExternalToolsService:
    def __init__(self):
        self.calendar = CalendarTool()
        self.crm = CRMTool()
        self.notify = NotificationTool()
```

### Phase 3: Import Path Standardization (Priority 3)

**Update all ecosystem components to use core services:**

```python
# Before (in tools/calendar.py)
# Standalone implementation

# After (in tools/calendar.py)
from voicehive.domains.appointments.services.appointment_service import AppointmentService
from voicehive.utils.exceptions import AppointmentServiceError
```

## 📋 Detailed Integration Tasks

### 1. Memory System Integration

#### Task 1.1: Create Unified Memory Interface
```python
# src/voicehive/services/memory/unified_memory_service.py
class UnifiedMemoryService:
    def __init__(self):
        self.local_manager = MemoryManager()  # For caching/cleanup
        self.persistent_memory = Mem0Integration()  # For long-term storage
```

#### Task 1.2: Update Domain Services
- Update appointment service to use unified memory
- Update lead service to use unified memory
- Update notification service to use unified memory

### 2. Tools Integration

#### Task 2.1: Create Service Adapters
- Create `ExternalToolsService` in `src/voicehive/services/external/`
- Wrap existing tools with error handling
- Add logging and monitoring

#### Task 2.2: Update Function Calling
- Update agent services to use new tool adapters
- Maintain backward compatibility
- Add proper error handling

### 3. Monitoring Integration

#### Task 3.1: Add Core App Metrics
- Add metrics to domain services
- Integrate with existing Prometheus setup
- Update Grafana dashboards

#### Task 3.2: Health Checks
- Add health endpoints to core app
- Integrate with existing monitoring

### 4. Test Suite Updates

#### Task 4.1: Update Import Paths
- Update all test files to use `voicehive.*` imports
- Fix broken test dependencies
- Add integration tests for ecosystem components

#### Task 4.2: Add Ecosystem Tests
- Test memory system integration
- Test tools integration
- Test monitoring integration

## 🚀 Implementation Priority

### High Priority (Complete Migration)
1. ✅ **Memory System Consolidation** - Critical for production
2. ✅ **Test Import Updates** - Required for validation
3. ✅ **Tools Service Adapters** - Required for function calling

### Medium Priority (Ecosystem Integration)
4. **Monitoring Integration** - Add core app metrics
5. **Vertex AI Integration** - Connect with core services
6. **Dashboard Updates** - Update API endpoints

### Low Priority (Optimization)
7. **Prompt Management Integration** - Optimize prompts
8. **Documentation Updates** - Update all docs
9. **Performance Optimization** - Optimize integrated system

## 📊 Benefits of Integration

### ✅ Completed Benefits
- **Consistent Architecture**: Domain-driven design throughout
- **Standardized Error Handling**: User-friendly vs technical messages
- **Memory Management**: TTL and cleanup for local caching
- **Import Consistency**: All core code uses `voicehive.*` pattern

### 🔄 Integration Benefits
- **Unified Memory**: Best of both local and persistent memory
- **Tool Consistency**: Standardized error handling for all tools
- **Monitoring**: Complete observability across ecosystem
- **Maintainability**: Single source of truth for core logic

## 🎯 Next Steps

1. **Validate Current Migration**: Run tests to ensure core migration works
2. **Implement Memory Integration**: Combine local and persistent memory
3. **Create Tool Adapters**: Wrap existing tools with core services
4. **Update Test Suite**: Fix all import paths and add integration tests
5. **Add Monitoring**: Integrate core app with existing monitoring stack

## 📝 Notes

- **Monorepo Approach**: Keep ecosystem components in root directories
- **Backward Compatibility**: Maintain existing APIs during transition
- **Incremental Integration**: Integrate one component at a time
- **Production Safety**: Test thoroughly before deploying integrated system
