"""
Health check and metrics endpoints for VoiceHive
Provides system health status, metrics, and monitoring capabilities
"""

import time
import psutil
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from voicehive.core.settings import get_settings
from voicehive.utils.logging import get_logger, log_with_context

logger = get_logger(__name__)
router = APIRouter()

# In-memory metrics storage (in production, use Redis or similar)
_metrics_store: Dict[str, List[Dict[str, Any]]] = {
    "api_requests": [],
    "function_calls": [],
    "external_api_calls": [],
    "errors": []
}


class HealthStatus(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: str
    timestamp: str
    uptime_seconds: float
    checks: Dict[str, Dict[str, Any]]


class MetricsResponse(BaseModel):
    """Metrics response model"""
    timestamp: str
    system: Dict[str, Any]
    application: Dict[str, Any]
    api: Dict[str, Any]


class SystemInfo(BaseModel):
    """System information model"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_average: List[float]
    python_version: str
    platform: str


# Application start time for uptime calculation
_start_time = time.time()


def get_system_info() -> SystemInfo:
    """Get current system information"""
    import platform
    import sys
    
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Get memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Get disk usage
    disk = psutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    
    # Get load average (Unix-like systems only)
    try:
        load_avg = list(psutil.getloadavg())
    except AttributeError:
        load_avg = [0.0, 0.0, 0.0]  # Windows doesn't have load average
    
    return SystemInfo(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        disk_percent=disk_percent,
        load_average=load_avg,
        python_version=sys.version,
        platform=platform.platform()
    )


async def check_external_services() -> Dict[str, Dict[str, Any]]:
    """Check health of external services"""
    checks = {}
    
    # Check OpenAI API
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {get_settings().openai_api_key}"},
                timeout=5.0
            )
            duration = time.time() - start_time
            
            checks["openai"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": round(duration * 1000, 2),
                "status_code": response.status_code
            }
    except Exception as e:
        checks["openai"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Mem0 service (if configured)
    settings = get_settings()
    if hasattr(settings, 'mem0_api_key') and settings.mem0_api_key:
        try:
            # Add Mem0 health check here when available
            checks["mem0"] = {
                "status": "healthy",
                "note": "Mem0 health check not implemented"
            }
        except Exception as e:
            checks["mem0"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return checks


def record_metric(metric_type: str, data: Dict[str, Any]) -> None:
    """Record a metric for monitoring"""
    if metric_type not in _metrics_store:
        _metrics_store[metric_type] = []
    
    # Add timestamp
    data["timestamp"] = datetime.utcnow().isoformat()
    
    # Store metric
    _metrics_store[metric_type].append(data)
    
    # Keep only last 1000 entries per metric type
    if len(_metrics_store[metric_type]) > 1000:
        _metrics_store[metric_type] = _metrics_store[metric_type][-1000:]


def get_metrics_summary() -> Dict[str, Any]:
    """Get summary of application metrics"""
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    
    summary = {}
    
    for metric_type, metrics in _metrics_store.items():
        # Filter metrics from last hour
        recent_metrics = [
            m for m in metrics 
            if datetime.fromisoformat(m["timestamp"].replace("Z", "")) > one_hour_ago
        ]
        
        if recent_metrics:
            summary[metric_type] = {
                "count": len(recent_metrics),
                "last_hour": len(recent_metrics)
            }
            
            # Add specific summaries based on metric type
            if metric_type == "api_requests":
                status_codes = {}
                total_duration = 0
                for metric in recent_metrics:
                    status_code = metric.get("status_code", "unknown")
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1
                    total_duration += metric.get("duration_ms", 0)
                
                summary[metric_type].update({
                    "status_codes": status_codes,
                    "avg_response_time_ms": round(total_duration / len(recent_metrics), 2) if recent_metrics else 0
                })
            
            elif metric_type == "errors":
                error_types = {}
                for metric in recent_metrics:
                    error_type = metric.get("error_type", "unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
                summary[metric_type]["error_types"] = error_types
        else:
            summary[metric_type] = {"count": 0, "last_hour": 0}
    
    return summary


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive health check endpoint
    Returns system health, external service status, and basic metrics
    """
    try:
        log_with_context(logger, "debug", "Health check requested", event="health_check_start")
        
        # Calculate uptime
        uptime = time.time() - _start_time
        
        # Check external services
        external_checks = await check_external_services()
        
        # Get system info
        system_info = get_system_info()
        
        # Determine overall status
        overall_status = "healthy"
        for service, check in external_checks.items():
            if check.get("status") != "healthy":
                overall_status = "degraded"
                break
        
        # Check system resources
        if system_info.cpu_percent > 90 or system_info.memory_percent > 90:
            overall_status = "degraded"
        
        health_response = HealthStatus(
            status=overall_status,
            service="voicehive-api",
            version="1.0.0",  # Should come from settings or package info
            timestamp=datetime.utcnow().isoformat() + "Z",
            uptime_seconds=round(uptime, 2),
            checks={
                "system": {
                    "status": "healthy" if system_info.cpu_percent < 90 and system_info.memory_percent < 90 else "degraded",
                    "cpu_percent": system_info.cpu_percent,
                    "memory_percent": system_info.memory_percent,
                    "disk_percent": system_info.disk_percent
                },
                **external_checks
            }
        )
        
        log_with_context(
            logger, "info", "Health check completed",
            event="health_check_complete",
            status=overall_status,
            uptime_seconds=uptime
        )
        
        return health_response
        
    except Exception as e:
        log_with_context(
            logger, "error", f"Health check failed: {str(e)}",
            event="health_check_error",
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint
    Returns 200 if service is ready to accept traffic
    """
    try:
        # Check critical dependencies
        external_checks = await check_external_services()
        
        # Check if OpenAI is available (critical for core functionality)
        if external_checks.get("openai", {}).get("status") != "healthy":
            raise HTTPException(status_code=503, detail="OpenAI service unavailable")
        
        return {"status": "ready"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger, "error", f"Readiness check failed: {str(e)}",
            event="readiness_check_error"
        )
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    Returns 200 if service is alive (basic functionality)
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat() + "Z"}


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get application metrics for monitoring
    """
    try:
        system_info = get_system_info()
        metrics_summary = get_metrics_summary()
        
        response = MetricsResponse(
            timestamp=datetime.utcnow().isoformat() + "Z",
            system={
                "cpu_percent": system_info.cpu_percent,
                "memory_percent": system_info.memory_percent,
                "disk_percent": system_info.disk_percent,
                "load_average": system_info.load_average,
                "uptime_seconds": round(time.time() - _start_time, 2)
            },
            application={
                "metrics": metrics_summary,
                "version": "1.0.0"
            },
            api={
                "total_requests": sum(
                    len(metrics) for metrics in _metrics_store.values()
                ),
                "error_rate": calculate_error_rate()
            }
        )
        
        return response
        
    except Exception as e:
        log_with_context(
            logger, "error", f"Metrics collection failed: {str(e)}",
            event="metrics_error"
        )
        raise HTTPException(status_code=500, detail="Metrics collection failed")


def calculate_error_rate() -> float:
    """Calculate error rate from recent metrics"""
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    
    total_requests = 0
    error_requests = 0
    
    # Count API requests
    for metric in _metrics_store.get("api_requests", []):
        if datetime.fromisoformat(metric["timestamp"].replace("Z", "")) > one_hour_ago:
            total_requests += 1
            if metric.get("status_code", 200) >= 400:
                error_requests += 1
    
    # Add explicit errors
    for metric in _metrics_store.get("errors", []):
        if datetime.fromisoformat(metric["timestamp"].replace("Z", "")) > one_hour_ago:
            error_requests += 1
    
    if total_requests == 0:
        return 0.0
    
    return round((error_requests / total_requests) * 100, 2)


# Middleware function to record API metrics
def record_api_request(method: str, path: str, status_code: int, duration_ms: float):
    """Record API request metric"""
    record_metric("api_requests", {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms
    })


def record_function_call(function_name: str, success: bool, duration_ms: float):
    """Record function call metric"""
    record_metric("function_calls", {
        "function_name": function_name,
        "success": success,
        "duration_ms": duration_ms
    })


def record_external_api_call(service: str, endpoint: str, status_code: int, duration_ms: float):
    """Record external API call metric"""
    record_metric("external_api_calls", {
        "service": service,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": duration_ms
    })


def record_error(error_type: str, error_message: str, context: Dict[str, Any] = None):
    """Record error metric"""
    record_metric("errors", {
        "error_type": error_type,
        "error_message": error_message,
        "context": context or {}
    })
