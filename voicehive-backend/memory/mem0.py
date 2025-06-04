"""
Mem0 Memory Integration - Real-time memory for voice agent conversations
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

# Mem0 imports
try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    Memory = None

logger = logging.getLogger(__name__)


@dataclass
class MemoryRecord:
    """Memory record data structure"""
    id: str
    session_id: str
    call_id: str
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    query: str = ""
    answer: str = ""
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class Mem0Integration:
    """Mem0 memory integration for voice agent"""
    
    def __init__(self):
        self.mem0_client = None
        self.fallback_memory: Dict[str, MemoryRecord] = {}
        self.session_memories: Dict[str, List[str]] = {}
        
        # Initialize Mem0 client
        if MEM0_AVAILABLE:
            try:
                api_key = os.getenv('MEM0_API_KEY')
                if api_key:
                    self.mem0_client = Memory(api_key=api_key)
                    logger.info("Mem0 client initialized successfully")
                else:
                    logger.warning("MEM0_API_KEY not found in environment variables")
            except Exception as e:
                logger.error(f"Failed to initialize Mem0 client: {str(e)}")
        else:
            logger.warning("Mem0 library not available, using fallback memory")
    
    def store_conversation_memory(self, session_id: str, call_id: str, 
                                user_name: str = None, user_phone: str = None,
                                query: str = "", answer: str = "", 
                                tags: List[str] = None, 
                                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store conversation memory in Mem0
        
        Args:
            session_id: Unique session identifier
            call_id: Unique call identifier
            user_name: User's name
            user_phone: User's phone number
            query: User's query/question
            answer: Agent's response
            tags: Memory tags for categorization
            metadata: Additional metadata
            
        Returns:
            Storage result
        """
        try:
            # Generate memory ID
            memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Prepare memory content
            memory_content = f"User: {query}\nAgent: {answer}"
            
            # Prepare metadata
            full_metadata = {
                "session_id": session_id,
                "call_id": call_id,
                "user_name": user_name,
                "user_phone": user_phone,
                "timestamp": datetime.utcnow().isoformat(),
                "memory_type": "conversation",
                **(metadata or {})
            }
            
            # Add tags
            memory_tags = tags or []
            if user_name:
                memory_tags.append(f"user:{user_name}")
            if user_phone:
                memory_tags.append(f"phone:{user_phone}")
            memory_tags.extend(["conversation", "voice_call"])
            
            if self.mem0_client:
                try:
                    # Store in Mem0
                    result = self.mem0_client.add(
                        messages=[{
                            "role": "user",
                            "content": memory_content
                        }],
                        user_id=session_id,
                        metadata=full_metadata
                    )
                    
                    # Track session memories
                    if session_id not in self.session_memories:
                        self.session_memories[session_id] = []
                    self.session_memories[session_id].append(memory_id)
                    
                    logger.info(f"Memory stored in Mem0: {memory_id} for session {session_id}")
                    
                    return {
                        "success": True,
                        "memory_id": memory_id,
                        "mem0_id": result.get("id") if result else None,
                        "message": "Memory stored successfully in Mem0",
                        "storage": "mem0"
                    }
                    
                except Exception as e:
                    logger.error(f"Error storing in Mem0: {str(e)}")
                    # Fall back to local storage
                    return self._store_fallback_memory(
                        memory_id, session_id, call_id, user_name, user_phone,
                        query, answer, memory_tags, full_metadata
                    )
            else:
                # Use fallback storage
                return self._store_fallback_memory(
                    memory_id, session_id, call_id, user_name, user_phone,
                    query, answer, memory_tags, full_metadata
                )
                
        except Exception as e:
            logger.error(f"Error storing conversation memory: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to store memory: {str(e)}"
            }
    
    def retrieve_user_memories(self, user_identifier: str, 
                             identifier_type: str = "session_id",
                             limit: int = 10) -> Dict[str, Any]:
        """
        Retrieve memories for a user
        
        Args:
            user_identifier: User identifier (session_id, phone, name)
            identifier_type: Type of identifier (session_id, phone, name)
            limit: Maximum number of memories to retrieve
            
        Returns:
            Retrieved memories
        """
        try:
            if self.mem0_client and identifier_type == "session_id":
                try:
                    # Retrieve from Mem0
                    memories = self.mem0_client.get_all(user_id=user_identifier, limit=limit)
                    
                    formatted_memories = []
                    for memory in memories:
                        formatted_memories.append({
                            "id": memory.get("id"),
                            "content": memory.get("memory"),
                            "metadata": memory.get("metadata", {}),
                            "created_at": memory.get("created_at"),
                            "source": "mem0"
                        })
                    
                    logger.info(f"Retrieved {len(formatted_memories)} memories from Mem0 for {user_identifier}")
                    
                    return {
                        "success": True,
                        "memories": formatted_memories,
                        "count": len(formatted_memories),
                        "user_identifier": user_identifier,
                        "source": "mem0"
                    }
                    
                except Exception as e:
                    logger.error(f"Error retrieving from Mem0: {str(e)}")
                    # Fall back to local search
                    return self._search_fallback_memories(user_identifier, identifier_type, limit)
            else:
                # Use fallback search
                return self._search_fallback_memories(user_identifier, identifier_type, limit)
                
        except Exception as e:
            logger.error(f"Error retrieving user memories: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to retrieve memories: {str(e)}"
            }
    
    def search_memories(self, query: str, user_id: str = None, 
                       limit: int = 5) -> Dict[str, Any]:
        """
        Search memories by content
        
        Args:
            query: Search query
            user_id: Optional user ID to filter by
            limit: Maximum number of results
            
        Returns:
            Search results
        """
        try:
            if self.mem0_client:
                try:
                    # Search in Mem0
                    results = self.mem0_client.search(
                        query=query,
                        user_id=user_id,
                        limit=limit
                    )
                    
                    formatted_results = []
                    for result in results:
                        formatted_results.append({
                            "id": result.get("id"),
                            "content": result.get("memory"),
                            "score": result.get("score", 0),
                            "metadata": result.get("metadata", {}),
                            "source": "mem0"
                        })
                    
                    logger.info(f"Found {len(formatted_results)} memories matching '{query}'")
                    
                    return {
                        "success": True,
                        "results": formatted_results,
                        "count": len(formatted_results),
                        "query": query,
                        "source": "mem0"
                    }
                    
                except Exception as e:
                    logger.error(f"Error searching Mem0: {str(e)}")
                    # Fall back to local search
                    return self._search_fallback_content(query, user_id, limit)
            else:
                # Use fallback search
                return self._search_fallback_content(query, user_id, limit)
                
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to search memories: {str(e)}"
            }
    
    def store_lead_summary(self, session_id: str, call_id: str, 
                          lead_data: Dict[str, Any], 
                          transcript_summary: str = "") -> Dict[str, Any]:
        """
        Store lead data and call summary
        
        Args:
            session_id: Session identifier
            call_id: Call identifier
            lead_data: Lead information
            transcript_summary: Summary of the call transcript
            
        Returns:
            Storage result
        """
        try:
            # Prepare memory content for lead
            memory_content = f"""
Lead Information:
Name: {lead_data.get('name', 'Unknown')}
Phone: {lead_data.get('phone', 'Unknown')}
Email: {lead_data.get('email', 'Not provided')}
Interest: {lead_data.get('interest', 'Not specified')}
Issue: {lead_data.get('issue', 'Not specified')}

Call Summary: {transcript_summary}
"""
            
            # Prepare metadata
            metadata = {
                "session_id": session_id,
                "call_id": call_id,
                "memory_type": "lead_summary",
                "lead_id": lead_data.get('id'),
                "lead_score": lead_data.get('score', 0),
                "timestamp": datetime.utcnow().isoformat(),
                **lead_data
            }
            
            # Tags for lead memory
            tags = [
                "lead", "call_summary", 
                f"score:{lead_data.get('score', 0)}",
                f"status:{lead_data.get('status', 'new')}"
            ]
            
            if lead_data.get('name'):
                tags.append(f"name:{lead_data['name']}")
            if lead_data.get('phone'):
                tags.append(f"phone:{lead_data['phone']}")
            
            return self.store_conversation_memory(
                session_id=session_id,
                call_id=call_id,
                user_name=lead_data.get('name'),
                user_phone=lead_data.get('phone'),
                query="Lead capture and call summary",
                answer=memory_content,
                tags=tags,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error storing lead summary: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to store lead summary: {str(e)}"
            }
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation context for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session context and recent memories
        """
        try:
            # Get recent memories for this session
            memories_result = self.retrieve_user_memories(session_id, "session_id", limit=5)
            
            if not memories_result["success"]:
                return memories_result
            
            memories = memories_result["memories"]
            
            # Extract context information
            context = {
                "session_id": session_id,
                "total_interactions": len(memories),
                "recent_topics": [],
                "user_info": {},
                "last_interaction": None
            }
            
            # Analyze memories for context
            for memory in memories:
                metadata = memory.get("metadata", {})
                
                # Extract user info
                if metadata.get("user_name") and not context["user_info"].get("name"):
                    context["user_info"]["name"] = metadata["user_name"]
                if metadata.get("user_phone") and not context["user_info"].get("phone"):
                    context["user_info"]["phone"] = metadata["user_phone"]
                
                # Track last interaction
                if not context["last_interaction"] or memory.get("created_at", "") > context["last_interaction"]:
                    context["last_interaction"] = memory.get("created_at")
            
            return {
                "success": True,
                "context": context,
                "recent_memories": memories[:3]  # Most recent 3
            }
            
        except Exception as e:
            logger.error(f"Error getting session context: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get session context: {str(e)}"
            }
    
    def _store_fallback_memory(self, memory_id: str, session_id: str, call_id: str,
                              user_name: str, user_phone: str, query: str, 
                              answer: str, tags: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store memory in fallback local storage"""
        try:
            memory_record = MemoryRecord(
                id=memory_id,
                session_id=session_id,
                call_id=call_id,
                user_name=user_name,
                user_phone=user_phone,
                query=query,
                answer=answer,
                tags=tags,
                metadata=metadata
            )
            
            self.fallback_memory[memory_id] = memory_record
            
            # Track session memories
            if session_id not in self.session_memories:
                self.session_memories[session_id] = []
            self.session_memories[session_id].append(memory_id)
            
            logger.info(f"Memory stored in fallback storage: {memory_id}")
            
            return {
                "success": True,
                "memory_id": memory_id,
                "message": "Memory stored in fallback storage",
                "storage": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Error storing fallback memory: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to store fallback memory: {str(e)}"
            }
    
    def _search_fallback_memories(self, user_identifier: str, identifier_type: str, 
                                 limit: int) -> Dict[str, Any]:
        """Search memories in fallback storage"""
        try:
            results = []
            
            for memory in self.fallback_memory.values():
                match = False
                
                if identifier_type == "session_id" and memory.session_id == user_identifier:
                    match = True
                elif identifier_type == "phone" and memory.user_phone == user_identifier:
                    match = True
                elif identifier_type == "name" and memory.user_name and user_identifier.lower() in memory.user_name.lower():
                    match = True
                
                if match:
                    results.append({
                        "id": memory.id,
                        "content": f"User: {memory.query}\nAgent: {memory.answer}",
                        "metadata": memory.metadata,
                        "created_at": memory.created_at,
                        "source": "fallback"
                    })
            
            # Sort by created_at (most recent first)
            results.sort(key=lambda x: x["created_at"], reverse=True)
            results = results[:limit]
            
            return {
                "success": True,
                "memories": results,
                "count": len(results),
                "user_identifier": user_identifier,
                "source": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Error searching fallback memories: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to search fallback memories: {str(e)}"
            }
    
    def _search_fallback_content(self, query: str, user_id: str, limit: int) -> Dict[str, Any]:
        """Search content in fallback storage"""
        try:
            results = []
            query_lower = query.lower()
            
            for memory in self.fallback_memory.values():
                # Filter by user_id if provided
                if user_id and memory.session_id != user_id:
                    continue
                
                # Search in query and answer content
                content = f"{memory.query} {memory.answer}".lower()
                if query_lower in content:
                    # Simple scoring based on query frequency
                    score = content.count(query_lower) / len(content.split())
                    
                    results.append({
                        "id": memory.id,
                        "content": f"User: {memory.query}\nAgent: {memory.answer}",
                        "score": score,
                        "metadata": memory.metadata,
                        "source": "fallback"
                    })
            
            # Sort by score (highest first)
            results.sort(key=lambda x: x["score"], reverse=True)
            results = results[:limit]
            
            return {
                "success": True,
                "results": results,
                "count": len(results),
                "query": query,
                "source": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Error searching fallback content: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to search fallback content: {str(e)}"
            }


# Global memory instance
memory_system = Mem0Integration()


# Convenience functions for agent integration
def store_memory(session_id: str, call_id: str, user_name: str = None, 
                user_phone: str = None, query: str = "", answer: str = "",
                tags: List[str] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Store conversation memory"""
    return memory_system.store_conversation_memory(
        session_id, call_id, user_name, user_phone, query, answer, tags, metadata
    )


def get_user_memories(user_identifier: str, identifier_type: str = "session_id", 
                     limit: int = 10) -> Dict[str, Any]:
    """Get memories for a user"""
    return memory_system.retrieve_user_memories(user_identifier, identifier_type, limit)


def search_memories(query: str, user_id: str = None, limit: int = 5) -> Dict[str, Any]:
    """Search memories by content"""
    return memory_system.search_memories(query, user_id, limit)


def store_lead_memory(session_id: str, call_id: str, lead_data: Dict[str, Any], 
                     transcript_summary: str = "") -> Dict[str, Any]:
    """Store lead data and call summary"""
    return memory_system.store_lead_summary(session_id, call_id, lead_data, transcript_summary)


def get_session_context(session_id: str) -> Dict[str, Any]:
    """Get session context and recent memories"""
    return memory_system.get_session_context(session_id)
