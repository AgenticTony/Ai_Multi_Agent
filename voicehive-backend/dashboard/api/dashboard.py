"""
Dashboard API endpoints for VoiceHive monitoring system.
Provides real-time metrics, system health, and analytics data.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
from pydantic import BaseModel

# Import existing services
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from vertex.monitoring_service import MonitoringService
from vertex.vertex_feedback_service import VertexFeedbackService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
security = HTTPBearer()

# Pydantic models for API responses
class DashboardMetrics(BaseModel):
    total_calls: int
    active_calls: int
    success_rate: float
    avg_duration: float
    system_health: str
    alerts: int
    last_updated: datetime

class SystemHealth(BaseModel):
    status: str
    api_response_time: float
    memory_usage: float
    cpu_usage: float
    active_alerts: int
    uptime: str

class CallVolumeData(BaseModel):
    time: str
    calls: int

class RecentActivity(BaseModel):
    timestamp: datetime
    event: str
    status: str
    details: Optional[str] = None

class AlertData(BaseModel):
    id: str
    severity: str
    message: str
    timestamp: datetime
    acknowledged: bool

# Initialize services
monitoring_service = MonitoringService()
feedback_service = VertexFeedbackService()

@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get current dashboard metrics including calls, success rate, and system health."""
    try:
        # Get real-time metrics from monitoring service
        health_data = await monitoring_service.get_system_health()
        
        # Calculate metrics from recent data
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # Mock data for now - in production, this would query your database
        metrics = DashboardMetrics(
            total_calls=1247,
            active_calls=8,
            success_rate=94.2,
            avg_duration=4.3,
            system_health=health_data.get('overall_status', 'healthy'),
            alerts=len(health_data.get('alerts', [])),
            last_updated=now
        )
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")

@router.get("/health", response_model=SystemHealth)
async def get_system_health():
    """Get detailed system health information."""
    try:
        health_data = await monitoring_service.get_system_health()
        
        system_health = SystemHealth(
            status=health_data.get('overall_status', 'healthy'),
            api_response_time=health_data.get('api_response_time', 45.0),
            memory_usage=health_data.get('memory_usage', 72.0),
            cpu_usage=health_data.get('cpu_usage', 35.0),
            active_alerts=len(health_data.get('alerts', [])),
            uptime=health_data.get('uptime', '5d 12h 30m')
        )
        
        return system_health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch system health: {str(e)}")

@router.get("/call-volume", response_model=List[CallVolumeData])
async def get_call_volume(hours: int = 24):
    """Get call volume data for the specified time period."""
    try:
        # Mock data for demonstration - replace with actual database queries
        data = [
            CallVolumeData(time="00:00", calls=12),
            CallVolumeData(time="02:00", calls=8),
            CallVolumeData(time="04:00", calls=5),
            CallVolumeData(time="06:00", calls=15),
            CallVolumeData(time="08:00", calls=32),
            CallVolumeData(time="10:00", calls=45),
            CallVolumeData(time="12:00", calls=38),
            CallVolumeData(time="14:00", calls=42),
            CallVolumeData(time="16:00", calls=35),
            CallVolumeData(time="18:00", calls=28),
            CallVolumeData(time="20:00", calls=22),
            CallVolumeData(time="22:00", calls=18),
        ]
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch call volume: {str(e)}")

@router.get("/recent-activity", response_model=List[RecentActivity])
async def get_recent_activity(limit: int = 10):
    """Get recent system activity and events."""
    try:
        # Mock data for demonstration
        activities = [
            RecentActivity(
                timestamp=datetime.utcnow() - timedelta(minutes=2),
                event="Call completed successfully",
                status="success",
                details="Duration: 4.2 minutes"
            ),
            RecentActivity(
                timestamp=datetime.utcnow() - timedelta(minutes=5),
                event="New appointment scheduled",
                status="info",
                details="Customer: John Doe"
            ),
            RecentActivity(
                timestamp=datetime.utcnow() - timedelta(minutes=8),
                event="System health check passed",
                status="success"
            ),
            RecentActivity(
                timestamp=datetime.utcnow() - timedelta(minutes=12),
                event="High memory usage detected",
                status="warning",
                details="Memory usage: 85%"
            ),
            RecentActivity(
                timestamp=datetime.utcnow() - timedelta(minutes=15),
                event="Call failed - network timeout",
                status="error",
                details="Retry scheduled"
            ),
        ]
        
        return activities[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent activity: {str(e)}")

@router.get("/alerts", response_model=List[AlertData])
async def get_alerts(active_only: bool = True):
    """Get system alerts."""
    try:
        health_data = await monitoring_service.get_system_health()
        alerts = health_data.get('alerts', [])
        
        alert_data = []
        for alert in alerts:
            alert_data.append(AlertData(
                id=alert.get('id', 'unknown'),
                severity=alert.get('severity', 'info'),
                message=alert.get('message', 'No message'),
                timestamp=datetime.fromisoformat(alert.get('timestamp', datetime.utcnow().isoformat())),
                acknowledged=alert.get('acknowledged', False)
            ))
        
        if active_only:
            alert_data = [a for a in alert_data if not a.acknowledged]
        
        return alert_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    try:
        # In a real implementation, this would update the alert status in the database
        return {"message": f"Alert {alert_id} acknowledged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.get("/performance-metrics")
async def get_performance_metrics():
    """Get detailed performance metrics for the dashboard."""
    try:
        # Get performance data from monitoring service
        performance_data = await monitoring_service.get_performance_metrics()
        
        return {
            "response_times": performance_data.get('response_times', {}),
            "throughput": performance_data.get('throughput', {}),
            "error_rates": performance_data.get('error_rates', {}),
            "resource_usage": performance_data.get('resource_usage', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance metrics: {str(e)}")

@router.get("/call-analytics")
async def get_call_analytics(days: int = 7):
    """Get call analytics data for the specified period."""
    try:
        # This would integrate with the feedback service to get call analysis data
        analytics_data = await feedback_service.get_analytics_summary(days=days)
        
        return {
            "success_rate_trend": analytics_data.get('success_rate_trend', []),
            "sentiment_analysis": analytics_data.get('sentiment_analysis', {}),
            "common_issues": analytics_data.get('common_issues', []),
            "performance_improvements": analytics_data.get('improvements', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch call analytics: {str(e)}")

@router.get("/call-logs")
async def get_call_logs(limit: int = 50, status: Optional[str] = None):
    """Get call logs with optional filtering."""
    try:
        # Mock data for demonstration - replace with actual database queries
        logs = [
            {
                "id": "call-001",
                "timestamp": "2025-01-06T15:30:00Z",
                "duration": 245,
                "status": "completed",
                "caller": "+1-555-0123",
                "agent": "Roxy",
                "summary": "Customer inquiry about appointment scheduling",
                "sentiment": "positive"
            },
            {
                "id": "call-002",
                "timestamp": "2025-01-06T15:25:00Z",
                "duration": 180,
                "status": "completed",
                "caller": "+1-555-0456",
                "agent": "Roxy",
                "summary": "Lead qualification for dental services",
                "sentiment": "neutral"
            },
            {
                "id": "call-003",
                "timestamp": "2025-01-06T15:20:00Z",
                "duration": 0,
                "status": "failed",
                "caller": "+1-555-0789",
                "agent": "Roxy",
                "summary": "Call failed to connect",
                "sentiment": "negative"
            }
        ]
        
        # Filter by status if provided
        if status:
            logs = [log for log in logs if log["status"] == status]
        
        return {"logs": logs[:limit], "total": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch call logs: {str(e)}")

@router.get("/usage-analytics")
async def get_usage_analytics(time_range: str = "7d"):
    """Get comprehensive usage analytics data."""
    try:
        # Mock analytics data - replace with actual analytics service
        analytics = {
            "call_volume": [
                {"date": "2025-01-01", "calls": 45},
                {"date": "2025-01-02", "calls": 52},
                {"date": "2025-01-03", "calls": 38},
                {"date": "2025-01-04", "calls": 61},
                {"date": "2025-01-05", "calls": 49},
                {"date": "2025-01-06", "calls": 67},
                {"date": "2025-01-07", "calls": 55}
            ],
            "success_rate": [
                {"date": "2025-01-01", "rate": 92.5},
                {"date": "2025-01-02", "rate": 94.2},
                {"date": "2025-01-03", "rate": 89.1},
                {"date": "2025-01-04", "rate": 96.7},
                {"date": "2025-01-05", "rate": 91.8},
                {"date": "2025-01-06", "rate": 95.5},
                {"date": "2025-01-07", "rate": 93.6}
            ],
            "avg_duration": [
                {"date": "2025-01-01", "duration": 185},
                {"date": "2025-01-02", "duration": 192},
                {"date": "2025-01-03", "duration": 178},
                {"date": "2025-01-04", "duration": 205},
                {"date": "2025-01-05", "duration": 188},
                {"date": "2025-01-06", "duration": 198},
                {"date": "2025-01-07", "duration": 182}
            ],
            "sentiment_trends": [
                {"date": "2025-01-01", "positive": 65, "neutral": 25, "negative": 10},
                {"date": "2025-01-02", "positive": 70, "neutral": 22, "negative": 8},
                {"date": "2025-01-03", "positive": 62, "neutral": 28, "negative": 10},
                {"date": "2025-01-04", "positive": 75, "neutral": 20, "negative": 5},
                {"date": "2025-01-05", "positive": 68, "neutral": 24, "negative": 8},
                {"date": "2025-01-06", "positive": 72, "neutral": 21, "negative": 7},
                {"date": "2025-01-07", "positive": 69, "neutral": 23, "negative": 8}
            ],
            "hourly_distribution": [
                {"hour": 9, "calls": 12},
                {"hour": 10, "calls": 18},
                {"hour": 11, "calls": 25},
                {"hour": 12, "calls": 22},
                {"hour": 13, "calls": 15},
                {"hour": 14, "calls": 28},
                {"hour": 15, "calls": 32},
                {"hour": 16, "calls": 29},
                {"hour": 17, "calls": 20}
            ],
            "top_callers": [
                {"phone": "+1-555-0123", "calls": 8, "total_duration": 1560},
                {"phone": "+1-555-0456", "calls": 6, "total_duration": 1200},
                {"phone": "+1-555-0789", "calls": 5, "total_duration": 980},
                {"phone": "+1-555-0321", "calls": 4, "total_duration": 840},
                {"phone": "+1-555-0654", "calls": 4, "total_duration": 720}
            ],
            "agent_performance": [
                {"agent": "Roxy", "calls": 367, "avg_duration": 192, "success_rate": 94.2}
            ]
        }
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch usage analytics: {str(e)}")

# WebSocket endpoint for real-time updates
@router.websocket("/ws/real-time")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket.accept()
    try:
        while True:
            # Send real-time updates every 5 seconds
            metrics = await get_dashboard_metrics()
            await websocket.send_json(metrics.dict())
            await asyncio.sleep(5)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
