"""
Autonomous Decision Controller for VoiceHive Phase 3

This module implements confidence-based autonomous decision making with human-in-the-loop
capabilities for critical decisions. Provides safety constraints and escalation paths.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from voicehive.services.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of autonomous decisions"""
    OPERATIONAL = "operational"  # Day-to-day operations
    STRATEGIC = "strategic"      # Long-term planning
    EMERGENCY = "emergency"      # Crisis response
    OPTIMIZATION = "optimization"  # Performance tuning
    SAFETY = "safety"           # Safety-critical decisions


class ConfidenceLevel(Enum):
    """Confidence levels for autonomous decisions"""
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 20-40%
    MEDIUM = "medium"          # 40-60%
    HIGH = "high"              # 60-80%
    VERY_HIGH = "very_high"    # 80-100%


class DecisionStatus(Enum):
    """Status of autonomous decisions"""
    PENDING = "pending"
    AUTONOMOUS = "autonomous"
    ESCALATED = "escalated"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass
class DecisionContext:
    """Context information for decision making"""
    decision_id: str
    decision_type: DecisionType
    description: str
    data: Dict[str, Any]
    urgency: int = 1  # 1-10 scale
    impact: int = 1   # 1-10 scale
    risk_level: int = 1  # 1-10 scale
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DecisionResult:
    """Result of autonomous decision making"""
    decision_id: str
    action: str
    confidence: float
    reasoning: str
    status: DecisionStatus
    execution_plan: List[str]
    rollback_plan: List[str]
    monitoring_metrics: List[str]
    human_approval_required: bool = False
    escalation_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SafetyConstraint:
    """Safety constraint for autonomous decisions"""
    name: str
    condition: str
    max_risk_level: int
    requires_human_approval: bool = True
    description: str = ""


class AutonomousController:
    """
    Advanced autonomous decision controller with confidence-based decision making,
    human-in-the-loop capabilities, and comprehensive safety constraints.
    """
    
    def __init__(self, openai_service: Optional[OpenAIService] = None):
        self.openai_service = openai_service or OpenAIService()
        
        # Decision configuration
        self.confidence_thresholds = {
            DecisionType.OPERATIONAL: 0.7,
            DecisionType.STRATEGIC: 0.8,
            DecisionType.EMERGENCY: 0.6,  # Lower threshold for urgent decisions
            DecisionType.OPTIMIZATION: 0.75,
            DecisionType.SAFETY: 0.9  # Highest threshold for safety decisions
        }
        
        # Safety constraints
        self.safety_constraints: List[SafetyConstraint] = []
        self._initialize_default_constraints()
        
        # Decision history and monitoring
        self.decision_history: List[DecisionResult] = []
        self.pending_decisions: Dict[str, DecisionContext] = {}
        self.human_approval_callbacks: Dict[str, Callable] = {}
        
        # Performance metrics
        self.metrics = {
            "total_decisions": 0,
            "autonomous_decisions": 0,
            "escalated_decisions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_confidence": 0.0
        }
        
        logger.info("Autonomous controller initialized")
    
    def _initialize_default_constraints(self):
        """Initialize default safety constraints"""
        default_constraints = [
            SafetyConstraint(
                name="high_risk_operations",
                condition="risk_level > 7",
                max_risk_level=7,
                requires_human_approval=True,
                description="High-risk operations require human approval"
            ),
            SafetyConstraint(
                name="strategic_decisions",
                condition="decision_type == 'strategic' and impact > 5",
                max_risk_level=5,
                requires_human_approval=True,
                description="Strategic decisions with high impact require approval"
            ),
            SafetyConstraint(
                name="safety_critical",
                condition="decision_type == 'safety'",
                max_risk_level=3,
                requires_human_approval=True,
                description="All safety-critical decisions require human oversight"
            ),
            SafetyConstraint(
                name="emergency_override",
                condition="decision_type == 'emergency' and urgency > 8",
                max_risk_level=10,
                requires_human_approval=False,
                description="Emergency decisions with high urgency can be autonomous"
            )
        ]
        
        self.safety_constraints.extend(default_constraints)
    
    def add_safety_constraint(self, constraint: SafetyConstraint):
        """Add a custom safety constraint"""
        self.safety_constraints.append(constraint)
        logger.info(f"Added safety constraint: {constraint.name}")
    
    def set_confidence_threshold(self, decision_type: DecisionType, threshold: float):
        """Set confidence threshold for a decision type"""
        self.confidence_thresholds[decision_type] = threshold
        logger.info(f"Set confidence threshold for {decision_type.value}: {threshold}")
    
    async def make_decision(self, context: DecisionContext) -> DecisionResult:
        """
        Make an autonomous decision based on context and constraints
        
        Args:
            context: Decision context with all relevant information
            
        Returns:
            DecisionResult with decision outcome and execution plan
        """
        logger.info(f"Making decision: {context.decision_id} ({context.decision_type.value})")
        
        try:
            # Store pending decision
            self.pending_decisions[context.decision_id] = context
            
            # Check safety constraints
            constraint_check = self._check_safety_constraints(context)
            if not constraint_check["allowed"]:
                return self._escalate_decision(context, constraint_check["reason"])
            
            # Generate decision using AI
            decision_result = await self._generate_ai_decision(context)
            
            # Evaluate confidence and determine if human approval is needed
            confidence_threshold = self.confidence_thresholds.get(
                context.decision_type, 0.8
            )
            
            if decision_result.confidence < confidence_threshold:
                decision_result.human_approval_required = True
                decision_result.escalation_reason = f"Confidence {decision_result.confidence:.2f} below threshold {confidence_threshold}"
                decision_result.status = DecisionStatus.ESCALATED
            else:
                decision_result.status = DecisionStatus.AUTONOMOUS
            
            # Update metrics
            self._update_metrics(decision_result)
            
            # Store decision
            self.decision_history.append(decision_result)
            
            logger.info(f"Decision made: {decision_result.status.value} (confidence: {decision_result.confidence:.2f})")
            
            return decision_result
            
        except Exception as e:
            logger.error(f"Decision making failed: {str(e)}")
            return DecisionResult(
                decision_id=context.decision_id,
                action="error",
                confidence=0.0,
                reasoning=f"Decision making failed: {str(e)}",
                status=DecisionStatus.FAILED,
                execution_plan=[],
                rollback_plan=[],
                monitoring_metrics=[],
                human_approval_required=True,
                escalation_reason="System error"
            )
    
    def _check_safety_constraints(self, context: DecisionContext) -> Dict[str, Any]:
        """Check if decision violates any safety constraints"""
        for constraint in self.safety_constraints:
            if self._evaluate_constraint_condition(constraint, context):
                if constraint.requires_human_approval:
                    return {
                        "allowed": False,
                        "reason": f"Safety constraint violated: {constraint.name}",
                        "constraint": constraint.name
                    }
                elif context.risk_level > constraint.max_risk_level:
                    return {
                        "allowed": False,
                        "reason": f"Risk level {context.risk_level} exceeds maximum {constraint.max_risk_level}",
                        "constraint": constraint.name
                    }
        
        return {"allowed": True, "reason": "All constraints satisfied"}
    
    def _evaluate_constraint_condition(self, constraint: SafetyConstraint, context: DecisionContext) -> bool:
        """Evaluate if a constraint condition is met"""
        # Simple condition evaluation - in practice, you'd use a proper expression evaluator
        condition = constraint.condition
        
        # Replace variables with actual values
        condition = condition.replace("risk_level", str(context.risk_level))
        condition = condition.replace("impact", str(context.impact))
        condition = condition.replace("urgency", str(context.urgency))
        condition = condition.replace("decision_type", f"'{context.decision_type.value}'")
        
        try:
            # WARNING: In production, use a safe expression evaluator
            return eval(condition)
        except Exception:
            logger.warning(f"Failed to evaluate constraint condition: {condition}")
            return False
    
    def _escalate_decision(self, context: DecisionContext, reason: str) -> DecisionResult:
        """Escalate decision to human oversight"""
        return DecisionResult(
            decision_id=context.decision_id,
            action="escalated",
            confidence=0.0,
            reasoning=f"Decision escalated: {reason}",
            status=DecisionStatus.ESCALATED,
            execution_plan=[],
            rollback_plan=[],
            monitoring_metrics=[],
            human_approval_required=True,
            escalation_reason=reason
        )
    
    async def _generate_ai_decision(self, context: DecisionContext) -> DecisionResult:
        """Generate decision using AI reasoning"""
        try:
            prompt = f"""
            As an autonomous decision-making system, analyze this situation and provide a decision:
            
            Context:
            - Decision ID: {context.decision_id}
            - Type: {context.decision_type.value}
            - Description: {context.description}
            - Data: {json.dumps(context.data, indent=2)}
            - Urgency: {context.urgency}/10
            - Impact: {context.impact}/10
            - Risk Level: {context.risk_level}/10
            
            Provide a decision with:
            1. Recommended action
            2. Confidence level (0-1)
            3. Detailed reasoning
            4. Step-by-step execution plan
            5. Rollback plan if things go wrong
            6. Key metrics to monitor
            
            Format as JSON:
            {{
                "action": "specific action to take",
                "confidence": 0.85,
                "reasoning": "detailed explanation",
                "execution_plan": ["step 1", "step 2", "step 3"],
                "rollback_plan": ["rollback step 1", "rollback step 2"],
                "monitoring_metrics": ["metric 1", "metric 2"]
            }}
            """
            
            response = await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=800,
                temperature=0.2
            )
            
            # Parse AI response
            try:
                ai_decision = json.loads(response)
                
                return DecisionResult(
                    decision_id=context.decision_id,
                    action=ai_decision.get("action", "no action"),
                    confidence=float(ai_decision.get("confidence", 0.0)),
                    reasoning=ai_decision.get("reasoning", "No reasoning provided"),
                    status=DecisionStatus.PENDING,
                    execution_plan=ai_decision.get("execution_plan", []),
                    rollback_plan=ai_decision.get("rollback_plan", []),
                    monitoring_metrics=ai_decision.get("monitoring_metrics", [])
                )
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI decision response")
                return self._create_fallback_decision(context)
                
        except Exception as e:
            logger.error(f"AI decision generation failed: {str(e)}")
            return self._create_fallback_decision(context)
    
    def _create_fallback_decision(self, context: DecisionContext) -> DecisionResult:
        """Create fallback decision when AI fails"""
        return DecisionResult(
            decision_id=context.decision_id,
            action="manual_review_required",
            confidence=0.0,
            reasoning="AI decision generation failed, manual review required",
            status=DecisionStatus.ESCALATED,
            execution_plan=["Escalate to human operator"],
            rollback_plan=["No action taken"],
            monitoring_metrics=["system_health"],
            human_approval_required=True,
            escalation_reason="AI system failure"
        )

    def _update_metrics(self, decision_result: DecisionResult):
        """Update performance metrics"""
        self.metrics["total_decisions"] += 1

        if decision_result.status == DecisionStatus.AUTONOMOUS:
            self.metrics["autonomous_decisions"] += 1
        elif decision_result.status == DecisionStatus.ESCALATED:
            self.metrics["escalated_decisions"] += 1

        # Update average confidence
        total_confidence = (self.metrics["average_confidence"] *
                          (self.metrics["total_decisions"] - 1) +
                          decision_result.confidence)
        self.metrics["average_confidence"] = total_confidence / self.metrics["total_decisions"]

    async def execute_decision(self, decision_id: str) -> Dict[str, Any]:
        """Execute an approved autonomous decision"""
        decision = next((d for d in self.decision_history if d.decision_id == decision_id), None)
        if not decision:
            return {"success": False, "error": "Decision not found"}

        if decision.status not in [DecisionStatus.AUTONOMOUS, DecisionStatus.APPROVED]:
            return {"success": False, "error": f"Decision not ready for execution: {decision.status.value}"}

        try:
            logger.info(f"Executing decision: {decision_id}")

            # Execute each step in the execution plan
            execution_results = []
            for i, step in enumerate(decision.execution_plan):
                logger.info(f"Executing step {i+1}: {step}")

                # Simulate step execution (in practice, this would call actual functions)
                step_result = await self._execute_step(step, decision)
                execution_results.append(step_result)

                if not step_result.get("success", False):
                    # Execution failed, initiate rollback
                    logger.warning(f"Step {i+1} failed, initiating rollback")
                    rollback_result = await self._execute_rollback(decision, i)

                    decision.status = DecisionStatus.FAILED
                    self.metrics["failed_executions"] += 1

                    return {
                        "success": False,
                        "error": f"Execution failed at step {i+1}",
                        "step_results": execution_results,
                        "rollback_result": rollback_result
                    }

            # Execution successful
            decision.status = DecisionStatus.EXECUTED
            self.metrics["successful_executions"] += 1

            # Start monitoring
            await self._start_decision_monitoring(decision)

            logger.info(f"Decision {decision_id} executed successfully")

            return {
                "success": True,
                "execution_results": execution_results,
                "monitoring_started": True
            }

        except Exception as e:
            logger.error(f"Decision execution failed: {str(e)}")
            decision.status = DecisionStatus.FAILED
            self.metrics["failed_executions"] += 1

            return {"success": False, "error": str(e)}

    async def _execute_step(self, step: str, decision: DecisionResult) -> Dict[str, Any]:
        """Execute a single step of the decision plan"""
        # This is a placeholder - in practice, this would route to actual
        # implementation functions based on the step description
        logger.info(f"Simulating execution of step: {step}")

        # Simulate success/failure
        import random
        success = random.random() > 0.05  # 95% success rate for testing

        return {
            "success": success,
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "details": f"Step executed: {step}"
        }

    async def _execute_rollback(self, decision: DecisionResult, failed_step_index: int) -> Dict[str, Any]:
        """Execute rollback plan when decision execution fails"""
        logger.info(f"Executing rollback for decision: {decision.decision_id}")

        rollback_results = []
        for step in decision.rollback_plan:
            logger.info(f"Rollback step: {step}")

            # Simulate rollback execution
            result = {
                "success": True,
                "step": step,
                "timestamp": datetime.now().isoformat()
            }
            rollback_results.append(result)

        return {
            "success": True,
            "rollback_steps": rollback_results,
            "failed_at_step": failed_step_index
        }

    async def _start_decision_monitoring(self, decision: DecisionResult):
        """Start monitoring for executed decision"""
        logger.info(f"Starting monitoring for decision: {decision.decision_id}")

        # In practice, this would set up actual monitoring based on the metrics
        for metric in decision.monitoring_metrics:
            logger.info(f"Monitoring metric: {metric}")

    async def approve_decision(self, decision_id: str, approver: str) -> Dict[str, Any]:
        """Approve an escalated decision for execution"""
        decision = next((d for d in self.decision_history if d.decision_id == decision_id), None)
        if not decision:
            return {"success": False, "error": "Decision not found"}

        if decision.status != DecisionStatus.ESCALATED:
            return {"success": False, "error": f"Decision not in escalated status: {decision.status.value}"}

        decision.status = DecisionStatus.APPROVED
        logger.info(f"Decision {decision_id} approved by {approver}")

        return {"success": True, "message": f"Decision approved by {approver}"}

    async def reject_decision(self, decision_id: str, rejector: str, reason: str) -> Dict[str, Any]:
        """Reject an escalated decision"""
        decision = next((d for d in self.decision_history if d.decision_id == decision_id), None)
        if not decision:
            return {"success": False, "error": "Decision not found"}

        if decision.status != DecisionStatus.ESCALATED:
            return {"success": False, "error": f"Decision not in escalated status: {decision.status.value}"}

        decision.status = DecisionStatus.REJECTED
        decision.escalation_reason = f"Rejected by {rejector}: {reason}"

        logger.info(f"Decision {decision_id} rejected by {rejector}: {reason}")

        return {"success": True, "message": f"Decision rejected by {rejector}"}

    def get_pending_decisions(self) -> List[DecisionResult]:
        """Get all decisions pending human approval"""
        return [d for d in self.decision_history if d.status == DecisionStatus.ESCALATED]

    def get_decision_history(self, limit: int = 100) -> List[DecisionResult]:
        """Get recent decision history"""
        return self.decision_history[-limit:]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get autonomous controller performance metrics"""
        if self.metrics["total_decisions"] == 0:
            autonomy_rate = 0
        else:
            autonomy_rate = self.metrics["autonomous_decisions"] / self.metrics["total_decisions"]

        if self.metrics["autonomous_decisions"] + self.metrics["escalated_decisions"] == 0:
            success_rate = 0
        else:
            total_executed = self.metrics["successful_executions"] + self.metrics["failed_executions"]
            success_rate = self.metrics["successful_executions"] / max(total_executed, 1)

        return {
            **self.metrics,
            "autonomy_rate": autonomy_rate,
            "success_rate": success_rate,
            "pending_approvals": len(self.get_pending_decisions()),
            "safety_constraints": len(self.safety_constraints)
        }

    async def suggest_threshold_adjustments(self) -> Dict[str, Any]:
        """Suggest confidence threshold adjustments based on performance"""
        try:
            metrics = self.get_performance_metrics()

            prompt = f"""
            Analyze autonomous decision performance and suggest confidence threshold adjustments:

            Current Performance:
            - Total decisions: {metrics['total_decisions']}
            - Autonomy rate: {metrics['autonomy_rate']:.2f}
            - Success rate: {metrics['success_rate']:.2f}
            - Average confidence: {metrics['average_confidence']:.2f}
            - Pending approvals: {metrics['pending_approvals']}

            Current Thresholds:
            {json.dumps({dt.value: thresh for dt, thresh in self.confidence_thresholds.items()}, indent=2)}

            Suggest threshold adjustments to optimize autonomy while maintaining safety.
            Consider:
            1. If success rate is high, thresholds could be lowered
            2. If too many escalations, thresholds might be too high
            3. Safety-critical decisions should maintain high thresholds

            Format: {{"adjustments": {{"decision_type": new_threshold}}, "reasoning": "explanation"}}
            """

            response = await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=400,
                temperature=0.2
            )

            try:
                suggestions = json.loads(response)
                return suggestions
            except json.JSONDecodeError:
                return {
                    "adjustments": {},
                    "reasoning": "Unable to parse AI suggestions"
                }

        except Exception as e:
            logger.error(f"Failed to suggest threshold adjustments: {str(e)}")
            return {"error": "Unable to generate suggestions"}
