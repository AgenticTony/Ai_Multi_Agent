"""
VoiceHive Memory Service - Unified interface for memory operations
Integrates with Mem0 cloud service and provides fallback capabilities
"""

import logging
import sys
import os
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

# Add memory directory to path for Mem0 integration
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'memory'))

from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)


class MemoryServiceInterface(ABC):
    """Abstract interface for memory services"""
    
    @abstractmethod
    async def store_conversation_memory(
        self,
        session_id: str,
        call_id: str,
        user_name: Optional[str] = None,
        user_phone: Optional[str] = None,
        query: str = "",
        answer: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store conversation memory"""
        pass
    
    @abstractmethod
    async def retrieve_user_memories(
        self,
        user_identifier: str,
        identifier_type: str = "session_id",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Retrieve user memories"""
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search memories by content"""
        pass
    
    @abstractmethod
    async def store_lead_summary(
        self,
        session_id: str,
        call_id: str,
        lead_data: Dict[str, Any],
        transcript_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store lead summary"""
        pass
    
    @abstractmethod
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        pass


class Mem0MemoryService(MemoryServiceInterface):
    """Mem0 cloud memory service implementation"""
    
    def __init__(self):
        self.settings = get_settings()
        self._mem0_integration = None
        self._initialize_mem0()
    
    def _initialize_mem0(self):
        """Initialize Mem0 integration"""
        try:
            from mem0 import Mem0Integration
            self._mem0_integration = Mem0Integration()
            logger.info("Mem0 memory service initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import Mem0: {e}")
            self._mem0_integration = None
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            self._mem0_integration = None
    
    async def store_conversation_memory(
        self,
        session_id: str,
        call_id: str,
        user_name: Optional[str] = None,
        user_phone: Optional[str] = None,
        query: str = "",
        answer: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store conversation memory using Mem0"""
        if not self._mem0_integration:
            return {"success": False, "error": "Mem0 not available"}
        
        try:
            result = self._mem0_integration.store_conversation_memory(
                session_id=session_id,
                call_id=call_id,
                user_name=user_name,
                user_phone=user_phone,
                query=query,
                answer=answer,
                tags=tags,
                metadata=metadata
            )
            return result
        except Exception as e:
            logger.error(f"Error storing conversation memory: {e}")
            return {"success": False, "error": str(e)}
    
    async def retrieve_user_memories(
        self,
        user_identifier: str,
        identifier_type: str = "session_id",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Retrieve user memories using Mem0"""
        if not self._mem0_integration:
            return {"success": False, "error": "Mem0 not available"}
        
        try:
            result = self._mem0_integration.retrieve_user_memories(
                user_identifier=user_identifier,
                identifier_type=identifier_type,
                limit=limit
            )
            return result
        except Exception as e:
            logger.error(f"Error retrieving user memories: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search memories using Mem0"""
        if not self._mem0_integration:
            return {"success": False, "error": "Mem0 not available"}
        
        try:
            result = self._mem0_integration.search_memories(
                query=query,
                user_id=user_id,
                limit=limit
            )
            return result
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return {"success": False, "error": str(e)}
    
    async def store_lead_summary(
        self,
        session_id: str,
        call_id: str,
        lead_data: Dict[str, Any],
        transcript_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store lead summary using Mem0"""
        if not self._mem0_integration:
            return {"success": False, "error": "Mem0 not available"}
        
        try:
            result = self._mem0_integration.store_lead_summary(
                session_id=session_id,
                call_id=call_id,
                lead_data=lead_data,
                transcript_summary=transcript_summary
            )
            return result
        except Exception as e:
            logger.error(f"Error storing lead summary: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context using Mem0"""
        if not self._mem0_integration:
            return {"success": False, "error": "Mem0 not available"}
        
        try:
            result = self._mem0_integration.get_session_context(session_id)
            return result
        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            return {"success": False, "error": str(e)}


class FallbackMemoryService(MemoryServiceInterface):
    """Fallback in-memory service when Mem0 is unavailable"""
    
    def __init__(self):
        self._memory_store: Dict[str, Any] = {}
        self._session_store: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("Fallback memory service initialized")
    
    async def store_conversation_memory(
        self,
        session_id: str,
        call_id: str,
        user_name: Optional[str] = None,
        user_phone: Optional[str] = None,
        query: str = "",
        answer: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store conversation memory in fallback storage"""
        memory_id = f"fallback_{session_id}_{call_id}"
        
        memory_data = {
            "id": memory_id,
            "session_id": session_id,
            "call_id": call_id,
            "user_name": user_name,
            "user_phone": user_phone,
            "query": query,
            "answer": answer,
            "tags": tags or [],
            "metadata": metadata or {},
            "storage": "fallback"
        }
        
        self._memory_store[memory_id] = memory_data
        
        if session_id not in self._session_store:
            self._session_store[session_id] = []
        self._session_store[session_id].append(memory_data)
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory stored in fallback storage",
            "storage": "fallback"
        }
    
    async def retrieve_user_memories(
        self,
        user_identifier: str,
        identifier_type: str = "session_id",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Retrieve user memories from fallback storage"""
        memories = []
        
        if identifier_type == "session_id" and user_identifier in self._session_store:
            memories = self._session_store[user_identifier][-limit:]
        
        return {
            "success": True,
            "memories": memories,
            "count": len(memories),
            "source": "fallback"
        }
    
    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search memories in fallback storage"""
        matching_memories = []
        
        for memory in self._memory_store.values():
            if query.lower() in memory.get("query", "").lower() or \
               query.lower() in memory.get("answer", "").lower():
                if not user_id or memory.get("session_id") == user_id:
                    matching_memories.append(memory)
        
        return {
            "success": True,
            "memories": matching_memories[:limit],
            "count": len(matching_memories),
            "source": "fallback"
        }
    
    async def store_lead_summary(
        self,
        session_id: str,
        call_id: str,
        lead_data: Dict[str, Any],
        transcript_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store lead summary in fallback storage"""
        lead_id = f"lead_{session_id}_{call_id}"
        
        lead_summary = {
            "id": lead_id,
            "session_id": session_id,
            "call_id": call_id,
            "lead_data": lead_data,
            "transcript_summary": transcript_summary,
            "storage": "fallback"
        }
        
        self._memory_store[lead_id] = lead_summary
        
        return {
            "success": True,
            "lead_id": lead_id,
            "message": "Lead summary stored in fallback storage",
            "storage": "fallback"
        }
    
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context from fallback storage"""
        session_memories = self._session_store.get(session_id, [])
        
        return {
            "session_id": session_id,
            "recent_memories": session_memories[-5:],
            "total_interactions": len(session_memories),
            "source": "fallback"
        }


class UnifiedMemoryService:
    """Unified memory service with automatic fallback"""
    
    def __init__(self):
        self.settings = get_settings()
        self._primary_service = Mem0MemoryService()
        self._fallback_service = FallbackMemoryService()
        
    async def _execute_with_fallback(self, operation: str, *args, **kwargs):
        """Execute operation with automatic fallback"""
        try:
            # Try primary service first
            result = await getattr(self._primary_service, operation)(*args, **kwargs)
            if result.get("success", False):
                return result
        except Exception as e:
            logger.warning(f"Primary memory service failed for {operation}: {e}")
        
        # Fallback to secondary service
        logger.info(f"Using fallback memory service for {operation}")
        return await getattr(self._fallback_service, operation)(*args, **kwargs)
    
    async def store_conversation_memory(self, *args, **kwargs):
        return await self._execute_with_fallback("store_conversation_memory", *args, **kwargs)
    
    async def retrieve_user_memories(self, *args, **kwargs):
        return await self._execute_with_fallback("retrieve_user_memories", *args, **kwargs)
    
    async def search_memories(self, *args, **kwargs):
        return await self._execute_with_fallback("search_memories", *args, **kwargs)
    
    async def store_lead_summary(self, *args, **kwargs):
        return await self._execute_with_fallback("store_lead_summary", *args, **kwargs)
    
    async def get_session_context(self, *args, **kwargs):
        return await self._execute_with_fallback("get_session_context", *args, **kwargs)
