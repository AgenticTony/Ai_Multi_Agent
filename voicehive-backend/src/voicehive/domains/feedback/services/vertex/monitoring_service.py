#!/usr/bin/env python3
"""
VoiceHive Vertex AI Monitoring Service

Comprehensive monitoring, metrics collection, and alerting system for the
feedback pipeline with health checks and performance tracking.
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
from google.cloud import monitoring_v3
from google.cloud import logging as cloud_logging
from google.cloud import secretmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class HealthCheck:
    """Health check result"""
    service: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time_ms: float
    details: Dict[str, Any] = None

@dataclass
class MetricData:
    """Metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None
    unit: str = "count"

@dataclass
class Alert:
    """Alert definition"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    service: str
    metric_name: str = None
    threshold_value: float = None
    current_value: float = None
    resolved: bool = False

class MonitoringService:
    """
    Comprehensive monitoring service for VoiceHive Vertex AI system.
    
    Features:
    - Health checks for all system components
    - Performance metrics collection
    - Alert generation and management
    - Integration with Google Cloud Monitoring
    - Custom dashboards and reporting
    """
    
    def __init__(self, project_id: str = None):
        """
        Initialize monitoring service.
        
        Args:
            project_id: Google Cloud project ID
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        
        # Initialize Google Cloud clients
        try:
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            self.logging_client = cloud_logging.Client()
            self.secret_client = secretmanager.SecretManagerServiceClient()
        except Exception as e:
            logger.warning(f"Could not initialize Google Cloud clients: {e}")
            self.monitoring_client = None
            self.logging_client = None
            self.secret_client = None
        
        # Metrics storage
        self.metrics_buffer: List[MetricData] = []
        self.alerts_buffer: List[Alert] = []
        self.health_checks: Dict[str, HealthCheck] = {}
        
        # Performance thresholds
        self.thresholds = {
            "analysis_time_ms": 5000,  # 5 seconds max
            "memory_usage_mb": 1000,   # 1GB max
            "error_rate_percent": 5,   # 5% max error rate
            "api_response_time_ms": 2000,  # 2 seconds max
            "queue_depth": 100,        # 100 items max in queue
            "disk_usage_percent": 80   # 80% max disk usage
        }
        
        # Alert rules
        self.alert_rules = self._initialize_alert_rules()
    
    def _initialize_alert_rules(self) -> Dict[str, Dict]:
        """Initialize alert rules configuration"""
        return {
            "high_error_rate": {
                "metric": "error_rate_percent",
                "threshold": 10,
                "severity": AlertSeverity.HIGH,
                "duration_minutes": 5
            },
            "slow_analysis": {
                "metric": "analysis_time_ms",
                "threshold": 10000,
                "severity": AlertSeverity.MEDIUM,
                "duration_minutes": 3
            },
            "memory_leak": {
                "metric": "memory_usage_mb",
                "threshold": 2000,
                "severity": AlertSeverity.HIGH,
                "duration_minutes": 10
            },
            "pipeline_failure": {
                "metric": "pipeline_success_rate",
                "threshold": 0.9,
                "severity": AlertSeverity.CRITICAL,
                "duration_minutes": 1
            },
            "api_unavailable": {
                "metric": "api_availability_percent",
                "threshold": 95,
                "severity": AlertSeverity.CRITICAL,
                "duration_minutes": 2
            }
        }
    
    async def check_system_health(self) -> Dict[str, HealthCheck]:
        """
        Perform comprehensive system health checks.
        
        Returns:
            Dictionary of health check results by service
        """
        logger.info("🔍 Starting comprehensive health checks")
        
        health_checks = {}
        
        # Check core services
        services_to_check = [
            ("feedback_service", self._check_feedback_service_health),
            ("prompt_manager", self._check_prompt_manager_health),
            ("memory_system", self._check_memory_system_health),
            ("openai_api", self._check_openai_api_health),
            ("gcp_services", self._check_gcp_services_health),
            ("storage", self._check_storage_health),
            ("system_resources", self._check_system_resources_health)
        ]
        
        # Run health checks concurrently
        tasks = []
        for service_name, check_func in services_to_check:
            tasks.append(self._run_health_check(service_name, check_func))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            service_name = services_to_check[i][0]
            if isinstance(result, Exception):
                health_checks[service_name] = HealthCheck(
                    service=service_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}",
                    timestamp=datetime.now(),
                    response_time_ms=0
                )
            else:
                health_checks[service_name] = result
        
        self.health_checks = health_checks
        
        # Generate overall system health
        overall_status = self._calculate_overall_health(health_checks)
        health_checks["overall"] = HealthCheck(
            service="overall",
            status=overall_status,
            message=f"System overall status: {overall_status.value}",
            timestamp=datetime.now(),
            response_time_ms=0
        )
        
        logger.info(f"✅ Health checks completed. Overall status: {overall_status.value}")
        return health_checks
    
    async def _run_health_check(self, service_name: str, check_func) -> HealthCheck:
        """Run a single health check with timing"""
        start_time = time.time()
        try:
            result = await check_func()
            response_time = (time.time() - start_time) * 1000
            result.response_time_ms = response_time
            return result
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
    
    async def _check_feedback_service_health(self) -> HealthCheck:
        """Check feedback service health"""
        try:
            from vertex_feedback_service import VertexFeedbackService
            
            service = VertexFeedbackService()
            
            # Test with minimal transcript
            test_transcript = {
                "call_id": "health_check",
                "content": "Agent: Hello! Customer: Hi!",
                "timestamp": datetime.now().isoformat()
            }
            
            # Mock the OpenAI call for health check
            with patch.object(service, '_analyze_with_openai') as mock_openai:
                mock_openai.return_value = {
                    "sentiment_score": 0.7,
                    "booking_successful": True,
                    "issues_found": [],
                    "improvement_suggestions": []
                }
                
                result = await service.analyze_transcript(test_transcript)
                
                if result and "sentiment_score" in result:
                    return HealthCheck(
                        service="feedback_service",
                        status=HealthStatus.HEALTHY,
                        message="Feedback service is operational",
                        timestamp=datetime.now(),
                        response_time_ms=0
                    )
                else:
                    return HealthCheck(
                        service="feedback_service",
                        status=HealthStatus.DEGRADED,
                        message="Feedback service returned unexpected result",
                        timestamp=datetime.now(),
                        response_time_ms=0
                    )
        except Exception as e:
            return HealthCheck(
                service="feedback_service",
                status=HealthStatus.UNHEALTHY,
                message=f"Feedback service error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )
    
    async def _check_prompt_manager_health(self) -> HealthCheck:
        """Check prompt manager health"""
        try:
            from improvements.prompt_manager import PromptManager
            
            manager = PromptManager()
            current_prompt = manager.get_current_prompt()
            
            if current_prompt:
                return HealthCheck(
                    service="prompt_manager",
                    status=HealthStatus.HEALTHY,
                    message="Prompt manager is operational",
                    timestamp=datetime.now(),
                    response_time_ms=0,
                    details={"current_version": current_prompt.version}
                )
            else:
                return HealthCheck(
                    service="prompt_manager",
                    status=HealthStatus.DEGRADED,
                    message="No current prompt found",
                    timestamp=datetime.now(),
                    response_time_ms=0
                )
        except Exception as e:
            return HealthCheck(
                service="prompt_manager",
                status=HealthStatus.UNHEALTHY,
                message=f"Prompt manager error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )
    
    async def _check_memory_system_health(self) -> HealthCheck:
        """Check memory system health"""
        try:
            from memory.mem0 import memory_system
            
            # Test memory system with a simple query
            test_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            result = memory_system.get_memories_by_date(test_date)
            
            if result.get("success"):
                return HealthCheck(
                    service="memory_system",
                    status=HealthStatus.HEALTHY,
                    message="Memory system is operational",
                    timestamp=datetime.now(),
                    response_time_ms=0,
                    details={"memories_found": len(result.get("memories", []))}
                )
            else:
                return HealthCheck(
                    service="memory_system",
                    status=HealthStatus.DEGRADED,
                    message=f"Memory system returned error: {result.get('message')}",
                    timestamp=datetime.now(),
                    response_time_ms=0
                )
        except Exception as e:
            return HealthCheck(
                service="memory_system",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory system error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )
    
    async def _check_openai_api_health(self) -> HealthCheck:
        """Check OpenAI API health"""
        try:
            import openai
            
            # Simple API test
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Test with minimal request
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            if response and response.choices:
                return HealthCheck(
                    service="openai_api",
                    status=HealthStatus.HEALTHY,
                    message="OpenAI API is operational",
                    timestamp=datetime.now(),
                    response_time_ms=0
                )
            else:
                return HealthCheck(
                    service="openai_api",
                    status=HealthStatus.DEGRADED,
                    message="OpenAI API returned unexpected response",
                    timestamp=datetime.now(),
                    response_time_ms=0
                )
        except Exception as e:
            return HealthCheck(
                service="openai_api",
                status=HealthStatus.UNHEALTHY,
                message=f"OpenAI API error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )
    
    async def _check_gcp_services_health(self) -> HealthCheck:
        """Check Google Cloud services health"""
        try:
            services_status = {}
            
            # Check Secret Manager
            if self.secret_client:
                try:
                    # List secrets to test connectivity
                    parent = f"projects/{self.project_id}"
                    secrets = list(self.secret_client.list_secrets(request={"parent": parent}))
                    services_status["secret_manager"] = "healthy"
                except Exception as e:
                    services_status["secret_manager"] = f"error: {str(e)}"
            
            # Check Cloud Monitoring
            if self.monitoring_client:
                try:
                    # List metric descriptors to test connectivity
                    project_name = f"projects/{self.project_id}"
                    descriptors = list(self.monitoring_client.list_metric_descriptors(
                        request={"name": project_name}
                    ))
                    services_status["monitoring"] = "healthy"
                except Exception as e:
                    services_status["monitoring"] = f"error: {str(e)}"
            
            # Check Cloud Logging
            if self.logging_client:
                try:
                    # List log entries to test connectivity
                    entries = list(self.logging_client.list_entries(max_results=1))
                    services_status["logging"] = "healthy"
                except Exception as e:
                    services_status["logging"] = f"error: {str(e)}"
            
            # Determine overall GCP health
            healthy_services = sum(1 for status in services_status.values() if status == "healthy")
            total_services = len(services_status)
            
            if healthy_services == total_services:
                status = HealthStatus.HEALTHY
                message = "All GCP services are operational"
            elif healthy_services > 0:
                status = HealthStatus.DEGRADED
                message = f"{healthy_services}/{total_services} GCP services operational"
            else:
                status = HealthStatus.UNHEALTHY
                message = "GCP services are unavailable"
            
            return HealthCheck(
                service="gcp_services",
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time_ms=0,
                details=services_status
            )
        except Exception as e:
            return HealthCheck(
                service="gcp_services",
                status=HealthStatus.UNHEALTHY,
                message=f"GCP services check error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )
    
    async def _check_storage_health(self) -> HealthCheck:
        """Check storage system health"""
        try:
            # Check disk usage
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Check if we can write to temp directory
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
                f.write("health check")
                f.flush()
            
            if disk_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Disk usage critical: {disk_percent:.1f}%"
            elif disk_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Disk usage high: {disk_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Storage is healthy: {disk_percent:.1f}% used"
            
            return HealthCheck(
                service="storage",
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time_ms=0,
                details={
                    "disk_usage_percent": disk_percent,
                    "free_space_gb": disk_usage.free / (1024**3),
                    "total_space_gb": disk_usage.total / (1024**3)
                }
            )
        except Exception as e:
            return HealthCheck(
                service="storage",
                status=HealthStatus.UNHEALTHY,
                message=f"Storage check error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )
    
    async def _check_system_resources_health(self) -> HealthCheck:
        """Check system resources health"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Load average (Unix systems)
            try:
                load_avg = os.getloadavg()[0]  # 1-minute load average
            except (OSError, AttributeError):
                load_avg = 0  # Windows doesn't have load average
            
            # Determine status based on resource usage
            if cpu_percent > 90 or memory_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High resource usage: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%"
            elif cpu_percent > 70 or memory_percent > 70:
                status = HealthStatus.DEGRADED
                message = f"Moderate resource usage: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Resources healthy: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%"
            
            return HealthCheck(
                service="system_resources",
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time_ms=0,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "load_average": load_avg
                }
            )
        except Exception as e:
            return HealthCheck(
                service="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"System resources check error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )
    
    def _calculate_overall_health(self, health_checks: Dict[str, HealthCheck]) -> HealthStatus:
        """Calculate overall system health from individual checks"""
        if not health_checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in health_checks.values()]
        
        # If any critical service is unhealthy, system is unhealthy
        critical_services = ["feedback_service", "openai_api", "gcp_services"]
        for service in critical_services:
            if service in health_checks and health_checks[service].status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
        
        # If any service is unhealthy, system is degraded
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.DEGRADED
        
        # If any service is degraded, system is degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        # If all services are healthy, system is healthy
        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        
        return HealthStatus.UNKNOWN
    
    def collect_metrics(self) -> List[MetricData]:
        """
        Collect system and application metrics.
        
        Returns:
            List of metric data points
        """
        metrics = []
        timestamp = datetime.now()
        
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics.extend([
            MetricData("cpu_usage_percent", cpu_percent, timestamp, unit="percent"),
            MetricData("memory_usage_percent", memory.percent, timestamp, unit="percent"),
            MetricData("memory_usage_mb", memory.used / (1024**2), timestamp, unit="megabytes"),
            MetricData("disk_usage_percent", (disk.used / disk.total) * 100, timestamp, unit="percent"),
            MetricData("disk_free_gb", disk.free / (1024**3), timestamp, unit="gigabytes")
        ])
        
        # Application metrics from health checks
        if self.health_checks:
            healthy_services = sum(1 for check in self.health_checks.values() 
                                 if check.status == HealthStatus.HEALTHY)
            total_services = len(self.health_checks)
            
            metrics.extend([
                MetricData("healthy_services_count", healthy_services, timestamp),
                MetricData("total_services_count", total_services, timestamp),
                MetricData("service_health_ratio", healthy_services / total_services if total_services > 0 else 0, 
                          timestamp, unit="ratio")
            ])
            
            # Response time metrics
            for service, check in self.health_checks.items():
                if check.response_time_ms > 0:
                    metrics.append(MetricData(
                        f"{service}_response_time_ms", 
                        check.response_time_ms, 
                        timestamp, 
                        labels={"service": service},
                        unit="milliseconds"
                    ))
        
        self.metrics_buffer.extend(metrics)
        return metrics
    
    def check_alert_conditions(self, metrics: List[MetricData]) -> List[Alert]:
        """
        Check metrics against alert conditions and generate alerts.
        
        Args:
            metrics: List of metric data points
            
        Returns:
            List of generated alerts
        """
        alerts = []
        
        for metric in metrics:
            # Check against thresholds
            if metric.name in self.thresholds:
                threshold = self.thresholds[metric.name]
                
                if metric.value > threshold:
                    alert = Alert(
                        id=f"{metric.name}_{int(time.time())}",
                        severity=AlertSeverity.HIGH,
                        title=f"High {metric.name}",
                        message=f"{metric.name} is {metric.value:.2f} {metric.unit}, exceeding threshold of {threshold}",
                        timestamp=datetime.now(),
                        service="monitoring",
                        metric_name=metric.name,
                        threshold_value=threshold,
                        current_value=metric.value
                    )
                    alerts.append(alert)
        
        # Check health status alerts
        if self.health_checks:
            for service, check in self.health_checks.items():
                if check.status == HealthStatus.UNHEALTHY:
                    alert = Alert(
                        id=f"health_{service}_{int(time.time())}",
                        severity=AlertSeverity.CRITICAL,
                        title=f"Service Unhealthy: {service}",
                        message=f"Service {service} is unhealthy: {check.message}",
                        timestamp=datetime.now(),
                        service=service
                    )
                    alerts.append(alert)
        
        self.alerts_buffer.extend(alerts)
        return alerts
    
    async def send_alerts(self, alerts: List[Alert]):
        """
        Send alerts to configured notification channels.
        
        Args:
            alerts: List of alerts to send
        """
        for alert in alerts:
            try:
                # Log alert
                logger.warning(f"🚨 ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")
                
                # Send to Google Cloud Logging
                if self.logging_client:
                    self.logging_client.logger("voicehive-alerts").log_struct({
                        "alert_id": alert.id,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "message": alert.message,
                        "service": alert.service,
                        "timestamp": alert.timestamp.isoformat()
                    }, severity=alert.severity.value.upper())
                
                # TODO: Add integrations for:
                # - Slack notifications
                # - Email alerts
                # - PagerDuty integration
                # - SMS notifications
                
            except Exception as e:
                logger.error(f"Failed to send alert {alert.id}: {e}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health"""
        if not self.health_checks:
            return {"status": "unknown", "message": "No health checks performed"}
        
        overall_check = self.health_checks.get("overall")
        if not overall_check:
            return {"status": "unknown", "message": "Overall health not calculated"}
        
        return {
            "status": overall_check.status.value,
            "message": overall_check.message,
            "timestamp": overall_check.timestamp.isoformat(),
            "services": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms
                }
                for name, check in self.health_checks.items()
                if name != "overall"
            }
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of recent metrics"""
        if not self.metrics_buffer:
            return {"message": "No metrics collected"}
        
        # Get latest metrics
        latest_metrics = {}
        for metric in reversed(self.metrics_buffer[-50:]):  # Last 50 metrics
            if metric.name not in latest_metrics:
                latest_metrics[metric.name] = {
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat()
                }
        
        return {
            "latest_metrics": latest_metrics,
            "total_metrics_collected": len(self.metrics_buffer),
            "collection_period": "last_hour"  # TODO: Make this configurable
        }

# Global monitoring service instance
monitoring_service = MonitoringService()

async def run_monitoring_cycle():
    """Run a complete monitoring cycle"""
    logger.info("🔍 Starting monitoring cycle")
    
    try:
        # Perform health checks
        health_checks = await monitoring_service.check_system_health()
        
        # Collect metrics
        metrics = monitoring_service.collect_metrics()
        
        # Check for alerts
        alerts = monitoring_service.check_alert_conditions(metrics)
        
        # Send alerts if any
        if alerts:
            await monitoring_service.send_alerts(alerts)
        
        logger.info(f"✅ Monitoring cycle completed. Health: {health_checks['overall'].status.value}, "
                   f"Metrics: {len(metrics)}, Alerts: {len(alerts)}")
        
        return {
            "health_checks": len(health_checks),
            "metrics_collected": len(metrics),
            "alerts_generated": len(alerts),
            "overall_health": health_checks['overall'].status.value
        }
        
    except Exception as e:
        logger.error(f"❌ Monitoring cycle failed: {e}")
        raise

if __name__ == "__main__":
    # Run monitoring cycle if executed directly
    asyncio.run(run_monitoring_cycle())
