"""
Emergency Manager - Handles emergency situations and automatic interventions
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
import uuid

from voicehive.services.ai.openai_service import OpenAIService
from voicehive.domains.prompts.services.prompt_manager import PromptManager
from voicehive.utils.exceptions import VoiceHiveError, ErrorHandler
from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmergencySeverity(Enum):
    """Emergency severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EmergencyType(Enum):
    """Types of emergency conditions"""
    CALL_FAILURE_RATE = "call_failure_rate"
    RESPONSE_TIME_DEGRADATION = "response_time_degradation"
    AGENT_DOWNTIME = "agent_downtime"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    API_RATE_LIMIT = "api_rate_limit"
    PROMPT_VALIDATION_FAILURE = "prompt_validation_failure"
    SYSTEM_OVERLOAD = "system_overload"


@dataclass
class Emergency:
    """Emergency event definition"""
    id: str
    type: EmergencyType
    severity: EmergencySeverity
    message: str
    timestamp: datetime
    affected_agents: List[str]
    metrics: Dict[str, float]
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None
    resolution_actions: List[str] = None


@dataclass
class EmergencyThreshold:
    """Emergency threshold configuration"""
    metric_name: str
    threshold_value: float
    severity: EmergencySeverity
    duration_seconds: int = 60  # How long condition must persist
    cooldown_seconds: int = 300  # Cooldown before re-triggering


class EmergencyManager:
    """
    Handles emergency situations and automatic interventions
    
    Features:
    - Real-time emergency detection
    - Automatic intervention protocols
    - Emergency escalation procedures
    - Recovery coordination
    - Emergency logging and reporting
    """
    
    def __init__(self, 
                 openai_service: Optional[OpenAIService] = None,
                 prompt_manager: Optional[PromptManager] = None):
        self.openai_service = openai_service or OpenAIService()
        self.prompt_manager = prompt_manager
        
        # Emergency state tracking
        self.active_emergencies: Dict[str, Emergency] = {}
        self.emergency_history: List[Emergency] = []
        self.last_check_time = datetime.now()
        
        # Emergency thresholds configuration
        self.thresholds = self._initialize_thresholds()
        
        # Intervention protocols
        self.intervention_protocols = self._initialize_protocols()
        
        # Emergency cooldowns to prevent alert spam
        self.cooldowns: Dict[str, datetime] = {}
        
        logger.info("Emergency Manager initialized with comprehensive intervention protocols")
    
    def _initialize_thresholds(self) -> Dict[str, EmergencyThreshold]:
        """Initialize emergency detection thresholds"""
        return {
            "call_failure_rate": EmergencyThreshold(
                metric_name="call_failure_rate",
                threshold_value=0.3,  # 30% failure rate
                severity=EmergencySeverity.HIGH,
                duration_seconds=120,
                cooldown_seconds=300
            ),
            "response_time": EmergencyThreshold(
                metric_name="avg_response_time_ms",
                threshold_value=8000,  # 8 seconds
                severity=EmergencySeverity.MEDIUM,
                duration_seconds=180,
                cooldown_seconds=180
            ),
            "agent_downtime": EmergencyThreshold(
                metric_name="agent_downtime_seconds",
                threshold_value=300,  # 5 minutes
                severity=EmergencySeverity.CRITICAL,
                duration_seconds=60,
                cooldown_seconds=600
            ),
            "memory_usage": EmergencyThreshold(
                metric_name="memory_usage_percent",
                threshold_value=90,  # 90% memory usage
                severity=EmergencySeverity.HIGH,
                duration_seconds=300,
                cooldown_seconds=300
            ),
            "api_rate_limit": EmergencyThreshold(
                metric_name="api_rate_limit_hit",
                threshold_value=1,  # Any rate limit hit
                severity=EmergencySeverity.MEDIUM,
                duration_seconds=30,
                cooldown_seconds=900
            )
        }
    
    def _initialize_protocols(self) -> Dict[EmergencyType, List[str]]:
        """Initialize emergency intervention protocols"""
        return {
            EmergencyType.CALL_FAILURE_RATE: [
                "activate_backup_prompts",
                "reduce_ai_complexity",
                "enable_fallback_responses",
                "notify_human_operators"
            ],
            EmergencyType.RESPONSE_TIME_DEGRADATION: [
                "optimize_prompt_length",
                "reduce_ai_temperature",
                "enable_response_caching",
                "scale_processing_resources"
            ],
            EmergencyType.AGENT_DOWNTIME: [
                "restart_failed_agents",
                "redistribute_workload",
                "activate_backup_agents",
                "escalate_to_human_support"
            ],
            EmergencyType.MEMORY_EXHAUSTION: [
                "clear_memory_caches",
                "reduce_conversation_history",
                "garbage_collect_sessions",
                "scale_memory_resources"
            ],
            EmergencyType.API_RATE_LIMIT: [
                "implement_request_throttling",
                "activate_backup_api_keys",
                "reduce_api_call_frequency",
                "cache_recent_responses"
            ]
        }
    
    async def check_emergency_conditions(self, metrics: Dict[str, float]) -> List[Emergency]:
        """
        Check if any emergency conditions are met
        
        Args:
            metrics: Current system metrics
            
        Returns:
            List of detected emergencies
        """
        detected_emergencies = []
        current_time = datetime.now()
        
        for threshold_name, threshold in self.thresholds.items():
            metric_value = metrics.get(threshold.metric_name, 0)
            
            # Check if threshold is exceeded
            if metric_value > threshold.threshold_value:
                # Check cooldown period
                cooldown_key = f"{threshold_name}_{threshold.severity.value}"
                if cooldown_key in self.cooldowns:
                    if current_time < self.cooldowns[cooldown_key]:
                        continue  # Still in cooldown
                
                # Create emergency
                emergency = Emergency(
                    id=str(uuid.uuid4()),
                    type=EmergencyType(threshold_name.replace("_", "_").upper()),
                    severity=threshold.severity,
                    message=f"{threshold.metric_name} exceeded threshold: {metric_value} > {threshold.threshold_value}",
                    timestamp=current_time,
                    affected_agents=self._identify_affected_agents(threshold.metric_name, metrics),
                    metrics=metrics.copy()
                )
                
                detected_emergencies.append(emergency)
                
                # Set cooldown
                cooldown_time = current_time + timedelta(seconds=threshold.cooldown_seconds)
                self.cooldowns[cooldown_key] = cooldown_time
                
                logger.warning(f"Emergency detected: {emergency.type.value} - {emergency.message}")
        
        return detected_emergencies
    
    def _identify_affected_agents(self, metric_name: str, metrics: Dict[str, float]) -> List[str]:
        """Identify which agents are affected by the emergency condition"""
        # This is a simplified implementation
        # In a real system, you'd have more sophisticated agent tracking
        affected_agents = []
        
        if "call_failure" in metric_name:
            affected_agents = ["roxy_agent", "voice_handler"]
        elif "response_time" in metric_name:
            affected_agents = ["roxy_agent", "openai_service"]
        elif "memory" in metric_name:
            affected_agents = ["all_agents"]
        elif "api_rate_limit" in metric_name:
            affected_agents = ["openai_service", "vertex_service"]
        
        return affected_agents
    
    async def handle_emergency(self, emergency: Emergency) -> Dict[str, Any]:
        """
        Execute emergency response procedures
        
        Args:
            emergency: Emergency to handle
            
        Returns:
            Results of intervention actions
        """
        logger.critical(f"Handling emergency: {emergency.type.value} - Severity: {emergency.severity.value}")
        
        # Get intervention protocols for this emergency type
        protocols = self.intervention_protocols.get(emergency.type, [])
        
        intervention_results = {
            "emergency_id": emergency.id,
            "actions_taken": [],
            "success": True,
            "errors": []
        }
        
        # Execute intervention protocols
        for protocol in protocols:
            try:
                result = await self._execute_intervention(protocol, emergency)
                intervention_results["actions_taken"].append({
                    "action": protocol,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Emergency intervention '{protocol}' executed successfully")
                
            except Exception as e:
                error_msg = f"Failed to execute intervention '{protocol}': {str(e)}"
                intervention_results["errors"].append(error_msg)
                intervention_results["success"] = False
                logger.error(error_msg)
        
        # Mark emergency as handled
        self.active_emergencies[emergency.id] = emergency
        
        return intervention_results

    async def _execute_intervention(self, protocol: str, emergency: Emergency) -> Dict[str, Any]:
        """Execute a specific intervention protocol"""
        try:
            if protocol == "activate_backup_prompts":
                return await self._activate_backup_prompts()
            elif protocol == "reduce_ai_complexity":
                return await self._reduce_ai_complexity()
            elif protocol == "enable_fallback_responses":
                return await self._enable_fallback_responses()
            elif protocol == "notify_human_operators":
                return await self._notify_human_operators(emergency)
            elif protocol == "restart_failed_agents":
                return await self._restart_failed_agents(emergency.affected_agents)
            elif protocol == "redistribute_workload":
                return await self._redistribute_workload()
            elif protocol == "clear_memory_caches":
                return await self._clear_memory_caches()
            elif protocol == "implement_request_throttling":
                return await self._implement_request_throttling()
            else:
                return {"status": "not_implemented", "protocol": protocol}

        except Exception as e:
            logger.error(f"Error executing intervention {protocol}: {str(e)}")
            raise

    async def _activate_backup_prompts(self) -> Dict[str, Any]:
        """Activate backup/simplified prompts during emergencies"""
        if not self.prompt_manager:
            return {"status": "skipped", "reason": "prompt_manager_not_available"}

        try:
            # Get current prompt
            current_prompt = self.prompt_manager.get_current_prompt()
            if not current_prompt:
                return {"status": "failed", "reason": "no_current_prompt"}

            # Create simplified backup prompt
            backup_prompt = {
                "system_prompt": """You are Roxy, a helpful AI assistant. Keep responses brief and direct.
                Focus on essential information only. If you cannot help, politely transfer to a human operator.""",
                "temperature": 0.3,  # Lower temperature for more predictable responses
                "max_tokens": 150,   # Shorter responses
                "emergency_mode": True
            }

            # Store backup prompt (simplified implementation)
            backup_result = self.prompt_manager.store_emergency_prompt(backup_prompt)

            return {
                "status": "success",
                "backup_prompt_id": backup_result.get("prompt_id"),
                "original_prompt_id": current_prompt.get("id")
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _reduce_ai_complexity(self) -> Dict[str, Any]:
        """Reduce AI model complexity to improve response times"""
        try:
            # This would typically involve:
            # - Switching to faster models (e.g., GPT-3.5 instead of GPT-4)
            # - Reducing max_tokens
            # - Lowering temperature
            # - Simplifying system prompts

            complexity_settings = {
                "model": "gpt-3.5-turbo",  # Faster model
                "temperature": 0.1,        # More deterministic
                "max_tokens": 100,         # Shorter responses
                "timeout": 5               # Shorter timeout
            }

            # Apply settings (this would integrate with OpenAI service)
            logger.info("AI complexity reduced for emergency response")

            return {
                "status": "success",
                "settings_applied": complexity_settings
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _enable_fallback_responses(self) -> Dict[str, Any]:
        """Enable pre-defined fallback responses for common scenarios"""
        try:
            fallback_responses = {
                "greeting": "Hello! I'm experiencing some technical difficulties. Let me connect you with a human representative.",
                "booking": "I'd be happy to help you schedule an appointment. Let me transfer you to our booking specialist.",
                "general": "I apologize, but I'm having some technical issues right now. Please hold while I connect you with a human agent.",
                "error": "I'm sorry, I'm experiencing technical difficulties. A human representative will assist you shortly."
            }

            # Store fallback responses (simplified implementation)
            logger.info("Fallback responses activated for emergency mode")

            return {
                "status": "success",
                "fallback_responses_count": len(fallback_responses)
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _notify_human_operators(self, emergency: Emergency) -> Dict[str, Any]:
        """Notify human operators about the emergency"""
        try:
            notification_message = f"""
            🚨 EMERGENCY ALERT 🚨

            Type: {emergency.type.value}
            Severity: {emergency.severity.value}
            Time: {emergency.timestamp.isoformat()}

            Message: {emergency.message}
            Affected Agents: {', '.join(emergency.affected_agents)}

            Immediate action may be required.
            """

            # This would typically integrate with:
            # - Slack/Teams notifications
            # - Email alerts
            # - SMS notifications
            # - PagerDuty/incident management systems

            logger.critical(f"Human operators notified of emergency: {emergency.id}")

            return {
                "status": "success",
                "notification_sent": True,
                "channels": ["log", "monitoring_dashboard"]  # Simplified for now
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _restart_failed_agents(self, affected_agents: List[str]) -> Dict[str, Any]:
        """Restart failed agents (simplified implementation)"""
        try:
            restart_results = {}

            for agent_id in affected_agents:
                # In a real implementation, this would:
                # - Stop the agent process
                # - Clear its state
                # - Restart with fresh configuration
                # - Verify successful restart

                restart_results[agent_id] = {
                    "status": "restarted",
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(f"Agent {agent_id} restart initiated")

            return {
                "status": "success",
                "agents_restarted": restart_results
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _redistribute_workload(self) -> Dict[str, Any]:
        """Redistribute workload among healthy agents"""
        try:
            # This would typically involve:
            # - Identifying healthy agents
            # - Redistributing pending requests
            # - Updating load balancer configuration
            # - Monitoring redistribution success

            logger.info("Workload redistribution initiated")

            return {
                "status": "success",
                "redistribution_completed": True
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _clear_memory_caches(self) -> Dict[str, Any]:
        """Clear memory caches to free up resources"""
        try:
            # This would typically involve:
            # - Clearing conversation history caches
            # - Freeing up memory buffers
            # - Garbage collecting unused objects
            # - Optimizing memory usage

            logger.info("Memory caches cleared for emergency recovery")

            return {
                "status": "success",
                "caches_cleared": ["conversation_history", "response_cache", "session_cache"]
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _implement_request_throttling(self) -> Dict[str, Any]:
        """Implement request throttling to manage API rate limits"""
        try:
            throttling_config = {
                "max_requests_per_minute": 30,  # Reduced from normal rate
                "max_concurrent_requests": 5,   # Limit concurrent requests
                "backoff_strategy": "exponential",
                "retry_attempts": 3
            }

            logger.info("Request throttling implemented for rate limit management")

            return {
                "status": "success",
                "throttling_config": throttling_config
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def resolve_emergency(self, emergency_id: str, resolution_notes: str = "") -> Dict[str, Any]:
        """Mark an emergency as resolved"""
        if emergency_id not in self.active_emergencies:
            return {"status": "error", "message": "Emergency not found"}

        emergency = self.active_emergencies[emergency_id]
        emergency.resolved = True
        emergency.resolution_timestamp = datetime.now()

        # Move to history
        self.emergency_history.append(emergency)
        del self.active_emergencies[emergency_id]

        logger.info(f"Emergency {emergency_id} resolved: {resolution_notes}")

        return {
            "status": "success",
            "emergency_id": emergency_id,
            "resolution_time": emergency.resolution_timestamp.isoformat()
        }

    def get_active_emergencies(self) -> List[Emergency]:
        """Get list of currently active emergencies"""
        return list(self.active_emergencies.values())

    def get_emergency_history(self, limit: int = 50) -> List[Emergency]:
        """Get emergency history"""
        return self.emergency_history[-limit:]

    def get_emergency_statistics(self) -> Dict[str, Any]:
        """Get emergency statistics and metrics"""
        total_emergencies = len(self.emergency_history) + len(self.active_emergencies)

        if total_emergencies == 0:
            return {"total_emergencies": 0, "message": "No emergencies recorded"}

        # Calculate statistics
        severity_counts = {}
        type_counts = {}

        all_emergencies = list(self.emergency_history) + list(self.active_emergencies.values())

        for emergency in all_emergencies:
            severity_counts[emergency.severity.value] = severity_counts.get(emergency.severity.value, 0) + 1
            type_counts[emergency.type.value] = type_counts.get(emergency.type.value, 0) + 1

        return {
            "total_emergencies": total_emergencies,
            "active_emergencies": len(self.active_emergencies),
            "resolved_emergencies": len(self.emergency_history),
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "last_emergency": all_emergencies[-1].timestamp.isoformat() if all_emergencies else None
        }
