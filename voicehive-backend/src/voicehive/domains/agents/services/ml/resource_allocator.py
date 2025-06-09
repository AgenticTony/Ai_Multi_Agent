"""
Dynamic Resource Allocation - Intelligent scheduling and resource optimization
Implements adaptive resource management based on demand and performance
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json
import uuid

# Google Cloud imports
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from google.cloud import aiplatform
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Vertex AI not available - using heuristic allocation")

from voicehive.services.ai.openai_service import OpenAIService
from voicehive.utils.exceptions import VoiceHiveError, ErrorHandler
from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ResourceType(Enum):
    """Types of resources that can be allocated"""
    COMPUTE_INSTANCE = "compute_instance"
    AI_MODEL_CAPACITY = "ai_model_capacity"
    MEMORY_ALLOCATION = "memory_allocation"
    NETWORK_BANDWIDTH = "network_bandwidth"
    STORAGE_CAPACITY = "storage_capacity"
    AGENT_WORKERS = "agent_workers"


class AllocationStrategy(Enum):
    """Resource allocation strategies"""
    DEMAND_BASED = "demand_based"
    PREDICTIVE = "predictive"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    BALANCED = "balanced"


class ResourceStatus(Enum):
    """Status of allocated resources"""
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    OVERLOADED = "overloaded"
    SCALING = "scaling"
    FAILED = "failed"


@dataclass
class ResourceSpec:
    """Resource specification"""
    resource_type: ResourceType
    capacity: float
    unit: str
    cost_per_unit: float
    scaling_limits: Tuple[float, float]  # (min, max)
    scaling_step: float


@dataclass
class ResourceAllocation:
    """Resource allocation record"""
    id: str
    resource_type: ResourceType
    allocated_amount: float
    target_agent: str
    allocation_time: datetime
    expiry_time: Optional[datetime]
    status: ResourceStatus
    utilization: float = 0.0
    cost: float = 0.0
    metadata: Dict[str, Any] = None


@dataclass
class AllocationRequest:
    """Resource allocation request"""
    id: str
    requesting_agent: str
    resource_type: ResourceType
    requested_amount: float
    priority: int  # 1=highest, 5=lowest
    duration_hours: Optional[float]
    justification: str
    timestamp: datetime
    deadline: Optional[datetime] = None


@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    resource_type: ResourceType
    total_capacity: float
    allocated_amount: float
    utilization_percentage: float
    pending_requests: int
    cost_per_hour: float
    efficiency_score: float
    timestamp: datetime


class ResourceOptimizer:
    """Optimization engine for resource allocation"""
    
    def __init__(self):
        # Resource specifications
        self.resource_specs = self._initialize_resource_specs()
        
        # Current allocations
        self.active_allocations: Dict[str, ResourceAllocation] = {}
        self.allocation_history: List[ResourceAllocation] = []
        
        # Optimization parameters
        self.optimization_weights = {
            "cost": 0.3,
            "performance": 0.4,
            "utilization": 0.2,
            "fairness": 0.1
        }
    
    def _initialize_resource_specs(self) -> Dict[ResourceType, ResourceSpec]:
        """Initialize resource specifications"""
        return {
            ResourceType.COMPUTE_INSTANCE: ResourceSpec(
                resource_type=ResourceType.COMPUTE_INSTANCE,
                capacity=100.0,  # vCPUs
                unit="vCPU",
                cost_per_unit=0.05,  # $ per vCPU per hour
                scaling_limits=(1.0, 1000.0),
                scaling_step=2.0
            ),
            ResourceType.AI_MODEL_CAPACITY: ResourceSpec(
                resource_type=ResourceType.AI_MODEL_CAPACITY,
                capacity=1000.0,  # requests per minute
                unit="rpm",
                cost_per_unit=0.002,  # $ per request
                scaling_limits=(10.0, 10000.0),
                scaling_step=100.0
            ),
            ResourceType.MEMORY_ALLOCATION: ResourceSpec(
                resource_type=ResourceType.MEMORY_ALLOCATION,
                capacity=1000.0,  # GB
                unit="GB",
                cost_per_unit=0.01,  # $ per GB per hour
                scaling_limits=(1.0, 10000.0),
                scaling_step=4.0
            ),
            ResourceType.AGENT_WORKERS: ResourceSpec(
                resource_type=ResourceType.AGENT_WORKERS,
                capacity=50.0,  # worker instances
                unit="workers",
                cost_per_unit=0.10,  # $ per worker per hour
                scaling_limits=(1.0, 500.0),
                scaling_step=1.0
            )
        }
    
    def calculate_optimal_allocation(self, 
                                   requests: List[AllocationRequest],
                                   current_metrics: Dict[ResourceType, ResourceMetrics],
                                   strategy: AllocationStrategy = AllocationStrategy.BALANCED) -> List[ResourceAllocation]:
        """Calculate optimal resource allocation"""
        
        allocations = []
        
        # Sort requests by priority and deadline
        sorted_requests = sorted(requests, key=lambda r: (r.priority, r.deadline or datetime.max))
        
        for request in sorted_requests:
            allocation = self._allocate_for_request(request, current_metrics, strategy)
            if allocation:
                allocations.append(allocation)
        
        return allocations
    
    def _allocate_for_request(self, 
                            request: AllocationRequest,
                            current_metrics: Dict[ResourceType, ResourceMetrics],
                            strategy: AllocationStrategy) -> Optional[ResourceAllocation]:
        """Allocate resources for a specific request"""
        
        resource_spec = self.resource_specs.get(request.resource_type)
        if not resource_spec:
            return None
        
        current_metric = current_metrics.get(request.resource_type)
        if not current_metric:
            return None
        
        # Check if we have enough capacity
        available_capacity = current_metric.total_capacity - current_metric.allocated_amount
        
        if available_capacity < request.requested_amount:
            # Check if we can scale up
            max_capacity = resource_spec.scaling_limits[1]
            if current_metric.total_capacity < max_capacity:
                # Scale up
                scale_amount = min(
                    request.requested_amount - available_capacity,
                    max_capacity - current_metric.total_capacity
                )
                # This would trigger actual scaling in production
                logger.info(f"Scaling up {request.resource_type.value} by {scale_amount}")
                available_capacity += scale_amount
            else:
                logger.warning(f"Cannot fulfill request {request.id} - insufficient capacity")
                return None
        
        # Create allocation
        allocation_amount = min(request.requested_amount, available_capacity)
        expiry_time = None
        if request.duration_hours:
            expiry_time = request.timestamp + timedelta(hours=request.duration_hours)
        
        allocation = ResourceAllocation(
            id=str(uuid.uuid4()),
            resource_type=request.resource_type,
            allocated_amount=allocation_amount,
            target_agent=request.requesting_agent,
            allocation_time=datetime.now(),
            expiry_time=expiry_time,
            status=ResourceStatus.ALLOCATED,
            cost=allocation_amount * resource_spec.cost_per_unit,
            metadata={
                "request_id": request.id,
                "strategy": strategy.value,
                "priority": request.priority
            }
        )
        
        return allocation
    
    def optimize_existing_allocations(self, 
                                    allocations: List[ResourceAllocation],
                                    metrics: Dict[ResourceType, ResourceMetrics]) -> List[Dict[str, Any]]:
        """Optimize existing resource allocations"""
        optimizations = []
        
        for allocation in allocations:
            if allocation.status != ResourceStatus.ALLOCATED:
                continue
            
            # Check utilization
            if allocation.utilization < 0.3:  # Low utilization
                optimizations.append({
                    "type": "downscale",
                    "allocation_id": allocation.id,
                    "current_amount": allocation.allocated_amount,
                    "recommended_amount": allocation.allocated_amount * 0.7,
                    "reason": "Low utilization detected",
                    "potential_savings": allocation.cost * 0.3
                })
            elif allocation.utilization > 0.9:  # High utilization
                resource_spec = self.resource_specs[allocation.resource_type]
                max_scale = resource_spec.scaling_limits[1]
                
                if allocation.allocated_amount < max_scale:
                    optimizations.append({
                        "type": "upscale",
                        "allocation_id": allocation.id,
                        "current_amount": allocation.allocated_amount,
                        "recommended_amount": min(allocation.allocated_amount * 1.3, max_scale),
                        "reason": "High utilization detected",
                        "performance_impact": "Improved response times"
                    })
        
        return optimizations


class VertexAIOptimizer:
    """Vertex AI integration for advanced resource optimization"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.initialized = False
        
        if VERTEX_AI_AVAILABLE:
            try:
                vertexai.init(project=project_id, location=location)
                self.generative_model = GenerativeModel("gemini-2.0-flash")
                self.initialized = True
                logger.info("Vertex AI Optimizer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI Optimizer: {str(e)}")
                self.initialized = False
    
    async def optimize_allocation_strategy(self, 
                                         historical_data: Dict[str, Any],
                                         current_demand: Dict[str, Any],
                                         constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Use Vertex AI to optimize allocation strategy"""
        if not self.initialized:
            return {"strategy": "balanced", "reason": "Vertex AI not available"}
        
        try:
            prompt = f"""
            Analyze the following resource allocation scenario and recommend the optimal strategy:
            
            Historical Data: {json.dumps(historical_data, indent=2)}
            Current Demand: {json.dumps(current_demand, indent=2)}
            Constraints: {json.dumps(constraints, indent=2)}
            
            Available strategies:
            - demand_based: Allocate based on current demand
            - predictive: Allocate based on predicted future demand
            - cost_optimized: Minimize costs while meeting requirements
            - performance_optimized: Maximize performance regardless of cost
            - balanced: Balance cost and performance
            
            Provide recommendation with reasoning in JSON format:
            {{
                "recommended_strategy": "<strategy>",
                "confidence": <0.0-1.0>,
                "reasoning": "<explanation>",
                "expected_benefits": ["<benefit1>", "<benefit2>"],
                "potential_risks": ["<risk1>", "<risk2>"],
                "optimization_parameters": {{
                    "cost_weight": <0.0-1.0>,
                    "performance_weight": <0.0-1.0>,
                    "utilization_weight": <0.0-1.0>
                }}
            }}
            """
            
            response = await self._generate_content(prompt)
            return self._parse_optimization_response(response)
            
        except Exception as e:
            logger.error(f"Error in Vertex AI optimization: {str(e)}")
            return {"strategy": "balanced", "error": str(e)}
    
    async def _generate_content(self, prompt: str) -> str:
        """Generate content using Vertex AI"""
        try:
            response = self.generative_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return "Error in content generation"
    
    def _parse_optimization_response(self, response: str) -> Dict[str, Any]:
        """Parse Vertex AI optimization response"""
        try:
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"strategy": "balanced", "reasoning": response}
        except Exception as e:
            logger.error(f"Error parsing optimization response: {str(e)}")
            return {"strategy": "balanced", "error": "Failed to parse response"}


class ResourceAllocator:
    """
    Dynamic Resource Allocation System
    
    Features:
    - Intelligent resource scheduling based on demand
    - Predictive scaling using ML models
    - Cost optimization with performance constraints
    - Multi-criteria decision making
    - Real-time allocation adjustments
    """
    
    def __init__(self, 
                 project_id: Optional[str] = None,
                 location: str = "us-central1",
                 openai_service: Optional[OpenAIService] = None):
        
        self.project_id = project_id or getattr(settings, 'google_cloud_project', 'default-project')
        self.resource_optimizer = ResourceOptimizer()
        self.vertex_optimizer = VertexAIOptimizer(self.project_id, location)
        self.openai_service = openai_service or OpenAIService()
        
        # Allocation state
        self.pending_requests: List[AllocationRequest] = []
        self.active_allocations: Dict[str, ResourceAllocation] = {}
        self.allocation_history: List[ResourceAllocation] = []
        
        # Metrics tracking
        self.resource_metrics: Dict[ResourceType, ResourceMetrics] = {}
        self.last_optimization_time = datetime.now()
        
        # Configuration
        self.optimization_interval = timedelta(minutes=10)
        self.max_allocation_history = 10000
        
        logger.info("Resource Allocator initialized with intelligent scheduling")
    
    async def request_resources(self, 
                              requesting_agent: str,
                              resource_type: ResourceType,
                              amount: float,
                              priority: int = 3,
                              duration_hours: Optional[float] = None,
                              justification: str = "",
                              deadline: Optional[datetime] = None) -> str:
        """
        Request resource allocation
        
        Args:
            requesting_agent: ID of the requesting agent
            resource_type: Type of resource needed
            amount: Amount of resource requested
            priority: Priority level (1=highest, 5=lowest)
            duration_hours: How long the resource is needed
            justification: Reason for the request
            deadline: When the resource is needed by
            
        Returns:
            Request ID
        """
        request_id = str(uuid.uuid4())
        
        request = AllocationRequest(
            id=request_id,
            requesting_agent=requesting_agent,
            resource_type=resource_type,
            requested_amount=amount,
            priority=priority,
            duration_hours=duration_hours,
            justification=justification,
            timestamp=datetime.now(),
            deadline=deadline
        )
        
        self.pending_requests.append(request)
        
        logger.info(f"Resource request {request_id} created for {requesting_agent}")
        
        # Trigger immediate allocation for high-priority requests
        if priority <= 2:
            await self._process_high_priority_request(request)
        
        return request_id
    
    async def _process_high_priority_request(self, request: AllocationRequest):
        """Process high-priority requests immediately"""
        try:
            # Get current metrics
            current_metrics = await self._get_current_metrics()
            
            # Calculate allocation
            allocation = self.resource_optimizer._allocate_for_request(
                request, current_metrics, AllocationStrategy.PERFORMANCE_OPTIMIZED
            )
            
            if allocation:
                self.active_allocations[allocation.id] = allocation
                self.pending_requests.remove(request)
                
                logger.info(f"High-priority allocation {allocation.id} processed immediately")
            else:
                logger.warning(f"Could not fulfill high-priority request {request.id}")
                
        except Exception as e:
            logger.error(f"Error processing high-priority request: {str(e)}")
    
    async def optimize_allocations(self, strategy: Optional[AllocationStrategy] = None) -> Dict[str, Any]:
        """
        Optimize current resource allocations
        
        Args:
            strategy: Allocation strategy to use
            
        Returns:
            Optimization results
        """
        try:
            # Get current metrics
            current_metrics = await self._get_current_metrics()
            
            # Determine optimal strategy if not provided
            if not strategy:
                strategy = await self._determine_optimal_strategy(current_metrics)
            
            # Process pending requests
            new_allocations = self.resource_optimizer.calculate_optimal_allocation(
                self.pending_requests, current_metrics, strategy
            )
            
            # Apply new allocations
            allocated_requests = []
            for allocation in new_allocations:
                self.active_allocations[allocation.id] = allocation
                
                # Find and remove corresponding request
                for request in self.pending_requests:
                    if request.id == allocation.metadata.get("request_id"):
                        allocated_requests.append(request)
                        break
            
            # Remove allocated requests from pending
            for request in allocated_requests:
                self.pending_requests.remove(request)
            
            # Optimize existing allocations
            optimizations = self.resource_optimizer.optimize_existing_allocations(
                list(self.active_allocations.values()), current_metrics
            )
            
            # Apply optimizations
            applied_optimizations = await self._apply_optimizations(optimizations)
            
            self.last_optimization_time = datetime.now()
            
            return {
                "strategy_used": strategy.value,
                "new_allocations": len(new_allocations),
                "pending_requests": len(self.pending_requests),
                "active_allocations": len(self.active_allocations),
                "optimizations_applied": len(applied_optimizations),
                "total_cost_per_hour": sum(alloc.cost for alloc in self.active_allocations.values()),
                "optimization_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in allocation optimization: {str(e)}")
            return {"error": str(e)}
    
    async def _determine_optimal_strategy(self, 
                                        current_metrics: Dict[ResourceType, ResourceMetrics]) -> AllocationStrategy:
        """Determine optimal allocation strategy using AI"""
        try:
            # Prepare data for AI analysis
            historical_data = {
                "allocation_history_size": len(self.allocation_history),
                "average_utilization": self._calculate_average_utilization(current_metrics),
                "cost_trend": "stable"  # This would be calculated from history
            }
            
            current_demand = {
                "pending_requests": len(self.pending_requests),
                "high_priority_requests": len([r for r in self.pending_requests if r.priority <= 2]),
                "resource_pressure": self._calculate_resource_pressure(current_metrics)
            }
            
            constraints = {
                "budget_limit": 1000.0,  # $ per hour
                "performance_sla": 0.95,  # 95% availability
                "max_scaling_factor": 2.0
            }
            
            # Use Vertex AI for strategy optimization
            optimization_result = await self.vertex_optimizer.optimize_allocation_strategy(
                historical_data, current_demand, constraints
            )
            
            strategy_name = optimization_result.get("recommended_strategy", "balanced")
            
            try:
                return AllocationStrategy(strategy_name)
            except ValueError:
                return AllocationStrategy.BALANCED
                
        except Exception as e:
            logger.error(f"Error determining optimal strategy: {str(e)}")
            return AllocationStrategy.BALANCED
    
    async def _get_current_metrics(self) -> Dict[ResourceType, ResourceMetrics]:
        """Get current resource metrics"""
        metrics = {}
        
        for resource_type, spec in self.resource_optimizer.resource_specs.items():
            # Calculate current allocation
            allocated_amount = sum(
                alloc.allocated_amount for alloc in self.active_allocations.values()
                if alloc.resource_type == resource_type and alloc.status == ResourceStatus.ALLOCATED
            )
            
            # Calculate utilization
            utilization = (allocated_amount / spec.capacity) * 100 if spec.capacity > 0 else 0
            
            # Calculate efficiency (simplified)
            efficiency = min(100, utilization * 1.2) if utilization > 0 else 100
            
            metrics[resource_type] = ResourceMetrics(
                resource_type=resource_type,
                total_capacity=spec.capacity,
                allocated_amount=allocated_amount,
                utilization_percentage=utilization,
                pending_requests=len([r for r in self.pending_requests if r.resource_type == resource_type]),
                cost_per_hour=allocated_amount * spec.cost_per_unit,
                efficiency_score=efficiency,
                timestamp=datetime.now()
            )
        
        self.resource_metrics = metrics
        return metrics
    
    def _calculate_average_utilization(self, metrics: Dict[ResourceType, ResourceMetrics]) -> float:
        """Calculate average utilization across all resources"""
        if not metrics:
            return 0.0
        
        total_utilization = sum(metric.utilization_percentage for metric in metrics.values())
        return total_utilization / len(metrics)
    
    def _calculate_resource_pressure(self, metrics: Dict[ResourceType, ResourceMetrics]) -> float:
        """Calculate overall resource pressure"""
        if not metrics:
            return 0.0
        
        pressure_scores = []
        for metric in metrics.values():
            # Higher utilization and more pending requests = higher pressure
            pressure = (metric.utilization_percentage / 100) + (metric.pending_requests * 0.1)
            pressure_scores.append(min(1.0, pressure))
        
        return sum(pressure_scores) / len(pressure_scores)
    
    async def _apply_optimizations(self, optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply optimization recommendations"""
        applied = []
        
        for optimization in optimizations:
            try:
                allocation_id = optimization["allocation_id"]
                if allocation_id in self.active_allocations:
                    allocation = self.active_allocations[allocation_id]
                    
                    if optimization["type"] == "downscale":
                        allocation.allocated_amount = optimization["recommended_amount"]
                        allocation.status = ResourceStatus.SCALING
                        applied.append(optimization)
                        
                    elif optimization["type"] == "upscale":
                        allocation.allocated_amount = optimization["recommended_amount"]
                        allocation.status = ResourceStatus.SCALING
                        applied.append(optimization)
                
            except Exception as e:
                logger.error(f"Error applying optimization: {str(e)}")
        
        return applied
    
    def get_allocation_status(self, allocation_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of allocations"""
        if allocation_id:
            allocation = self.active_allocations.get(allocation_id)
            if allocation:
                return {
                    "allocation_id": allocation_id,
                    "resource_type": allocation.resource_type.value,
                    "allocated_amount": allocation.allocated_amount,
                    "target_agent": allocation.target_agent,
                    "status": allocation.status.value,
                    "utilization": allocation.utilization,
                    "cost": allocation.cost
                }
            else:
                return {"error": "Allocation not found"}
        
        # Return summary of all allocations
        return {
            "active_allocations": len(self.active_allocations),
            "pending_requests": len(self.pending_requests),
            "total_cost_per_hour": sum(alloc.cost for alloc in self.active_allocations.values()),
            "resource_utilization": {
                rt.value: metrics.utilization_percentage 
                for rt, metrics in self.resource_metrics.items()
            },
            "last_optimization": self.last_optimization_time.isoformat()
        }
    
    def get_allocation_statistics(self) -> Dict[str, Any]:
        """Get allocation statistics"""
        return {
            "total_allocations": len(self.allocation_history) + len(self.active_allocations),
            "active_allocations": len(self.active_allocations),
            "pending_requests": len(self.pending_requests),
            "vertex_ai_available": self.vertex_optimizer.initialized,
            "resource_types_managed": len(self.resource_optimizer.resource_specs),
            "last_optimization": self.last_optimization_time.isoformat()
        }
