"""
A/B Testing API - Endpoints for comparing prompt performance
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from voicehive.auth.dependencies import get_current_admin_user
from voicehive.improvements.prompt_manager import PromptManager
from voicehive.monitoring.metrics import get_metrics_service

router = APIRouter(prefix="/api/dashboard/ab-testing", tags=["ab-testing"])
logger = logging.getLogger(__name__)

# Models
class ABTestConfig(BaseModel):
    test_id: str
    prompt_a: str  # Version ID
    prompt_b: str  # Version ID
    traffic_split: int  # Percentage for B (0-100)
    start_date: str
    end_date: Optional[str]
    status: str  # "active", "completed", "cancelled"

class ABTestResults(BaseModel):
    test_id: str
    prompt_a: str
    prompt_b: str
    metrics: Dict[str, Dict[str, Any]]
    winner: Optional[str]
    confidence: Optional[float]

class CreateABTest(BaseModel):
    prompt_a: str
    prompt_b: str
    traffic_split: int
    duration_days: int

# Initialize services
prompt_manager = PromptManager()
metrics_service = get_metrics_service()

@router.get("/tests", response_model=List[ABTestConfig])
async def get_ab_tests(current_user = Depends(get_current_admin_user)):
    """Get all A/B tests"""
    try:
        # In production, would fetch from database
        # Mock data for now
        return [
            {
                "test_id": "test_001",
                "prompt_a": "v1.0",
                "prompt_b": "v1.1",
                "traffic_split": 50,
                "start_date": "2024-01-15T00:00:00Z",
                "end_date": None,
                "status": "active"
            },
            {
                "test_id": "test_002",
                "prompt_a": "v1.0",
                "prompt_b": "v1.2",
                "traffic_split": 25,
                "start_date": "2024-01-10T00:00:00Z",
                "end_date": "2024-01-14T23:59:59Z",
                "status": "completed"
            }
        ]
    except Exception as e:
        logger.error(f"Error fetching A/B tests: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch A/B tests")

@router.get("/tests/{test_id}/results", response_model=ABTestResults)
async def get_ab_test_results(test_id: str, current_user = Depends(get_current_admin_user)):
    """Get results for a specific A/B test"""
    try:
        # In production, would fetch from metrics database
        # Mock data for now
        return {
            "test_id": test_id,
            "prompt_a": "v1.0",
            "prompt_b": "v1.1",
            "metrics": {
                "booking_rate": {
                    "a": 65.2,
                    "b": 72.8,
                    "diff": 7.6,
                    "diff_percent": 11.7
                },
                "call_duration": {
                    "a": 4.2,
                    "b": 3.8,
                    "diff": -0.4,
                    "diff_percent": -9.5
                },
                "customer_satisfaction": {
                    "a": 4.1,
                    "b": 4.3,
                    "diff": 0.2,
                    "diff_percent": 4.9
                }
            },
            "winner": "b",
            "confidence": 92.5
        }
    except Exception as e:
        logger.error(f"Error fetching A/B test results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch A/B test results")

@router.post("/tests", response_model=ABTestConfig)
async def create_ab_test(test_config: CreateABTest, current_user = Depends(get_current_admin_user)):
    """Create a new A/B test"""
    try:
        # Validate prompts exist
        prompt_a = prompt_manager.get_prompt_version(test_config.prompt_a)
        prompt_b = prompt_manager.get_prompt_version(test_config.prompt_b)
        
        if not prompt_a:
            raise HTTPException(status_code=404, detail=f"Prompt A version {test_config.prompt_a} not found")
            
        if not