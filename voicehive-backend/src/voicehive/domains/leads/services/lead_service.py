import logging
from datetime import datetime
from typing import Dict, Any

from app.models.vapi import LeadCaptureRequest
from app.utils.exceptions import LeadServiceError

logger = logging.getLogger(__name__)


class LeadService:
    """Service for handling lead capture and management"""
    
    def __init__(self):
        # In Sprint 2, this would integrate with actual CRM systems
        # For now, we'll use a simple in-memory store for demonstration
        self.leads = {}
        
    async def capture_lead(self, lead_request: LeadCaptureRequest) -> Dict[str, Any]:
        """
        Capture lead information
        
        Args:
            lead_request: Validated lead capture request
            
        Returns:
            Lead capture result
        """
        try:
            # Generate lead ID
            lead_id = f"lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # In a real implementation, this would:
            # 1. Store in CRM system (Salesforce, HubSpot, Pipedrive, etc.)
            # 2. Trigger lead scoring algorithms
            # 3. Send notifications to sales team
            # 4. Add to email marketing lists
            
            lead_data = {
                "id": lead_id,
                "name": lead_request.name,
                "phone": lead_request.phone,
                "email": lead_request.email,
                "interest": lead_request.interest,
                "source": "voice_call",
                "status": "new",
                "score": self._calculate_lead_score(lead_request),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store lead (in-memory for now)
            self.leads[lead_id] = lead_data
            
            logger.info(f"Lead captured: {lead_id} for {lead_request.name}")
            
            return {
                "lead_id": lead_id,
                "status": "captured",
                "score": lead_data["score"],
                "message": f"Lead information captured for {lead_request.name}"
            }
            
        except Exception as e:
            logger.error(f"Error capturing lead: {str(e)}")
            raise LeadServiceError(f"Failed to capture lead: {str(e)}")
    
    def _calculate_lead_score(self, lead_request: LeadCaptureRequest) -> int:
        """
        Calculate lead score based on available information
        
        Args:
            lead_request: Lead information
            
        Returns:
            Lead score (0-100)
        """
        score = 50  # Base score
        
        # Add points for having email
        if lead_request.email:
            score += 20
        
        # Add points for specific interests
        if lead_request.interest:
            high_value_keywords = ["enterprise", "business", "company", "urgent", "asap"]
            if any(keyword in lead_request.interest.lower() for keyword in high_value_keywords):
                score += 20
        
        # Ensure score is within bounds
        return min(100, max(0, score))
    
    async def get_lead(self, lead_id: str) -> Dict[str, Any]:
        """
        Get lead details
        
        Args:
            lead_id: Unique lead identifier
            
        Returns:
            Lead details
        """
        try:
            lead = self.leads.get(lead_id)
            if not lead:
                raise LeadServiceError(f"Lead {lead_id} not found")
            
            return lead
            
        except Exception as e:
            logger.error(f"Error getting lead {lead_id}: {str(e)}")
            raise LeadServiceError(f"Failed to get lead: {str(e)}")
    
    async def update_lead_status(self, lead_id: str, status: str) -> Dict[str, Any]:
        """
        Update lead status
        
        Args:
            lead_id: Unique lead identifier
            status: New status (new, contacted, qualified, converted, lost)
            
        Returns:
            Update result
        """
        try:
            if lead_id not in self.leads:
                raise LeadServiceError(f"Lead {lead_id} not found")
            
            valid_statuses = ["new", "contacted", "qualified", "converted", "lost"]
            if status not in valid_statuses:
                raise LeadServiceError(f"Invalid status: {status}")
            
            # Update lead status
            self.leads[lead_id]["status"] = status
            self.leads[lead_id]["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Lead status updated: {lead_id} -> {status}")
            
            return {
                "lead_id": lead_id,
                "status": status,
                "message": f"Lead status updated to {status}"
            }
            
        except Exception as e:
            logger.error(f"Error updating lead status {lead_id}: {str(e)}")
            raise LeadServiceError(f"Failed to update lead status: {str(e)}")
    
    async def search_leads(self, query: str = None, status: str = None) -> Dict[str, Any]:
        """
        Search leads by various criteria
        
        Args:
            query: Search query (name, phone, email)
            status: Filter by status
            
        Returns:
            Search results
        """
        try:
            results = []
            
            for lead_id, lead_data in self.leads.items():
                # Filter by status if provided
                if status and lead_data["status"] != status:
                    continue
                
                # Filter by query if provided
                if query:
                    query_lower = query.lower()
                    if not any([
                        query_lower in lead_data["name"].lower(),
                        query_lower in lead_data["phone"],
                        lead_data["email"] and query_lower in lead_data["email"].lower()
                    ]):
                        continue
                
                results.append(lead_data)
            
            return {
                "leads": results,
                "count": len(results),
                "query": query,
                "status_filter": status
            }
            
        except Exception as e:
            logger.error(f"Error searching leads: {str(e)}")
            raise LeadServiceError(f"Failed to search leads: {str(e)}")
