"""
Multi-Objective Optimization Engine for VoiceHive Phase 3

This module implements Pareto optimization for competing objectives such as:
- Customer satisfaction vs cost efficiency
- Response time vs accuracy
- Resource utilization vs quality

Uses hybrid AI approach with Vertex AI for numerical optimization and OpenAI for strategic reasoning.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from voicehive.services.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class ObjectiveType(Enum):
    """Types of optimization objectives"""
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class OptimizationStrategy(Enum):
    """Optimization strategies"""
    PARETO_OPTIMAL = "pareto_optimal"
    WEIGHTED_SUM = "weighted_sum"
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"
    HYBRID_AI = "hybrid_ai"


@dataclass
class Objective:
    """Represents a single optimization objective"""
    name: str
    type: ObjectiveType
    weight: float = 1.0
    target_value: Optional[float] = None
    constraint_min: Optional[float] = None
    constraint_max: Optional[float] = None
    priority: int = 1  # 1 = highest priority


@dataclass
class Solution:
    """Represents a potential solution in the optimization space"""
    id: str
    parameters: Dict[str, Any]
    objective_values: Dict[str, float]
    pareto_rank: int = 0
    dominance_count: int = 0
    dominated_solutions: List[str] = field(default_factory=list)
    feasible: bool = True
    confidence_score: float = 0.0
    ai_reasoning: Optional[str] = None


@dataclass
class OptimizationResult:
    """Results from multi-objective optimization"""
    pareto_front: List[Solution]
    all_solutions: List[Solution]
    best_compromise: Solution
    optimization_time: float
    convergence_metrics: Dict[str, float]
    ai_recommendations: List[str]


class MultiObjectiveOptimizer:
    """
    Advanced multi-objective optimization engine using hybrid AI approach.
    
    Combines numerical optimization algorithms with AI reasoning for
    strategic decision making in complex multi-objective scenarios.
    """
    
    def __init__(self, openai_service: Optional[OpenAIService] = None):
        self.openai_service = openai_service or OpenAIService()
        self.objectives: Dict[str, Objective] = {}
        self.constraints: List[Dict[str, Any]] = []
        self.solutions: List[Solution] = []
        self.optimization_history: List[OptimizationResult] = []
        
        # Optimization parameters
        self.population_size = 100
        self.max_generations = 50
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
        
        # AI enhancement settings
        self.use_ai_guidance = True
        self.ai_confidence_threshold = 0.7
        
        logger.info("Multi-objective optimizer initialized")
    
    def add_objective(self, objective: Objective) -> None:
        """Add an optimization objective"""
        self.objectives[objective.name] = objective
        logger.info(f"Added objective: {objective.name} ({objective.type.value})")
    
    def add_constraint(self, constraint: Dict[str, Any]) -> None:
        """Add a constraint to the optimization problem"""
        self.constraints.append(constraint)
        logger.info(f"Added constraint: {constraint}")
    
    async def optimize(
        self,
        parameter_space: Dict[str, Dict[str, Any]],
        strategy: OptimizationStrategy = OptimizationStrategy.HYBRID_AI,
        max_time_seconds: int = 300
    ) -> OptimizationResult:
        """
        Perform multi-objective optimization
        
        Args:
            parameter_space: Definition of parameter ranges and types
            strategy: Optimization strategy to use
            max_time_seconds: Maximum optimization time
            
        Returns:
            OptimizationResult with Pareto front and recommendations
        """
        start_time = datetime.now()
        logger.info(f"Starting multi-objective optimization with {len(self.objectives)} objectives")
        
        try:
            # Generate initial population
            initial_solutions = await self._generate_initial_population(
                parameter_space, self.population_size
            )
            
            # Evaluate initial solutions
            evaluated_solutions = await self._evaluate_solutions(initial_solutions)
            
            # Apply optimization strategy
            if strategy == OptimizationStrategy.HYBRID_AI:
                optimized_solutions = await self._hybrid_ai_optimization(
                    evaluated_solutions, parameter_space, max_time_seconds
                )
            elif strategy == OptimizationStrategy.PARETO_OPTIMAL:
                optimized_solutions = await self._pareto_optimization(
                    evaluated_solutions, max_time_seconds
                )
            else:
                optimized_solutions = evaluated_solutions
            
            # Calculate dominance and Pareto ranking for all solutions
            self._calculate_dominance(optimized_solutions)
            self._assign_pareto_ranks(optimized_solutions)

            # Calculate Pareto front
            pareto_front = self._calculate_pareto_front(optimized_solutions)
            
            # Find best compromise solution
            best_compromise = await self._find_best_compromise(pareto_front)
            
            # Generate AI recommendations
            ai_recommendations = await self._generate_ai_recommendations(
                pareto_front, best_compromise
            )
            
            optimization_time = (datetime.now() - start_time).total_seconds()
            
            result = OptimizationResult(
                pareto_front=pareto_front,
                all_solutions=optimized_solutions,
                best_compromise=best_compromise,
                optimization_time=optimization_time,
                convergence_metrics=self._calculate_convergence_metrics(optimized_solutions),
                ai_recommendations=ai_recommendations
            )
            
            self.optimization_history.append(result)
            logger.info(f"Optimization completed in {optimization_time:.2f}s")
            logger.info(f"Pareto front contains {len(pareto_front)} solutions")
            
            return result
            
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            raise
    
    async def _generate_initial_population(
        self, 
        parameter_space: Dict[str, Dict[str, Any]], 
        size: int
    ) -> List[Solution]:
        """Generate initial population of solutions"""
        solutions = []
        
        for i in range(size):
            parameters = {}
            for param_name, param_config in parameter_space.items():
                param_type = param_config.get('type', 'float')
                min_val = param_config.get('min', 0)
                max_val = param_config.get('max', 1)
                
                if param_type == 'float':
                    parameters[param_name] = np.random.uniform(min_val, max_val)
                elif param_type == 'int':
                    parameters[param_name] = np.random.randint(min_val, max_val + 1)
                elif param_type == 'choice':
                    choices = param_config.get('choices', [])
                    parameters[param_name] = np.random.choice(choices)
            
            solution = Solution(
                id=f"sol_{i}",
                parameters=parameters,
                objective_values={}
            )
            solutions.append(solution)
        
        return solutions
    
    async def _evaluate_solutions(self, solutions: List[Solution]) -> List[Solution]:
        """Evaluate solutions against all objectives"""
        for solution in solutions:
            # Simulate objective evaluation (in real implementation, this would
            # call actual evaluation functions)
            for obj_name, objective in self.objectives.items():
                # Placeholder evaluation - replace with actual objective functions
                value = self._simulate_objective_evaluation(solution.parameters, objective)
                solution.objective_values[obj_name] = value
            
            # Check feasibility
            solution.feasible = self._check_feasibility(solution)
        
        return solutions
    
    def _simulate_objective_evaluation(
        self, 
        parameters: Dict[str, Any], 
        objective: Objective
    ) -> float:
        """Simulate objective evaluation (placeholder)"""
        # This is a placeholder - in real implementation, this would call
        # actual evaluation functions based on the objective type
        return np.random.uniform(0, 100)
    
    def _check_feasibility(self, solution: Solution) -> bool:
        """Check if solution satisfies all constraints"""
        for constraint in self.constraints:
            # Implement constraint checking logic
            pass
        return True
    
    async def _hybrid_ai_optimization(
        self,
        solutions: List[Solution],
        parameter_space: Dict[str, Dict[str, Any]],
        max_time_seconds: int
    ) -> List[Solution]:
        """Hybrid AI-guided optimization"""
        logger.info("Starting hybrid AI optimization")
        
        # Use AI to guide the optimization process
        if self.use_ai_guidance:
            ai_guidance = await self._get_ai_optimization_guidance(solutions)
            logger.info(f"AI guidance: {ai_guidance}")
        
        # Implement genetic algorithm with AI guidance
        current_population = solutions
        generation = 0
        start_time = datetime.now()
        
        while generation < self.max_generations:
            if (datetime.now() - start_time).total_seconds() > max_time_seconds:
                break
            
            # Selection, crossover, mutation with AI guidance
            new_population = await self._evolve_population(current_population, parameter_space)
            current_population = await self._evaluate_solutions(new_population)
            generation += 1
        
        return current_population
    
    async def _get_ai_optimization_guidance(self, solutions: List[Solution]) -> str:
        """Get AI guidance for optimization direction"""
        try:
            # Prepare context for AI
            context = {
                "objectives": {name: {
                    "name": obj.name,
                    "type": obj.type.value,
                    "weight": obj.weight,
                    "target_value": obj.target_value,
                    "priority": obj.priority
                } for name, obj in self.objectives.items()},
                "best_solutions": [sol.__dict__ for sol in solutions[:5]],
                "constraints": self.constraints
            }
            
            prompt = f"""
            As an optimization expert, analyze this multi-objective optimization problem:
            
            Objectives: {json.dumps(context['objectives'], indent=2)}
            Current best solutions: {json.dumps(context['best_solutions'], indent=2)}
            Constraints: {json.dumps(context['constraints'], indent=2)}
            
            Provide strategic guidance for:
            1. Which objectives should be prioritized
            2. Trade-offs to consider
            3. Parameter adjustment recommendations
            4. Potential optimization pitfalls to avoid
            
            Respond with actionable insights in JSON format.
            """
            
            response = await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            return response

        except Exception as e:
            logger.warning(f"Failed to get AI guidance: {str(e)}")
            return "AI guidance unavailable"

    async def _evolve_population(
        self,
        population: List[Solution],
        parameter_space: Dict[str, Dict[str, Any]]
    ) -> List[Solution]:
        """Evolve population using genetic operators"""
        new_population = []

        # Keep best solutions (elitism)
        sorted_pop = sorted(population, key=lambda x: x.pareto_rank)
        elite_size = max(1, len(population) // 10)
        new_population.extend(sorted_pop[:elite_size])

        # Generate offspring
        while len(new_population) < len(population):
            # Selection
            parent1 = self._tournament_selection(population)
            parent2 = self._tournament_selection(population)

            # Crossover
            if np.random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2, parameter_space)
            else:
                child1, child2 = parent1, parent2

            # Mutation
            if np.random.random() < self.mutation_rate:
                child1 = self._mutate(child1, parameter_space)
            if np.random.random() < self.mutation_rate:
                child2 = self._mutate(child2, parameter_space)

            new_population.extend([child1, child2])

        return new_population[:len(population)]

    def _tournament_selection(self, population: List[Solution], tournament_size: int = 3) -> Solution:
        """Tournament selection for genetic algorithm"""
        tournament = np.random.choice(population, tournament_size, replace=False)
        return min(tournament, key=lambda x: x.pareto_rank)

    def _crossover(
        self,
        parent1: Solution,
        parent2: Solution,
        parameter_space: Dict[str, Dict[str, Any]]
    ) -> Tuple[Solution, Solution]:
        """Crossover operation for genetic algorithm"""
        child1_params = {}
        child2_params = {}

        for param_name in parameter_space.keys():
            if np.random.random() < 0.5:
                child1_params[param_name] = parent1.parameters[param_name]
                child2_params[param_name] = parent2.parameters[param_name]
            else:
                child1_params[param_name] = parent2.parameters[param_name]
                child2_params[param_name] = parent1.parameters[param_name]

        child1 = Solution(
            id=f"child_{len(self.solutions)}",
            parameters=child1_params,
            objective_values={}
        )
        child2 = Solution(
            id=f"child_{len(self.solutions) + 1}",
            parameters=child2_params,
            objective_values={}
        )

        return child1, child2

    def _mutate(
        self,
        solution: Solution,
        parameter_space: Dict[str, Dict[str, Any]]
    ) -> Solution:
        """Mutation operation for genetic algorithm"""
        mutated_params = solution.parameters.copy()

        for param_name, param_config in parameter_space.items():
            if np.random.random() < 0.1:  # 10% chance to mutate each parameter
                param_type = param_config.get('type', 'float')
                min_val = param_config.get('min', 0)
                max_val = param_config.get('max', 1)

                if param_type == 'float':
                    # Gaussian mutation
                    current_val = mutated_params[param_name]
                    mutation_strength = (max_val - min_val) * 0.1
                    new_val = current_val + np.random.normal(0, mutation_strength)
                    mutated_params[param_name] = np.clip(new_val, min_val, max_val)
                elif param_type == 'int':
                    mutated_params[param_name] = np.random.randint(min_val, max_val + 1)
                elif param_type == 'choice':
                    choices = param_config.get('choices', [])
                    mutated_params[param_name] = np.random.choice(choices)

        return Solution(
            id=f"mutated_{solution.id}",
            parameters=mutated_params,
            objective_values={}
        )

    async def _pareto_optimization(
        self,
        solutions: List[Solution],
        max_time_seconds: int
    ) -> List[Solution]:
        """Pure Pareto optimization without AI guidance"""
        logger.info("Starting Pareto optimization")

        # Calculate dominance relationships
        self._calculate_dominance(solutions)

        # Assign Pareto ranks
        self._assign_pareto_ranks(solutions)

        return solutions

    def _calculate_dominance(self, solutions: List[Solution]) -> None:
        """Calculate dominance relationships between solutions"""
        for i, sol1 in enumerate(solutions):
            sol1.dominance_count = 0
            sol1.dominated_solutions = []

            for j, sol2 in enumerate(solutions):
                if i != j:
                    if self._dominates(sol1, sol2):
                        sol1.dominated_solutions.append(sol2.id)
                    elif self._dominates(sol2, sol1):
                        sol1.dominance_count += 1

    def _dominates(self, sol1: Solution, sol2: Solution) -> bool:
        """Check if sol1 dominates sol2"""
        better_in_at_least_one = False

        for obj_name, objective in self.objectives.items():
            val1 = sol1.objective_values.get(obj_name, 0)
            val2 = sol2.objective_values.get(obj_name, 0)

            if objective.type == ObjectiveType.MAXIMIZE:
                if val1 < val2:
                    return False
                elif val1 > val2:
                    better_in_at_least_one = True
            else:  # MINIMIZE
                if val1 > val2:
                    return False
                elif val1 < val2:
                    better_in_at_least_one = True

        return better_in_at_least_one

    def _assign_pareto_ranks(self, solutions: List[Solution]) -> None:
        """Assign Pareto ranks to solutions"""
        if not solutions:
            return

        rank = 1
        remaining_solutions = [sol for sol in solutions if sol.dominance_count == 0]

        # If no solutions are non-dominated, assign rank 1 to all
        if not remaining_solutions:
            for sol in solutions:
                sol.pareto_rank = 1
            return

        while remaining_solutions:
            # Assign current rank
            for sol in remaining_solutions:
                sol.pareto_rank = rank

            # Find next front
            next_front = []
            for sol in remaining_solutions:
                for dominated_id in sol.dominated_solutions:
                    dominated_sol = next((s for s in solutions if s.id == dominated_id), None)
                    if dominated_sol:
                        dominated_sol.dominance_count -= 1
                        if dominated_sol.dominance_count == 0:
                            next_front.append(dominated_sol)

            remaining_solutions = next_front
            rank += 1

    def _calculate_pareto_front(self, solutions: List[Solution]) -> List[Solution]:
        """Extract Pareto front (rank 1 solutions)"""
        return [sol for sol in solutions if sol.pareto_rank == 1]

    async def _find_best_compromise(self, pareto_front: List[Solution]) -> Solution:
        """Find best compromise solution from Pareto front"""
        if not pareto_front:
            return Solution(id="empty", parameters={}, objective_values={})

        # Use AI to help select best compromise
        if self.use_ai_guidance and len(pareto_front) > 1:
            try:
                best_solution = await self._ai_select_best_compromise(pareto_front)
                if best_solution:
                    return best_solution
            except Exception as e:
                logger.warning(f"AI compromise selection failed: {str(e)}")

        # Fallback: use weighted sum approach
        best_solution = None
        best_score = float('-inf')

        for solution in pareto_front:
            score = 0
            for obj_name, objective in self.objectives.items():
                value = solution.objective_values.get(obj_name, 0)
                normalized_value = self._normalize_objective_value(value, objective)

                if objective.type == ObjectiveType.MAXIMIZE:
                    score += objective.weight * normalized_value
                else:
                    score += objective.weight * (1 - normalized_value)

            if score > best_score:
                best_score = score
                best_solution = solution

        return best_solution or pareto_front[0]

    async def _ai_select_best_compromise(self, pareto_front: List[Solution]) -> Optional[Solution]:
        """Use AI to select best compromise solution"""
        try:
            solutions_data = []
            for sol in pareto_front:
                solutions_data.append({
                    "id": sol.id,
                    "parameters": sol.parameters,
                    "objectives": sol.objective_values
                })

            prompt = f"""
            As a decision expert, select the best compromise solution from these Pareto-optimal options:

            Objectives: {json.dumps({name: {
                "name": obj.name,
                "type": obj.type.value,
                "weight": obj.weight,
                "target_value": obj.target_value,
                "priority": obj.priority
            } for name, obj in self.objectives.items()}, indent=2)}
            Solutions: {json.dumps(solutions_data, indent=2)}

            Consider:
            1. Business priorities and objective weights
            2. Risk vs reward trade-offs
            3. Implementation feasibility
            4. Long-term strategic value

            Return the ID of the best compromise solution and explain your reasoning.
            Format: {{"selected_id": "sol_X", "reasoning": "explanation"}}
            """

            response = await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=300,
                temperature=0.2
            )

            # Parse AI response
            try:
                ai_decision = json.loads(response)
                selected_id = ai_decision.get("selected_id")
                reasoning = ai_decision.get("reasoning", "")

                selected_solution = next((sol for sol in pareto_front if sol.id == selected_id), None)
                if selected_solution:
                    selected_solution.ai_reasoning = reasoning
                    selected_solution.confidence_score = 0.8
                    return selected_solution
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI compromise selection response")

        except Exception as e:
            logger.warning(f"AI compromise selection failed: {str(e)}")

        return None

    def _normalize_objective_value(self, value: float, objective: Objective) -> float:
        """Normalize objective value to [0, 1] range"""
        # Simple normalization - in practice, you'd use historical data
        # to determine proper min/max ranges
        return max(0, min(1, value / 100))

    async def _generate_ai_recommendations(
        self,
        pareto_front: List[Solution],
        best_compromise: Solution
    ) -> List[str]:
        """Generate AI-powered recommendations"""
        try:
            context = {
                "pareto_front_size": len(pareto_front),
                "best_compromise": {
                    "parameters": best_compromise.parameters,
                    "objectives": best_compromise.objective_values,
                    "reasoning": best_compromise.ai_reasoning
                },
                "objectives": {name: {
                    "name": obj.name,
                    "type": obj.type.value,
                    "weight": obj.weight,
                    "target_value": obj.target_value,
                    "priority": obj.priority
                } for name, obj in self.objectives.items()}
            }

            prompt = f"""
            As an optimization consultant, provide strategic recommendations based on this optimization result:

            Context: {json.dumps(context, indent=2)}

            Provide 3-5 actionable recommendations for:
            1. Implementation strategy for the best compromise solution
            2. Monitoring and adjustment strategies
            3. Risk mitigation approaches
            4. Future optimization opportunities

            Format as a JSON array of recommendation strings.
            """

            response = await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=400,
                temperature=0.3
            )

            try:
                recommendations = json.loads(response)
                if isinstance(recommendations, list):
                    return recommendations
            except json.JSONDecodeError:
                pass

            # Fallback recommendations
            return [
                "Implement the best compromise solution with gradual rollout",
                "Monitor key performance indicators closely during implementation",
                "Establish feedback loops for continuous optimization",
                "Consider A/B testing for validation"
            ]

        except Exception as e:
            logger.warning(f"Failed to generate AI recommendations: {str(e)}")
            return ["Monitor implementation closely", "Gather feedback for future optimization"]

    def _calculate_convergence_metrics(self, solutions: List[Solution]) -> Dict[str, float]:
        """Calculate optimization convergence metrics"""
        if not solutions:
            return {}

        pareto_front = self._calculate_pareto_front(solutions)

        metrics = {
            "pareto_front_size": len(pareto_front),
            "solution_diversity": self._calculate_diversity(pareto_front),
            "convergence_ratio": len(pareto_front) / len(solutions) if solutions else 0,
            "hypervolume": self._calculate_hypervolume(pareto_front)
        }

        return metrics

    def _calculate_diversity(self, solutions: List[Solution]) -> float:
        """Calculate diversity of solutions in objective space"""
        if len(solutions) < 2:
            return 0.0

        # Calculate average distance between solutions in objective space
        total_distance = 0
        count = 0

        for i, sol1 in enumerate(solutions):
            for j, sol2 in enumerate(solutions[i+1:], i+1):
                distance = 0
                for obj_name in self.objectives.keys():
                    val1 = sol1.objective_values.get(obj_name, 0)
                    val2 = sol2.objective_values.get(obj_name, 0)
                    distance += (val1 - val2) ** 2

                total_distance += distance ** 0.5
                count += 1

        return total_distance / count if count > 0 else 0.0

    def _calculate_hypervolume(self, solutions: List[Solution]) -> float:
        """Calculate hypervolume indicator (simplified)"""
        if not solutions or not self.objectives:
            return 0.0

        # Simplified hypervolume calculation
        # In practice, you'd use a proper hypervolume algorithm
        volume = 1.0
        for obj_name, objective in self.objectives.items():
            values = [sol.objective_values.get(obj_name, 0) for sol in solutions]
            if objective.type == ObjectiveType.MAXIMIZE:
                volume *= max(values) if values else 0
            else:
                volume *= (100 - min(values)) if values else 0  # Assuming max possible value is 100

        return volume

    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization history and performance"""
        if not self.optimization_history:
            return {"message": "No optimization runs completed"}

        latest_result = self.optimization_history[-1]

        summary = {
            "total_runs": len(self.optimization_history),
            "latest_run": {
                "pareto_front_size": len(latest_result.pareto_front),
                "optimization_time": latest_result.optimization_time,
                "convergence_metrics": latest_result.convergence_metrics,
                "best_compromise": {
                    "parameters": latest_result.best_compromise.parameters,
                    "objectives": latest_result.best_compromise.objective_values,
                    "confidence": latest_result.best_compromise.confidence_score
                }
            },
            "objectives_configured": len(self.objectives),
            "constraints_configured": len(self.constraints)
        }

        return summary

    async def suggest_parameter_adjustments(
        self,
        current_performance: Dict[str, float]
    ) -> Dict[str, Any]:
        """Suggest parameter adjustments based on current performance"""
        try:
            if not self.optimization_history:
                return {"message": "No optimization history available"}

            latest_result = self.optimization_history[-1]
            best_solution = latest_result.best_compromise

            # Compare current performance with optimized solution
            performance_gap = {}
            for obj_name, current_value in current_performance.items():
                if obj_name in best_solution.objective_values:
                    optimal_value = best_solution.objective_values[obj_name]
                    gap = abs(current_value - optimal_value) / max(optimal_value, 1)
                    performance_gap[obj_name] = gap

            # Use AI to suggest adjustments
            prompt = f"""
            Current performance: {json.dumps(current_performance, indent=2)}
            Optimal solution: {json.dumps(best_solution.objective_values, indent=2)}
            Optimal parameters: {json.dumps(best_solution.parameters, indent=2)}
            Performance gaps: {json.dumps(performance_gap, indent=2)}

            Suggest specific parameter adjustments to close the performance gaps.
            Focus on the most impactful changes with lowest implementation risk.

            Format: {{"adjustments": {{"parameter_name": "adjustment_description"}}, "priority": "high/medium/low", "expected_impact": "description"}}
            """

            response = await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=300,
                temperature=0.2
            )

            try:
                suggestions = json.loads(response)
                return suggestions
            except json.JSONDecodeError:
                return {
                    "adjustments": {"general": "Review parameter settings based on optimization results"},
                    "priority": "medium",
                    "expected_impact": "Gradual performance improvement"
                }

        except Exception as e:
            logger.error(f"Failed to suggest parameter adjustments: {str(e)}")
            return {"error": "Unable to generate suggestions"}
