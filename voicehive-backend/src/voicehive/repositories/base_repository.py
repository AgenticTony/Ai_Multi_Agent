"""
VoiceHive Base Repository Pattern
Provides abstract base classes for data access layer
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository for data access operations"""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """Update entity"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity"""
        pass
    
    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List entities with pagination"""
        pass
    
    @abstractmethod
    async def search(self, criteria: Dict[str, Any]) -> List[T]:
        """Search entities by criteria"""
        pass


class InMemoryRepository(BaseRepository[T]):
    """In-memory repository implementation for development/testing"""
    
    def __init__(self):
        self._storage: Dict[str, T] = {}
        self._id_counter = 0
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        self._id_counter += 1
        return f"{self.__class__.__name__.lower()}_{self._id_counter}"
    
    async def create(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new entity"""
        entity_id = entity.get('id') or self._generate_id()
        entity['id'] = entity_id
        entity['created_at'] = datetime.utcnow().isoformat()
        entity['updated_at'] = datetime.utcnow().isoformat()
        
        self._storage[entity_id] = entity
        return entity
    
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID"""
        return self._storage.get(entity_id)
    
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update entity"""
        if entity_id not in self._storage:
            return None
        
        entity = self._storage[entity_id].copy()
        entity.update(updates)
        entity['updated_at'] = datetime.utcnow().isoformat()
        
        self._storage[entity_id] = entity
        return entity
    
    async def delete(self, entity_id: str) -> bool:
        """Delete entity"""
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List entities with pagination"""
        entities = list(self._storage.values())
        return entities[offset:offset + limit]
    
    async def search(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search entities by criteria"""
        results = []
        
        for entity in self._storage.values():
            match = True
            for key, value in criteria.items():
                if key not in entity or entity[key] != value:
                    match = False
                    break
            
            if match:
                results.append(entity)
        
        return results


class AppointmentRepository(InMemoryRepository):
    """Repository for appointment entities"""
    
    async def find_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Find appointments within date range"""
        results = []
        
        for appointment in self._storage.values():
            appointment_date = appointment.get('date', '')
            if start_date <= appointment_date <= end_date:
                results.append(appointment)
        
        return results
    
    async def find_by_phone(self, phone: str) -> List[Dict[str, Any]]:
        """Find appointments by phone number"""
        return await self.search({'phone': phone})
    
    async def find_available_slots(self, date: str) -> List[str]:
        """Find available time slots for a date"""
        # This would integrate with actual calendar system
        booked_times = []
        
        for appointment in self._storage.values():
            if appointment.get('date') == date and appointment.get('status') == 'confirmed':
                booked_times.append(appointment.get('time'))
        
        # Return available slots (simplified)
        all_slots = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
        return [slot for slot in all_slots if slot not in booked_times]


class LeadRepository(InMemoryRepository):
    """Repository for lead entities"""
    
    async def find_by_score_range(self, min_score: int, max_score: int) -> List[Dict[str, Any]]:
        """Find leads by score range"""
        results = []
        
        for lead in self._storage.values():
            score = lead.get('score', 0)
            if min_score <= score <= max_score:
                results.append(lead)
        
        return results
    
    async def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Find leads by status"""
        return await self.search({'status': status})
    
    async def find_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Find leads by source"""
        return await self.search({'source': source})


class NotificationRepository(InMemoryRepository):
    """Repository for notification entities"""
    
    async def find_by_recipient(self, recipient: str) -> List[Dict[str, Any]]:
        """Find notifications by recipient"""
        results = []
        
        for notification in self._storage.values():
            if (notification.get('phone') == recipient or 
                notification.get('email') == recipient):
                results.append(notification)
        
        return results
    
    async def find_pending(self) -> List[Dict[str, Any]]:
        """Find pending notifications"""
        return await self.search({'status': 'pending'})
    
    async def mark_as_sent(self, notification_id: str) -> bool:
        """Mark notification as sent"""
        result = await self.update(notification_id, {
            'status': 'sent',
            'sent_at': datetime.utcnow().isoformat()
        })
        return result is not None


# Repository factory for dependency injection
class RepositoryFactory:
    """Factory for creating repository instances"""
    
    def __init__(self):
        self._repositories = {}
    
    def get_appointment_repository(self) -> AppointmentRepository:
        """Get appointment repository instance"""
        if 'appointment' not in self._repositories:
            self._repositories['appointment'] = AppointmentRepository()
        return self._repositories['appointment']
    
    def get_lead_repository(self) -> LeadRepository:
        """Get lead repository instance"""
        if 'lead' not in self._repositories:
            self._repositories['lead'] = LeadRepository()
        return self._repositories['lead']
    
    def get_notification_repository(self) -> NotificationRepository:
        """Get notification repository instance"""
        if 'notification' not in self._repositories:
            self._repositories['notification'] = NotificationRepository()
        return self._repositories['notification']


# Global repository factory instance
_repository_factory: Optional[RepositoryFactory] = None


def get_repository_factory() -> RepositoryFactory:
    """Get the global repository factory instance"""
    global _repository_factory
    if _repository_factory is None:
        _repository_factory = RepositoryFactory()
    return _repository_factory
