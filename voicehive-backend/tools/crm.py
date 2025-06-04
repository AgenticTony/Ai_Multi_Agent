"""
CRM Tool - Enhanced lead management and customer relationship functionality
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class Lead:
    """Lead data structure"""
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    issue: Optional[str] = None
    interest: Optional[str] = None
    source: str = "voice_call"
    status: str = "new"
    score: int = 0
    notes: List[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


class CRMTool:
    """Enhanced CRM functionality for lead management"""
    
    def __init__(self):
        # In production, this would connect to actual CRM systems
        # (Salesforce, HubSpot, Pipedrive, etc.)
        self.leads: Dict[str, Lead] = {}
        self.interaction_history: Dict[str, List[Dict]] = {}
        
    def create_lead(self, name: str, phone: str, email: str = None, 
                   issue: str = None, interest: str = None) -> Dict[str, Any]:
        """
        Create a new lead in the CRM system
        
        Args:
            name: Lead's full name
            phone: Phone number
            email: Email address (optional)
            issue: Specific issue or problem mentioned
            interest: Area of interest or service needed
            
        Returns:
            Lead creation result with lead ID
        """
        try:
            # Generate unique lead ID
            lead_id = f"lead_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Calculate lead score based on available information
            score = self._calculate_lead_score(name, phone, email, issue, interest)
            
            # Create lead object
            lead = Lead(
                id=lead_id,
                name=name,
                phone=phone,
                email=email,
                issue=issue,
                interest=interest,
                score=score
            )
            
            # Store lead
            self.leads[lead_id] = lead
            
            # Initialize interaction history
            self.interaction_history[lead_id] = []
            
            # Log lead creation
            self._log_interaction(lead_id, "lead_created", {
                "name": name,
                "phone": phone,
                "email": email,
                "score": score
            })
            
            logger.info(f"Lead created: {lead_id} - {name} ({phone})")
            
            return {
                "success": True,
                "lead_id": lead_id,
                "message": f"Lead {name} created successfully",
                "score": score,
                "status": "new"
            }
            
        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create lead: {str(e)}"
            }
    
    def update_lead(self, lead_id: str, **updates) -> Dict[str, Any]:
        """
        Update existing lead information
        
        Args:
            lead_id: Unique lead identifier
            **updates: Fields to update
            
        Returns:
            Update result
        """
        try:
            if lead_id not in self.leads:
                return {
                    "success": False,
                    "message": f"Lead {lead_id} not found"
                }
            
            lead = self.leads[lead_id]
            updated_fields = []
            
            # Update allowed fields
            for field, value in updates.items():
                if hasattr(lead, field) and field not in ['id', 'created_at']:
                    old_value = getattr(lead, field)
                    setattr(lead, field, value)
                    updated_fields.append(f"{field}: {old_value} -> {value}")
            
            # Update timestamp
            lead.updated_at = datetime.utcnow().isoformat()
            
            # Log update
            self._log_interaction(lead_id, "lead_updated", {
                "updated_fields": updated_fields
            })
            
            logger.info(f"Lead updated: {lead_id} - {updated_fields}")
            
            return {
                "success": True,
                "lead_id": lead_id,
                "message": f"Lead updated successfully",
                "updated_fields": updated_fields
            }
            
        except Exception as e:
            logger.error(f"Error updating lead: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update lead: {str(e)}"
            }
    
    def get_lead(self, lead_id: str) -> Dict[str, Any]:
        """
        Retrieve lead information
        
        Args:
            lead_id: Unique lead identifier
            
        Returns:
            Lead information or error
        """
        try:
            if lead_id not in self.leads:
                return {
                    "success": False,
                    "message": f"Lead {lead_id} not found"
                }
            
            lead = self.leads[lead_id]
            interactions = self.interaction_history.get(lead_id, [])
            
            return {
                "success": True,
                "lead": {
                    "id": lead.id,
                    "name": lead.name,
                    "phone": lead.phone,
                    "email": lead.email,
                    "issue": lead.issue,
                    "interest": lead.interest,
                    "source": lead.source,
                    "status": lead.status,
                    "score": lead.score,
                    "notes": lead.notes,
                    "created_at": lead.created_at,
                    "updated_at": lead.updated_at
                },
                "interaction_count": len(interactions)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving lead: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to retrieve lead: {str(e)}"
            }
    
    def search_leads(self, query: str = None, status: str = None, 
                    phone: str = None) -> Dict[str, Any]:
        """
        Search leads by various criteria
        
        Args:
            query: Search query (name, email)
            status: Filter by status
            phone: Search by phone number
            
        Returns:
            Search results
        """
        try:
            results = []
            
            for lead_id, lead in self.leads.items():
                # Filter by status
                if status and lead.status != status:
                    continue
                
                # Filter by phone (exact match)
                if phone and lead.phone != phone:
                    continue
                
                # Filter by query (name, email)
                if query:
                    query_lower = query.lower()
                    if not any([
                        query_lower in lead.name.lower(),
                        lead.email and query_lower in lead.email.lower()
                    ]):
                        continue
                
                results.append({
                    "id": lead.id,
                    "name": lead.name,
                    "phone": lead.phone,
                    "email": lead.email,
                    "status": lead.status,
                    "score": lead.score,
                    "created_at": lead.created_at
                })
            
            # Sort by score (highest first) then by creation date
            results.sort(key=lambda x: (-x["score"], x["created_at"]), reverse=True)
            
            return {
                "success": True,
                "leads": results,
                "count": len(results),
                "query": query,
                "status_filter": status
            }
            
        except Exception as e:
            logger.error(f"Error searching leads: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to search leads: {str(e)}"
            }
    
    def add_note(self, lead_id: str, note: str, note_type: str = "general") -> Dict[str, Any]:
        """
        Add a note to a lead
        
        Args:
            lead_id: Unique lead identifier
            note: Note content
            note_type: Type of note (general, call, meeting, etc.)
            
        Returns:
            Note addition result
        """
        try:
            if lead_id not in self.leads:
                return {
                    "success": False,
                    "message": f"Lead {lead_id} not found"
                }
            
            lead = self.leads[lead_id]
            timestamp = datetime.utcnow().isoformat()
            
            note_entry = f"[{timestamp}] ({note_type}) {note}"
            lead.notes.append(note_entry)
            lead.updated_at = timestamp
            
            # Log note addition
            self._log_interaction(lead_id, "note_added", {
                "note_type": note_type,
                "note": note
            })
            
            logger.info(f"Note added to lead {lead_id}: {note_type}")
            
            return {
                "success": True,
                "lead_id": lead_id,
                "message": "Note added successfully",
                "note_count": len(lead.notes)
            }
            
        except Exception as e:
            logger.error(f"Error adding note: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to add note: {str(e)}"
            }
    
    def _calculate_lead_score(self, name: str, phone: str, email: str = None,
                             issue: str = None, interest: str = None) -> int:
        """Calculate lead score based on available information"""
        score = 0
        
        # Base score for having name and phone
        score += 20
        
        # Email provided
        if email:
            score += 15
        
        # Specific issue mentioned
        if issue:
            score += 25
        
        # Interest area specified
        if interest:
            score += 20
        
        # High-value keywords in issue/interest
        high_value_keywords = [
            'urgent', 'immediate', 'asap', 'emergency',
            'budget', 'purchase', 'buy', 'invest',
            'enterprise', 'business', 'company'
        ]
        
        text_to_check = f"{issue or ''} {interest or ''}".lower()
        for keyword in high_value_keywords:
            if keyword in text_to_check:
                score += 10
        
        return min(score, 100)  # Cap at 100
    
    def _log_interaction(self, lead_id: str, interaction_type: str, 
                        data: Dict[str, Any]) -> None:
        """Log interaction with lead"""
        if lead_id not in self.interaction_history:
            self.interaction_history[lead_id] = []
        
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": interaction_type,
            "data": data
        }
        
        self.interaction_history[lead_id].append(interaction)
    
    def get_lead_stats(self) -> Dict[str, Any]:
        """Get overall CRM statistics"""
        try:
            total_leads = len(self.leads)
            status_counts = {}
            score_distribution = {"high": 0, "medium": 0, "low": 0}
            
            for lead in self.leads.values():
                # Count by status
                status_counts[lead.status] = status_counts.get(lead.status, 0) + 1
                
                # Score distribution
                if lead.score >= 70:
                    score_distribution["high"] += 1
                elif lead.score >= 40:
                    score_distribution["medium"] += 1
                else:
                    score_distribution["low"] += 1
            
            return {
                "success": True,
                "total_leads": total_leads,
                "status_breakdown": status_counts,
                "score_distribution": score_distribution,
                "avg_score": sum(lead.score for lead in self.leads.values()) / total_leads if total_leads > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting lead stats: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get stats: {str(e)}"
            }


# Global CRM instance
crm_tool = CRMTool()


# Convenience functions for agent integration
def create_lead(name: str, phone: str, email: str = None, 
               issue: str = None, interest: str = None) -> Dict[str, Any]:
    """Create a new lead"""
    return crm_tool.create_lead(name, phone, email, issue, interest)


def update_lead(lead_id: str, **updates) -> Dict[str, Any]:
    """Update existing lead"""
    return crm_tool.update_lead(lead_id, **updates)


def get_lead(lead_id: str) -> Dict[str, Any]:
    """Get lead information"""
    return crm_tool.get_lead(lead_id)


def search_leads(query: str = None, status: str = None, 
                phone: str = None) -> Dict[str, Any]:
    """Search leads"""
    return crm_tool.search_leads(query, status, phone)


def add_lead_note(lead_id: str, note: str, note_type: str = "call") -> Dict[str, Any]:
    """Add note to lead"""
    return crm_tool.add_note(lead_id, note, note_type)


def get_crm_stats() -> Dict[str, Any]:
    """Get CRM statistics"""
    return crm_tool.get_lead_stats()
