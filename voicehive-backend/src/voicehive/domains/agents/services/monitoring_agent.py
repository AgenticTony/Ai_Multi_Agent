"""
Monitoring Agent - Real-time system monitoring for supervisor coordination
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
import psutil
import uuid

from voicehive.domains.communication.services.message_bus import MessageBus, MessageType, MessagePriority
from voicehive.domains.feedback.services.vertex.monitoring_service import MonitoringService, HealthStatus
from voicehive.utils.exceptions import VoiceHiveError, ErrorHandler
from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentStatus(Enum):
    """Agent status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    agent_id: str
    status: AgentStatus
    response_time_ms: float
    success_rate: float
    error_count: int
    memory_usage_mb: float
    cpu_usage_percent: float
    last_heartbeat: datetime
    uptime_seconds: int


@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    timestamp: datetime
    total_agents: int
    healthy_agents: int
    degraded_agents: int
    unhealthy_agents: int
    offline_agents: int
    avg_response_time_ms: float
    overall_success_rate: float
    system_cpu_percent: float
    system_memory_percent: float
    active_emergencies: int


class MonitoringAgent:
    """
    Real-time system monitoring agent for supervisor coordination
    
    Features:
    - Agent health monitoring
    - Performance metrics collection
    - Real-time alerting
    - Dashboard data provision
    - Integration with supervisor systems
    """
    
    def __init__(self, 
                 message_bus: Optional[MessageBus] = None,
                 monitoring_service: Optional[MonitoringService] = None):
        self.message_bus = message_bus or MessageBus()
        self.monitoring_service = monitoring_service or MonitoringService()
        
        # Agent tracking
        self.registered_agents: Dict[str, AgentMetrics] = {}
        self.agent_heartbeats: Dict[str, datetime] = {}
        
        # Monitoring configuration
        self.monitoring_interval = 5  # seconds
        self.heartbeat_timeout = 30   # seconds
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
        
        # Monitoring state
        self.is_running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Performance thresholds
        self.thresholds = {
            "response_time_ms": 5000,      # 5 seconds
            "success_rate": 0.95,          # 95%
            "memory_usage_mb": 1000,       # 1GB
            "cpu_usage_percent": 80,       # 80%
            "heartbeat_timeout_seconds": 30 # 30 seconds
        }
        
        logger.info("Monitoring Agent initialized for supervisor coordination")
    
    async def start(self):
        """Start the monitoring agent"""
        if self.is_running:
            logger.warning("Monitoring agent is already running")
            return
        
        # Start message bus if not running
        if not self.message_bus.is_running:
            await self.message_bus.start()
        
        # Subscribe to agent messages
        self.message_bus.subscribe(
            subscriber_id="monitoring_agent",
            message_types=[
                MessageType.AGENT_HEARTBEAT,
                MessageType.AGENT_STATUS_UPDATE,
                MessageType.PERFORMANCE_METRIC
            ],
            handler=self._handle_agent_message
        )
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Monitoring Agent started and collecting metrics")
    
    async def stop(self):
        """Stop the monitoring agent"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring Agent stopped")
    
    async def register_agent(self, 
                           agent_id: str, 
                           agent_type: str,
                           capabilities: List[str]) -> bool:
        """Register an agent for monitoring"""
        try:
            initial_metrics = AgentMetrics(
                agent_id=agent_id,
                status=AgentStatus.HEALTHY,
                response_time_ms=0.0,
                success_rate=1.0,
                error_count=0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                last_heartbeat=datetime.now(),
                uptime_seconds=0
            )
            
            self.registered_agents[agent_id] = initial_metrics
            self.agent_heartbeats[agent_id] = datetime.now()
            
            # Publish registration event
            await self.message_bus.publish(
                message_type=MessageType.AGENT_STATUS_UPDATE,
                data={
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "capabilities": capabilities,
                    "status": "registered",
                    "timestamp": datetime.now().isoformat()
                },
                sender_id="monitoring_agent",
                priority=MessagePriority.NORMAL
            )
            
            logger.info(f"Agent {agent_id} registered for monitoring")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {str(e)}")
            return False
    
    async def _handle_agent_message(self, message):
        """Handle incoming agent messages"""
        try:
            agent_id = message.data.get("agent_id")
            if not agent_id:
                return
            
            if message.type == MessageType.AGENT_HEARTBEAT:
                await self._process_heartbeat(agent_id, message.data)
            elif message.type == MessageType.AGENT_STATUS_UPDATE:
                await self._process_status_update(agent_id, message.data)
            elif message.type == MessageType.PERFORMANCE_METRIC:
                await self._process_performance_metric(agent_id, message.data)
                
        except Exception as e:
            logger.error(f"Error handling agent message: {str(e)}")
    
    async def _process_heartbeat(self, agent_id: str, data: Dict[str, Any]):
        """Process agent heartbeat"""
        self.agent_heartbeats[agent_id] = datetime.now()
        
        if agent_id in self.registered_agents:
            metrics = self.registered_agents[agent_id]
            metrics.last_heartbeat = datetime.now()
            
            # Update status based on heartbeat data
            if data.get("status") == "healthy":
                metrics.status = AgentStatus.HEALTHY
            elif data.get("status") == "degraded":
                metrics.status = AgentStatus.DEGRADED
    
    async def _process_status_update(self, agent_id: str, data: Dict[str, Any]):
        """Process agent status update"""
        if agent_id not in self.registered_agents:
            return
        
        metrics = self.registered_agents[agent_id]
        status_str = data.get("status", "healthy")
        
        try:
            metrics.status = AgentStatus(status_str)
        except ValueError:
            metrics.status = AgentStatus.HEALTHY
        
        # Update other metrics if provided
        if "response_time_ms" in data:
            metrics.response_time_ms = float(data["response_time_ms"])
        if "success_rate" in data:
            metrics.success_rate = float(data["success_rate"])
        if "error_count" in data:
            metrics.error_count = int(data["error_count"])
    
    async def _process_performance_metric(self, agent_id: str, data: Dict[str, Any]):
        """Process agent performance metrics"""
        if agent_id not in self.registered_agents:
            return
        
        metrics = self.registered_agents[agent_id]
        
        # Update performance metrics
        if "memory_usage_mb" in data:
            metrics.memory_usage_mb = float(data["memory_usage_mb"])
        if "cpu_usage_percent" in data:
            metrics.cpu_usage_percent = float(data["cpu_usage_percent"])
        if "uptime_seconds" in data:
            metrics.uptime_seconds = int(data["uptime_seconds"])
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Check agent health
                await self._check_agent_health()
                
                # Collect system metrics
                system_metrics = await self._collect_system_metrics()
                
                # Store metrics in history
                self._add_to_history(system_metrics)
                
                # Check for alerts
                await self._check_alert_conditions(system_metrics)
                
                # Publish system metrics
                await self._publish_system_metrics(system_metrics)
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _check_agent_health(self):
        """Check health of all registered agents"""
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=self.heartbeat_timeout)
        
        for agent_id, last_heartbeat in self.agent_heartbeats.items():
            if current_time - last_heartbeat > timeout_threshold:
                # Agent is offline
                if agent_id in self.registered_agents:
                    self.registered_agents[agent_id].status = AgentStatus.OFFLINE
                    
                    # Publish offline alert
                    await self.message_bus.publish(
                        message_type=MessageType.EMERGENCY_ALERT,
                        data={
                            "alert_type": "agent_offline",
                            "agent_id": agent_id,
                            "last_heartbeat": last_heartbeat.isoformat(),
                            "timeout_seconds": self.heartbeat_timeout
                        },
                        sender_id="monitoring_agent",
                        priority=MessagePriority.HIGH
                    )
                    
                    logger.warning(f"Agent {agent_id} is offline (last heartbeat: {last_heartbeat})")
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide metrics"""
        current_time = datetime.now()
        
        # Count agents by status
        status_counts = {status: 0 for status in AgentStatus}
        total_response_time = 0
        total_success_rate = 0
        active_agents = 0
        
        for metrics in self.registered_agents.values():
            status_counts[metrics.status] += 1
            if metrics.status != AgentStatus.OFFLINE:
                total_response_time += metrics.response_time_ms
                total_success_rate += metrics.success_rate
                active_agents += 1
        
        # Calculate averages
        avg_response_time = total_response_time / max(active_agents, 1)
        overall_success_rate = total_success_rate / max(active_agents, 1)
        
        # Get system resource usage
        system_cpu = psutil.cpu_percent()
        system_memory = psutil.virtual_memory().percent
        
        # Count active emergencies (simplified)
        active_emergencies = 0  # This would integrate with EmergencyManager
        
        return SystemMetrics(
            timestamp=current_time,
            total_agents=len(self.registered_agents),
            healthy_agents=status_counts[AgentStatus.HEALTHY],
            degraded_agents=status_counts[AgentStatus.DEGRADED],
            unhealthy_agents=status_counts[AgentStatus.UNHEALTHY],
            offline_agents=status_counts[AgentStatus.OFFLINE],
            avg_response_time_ms=avg_response_time,
            overall_success_rate=overall_success_rate,
            system_cpu_percent=system_cpu,
            system_memory_percent=system_memory,
            active_emergencies=active_emergencies
        )
    
    async def _check_alert_conditions(self, metrics: SystemMetrics):
        """Check for alert conditions and publish alerts"""
        alerts = []
        
        # Check response time
        if metrics.avg_response_time_ms > self.thresholds["response_time_ms"]:
            alerts.append({
                "type": "high_response_time",
                "value": metrics.avg_response_time_ms,
                "threshold": self.thresholds["response_time_ms"]
            })
        
        # Check success rate
        if metrics.overall_success_rate < self.thresholds["success_rate"]:
            alerts.append({
                "type": "low_success_rate",
                "value": metrics.overall_success_rate,
                "threshold": self.thresholds["success_rate"]
            })
        
        # Check system resources
        if metrics.system_cpu_percent > self.thresholds["cpu_usage_percent"]:
            alerts.append({
                "type": "high_cpu_usage",
                "value": metrics.system_cpu_percent,
                "threshold": self.thresholds["cpu_usage_percent"]
            })
        
        # Check offline agents
        if metrics.offline_agents > 0:
            alerts.append({
                "type": "agents_offline",
                "value": metrics.offline_agents,
                "threshold": 0
            })
        
        # Publish alerts
        for alert in alerts:
            await self.message_bus.publish(
                message_type=MessageType.EMERGENCY_ALERT,
                data=alert,
                sender_id="monitoring_agent",
                priority=MessagePriority.HIGH
            )
    
    async def _publish_system_metrics(self, metrics: SystemMetrics):
        """Publish system metrics for dashboard and other consumers"""
        await self.message_bus.publish(
            message_type=MessageType.PERFORMANCE_METRIC,
            data={
                "metric_type": "system_overview",
                "metrics": {
                    "timestamp": metrics.timestamp.isoformat(),
                    "total_agents": metrics.total_agents,
                    "healthy_agents": metrics.healthy_agents,
                    "degraded_agents": metrics.degraded_agents,
                    "unhealthy_agents": metrics.unhealthy_agents,
                    "offline_agents": metrics.offline_agents,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "overall_success_rate": metrics.overall_success_rate,
                    "system_cpu_percent": metrics.system_cpu_percent,
                    "system_memory_percent": metrics.system_memory_percent,
                    "active_emergencies": metrics.active_emergencies
                }
            },
            sender_id="monitoring_agent",
            priority=MessagePriority.NORMAL
        )
    
    def _add_to_history(self, metrics: SystemMetrics):
        """Add metrics to history with size management"""
        self.metrics_history.append(metrics)
        
        # Trim history if too large
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def get_agent_metrics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific agent or all agents"""
        if agent_id:
            if agent_id in self.registered_agents:
                return {
                    "agent_id": agent_id,
                    "metrics": self.registered_agents[agent_id].__dict__
                }
            else:
                return {"error": "Agent not found"}
        
        return {
            "total_agents": len(self.registered_agents),
            "agents": {
                agent_id: metrics.__dict__ 
                for agent_id, metrics in self.registered_agents.items()
            }
        }
    
    def get_system_metrics(self, limit: int = 100) -> List[SystemMetrics]:
        """Get recent system metrics"""
        return self.metrics_history[-limit:]
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get monitoring agent statistics"""
        return {
            "registered_agents": len(self.registered_agents),
            "metrics_history_size": len(self.metrics_history),
            "monitoring_interval_seconds": self.monitoring_interval,
            "heartbeat_timeout_seconds": self.heartbeat_timeout,
            "is_running": self.is_running,
            "thresholds": self.thresholds
        }
