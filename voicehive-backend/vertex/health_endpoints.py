#!/usr/bin/env python3
"""
Health Check Endpoints for VoiceHive Vertex AI System

FastAPI endpoints for system health monitoring, metrics, and status reporting.
Provides comprehensive health checks for all system components.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
import os

from monitoring_service import monitoring_service, run_monitoring_cycle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VoiceHive Vertex AI Health API",
    description="Health monitoring and metrics API for VoiceHive Vertex AI feedback system",
    version="1.0.0"
)

@app.get("/health", summary="Basic Health Check")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Basic system status and timestamp
        
    Example:
        GET /health
        
        Response:
        {
            "status": "healthy",
            "timestamp": "2024-01-05T10:00:00Z",
            "service": "voicehive-vertex-ai"
        }
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "voicehive-vertex-ai",
        "version": "1.0.0"
    }

@app.get("/health/detailed", summary="Detailed Health Check")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for all system components.
    
    Performs health checks on:
    - Feedback service
    - Prompt manager
    - Memory system
    - OpenAI API
    - Google Cloud services
    - Storage systems
    - System resources
    
    Returns:
        Detailed health status for each component
        
    Example:
        GET /health/detailed
        
        Response:
        {
            "overall_status": "healthy",
            "timestamp": "2024-01-05T10:00:00Z",
            "services": {
                "feedback_service": {
                    "status": "healthy",
                    "message": "Feedback service is operational",
                    "response_time_ms": 150.5
                },
                ...
            }
        }
    """
    try:
        health_checks = await monitoring_service.check_system_health()
        
        return {
            "overall_status": health_checks["overall"].status.value,
            "timestamp": datetime.now().isoformat(),
            "services": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "details": check.details
                }
                for name, check in health_checks.items()
                if name != "overall"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/health/pipeline", summary="Pipeline Health Check")
async def pipeline_health_check() -> Dict[str, Any]:
    """
    Check the health of the feedback pipeline specifically.
    
    Returns:
        Pipeline-specific health information including:
        - Last execution status
        - Processing metrics
        - Error rates
        - Queue status
        
    Example:
        GET /health/pipeline
        
        Response:
        {
            "status": "healthy",
            "last_execution": "2024-01-05T06:00:00Z",
            "calls_processed": 45,
            "success_rate": 0.98,
            "avg_processing_time_ms": 2500
        }
    """
    try:
        # Check pipeline-specific components
        pipeline_checks = {}
        
        # Check feedback service
        health_checks = await monitoring_service.check_system_health()
        feedback_status = health_checks.get("feedback_service")
        
        if feedback_status:
            pipeline_checks["feedback_service"] = {
                "status": feedback_status.status.value,
                "response_time_ms": feedback_status.response_time_ms
            }
        
        # Check memory system
        memory_status = health_checks.get("memory_system")
        if memory_status:
            pipeline_checks["memory_system"] = {
                "status": memory_status.status.value,
                "response_time_ms": memory_status.response_time_ms
            }
        
        # Check OpenAI API
        openai_status = health_checks.get("openai_api")
        if openai_status:
            pipeline_checks["openai_api"] = {
                "status": openai_status.status.value,
                "response_time_ms": openai_status.response_time_ms
            }
        
        # Determine overall pipeline health
        all_healthy = all(
            check["status"] == "healthy" 
            for check in pipeline_checks.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "components": pipeline_checks,
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pipeline health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline health check failed: {str(e)}")

@app.get("/health/dependencies", summary="External Dependencies Health")
async def dependencies_health_check() -> Dict[str, Any]:
    """
    Check the health of external dependencies.
    
    Checks:
    - OpenAI API connectivity and response time
    - Google Cloud services availability
    - Memory system (Mem0) connectivity
    - Network connectivity
    
    Returns:
        Status of all external dependencies
        
    Example:
        GET /health/dependencies
        
        Response:
        {
            "status": "healthy",
            "dependencies": {
                "openai_api": {
                    "status": "healthy",
                    "response_time_ms": 250,
                    "last_check": "2024-01-05T10:00:00Z"
                },
                ...
            }
        }
    """
    try:
        health_checks = await monitoring_service.check_system_health()
        
        # Extract dependency-specific checks
        dependencies = {}
        dependency_services = ["openai_api", "gcp_services", "memory_system"]
        
        for service in dependency_services:
            if service in health_checks:
                check = health_checks[service]
                dependencies[service] = {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "last_check": check.timestamp.isoformat(),
                    "details": check.details
                }
        
        # Determine overall dependency health
        all_healthy = all(
            dep["status"] == "healthy" 
            for dep in dependencies.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "dependencies": dependencies
        }
        
    except Exception as e:
        logger.error(f"Dependencies health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dependencies health check failed: {str(e)}")

@app.get("/metrics", summary="System Metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get current system metrics.
    
    Returns:
        Current system performance metrics including:
        - CPU and memory usage
        - Disk space
        - Service response times
        - Application-specific metrics
        
    Example:
        GET /metrics
        
        Response:
        {
            "timestamp": "2024-01-05T10:00:00Z",
            "system": {
                "cpu_usage_percent": 25.5,
                "memory_usage_percent": 45.2,
                "disk_usage_percent": 60.1
            },
            "application": {
                "healthy_services_count": 7,
                "total_services_count": 7,
                "service_health_ratio": 1.0
            }
        }
    """
    try:
        # Collect current metrics
        metrics = monitoring_service.collect_metrics()
        
        # Organize metrics by category
        system_metrics = {}
        application_metrics = {}
        
        for metric in metrics:
            if metric.name.startswith(("cpu_", "memory_", "disk_")):
                system_metrics[metric.name] = {
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat()
                }
            else:
                application_metrics[metric.name] = {
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat()
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": system_metrics,
            "application": application_metrics,
            "total_metrics": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")

@app.get("/metrics/summary", summary="Metrics Summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a summary of recent metrics and trends.
    
    Returns:
        Summary of metrics collected over time with trends and averages
        
    Example:
        GET /metrics/summary
        
        Response:
        {
            "period": "last_hour",
            "metrics_collected": 120,
            "latest_metrics": {
                "cpu_usage_percent": {
                    "current": 25.5,
                    "average": 23.2,
                    "peak": 45.1
                }
            }
        }
    """
    try:
        summary = monitoring_service.get_metrics_summary()
        return summary
    except Exception as e:
        logger.error(f"Metrics summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics summary failed: {str(e)}")

@app.get("/alerts", summary="Active Alerts")
async def get_alerts() -> Dict[str, Any]:
    """
    Get current active alerts.
    
    Returns:
        List of active alerts with severity and details
        
    Example:
        GET /alerts
        
        Response:
        {
            "active_alerts": [
                {
                    "id": "high_cpu_1704448800",
                    "severity": "high",
                    "title": "High CPU Usage",
                    "message": "CPU usage is 85%, exceeding threshold of 80%",
                    "timestamp": "2024-01-05T10:00:00Z",
                    "service": "system"
                }
            ],
            "total_alerts": 1
        }
    """
    try:
        # Get recent alerts from monitoring service
        active_alerts = [
            {
                "id": alert.id,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "service": alert.service,
                "resolved": alert.resolved
            }
            for alert in monitoring_service.alerts_buffer
            if not alert.resolved
        ]
        
        return {
            "active_alerts": active_alerts,
            "total_alerts": len(active_alerts),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Alerts retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Alerts retrieval failed: {str(e)}")

@app.post("/monitoring/run", summary="Trigger Monitoring Cycle")
async def trigger_monitoring_cycle() -> Dict[str, Any]:
    """
    Manually trigger a complete monitoring cycle.
    
    Useful for:
    - Testing monitoring system
    - Immediate health assessment
    - Debugging issues
    
    Returns:
        Results of the monitoring cycle
        
    Example:
        POST /monitoring/run
        
        Response:
        {
            "status": "completed",
            "health_checks": 8,
            "metrics_collected": 15,
            "alerts_generated": 0,
            "overall_health": "healthy",
            "execution_time_ms": 1250
        }
    """
    try:
        import time
        start_time = time.time()
        
        result = await run_monitoring_cycle()
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "execution_time_ms": execution_time,
            **result
        }
        
    except Exception as e:
        logger.error(f"Monitoring cycle trigger failed: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring cycle failed: {str(e)}")

@app.get("/status", summary="System Status Overview")
async def get_system_status() -> Dict[str, Any]:
    """
    Get a comprehensive system status overview.
    
    Combines health checks, metrics, and alerts into a single status view.
    Perfect for dashboards and monitoring systems.
    
    Returns:
        Complete system status overview
        
    Example:
        GET /status
        
        Response:
        {
            "overall_status": "healthy",
            "timestamp": "2024-01-05T10:00:00Z",
            "health": {
                "status": "healthy",
                "services_healthy": 7,
                "services_total": 7
            },
            "performance": {
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "response_time_avg": 150.5
            },
            "alerts": {
                "active_count": 0,
                "critical_count": 0
            }
        }
    """
    try:
        # Get health summary
        health_summary = monitoring_service.get_health_summary()
        
        # Get latest metrics
        metrics = monitoring_service.collect_metrics()
        
        # Get active alerts
        active_alerts = [alert for alert in monitoring_service.alerts_buffer if not alert.resolved]
        critical_alerts = [alert for alert in active_alerts if alert.severity.value == "critical"]
        
        # Calculate performance summary
        performance = {}
        for metric in metrics:
            if metric.name in ["cpu_usage_percent", "memory_usage_percent"]:
                performance[metric.name.replace("_percent", "")] = metric.value
        
        # Calculate average response time
        response_times = [
            metric.value for metric in metrics 
            if metric.name.endswith("_response_time_ms")
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "overall_status": health_summary.get("status", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "health": {
                "status": health_summary.get("status", "unknown"),
                "message": health_summary.get("message", ""),
                "services_healthy": len([
                    s for s in health_summary.get("services", {}).values() 
                    if s.get("status") == "healthy"
                ]),
                "services_total": len(health_summary.get("services", {}))
            },
            "performance": {
                **performance,
                "response_time_avg_ms": avg_response_time
            },
            "alerts": {
                "active_count": len(active_alerts),
                "critical_count": len(critical_alerts)
            },
            "uptime": {
                "service": "voicehive-vertex-ai",
                "version": "1.0.0"
            }
        }
        
    except Exception as e:
        logger.error(f"System status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"System status failed: {str(e)}")

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Run the health API server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("HEALTH_API_PORT", "8080")),
        log_level="info"
    )
