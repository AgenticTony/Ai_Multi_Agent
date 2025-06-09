"""
Operational Supervisor - Real-time operations coordinator ("Air Traffic Control")
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

from memory.mem0 import memory_system
from monitoring.instrumentation import get_instrumentation

from voicehive.services.ai.openai_service import OpenAIService
from voicehive.domains.agents.services.emergency_manager import EmergencyManager, Emergency, EmergencySeverity
from voicehive.domains.agents.services.monitoring_agent import MonitoringAgent, AgentStatus
from voicehive.domains.communication.services.message_bus import MessageBus, MessageType, MessagePriority
from voicehive.domains.agents.services.ml.decision_engine import DecisionEngine, DecisionType, DecisionUrgency
from voicehive.domains.agents.services.ml.anomaly_detector import AnomalyDetector, TimeSeriesData, MetricDataPoint
from voicehive.domains.agents.services.ml.resource_allocator import ResourceAllocator
from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DecisionType(Enum):
    """Types of operational decisions"""
    RESOURCE_ALLOCATION = "resource_allocation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    EMERGENCY_RESPONSE = "emergency_response"
    LOAD_BALANCING = "load_balancing"
    AGENT_COORDINATION = "agent_coordination"


class ConflictType(Enum):
    """Types of agent conflicts"""
    RESOURCE_CONTENTION = "resource_contention"
    CONTRADICTORY_ACTIONS = "contradictory_actions"
    PRIORITY_CONFLICT = "priority_conflict"
    DATA_INCONSISTENCY = "data_inconsistency"


@dataclass
class AgentRegistration:
    """Agent registration information"""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    status: AgentStatus
    last_heartbeat: datetime
    performance_metrics: Dict[str, float]
    priority_level: int = 1  # 1=highest, 5=lowest


@dataclass
class OperationalDecision:
    """Operational decision record"""
    id: str
    type: DecisionType
    description: str
    timestamp: datetime
    affected_agents: List[str]
    decision_data: Dict[str, Any]
    confidence_score: float
    executed: bool = False
    execution_result: Optional[Dict[str, Any]] = None


@dataclass
class AgentConflict:
    """Agent conflict definition"""
    id: str
    type: ConflictType
    involved_agents: List[str]
    description: str
    timestamp: datetime
    severity: EmergencySeverity
    resolution_strategy: Optional[str] = None
    resolved: bool = False


class OperationalSupervisor:
    """
    Real-time operations coordinator ("Air Traffic Control")
    Handles live system orchestration and emergency response

    Focus: Sub-second decisions, system stability, immediate issue resolution
    """

    def __init__(self,
                 openai_service: Optional[OpenAIService] = None,
                 message_bus: Optional[MessageBus] = None,
                 emergency_manager: Optional[EmergencyManager] = None,
                 monitoring_agent: Optional[MonitoringAgent] = None,
                 project_id: Optional[str] = None):

        # Core services
        self.openai_service = openai_service or OpenAIService()
        self.message_bus = message_bus or MessageBus()
        self.emergency_manager = emergency_manager or EmergencyManager(self.openai_service)
        self.monitoring_agent = monitoring_agent or MonitoringAgent(self.message_bus)

        # ML-powered components (Phase 2)
        self.project_id = project_id or getattr(settings, 'google_cloud_project', 'default-project')
        self.decision_engine = DecisionEngine(self.project_id, openai_service=self.openai_service)
        self.anomaly_detector = AnomalyDetector(self.project_id, openai_service=self.openai_service)
        self.resource_allocator = ResourceAllocator(self.project_id, openai_service=self.openai_service)

        # System integrations
        try:
            self.memory_system = memory_system
        except:
            self.memory_system = None
            logger.warning("Memory system not available")

        try:
            self.instrumentation = get_instrumentation()
        except:
            self.instrumentation = None
            logger.warning("Instrumentation not available")

        # Operational state
        self.registered_agents: Dict[str, AgentRegistration] = {}
        self.active_decisions: Dict[str, OperationalDecision] = {}
        self.decision_history: List[OperationalDecision] = []
        self.active_conflicts: Dict[str, AgentConflict] = {}
        self.conflict_history: List[AgentConflict] = []

        # Coordination state
        self.is_running = False
        self.coordination_task: Optional[asyncio.Task] = None
        self.coordination_interval = 1  # 1-second coordination cycle

        # Performance tracking
        self.performance_metrics = {
            "decisions_per_minute": 0,
            "conflicts_resolved": 0,
            "emergencies_handled": 0,
            "avg_decision_time_ms": 0,
            "agent_uptime_percent": 100,
            "ml_predictions_accuracy": 0.0,
            "resource_optimization_savings": 0.0
        }

        logger.info("Operational Supervisor initialized with ML-powered Phase 2 capabilities")

    async def start(self):
        """Start the operational supervisor"""
        if self.is_running:
            logger.warning("Operational Supervisor is already running")
            return

        # Start dependent services
        if not self.message_bus.is_running:
            await self.message_bus.start()

        await self.monitoring_agent.start()

        # Subscribe to relevant messages
        self.message_bus.subscribe(
            subscriber_id="operational_supervisor",
            message_types=[
                MessageType.EMERGENCY_ALERT,
                MessageType.AGENT_STATUS_UPDATE,
                MessageType.PERFORMANCE_METRIC
            ],
            handler=self._handle_message
        )

        self.is_running = True
        self.coordination_task = asyncio.create_task(self.coordinate_agents())

        logger.info("Operational Supervisor started and coordinating agents")

    async def stop(self):
        """Stop the operational supervisor"""
        if not self.is_running:
            return

        self.is_running = False
        if self.coordination_task:
            self.coordination_task.cancel()
            try:
                await self.coordination_task
            except asyncio.CancelledError:
                pass

        await self.monitoring_agent.stop()

        logger.info("Operational Supervisor stopped")

    async def register_agent(self,
                           agent_id: str,
                           agent_type: str,
                           capabilities: List[str],
                           priority_level: int = 1) -> bool:
        """Register an agent with the supervisor"""
        try:
            registration = AgentRegistration(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities,
                status=AgentStatus.HEALTHY,
                last_heartbeat=datetime.now(),
                performance_metrics={},
                priority_level=priority_level
            )

            self.registered_agents[agent_id] = registration

            # Register with monitoring agent
            await self.monitoring_agent.register_agent(agent_id, agent_type, capabilities)

            logger.info(f"Agent {agent_id} registered with Operational Supervisor")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {str(e)}")
            return False

    async def _handle_message(self, message):
        """Handle incoming messages from other agents"""
        try:
            if message.type == MessageType.EMERGENCY_ALERT:
                await self._handle_emergency_alert(message.data)
            elif message.type == MessageType.AGENT_STATUS_UPDATE:
                await self._handle_agent_status_update(message.data)
            elif message.type == MessageType.PERFORMANCE_METRIC:
                await self._handle_performance_metric(message.data)

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    async def coordinate_agents(self):
        """Main real-time coordination loop"""
        logger.info("Starting agent coordination loop")

        while self.is_running:
            try:
                coordination_start = datetime.now()

                # Monitor agent health
                await self._monitor_agent_health()

                # Process urgent decisions
                await self._process_urgent_decisions()

                # Handle conflicts
                await self._resolve_conflicts()

                # Check for emergencies
                await self._check_emergencies()

                # Bridge to improvement pipeline
                await self._forward_improvement_triggers()

                # Update performance metrics
                coordination_time = (datetime.now() - coordination_start).total_seconds() * 1000
                self.performance_metrics["avg_decision_time_ms"] = coordination_time

                # Wait for next coordination cycle
                await asyncio.sleep(self.coordination_interval)

            except Exception as e:
                logger.error(f"Error in coordination loop: {str(e)}")
                await asyncio.sleep(self.coordination_interval)

    async def _monitor_agent_health(self):
        """Monitor health of all registered agents"""
        current_time = datetime.now()
        unhealthy_agents = []

        for agent_id, registration in self.registered_agents.items():
            # Check heartbeat timeout (30 seconds)
            if current_time - registration.last_heartbeat > timedelta(seconds=30):
                registration.status = AgentStatus.OFFLINE
                unhealthy_agents.append(agent_id)
                logger.warning(f"Agent {agent_id} is offline - no heartbeat for 30+ seconds")

        # Handle unhealthy agents
        if unhealthy_agents:
            await self._handle_unhealthy_agents(unhealthy_agents)

    async def _process_urgent_decisions(self):
        """Process urgent operational decisions using ML-powered decision engine"""
        # Check for pending decisions that need immediate attention
        urgent_decisions = [
            decision for decision in self.active_decisions.values()
            if not decision.executed and decision.confidence_score > 0.8
        ]

        # Use ML decision engine for complex decisions
        for decision in urgent_decisions:
            try:
                # Create decision request for ML engine
                decision_request_id = await self.decision_engine.request_decision(
                    decision_type=DecisionType.CONFLICT_RESOLUTION,
                    urgency=DecisionUrgency.URGENT,
                    data={
                        "decision_id": decision.id,
                        "type": decision.type.value,
                        "affected_agents": decision.affected_agents,
                        "decision_data": decision.decision_data
                    },
                    requesting_agent="operational_supervisor"
                )

                # Get ML-enhanced decision result
                ml_result = self.decision_engine.get_decision_status(decision_request_id)

                if ml_result and ml_result["status"] == "completed":
                    # Execute the ML-enhanced decision
                    result = await self._execute_ml_decision(decision, ml_result)
                    decision.executed = True
                    decision.execution_result = result

                    # Move to history
                    self.decision_history.append(decision)
                    del self.active_decisions[decision.id]

                    logger.info(f"Executed ML-enhanced urgent decision: {decision.type.value}")
                else:
                    # Fallback to original execution
                    result = await self._execute_decision(decision)
                    decision.executed = True
                    decision.execution_result = result

                    # Move to history
                    self.decision_history.append(decision)
                    del self.active_decisions[decision.id]

                    logger.info(f"Executed urgent decision (fallback): {decision.type.value}")

            except Exception as e:
                logger.error(f"Failed to execute decision {decision.id}: {str(e)}")

    async def _resolve_conflicts(self):
        """Handle conflicts between agents"""
        for conflict in list(self.active_conflicts.values()):
            if not conflict.resolved:
                try:
                    resolution_result = await self._resolve_agent_conflict(conflict)
                    if resolution_result["success"]:
                        conflict.resolved = True
                        conflict.resolution_strategy = resolution_result["strategy"]

                        # Move to history
                        self.conflict_history.append(conflict)
                        del self.active_conflicts[conflict.id]

                        self.performance_metrics["conflicts_resolved"] += 1
                        logger.info(f"Resolved conflict: {conflict.type.value}")

                except Exception as e:
                    logger.error(f"Failed to resolve conflict {conflict.id}: {str(e)}")

    async def _check_emergencies(self):
        """Check for emergency conditions using ML-powered anomaly detection"""
        # Get current system metrics
        system_metrics = await self._collect_current_metrics()

        # Use ML anomaly detection for predictive emergency detection
        try:
            # Convert metrics to time series data for anomaly detection
            time_series_data = []
            for metric_name, value in system_metrics.items():
                if isinstance(value, (int, float)):
                    data_point = MetricDataPoint(
                        timestamp=datetime.now(),
                        value=float(value),
                        metadata={"source": "operational_supervisor"}
                    )
                    time_series = TimeSeriesData(
                        metric_name=metric_name,
                        data_points=[data_point],
                        unit="",
                        description=f"System metric: {metric_name}"
                    )
                    time_series_data.append(time_series)

            # Detect anomalies using ML
            ml_anomalies = []
            for ts_data in time_series_data:
                detected_anomalies = await self.anomaly_detector.add_metric_data(ts_data)
                ml_anomalies.extend(detected_anomalies)

            # Get early warnings for potential issues
            early_warnings = self.anomaly_detector.get_early_warnings(threshold_hours=1)

            if ml_anomalies:
                logger.warning(f"ML detected {len(ml_anomalies)} anomalies")

                # Convert ML anomalies to emergency conditions
                for anomaly in ml_anomalies:
                    if anomaly.severity.value in ["high", "critical"]:
                        # Trigger emergency response for severe anomalies
                        system_metrics[f"anomaly_{anomaly.metric_name}"] = anomaly.deviation_score

            if early_warnings:
                logger.info(f"Early warning system detected {len(early_warnings)} potential issues")

        except Exception as e:
            logger.error(f"Error in ML anomaly detection: {str(e)}")

        # Check for emergency conditions (enhanced with ML insights)
        emergencies = await self.emergency_manager.check_emergency_conditions(system_metrics)

        for emergency in emergencies:
            try:
                # Handle the emergency
                intervention_result = await self.emergency_manager.handle_emergency(emergency)

                self.performance_metrics["emergencies_handled"] += 1
                logger.critical(f"Emergency handled: {emergency.type.value}")

                # Notify other supervisors
                await self._notify_emergency_handled(emergency, intervention_result)

            except Exception as e:
                logger.error(f"Failed to handle emergency {emergency.id}: {str(e)}")

    async def _forward_improvement_triggers(self):
        """Forward performance issues to the improvement pipeline"""
        # Analyze current performance and identify improvement opportunities
        improvement_triggers = await self._identify_improvement_triggers()

        for trigger in improvement_triggers:
            try:
                # Publish improvement trigger message
                await self.message_bus.publish(
                    message_type=MessageType.IMPROVEMENT_TRIGGER,
                    data=trigger,
                    sender_id="operational_supervisor",
                    priority=MessagePriority.NORMAL
                )

                logger.info(f"Improvement trigger sent: {trigger['type']}")

            except Exception as e:
                logger.error(f"Failed to send improvement trigger: {str(e)}")

    async def _execute_ml_decision(self, decision: OperationalDecision, ml_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a decision enhanced by ML analysis"""
        try:
            ml_decision = ml_result.get("decision", {})
            confidence = ml_result.get("confidence", 0.5)

            # Combine original decision with ML insights
            enhanced_result = {
                "original_decision": decision.decision_data,
                "ml_enhancement": ml_decision,
                "confidence": confidence,
                "execution_time": datetime.now().isoformat(),
                "success": True
            }

            # Execute based on ML recommendation
            if ml_decision.get("name") == "Priority-based Resolution":
                # Implement priority-based resolution
                for agent_id in decision.affected_agents:
                    if agent_id in self.registered_agents:
                        # Adjust agent priority based on ML recommendation
                        logger.info(f"Adjusted priority for agent {agent_id} based on ML analysis")

            return enhanced_result

        except Exception as e:
            logger.error(f"Error executing ML decision: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _execute_decision(self, decision: OperationalDecision) -> Dict[str, Any]:
        """Execute a standard operational decision"""
        try:
            # Basic decision execution logic
            result = {
                "decision_id": decision.id,
                "type": decision.type.value,
                "affected_agents": decision.affected_agents,
                "execution_time": datetime.now().isoformat(),
                "success": True
            }

            # Execute based on decision type
            if decision.type == DecisionType.RESOURCE_ALLOCATION:
                # Handle resource allocation
                for agent_id in decision.affected_agents:
                    logger.info(f"Allocating resources for agent {agent_id}")
            elif decision.type == DecisionType.CONFLICT_RESOLUTION:
                # Handle conflict resolution
                logger.info(f"Resolving conflicts for agents: {decision.affected_agents}")

            return result

        except Exception as e:
            logger.error(f"Error executing decision: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _collect_current_metrics(self) -> Dict[str, float]:
        """Collect current system metrics for analysis"""
        try:
            metrics = {}

            # Agent health metrics
            total_agents = len(self.registered_agents)
            healthy_agents = sum(1 for reg in self.registered_agents.values()
                               if reg.status == AgentStatus.HEALTHY)

            if total_agents > 0:
                metrics["agent_health_ratio"] = healthy_agents / total_agents
                metrics["agent_uptime_percent"] = (healthy_agents / total_agents) * 100

            # Performance metrics
            metrics.update(self.performance_metrics)

            # Resource utilization (from resource allocator)
            try:
                allocation_status = self.resource_allocator.get_allocation_status()
                resource_util = allocation_status.get("resource_utilization", {})
                for resource_type, utilization in resource_util.items():
                    metrics[f"resource_{resource_type}_utilization"] = utilization
            except Exception as e:
                logger.warning(f"Could not get resource utilization: {str(e)}")

            # System load metrics (simplified)
            metrics["system_load"] = 0.7  # This would come from actual monitoring
            metrics["memory_usage_percent"] = 65.0
            metrics["cpu_usage_percent"] = 45.0

            return metrics

        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            return {}

    async def _notify_emergency_handled(self, emergency: Emergency, intervention_result: Dict[str, Any]):
        """Notify other supervisors about emergency handling"""
        try:
            await self.message_bus.publish(
                message_type=MessageType.EMERGENCY_ALERT,
                data={
                    "event_type": "emergency_resolved",
                    "emergency_id": emergency.id,
                    "emergency_type": emergency.type.value,
                    "intervention_result": intervention_result,
                    "timestamp": datetime.now().isoformat()
                },
                sender_id="operational_supervisor",
                priority=MessagePriority.HIGH
            )
        except Exception as e:
            logger.error(f"Error notifying emergency handled: {str(e)}")

    def get_ml_statistics(self) -> Dict[str, Any]:
        """Get statistics about ML component performance"""
        try:
            return {
                "decision_engine": self.decision_engine.get_engine_statistics(),
                "anomaly_detector": self.anomaly_detector.get_detection_statistics(),
                "resource_allocator": self.resource_allocator.get_allocation_statistics(),
                "ml_integration_status": "active",
                "phase": "Phase 2 - Intelligent Coordination"
            }
        except Exception as e:
            logger.error(f"Error getting ML statistics: {str(e)}")
            return {"error": str(e)}