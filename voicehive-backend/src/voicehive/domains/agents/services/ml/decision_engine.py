"""
Enhanced Decision Engine - Multi-criteria analysis and intelligent coordination
Integrates ML-based prioritization, anomaly detection, and resource allocation
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json
import uuid

from voicehive.domains.agents.services.ml.prioritization_engine import (
    PrioritizationEngine, ImprovementCandidate, PrioritizationResult, ImprovementPriority
)
from voicehive.domains.agents.services.ml.anomaly_detector import (
    AnomalyDetector, AnomalyDetection, TimeSeriesData, MetricDataPoint
)
from voicehive.domains.agents.services.ml.resource_allocator import (
    ResourceAllocator, AllocationStrategy, ResourceType
)
from voicehive.services.ai.openai_service import OpenAIService
from voicehive.utils.exceptions import VoiceHiveError, ErrorHandler
from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DecisionType(Enum):
    """Types of decisions the engine can make"""
    IMPROVEMENT_PRIORITIZATION = "improvement_prioritization"
    RESOURCE_ALLOCATION = "resource_allocation"
    EMERGENCY_RESPONSE = "emergency_response"
    CONFLICT_RESOLUTION = "conflict_resolution"
    STRATEGIC_PLANNING = "strategic_planning"


class DecisionUrgency(Enum):
    """Urgency levels for decisions"""
    IMMEDIATE = "immediate"  # < 1 minute
    URGENT = "urgent"        # < 5 minutes
    HIGH = "high"            # < 30 minutes
    NORMAL = "normal"        # < 2 hours
    LOW = "low"              # < 24 hours


@dataclass
class DecisionContext:
    """Context information for decision making"""
    current_performance: Dict[str, float]
    recent_anomalies: List[AnomalyDetection]
    resource_utilization: Dict[str, float]
    active_emergencies: List[Dict[str, Any]]
    business_priorities: List[str]
    constraints: Dict[str, Any]
    timestamp: datetime


@dataclass
class DecisionRequest:
    """Request for a decision"""
    id: str
    decision_type: DecisionType
    urgency: DecisionUrgency
    context: DecisionContext
    data: Dict[str, Any]
    requesting_agent: str
    timestamp: datetime
    deadline: Optional[datetime] = None


@dataclass
class DecisionResult:
    """Result of a decision"""
    request_id: str
    decision_type: DecisionType
    decision: Dict[str, Any]
    reasoning: str
    confidence: float
    alternatives: List[Dict[str, Any]]
    execution_plan: List[Dict[str, Any]]
    estimated_impact: Dict[str, float]
    timestamp: datetime


class MultiCriteriaAnalyzer:
    """Multi-criteria decision analysis engine"""
    
    def __init__(self):
        # Decision criteria weights (can be adjusted based on context)
        self.default_criteria_weights = {
            "performance_impact": 0.25,
            "cost_efficiency": 0.20,
            "risk_level": 0.15,
            "implementation_effort": 0.15,
            "strategic_alignment": 0.15,
            "urgency": 0.10
        }
    
    def analyze_decision(self, 
                        alternatives: List[Dict[str, Any]],
                        criteria_weights: Optional[Dict[str, float]] = None,
                        context: Optional[DecisionContext] = None) -> Dict[str, Any]:
        """
        Perform multi-criteria analysis on decision alternatives
        
        Args:
            alternatives: List of decision alternatives with criteria scores
            criteria_weights: Custom weights for criteria (optional)
            context: Decision context for weight adjustment
            
        Returns:
            Analysis results with ranked alternatives
        """
        if not alternatives:
            return {"error": "No alternatives provided"}
        
        # Use custom weights or defaults
        weights = criteria_weights or self.default_criteria_weights
        
        # Adjust weights based on context
        if context:
            weights = self._adjust_weights_for_context(weights, context)
        
        # Calculate weighted scores for each alternative
        scored_alternatives = []
        
        for i, alternative in enumerate(alternatives):
            weighted_score = 0.0
            criteria_scores = {}
            
            for criterion, weight in weights.items():
                score = alternative.get(criterion, 0.5)  # Default to neutral score
                weighted_score += score * weight
                criteria_scores[criterion] = score
            
            scored_alternatives.append({
                "index": i,
                "alternative": alternative,
                "weighted_score": weighted_score,
                "criteria_scores": criteria_scores
            })
        
        # Sort by weighted score (highest first)
        scored_alternatives.sort(key=lambda x: x["weighted_score"], reverse=True)
        
        # Calculate confidence based on score separation
        if len(scored_alternatives) > 1:
            top_score = scored_alternatives[0]["weighted_score"]
            second_score = scored_alternatives[1]["weighted_score"]
            confidence = min(0.95, (top_score - second_score) * 2)
        else:
            confidence = 0.8
        
        return {
            "ranked_alternatives": scored_alternatives,
            "criteria_weights": weights,
            "confidence": confidence,
            "recommendation": scored_alternatives[0]["alternative"],
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _adjust_weights_for_context(self, 
                                  base_weights: Dict[str, float],
                                  context: DecisionContext) -> Dict[str, float]:
        """Adjust criteria weights based on decision context"""
        adjusted_weights = base_weights.copy()
        
        # Increase urgency weight if there are active emergencies
        if context.active_emergencies:
            adjusted_weights["urgency"] *= 1.5
            adjusted_weights["risk_level"] *= 1.3
        
        # Increase cost efficiency weight if resource utilization is high
        avg_utilization = sum(context.resource_utilization.values()) / len(context.resource_utilization)
        if avg_utilization > 0.8:
            adjusted_weights["cost_efficiency"] *= 1.4
        
        # Increase performance weight if recent performance is poor
        avg_performance = sum(context.current_performance.values()) / len(context.current_performance)
        if avg_performance < 0.7:
            adjusted_weights["performance_impact"] *= 1.3
        
        # Normalize weights to sum to 1.0
        total_weight = sum(adjusted_weights.values())
        adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}
        
        return adjusted_weights


class DecisionEngine:
    """
    Enhanced Decision Engine with ML-based intelligence
    
    Features:
    - Multi-criteria decision analysis
    - Integration with ML components (prioritization, anomaly detection, resource allocation)
    - Context-aware decision making
    - Confidence scoring and alternative analysis
    - Execution planning and impact estimation
    """
    
    def __init__(self, 
                 project_id: Optional[str] = None,
                 location: str = "us-central1",
                 openai_service: Optional[OpenAIService] = None):
        
        self.project_id = project_id or getattr(settings, 'google_cloud_project', 'default-project')
        
        # Initialize ML components
        self.prioritization_engine = PrioritizationEngine(project_id, location, openai_service)
        self.anomaly_detector = AnomalyDetector(project_id, location, openai_service)
        self.resource_allocator = ResourceAllocator(project_id, location, openai_service)
        
        # Decision analysis
        self.multi_criteria_analyzer = MultiCriteriaAnalyzer()
        self.openai_service = openai_service or OpenAIService()
        
        # Decision state
        self.pending_decisions: List[DecisionRequest] = []
        self.decision_history: List[DecisionResult] = []
        self.active_decisions: Dict[str, DecisionResult] = {}
        
        # Performance tracking
        self.decision_metrics = {
            "total_decisions": 0,
            "avg_confidence": 0.0,
            "avg_processing_time_ms": 0.0,
            "success_rate": 0.0
        }
        
        logger.info("Enhanced Decision Engine initialized with ML integration")
    
    async def request_decision(self, 
                             decision_type: DecisionType,
                             urgency: DecisionUrgency,
                             data: Dict[str, Any],
                             requesting_agent: str,
                             deadline: Optional[datetime] = None) -> str:
        """
        Request a decision from the engine
        
        Args:
            decision_type: Type of decision needed
            urgency: How urgent the decision is
            data: Decision-specific data
            requesting_agent: Agent requesting the decision
            deadline: When the decision is needed by
            
        Returns:
            Decision request ID
        """
        request_id = str(uuid.uuid4())
        
        # Gather current context
        context = await self._gather_decision_context()
        
        request = DecisionRequest(
            id=request_id,
            decision_type=decision_type,
            urgency=urgency,
            context=context,
            data=data,
            requesting_agent=requesting_agent,
            timestamp=datetime.now(),
            deadline=deadline
        )
        
        self.pending_decisions.append(request)
        
        logger.info(f"Decision request {request_id} created for {requesting_agent}")
        
        # Process immediately if urgent
        if urgency in [DecisionUrgency.IMMEDIATE, DecisionUrgency.URGENT]:
            await self._process_urgent_decision(request)
        
        return request_id
    
    async def _gather_decision_context(self) -> DecisionContext:
        """Gather current system context for decision making"""
        try:
            # Get current performance metrics
            current_performance = {
                "response_time": 0.8,  # This would come from monitoring
                "success_rate": 0.95,
                "user_satisfaction": 0.9
            }
            
            # Get recent anomalies
            recent_anomalies = self.anomaly_detector.detected_anomalies[-10:]
            
            # Get resource utilization
            allocation_status = self.resource_allocator.get_allocation_status()
            resource_utilization = allocation_status.get("resource_utilization", {})
            
            # Get active emergencies (would come from emergency manager)
            active_emergencies = []
            
            # Business priorities (would come from configuration)
            business_priorities = ["performance", "cost_efficiency", "user_experience"]
            
            # System constraints
            constraints = {
                "budget_limit": 1000.0,
                "performance_sla": 0.95,
                "max_downtime_minutes": 5
            }
            
            return DecisionContext(
                current_performance=current_performance,
                recent_anomalies=recent_anomalies,
                resource_utilization=resource_utilization,
                active_emergencies=active_emergencies,
                business_priorities=business_priorities,
                constraints=constraints,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error gathering decision context: {str(e)}")
            # Return minimal context
            return DecisionContext(
                current_performance={},
                recent_anomalies=[],
                resource_utilization={},
                active_emergencies=[],
                business_priorities=[],
                constraints={},
                timestamp=datetime.now()
            )
    
    async def _process_urgent_decision(self, request: DecisionRequest):
        """Process urgent decisions immediately"""
        try:
            result = await self.make_decision(request)
            if result:
                self.active_decisions[result.request_id] = result
                self.pending_decisions.remove(request)
                logger.info(f"Urgent decision {request.id} processed immediately")
        except Exception as e:
            logger.error(f"Error processing urgent decision: {str(e)}")
    
    async def make_decision(self, request: DecisionRequest) -> Optional[DecisionResult]:
        """
        Make a decision based on the request
        
        Args:
            request: Decision request
            
        Returns:
            Decision result
        """
        start_time = datetime.now()
        
        try:
            # Route to appropriate decision handler
            if request.decision_type == DecisionType.IMPROVEMENT_PRIORITIZATION:
                result = await self._handle_improvement_prioritization(request)
            elif request.decision_type == DecisionType.RESOURCE_ALLOCATION:
                result = await self._handle_resource_allocation(request)
            elif request.decision_type == DecisionType.EMERGENCY_RESPONSE:
                result = await self._handle_emergency_response(request)
            elif request.decision_type == DecisionType.CONFLICT_RESOLUTION:
                result = await self._handle_conflict_resolution(request)
            elif request.decision_type == DecisionType.STRATEGIC_PLANNING:
                result = await self._handle_strategic_planning(request)
            else:
                raise VoiceHiveError(f"Unknown decision type: {request.decision_type}")
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_decision_metrics(result, processing_time)
            
            # Store in history
            self.decision_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error making decision {request.id}: {str(e)}")
            return None
    
    async def _handle_improvement_prioritization(self, request: DecisionRequest) -> DecisionResult:
        """Handle improvement prioritization decisions"""
        candidates_data = request.data.get("candidates", [])
        
        # Convert to ImprovementCandidate objects
        candidates = []
        for candidate_data in candidates_data:
            candidate = ImprovementCandidate(
                id=candidate_data.get("id", str(uuid.uuid4())),
                title=candidate_data.get("title", "Unknown"),
                description=candidate_data.get("description", ""),
                category=candidate_data.get("category", "performance"),
                estimated_impact=candidate_data.get("estimated_impact", 0.5),
                estimated_effort=candidate_data.get("estimated_effort", 0.5),
                risk_level=candidate_data.get("risk_level", 0.3),
                performance_data=candidate_data.get("performance_data", {}),
                timestamp=datetime.now(),
                source_agent=request.requesting_agent
            )
            candidates.append(candidate)
        
        # Use prioritization engine
        prioritization_results = await self.prioritization_engine.prioritize_improvements(
            candidates, request.context.__dict__
        )
        
        # Generate execution plan
        execution_plan = []
        for i, result in enumerate(prioritization_results[:5]):  # Top 5
            execution_plan.append({
                "step": i + 1,
                "action": f"Implement {result.candidate.title}",
                "priority": result.final_priority.value,
                "timeline": result.recommended_timeline,
                "estimated_impact": result.candidate.estimated_impact
            })
        
        return DecisionResult(
            request_id=request.id,
            decision_type=request.decision_type,
            decision={
                "prioritized_improvements": [
                    {
                        "id": result.candidate.id,
                        "title": result.candidate.title,
                        "priority": result.final_priority.value,
                        "score": result.combined_score,
                        "timeline": result.recommended_timeline
                    }
                    for result in prioritization_results
                ]
            },
            reasoning=f"Prioritized {len(candidates)} improvements using hybrid ML approach",
            confidence=sum(r.confidence for r in prioritization_results) / len(prioritization_results),
            alternatives=[],
            execution_plan=execution_plan,
            estimated_impact={"performance_improvement": 0.15, "cost_reduction": 0.10},
            timestamp=datetime.now()
        )
    
    async def _handle_resource_allocation(self, request: DecisionRequest) -> DecisionResult:
        """Handle resource allocation decisions"""
        resource_requests = request.data.get("resource_requests", [])
        
        # Process resource requests
        allocation_results = []
        for req_data in resource_requests:
            request_id = await self.resource_allocator.request_resources(
                requesting_agent=req_data.get("agent", request.requesting_agent),
                resource_type=ResourceType(req_data.get("resource_type", "compute_instance")),
                amount=req_data.get("amount", 1.0),
                priority=req_data.get("priority", 3),
                duration_hours=req_data.get("duration_hours"),
                justification=req_data.get("justification", "")
            )
            allocation_results.append(request_id)
        
        # Optimize allocations
        optimization_result = await self.resource_allocator.optimize_allocations()
        
        return DecisionResult(
            request_id=request.id,
            decision_type=request.decision_type,
            decision={
                "allocation_requests": allocation_results,
                "optimization_result": optimization_result
            },
            reasoning="Processed resource allocation requests with optimization",
            confidence=0.85,
            alternatives=[],
            execution_plan=[
                {"step": 1, "action": "Allocate requested resources", "timeline": "immediate"},
                {"step": 2, "action": "Monitor resource utilization", "timeline": "ongoing"}
            ],
            estimated_impact={"cost_change": optimization_result.get("total_cost_per_hour", 0)},
            timestamp=datetime.now()
        )
    
    async def _handle_emergency_response(self, request: DecisionRequest) -> DecisionResult:
        """Handle emergency response decisions"""
        emergency_data = request.data.get("emergency", {})
        
        # Generate response alternatives using OpenAI
        response_prompt = f"""
        An emergency situation has occurred:
        
        Emergency Type: {emergency_data.get('type', 'Unknown')}
        Severity: {emergency_data.get('severity', 'Unknown')}
        Description: {emergency_data.get('description', 'No description')}
        
        Current System State:
        - Performance: {request.context.current_performance}
        - Resource Utilization: {request.context.resource_utilization}
        
        Provide 3 emergency response alternatives with scores (0.0-1.0) for:
        - performance_impact
        - cost_efficiency  
        - risk_level
        - implementation_effort
        - strategic_alignment
        - urgency
        
        Format as JSON array of alternatives.
        """
        
        try:
            response = await self.openai_service.generate_response(
                system_prompt="You are an expert emergency response coordinator.",
                conversation_history=[{"role": "user", "content": response_prompt}]
            )
            
            # Parse alternatives (simplified)
            alternatives = [
                {
                    "name": "Immediate Failover",
                    "performance_impact": 0.9,
                    "cost_efficiency": 0.6,
                    "risk_level": 0.3,
                    "implementation_effort": 0.8,
                    "strategic_alignment": 0.7,
                    "urgency": 1.0
                },
                {
                    "name": "Gradual Recovery",
                    "performance_impact": 0.7,
                    "cost_efficiency": 0.8,
                    "risk_level": 0.2,
                    "implementation_effort": 0.5,
                    "strategic_alignment": 0.8,
                    "urgency": 0.6
                },
                {
                    "name": "Full System Restart",
                    "performance_impact": 0.95,
                    "cost_efficiency": 0.4,
                    "risk_level": 0.7,
                    "implementation_effort": 0.9,
                    "strategic_alignment": 0.6,
                    "urgency": 0.8
                }
            ]
            
        except Exception as e:
            logger.error(f"Error generating emergency alternatives: {str(e)}")
            alternatives = [{"name": "Default Emergency Response", "performance_impact": 0.7}]
        
        # Analyze alternatives
        analysis = self.multi_criteria_analyzer.analyze_decision(
            alternatives, context=request.context
        )
        
        return DecisionResult(
            request_id=request.id,
            decision_type=request.decision_type,
            decision=analysis["recommendation"],
            reasoning=f"Selected emergency response based on multi-criteria analysis",
            confidence=analysis["confidence"],
            alternatives=alternatives,
            execution_plan=[
                {"step": 1, "action": "Execute emergency response", "timeline": "immediate"},
                {"step": 2, "action": "Monitor system recovery", "timeline": "ongoing"}
            ],
            estimated_impact={"downtime_minutes": 2, "recovery_time_minutes": 15},
            timestamp=datetime.now()
        )
    
    async def _handle_conflict_resolution(self, request: DecisionRequest) -> DecisionResult:
        """Handle conflict resolution decisions"""
        # Simplified conflict resolution
        conflicts = request.data.get("conflicts", [])
        
        resolution_strategies = [
            {
                "name": "Priority-based Resolution",
                "description": "Resolve based on agent priority levels",
                "performance_impact": 0.8,
                "cost_efficiency": 0.9,
                "risk_level": 0.2,
                "implementation_effort": 0.3,
                "strategic_alignment": 0.7,
                "urgency": 0.9
            },
            {
                "name": "Resource Sharing",
                "description": "Share resources between conflicting agents",
                "performance_impact": 0.6,
                "cost_efficiency": 0.8,
                "risk_level": 0.3,
                "implementation_effort": 0.6,
                "strategic_alignment": 0.8,
                "urgency": 0.7
            }
        ]
        
        analysis = self.multi_criteria_analyzer.analyze_decision(
            resolution_strategies, context=request.context
        )
        
        return DecisionResult(
            request_id=request.id,
            decision_type=request.decision_type,
            decision=analysis["recommendation"],
            reasoning="Resolved conflicts using multi-criteria analysis",
            confidence=analysis["confidence"],
            alternatives=resolution_strategies,
            execution_plan=[
                {"step": 1, "action": "Apply conflict resolution", "timeline": "immediate"}
            ],
            estimated_impact={"conflicts_resolved": len(conflicts)},
            timestamp=datetime.now()
        )
    
    async def _handle_strategic_planning(self, request: DecisionRequest) -> DecisionResult:
        """Handle strategic planning decisions"""
        # Simplified strategic planning
        planning_horizon = request.data.get("planning_horizon_days", 30)
        
        strategic_options = [
            {
                "name": "Performance Optimization Focus",
                "performance_impact": 0.9,
                "cost_efficiency": 0.6,
                "risk_level": 0.3,
                "implementation_effort": 0.7,
                "strategic_alignment": 0.9,
                "urgency": 0.5
            },
            {
                "name": "Cost Reduction Focus",
                "performance_impact": 0.6,
                "cost_efficiency": 0.9,
                "risk_level": 0.2,
                "implementation_effort": 0.5,
                "strategic_alignment": 0.7,
                "urgency": 0.4
            }
        ]
        
        analysis = self.multi_criteria_analyzer.analyze_decision(
            strategic_options, context=request.context
        )
        
        return DecisionResult(
            request_id=request.id,
            decision_type=request.decision_type,
            decision=analysis["recommendation"],
            reasoning=f"Strategic plan for {planning_horizon} days based on current context",
            confidence=analysis["confidence"],
            alternatives=strategic_options,
            execution_plan=[
                {"step": 1, "action": "Implement strategic plan", "timeline": f"{planning_horizon} days"}
            ],
            estimated_impact={"strategic_alignment": 0.8},
            timestamp=datetime.now()
        )
    
    def _update_decision_metrics(self, result: DecisionResult, processing_time_ms: float):
        """Update decision engine metrics"""
        self.decision_metrics["total_decisions"] += 1
        
        # Update average confidence
        total_confidence = (self.decision_metrics["avg_confidence"] * 
                          (self.decision_metrics["total_decisions"] - 1) + result.confidence)
        self.decision_metrics["avg_confidence"] = total_confidence / self.decision_metrics["total_decisions"]
        
        # Update average processing time
        total_time = (self.decision_metrics["avg_processing_time_ms"] * 
                     (self.decision_metrics["total_decisions"] - 1) + processing_time_ms)
        self.decision_metrics["avg_processing_time_ms"] = total_time / self.decision_metrics["total_decisions"]
    
    def get_decision_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a decision request"""
        # Check active decisions
        if request_id in self.active_decisions:
            result = self.active_decisions[request_id]
            return {
                "status": "completed",
                "decision": result.decision,
                "confidence": result.confidence,
                "timestamp": result.timestamp.isoformat()
            }
        
        # Check pending decisions
        for request in self.pending_decisions:
            if request.id == request_id:
                return {
                    "status": "pending",
                    "urgency": request.urgency.value,
                    "timestamp": request.timestamp.isoformat()
                }
        
        # Check history
        for result in self.decision_history:
            if result.request_id == request_id:
                return {
                    "status": "completed",
                    "decision": result.decision,
                    "confidence": result.confidence,
                    "timestamp": result.timestamp.isoformat()
                }
        
        return None
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get decision engine statistics"""
        return {
            "total_decisions": self.decision_metrics["total_decisions"],
            "pending_decisions": len(self.pending_decisions),
            "active_decisions": len(self.active_decisions),
            "avg_confidence": self.decision_metrics["avg_confidence"],
            "avg_processing_time_ms": self.decision_metrics["avg_processing_time_ms"],
            "ml_components": {
                "prioritization_engine": "available",
                "anomaly_detector": "available",
                "resource_allocator": "available"
            }
        }
