"""
Prompt Management API - Endpoints for reviewing and managing prompts
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from voicehive.domains.prompts.services.prompt_manager import PromptManager
from voicehive.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/api/dashboard/prompts", tags=["prompts"])
logger = logging.getLogger(__name__)

# Models
class PromptVersionModel(BaseModel):
    version: str
    status: str
    created_at: str
    created_by: Optional[str]
    description: Optional[str]

class PromptDetail(BaseModel):
    version: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    performance_metrics: Optional[Dict[str, Any]]

class PromptDiff(BaseModel):
    current_version: str
    candidate_version: str
    additions: List[str]
    removals: List[str]
    changes: List[Dict[str, Any]]

class PromptApproval(BaseModel):
    version: str
    approved: bool
    notes: Optional[str]

# Initialize services
prompt_manager = PromptManager()

@router.get("/versions", response_model=List[PromptVersionModel])
async def get_prompt_versions(current_user = Depends(get_current_admin_user)):
    """Get all prompt versions"""
    try:
        history = prompt_manager.get_version_history()
        versions = []
        
        for entry in history:
            versions.append({
                "version": entry.get("version", "unknown"),
                "status": entry.get("status", "unknown"),
                "created_at": entry.get("timestamp", ""),
                "created_by": entry.get("created_by", None),
                "description": entry.get("rationale", "")
            })
            
        return versions
    except Exception as e:
        logger.error(f"Error fetching prompt versions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch prompt versions")

@router.get("/current", response_model=PromptDetail)
async def get_current_prompt(current_user = Depends(get_current_admin_user)):
    """Get the current active prompt"""
    try:
        current = prompt_manager.get_current_prompt()
        if not current:
            raise HTTPException(status_code=404, detail="No current prompt found")
            
        # Add performance metrics if available
        performance = await get_prompt_performance(current.version)
        
        return {
            "version": current.version,
            "content": {
                "prompt": current.prompt,
                "metadata": {
                    "version": current.version,
                    "timestamp": current.timestamp,
                    "status": current.status,
                    "rationale": current.rationale
                }
            },
            "metadata": {
                "version": current.version,
                "timestamp": current.timestamp,
                "status": current.status,
                "rationale": current.rationale
            },
            "performance_metrics": performance
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch current prompt")

@router.get("/candidates", response_model=List[PromptDetail])
async def get_candidate_prompts(current_user = Depends(get_current_admin_user)):
    """Get all candidate prompts pending approval"""
    try:
        # Get all versions with pending status
        history = prompt_manager.get_version_history()
        candidates = [entry for entry in history if entry.get("status") == "pending"]
        
        result = []
        for candidate_entry in candidates:
            version = candidate_entry.get("version")
            candidate = prompt_manager.get_prompt_version(version)
            
            if candidate:
                # Add performance metrics if available
                performance = await get_prompt_performance(version)
                
                result.append({
                    "version": version,
                    "content": {
                        "prompt": candidate.prompt,
                        "metadata": {
                            "version": candidate.version,
                            "timestamp": candidate.timestamp,
                            "status": candidate.status,
                            "rationale": candidate.rationale
                        }
                    },
                    "metadata": {
                        "version": candidate.version,
                        "timestamp": candidate.timestamp,
                        "status": candidate.status,
                        "rationale": candidate.rationale
                    },
                    "performance_metrics": performance
                })
            
        return result
    except Exception as e:
        logger.error(f"Error fetching candidate prompts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch candidate prompts")

@router.get("/diff/{version}", response_model=PromptDiff)
async def get_prompt_diff(version: str, current_user = Depends(get_current_admin_user)):
    """Get diff between current prompt and specified version"""
    try:
        current = prompt_manager.get_current_prompt()
        candidate = prompt_manager.get_prompt_version(version)
        
        if not current:
            raise HTTPException(status_code=404, detail="Current prompt not found")
            
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Prompt version {version} not found")
            
        # Generate diff (simplified - would be more sophisticated in production)
        current_str = str(current.prompt)
        candidate_str = str(candidate.prompt)
        
        # Simple diff for demonstration
        additions = []
        removals = []
        changes = []
        
        # In production, would use a proper diff algorithm
        # This is just a placeholder implementation
        current_lines = current_str.split('\n')
        candidate_lines = candidate_str.split('\n')
        
        for line in candidate_lines:
            if line not in current_lines:
                additions.append(line)
                
        for line in current_lines:
            if line not in candidate_lines:
                removals.append(line)
                
        # Identify changes in metadata
        if current.version != candidate.version:
            changes.append({
                "field": "version",
                "old": current.version,
                "new": candidate.version
            })
        
        if current.rationale != candidate.rationale:
            changes.append({
                "field": "rationale",
                "old": current.rationale,
                "new": candidate.rationale
            })
        
        return {
            "current_version": current.version,
            "candidate_version": version,
            "additions": additions,
            "removals": removals,
            "changes": changes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating prompt diff: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate prompt diff")

@router.post("/approve", response_model=Dict[str, Any])
async def approve_prompt(
    approval: PromptApproval, 
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_admin_user)
):
    """Approve or reject a candidate prompt"""
    try:
        if approval.approved:
            # Activate the version
            success = prompt_manager.activate_version(approval.version)
            
            if success:
                # Schedule background task to notify services
                background_tasks.add_task(notify_prompt_update, approval.version)
                
                return {
                    "success": True,
                    "message": f"Prompt version {approval.version} approved and activated"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to activate version")
        else:
            # Update status to rejected (would need to implement this in PromptManager)
            return {
                "success": True,
                "message": f"Prompt version {approval.version} rejected"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to approve prompt")

async def get_prompt_performance(version: str) -> Optional[Dict[str, Any]]:
    """Get performance metrics for a prompt version"""
    # In production, this would query your metrics database
    # For now, return mock data
    try:
        # Mock performance data
        return {
            "calls_handled": 124,
            "success_rate": 92.3,
            "avg_duration": 3.7,
            "booking_rate": 68.5
        }
    except Exception as e:
        logger.error(f"Error fetching prompt performance: {str(e)}")
        return None

async def notify_prompt_update(version: str):
    """Notify services about prompt update"""
    # In production, this would send notifications to services
    # to reload the prompt
    logger.info(f"Notifying services about prompt update to version {version}")
    # Implementation would depend on your service architecture
