"""
VoiceHive Dependency Injection Container
Manages service lifecycle and dependencies using the Dependency Injection pattern
"""

import logging
from typing import Dict, Any, TypeVar, Type, Optional, Callable
from functools import lru_cache
import asyncio
from contextlib import asynccontextmanager

from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceContainer:
    """
    Dependency Injection Container for managing service lifecycle and dependencies
    
    Features:
    - Singleton service management
    - Lazy initialization
    - Dependency resolution
    - Lifecycle management (startup/shutdown)
    - Configuration injection
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._startup_hooks: list = []
        self._shutdown_hooks: list = []
        self.settings = get_settings()
        
    def register_singleton(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a singleton service with its factory function"""
        service_name = service_type.__name__
        self._factories[service_name] = factory
        logger.debug(f"Registered singleton service: {service_name}")
        
    def register_transient(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a transient service (new instance each time)"""
        service_name = service_type.__name__
        self._services[service_name] = factory
        logger.debug(f"Registered transient service: {service_name}")
        
    def get(self, service_type: Type[T]) -> T:
        """Get a service instance, creating it if necessary"""
        service_name = service_type.__name__
        
        # Check if it's a singleton
        if service_name in self._factories:
            if service_name not in self._singletons:
                logger.debug(f"Creating singleton instance: {service_name}")
                self._singletons[service_name] = self._factories[service_name]()
            return self._singletons[service_name]
        
        # Check if it's a transient service
        if service_name in self._services:
            logger.debug(f"Creating transient instance: {service_name}")
            return self._services[service_name]()
        
        raise ValueError(f"Service {service_name} not registered")
    
    def add_startup_hook(self, hook: Callable) -> None:
        """Add a startup hook to be called during container initialization"""
        self._startup_hooks.append(hook)
        
    def add_shutdown_hook(self, hook: Callable) -> None:
        """Add a shutdown hook to be called during container cleanup"""
        self._shutdown_hooks.append(hook)
        
    async def startup(self) -> None:
        """Initialize all services and run startup hooks"""
        logger.info("Starting service container...")
        
        for hook in self._startup_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as e:
                logger.error(f"Error in startup hook: {e}")
                raise
                
        logger.info("Service container started successfully")
        
    async def shutdown(self) -> None:
        """Cleanup services and run shutdown hooks"""
        logger.info("Shutting down service container...")
        
        for hook in reversed(self._shutdown_hooks):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as e:
                logger.error(f"Error in shutdown hook: {e}")
                
        # Clear singletons
        self._singletons.clear()
        logger.info("Service container shutdown complete")


# Global container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container instance"""
    global _container
    if _container is None:
        _container = ServiceContainer()
        _configure_services(_container)
    return _container


def _configure_services(container: ServiceContainer) -> None:
    """Configure all services in the container"""
    from voicehive.services.ai.openai_service import OpenAIService
    from voicehive.domains.appointments.services.appointment_service import AppointmentService
    from voicehive.domains.leads.services.lead_service import LeadService
    from voicehive.domains.notifications.services.notification_service import NotificationService
    
    # Register services as singletons
    container.register_singleton(OpenAIService, lambda: OpenAIService())
    container.register_singleton(AppointmentService, lambda: AppointmentService())
    container.register_singleton(LeadService, lambda: LeadService())
    container.register_singleton(NotificationService, lambda: NotificationService())
    
    logger.info("Service container configured with all services")


@asynccontextmanager
async def container_lifespan():
    """Context manager for container lifecycle"""
    container = get_container()
    await container.startup()
    try:
        yield container
    finally:
        await container.shutdown()


# Dependency injection decorators
def inject(service_type: Type[T]) -> T:
    """Dependency injection decorator/function"""
    return get_container().get(service_type)


class Inject:
    """Dependency injection descriptor for class attributes"""
    
    def __init__(self, service_type: Type[T]):
        self.service_type = service_type
        self.service_name = f"_{service_type.__name__.lower()}"
        
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        if not hasattr(obj, self.service_name):
            service = get_container().get(self.service_type)
            setattr(obj, self.service_name, service)
        
        return getattr(obj, self.service_name)


# Service factory functions with proper configuration injection
def create_openai_service():
    """Factory function for OpenAI service with configuration"""
    from voicehive.services.ai.openai_service import OpenAIService
    return OpenAIService()


def create_mem0_service():
    """Factory function for Mem0 service with configuration"""
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'memory'))
    
    try:
        from mem0 import Mem0Integration
        return Mem0Integration()
    except ImportError:
        logger.warning("Mem0 not available, using fallback")
        return None


# Memory management integration
def setup_memory_integration(container: ServiceContainer) -> None:
    """Setup memory integration with proper service management"""
    mem0_service = create_mem0_service()
    if mem0_service:
        container._singletons['Mem0Integration'] = mem0_service
        logger.info("Mem0 integration configured in service container")


# Health check integration
def validate_services(container: ServiceContainer) -> Dict[str, bool]:
    """Validate all registered services are properly configured"""
    validation_results = {}
    
    for service_name in container._factories.keys():
        try:
            service = container.get(eval(service_name))
            validation_results[service_name] = service is not None
        except Exception as e:
            logger.error(f"Service validation failed for {service_name}: {e}")
            validation_results[service_name] = False
            
    return validation_results
