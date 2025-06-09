"""
Feedback Loop API - Endpoints for monitoring and controlling the feedback loop
"""
import logging
import time
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timedelta

from voicehive.auth.dependencies import get_current_admin_user
from voicehive.domains.feedback.services.complete_feedback_pipeline import CompleteFeedbackPipeline
from voicehive.domains.prompts.services.prompt_manager import PromptManager

router = APIRouter(prefix="/api/dashboard/feedback-loop", tags=["feedback-loop"])
logger = logging.getLogger(__name__)

# Models
class FeedbackLoopStatus(BaseModel):
    status: str  # "running", "idle", "error"
    last_run: Optional[str]
    next_scheduled_run: Optional[str]
    current_prompt_version: str
    pending_improvements: int
    total_runs: int
    success_rate: float

class FeedbackLoopRun(BaseModel):
    run_id: str
    start_time: str
    end_time: Optional[str]
    status: str
    prompt_before: str
    prompt_after: Optional[str]
    improvement_summary: Optional[str]
    error_message: Optional[str]

class ManualRunRequest(BaseModel):
    run_mode: str = "full"  # "full", "analysis_only", "simulation_only"
    date_range: Optional[Dict[str, str]] = None

# Initialize services
prompt_manager = PromptManager()
feedback_pipeline = CompleteFeedbackPipeline()

@router.get("/status", response_model=FeedbackLoopStatus)
async def get_feedback_loop_status(current_user = Depends(get_current_admin_user)):
    """Get current status of the feedback loop"""
    try:
        # Get current prompt version
        current_prompt = prompt_manager.get_current_prompt()
        current_version = current_prompt.version if current_prompt else "unknown"
        
        # Get pending improvements
        pending_improvements = len(prompt_manager.get_pending_improvements())
        
        # Get run history stats
        run_history = await get_run_history()
        total_runs = len(run_history)
        successful_runs = sum(1 for run in run_history if run["status"] == "completed")
        success_rate = (successful_runs / total_runs) * 100 if total_runs > 0 else 0
        
        # Get last and next run times
        last_run = max([run["start_time"] for run in run_history]) if run_history else None
        
        # Calculate next scheduled run (simplified)
        next_run = datetime.now() + timedelta(days=1)
        next_run = next_run.replace(hour=6, minute=0, second=0, microsecond=0)
        
        return {
            "status": "idle",  # Would be dynamic in production
            "last_run": last_run,
            "next_scheduled_run": next_run.isoformat(),
            "current_prompt_version": current_version,
            "pending_improvements": pending_improvements,
            "total_runs": total_runs,
            "success_rate": success_rate
        }
    except Exception as e:
        logger.error(f"Error getting feedback loop status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feedback loop status")

@router.get("/history", response_model=List[FeedbackLoopRun])
async def get_feedback_loop_history(current_user = Depends(get_current_admin_user)):
    """Get history of feedback loop runs"""
    try:
        return await get_run_history()
    except Exception as e:
        logger.error(f"Error getting feedback loop history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feedback loop history")

@router.post("/run", response_model=Dict[str, Any])
async def run_feedback_loop(
    request: ManualRunRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_admin_user)
):
    """Manually trigger a feedback loop run"""
    try:
        # Generate run ID
        run_id = f"manual-{int(time.time())}"
        
        # Create run record
        current_prompt = prompt_manager.get_current_prompt()
        prompt_version = current_prompt.version if current_prompt else "unknown"
        
        run_record = {
            "run_id": run_id,
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "triggered_by": current_user.username,
            "run_mode": request.run_mode,
            "prompt_before": prompt_version
        }
        
        # Save run record (would use database in production)
        # For now, just log it
        logger.info(f"Starting manual feedback loop run: {run_record}")
        
        # Start pipeline in background
        background_tasks.add_task(
            run_pipeline_background,
            run_id=run_id,
            run_mode=request.run_mode,
            date_range=request.date_range
        )
        
        return {
            "success": True,
            "message": f"Feedback loop run started with ID: {run_id}",
            "run_id": run_id
        }
    except Exception as e:
        logger.error(f"Error starting feedback loop run: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start feedback loop run: {str(e)}")

@router.get("/runs/{run_id}", response_model=FeedbackLoopRun)
async def get_feedback_loop_run(run_id: str, current_user = Depends(get_current_admin_user)):
    """Get details of a specific feedback loop run"""
    try:
        # In production, would fetch from database
        run_history = await get_run_history()
        for run in run_history:
            if run["run_id"] == run_id:
                return run
                
        raise HTTPException(status_code=404, detail=f"Run with ID {run_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback loop run: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feedback loop run")

async def get_run_history() -> List[Dict[str, Any]]:
    """Get history of feedback loop runs"""
    # In production, would fetch from database
    # Mock data for now
    return [
        {
            "run_id": "auto-20240115060000",
            "start_time": "2024-01-15T06:00:00Z",
            "end_time": "2024-01-15T06:15:23Z",
            "status": "completed",
            "prompt_before": "v1.0",
            "prompt_after": "v1.1",
            "improvement_summary": "Added better handling for appointment rescheduling scenarios"
        },
        {
            "run_id": "auto-20240114060000",
            "start_time": "2024-01-14T06:00:00Z",
            "end_time": "2024-01-14T06:12:45Z",
            "status": "rejected",
            "prompt_before": "v1.0",
            "prompt_after": None,
            "improvement_summary": "Proposed changes failed simulation testing"
        },
        {
            "run_id": "manual-1705142400",
            "start_time": "2024-01-13T12:00:00Z",
            "end_time": "2024-01-13T12:18:32Z",
            "status": "completed",
            "prompt_before": "v0.9",
            "prompt_after": "v1.0",
            "improvement_summary": "Enhanced objection handling and added more empathetic responses"
        }
    ]

async def run_pipeline_background(run_id: str, run_mode: str, date_range: Optional[Dict[str, str]]):
    """Run the feedback pipeline in the background"""
    try:
        logger.info(f"Starting background pipeline run: {run_id}, mode: {run_mode}")
        
        # Run appropriate pipeline based on mode
        if run_mode == "full":
            result = await feedback_pipeline.run_complete_pipeline()
        elif run_mode == "analysis_only":
            result = await feedback_pipeline.run_analysis_only()
        elif run_mode == "simulation_only":
            result = await feedback_pipeline.run_simulation_only()
        else:
            raise ValueError(f"Invalid run mode: {run_mode}")
        
        # Update run record with results
        # In production, would update database
        logger.info(f"Pipeline run completed: {run_id}, result: {result}")
        
    except Exception as e:
        logger.error(f"Error in background pipeline run {run_id}: {str(e)}")
        # In production, would update run record with error
