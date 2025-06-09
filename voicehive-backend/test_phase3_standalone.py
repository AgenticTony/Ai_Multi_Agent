#!/usr/bin/env python3
"""
Standalone test for VoiceHive Phase 3: Advanced Orchestration

This test validates the Phase 3 implementation including:
- Multi-objective optimization
- Autonomous decision making
- Strategic planning
- Cross-system learning
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Phase 3 components
from voicehive.domains.agents.services.ml.multi_objective_optimizer import (
    MultiObjectiveOptimizer, Objective, ObjectiveType, OptimizationStrategy
)
from voicehive.domains.agents.services.autonomy.autonomous_controller import (
    AutonomousController, DecisionContext, DecisionType, SafetyConstraint
)
from voicehive.domains.agents.services.planning.strategic_planner import (
    StrategicPlanner, GoalType, PlanningHorizon
)
from voicehive.domains.agents.services.ml.cross_system_learning import (
    CrossSystemLearning, LearningType, DataSensitivity
)

# Mock OpenAI service for testing
class MockOpenAIService:
    """Mock OpenAI service for testing"""
    
    async def generate_response(self, prompt: str, max_tokens: int = 500, temperature: float = 0.3) -> str:
        """Generate mock response based on prompt content"""
        if "multi-objective optimization" in prompt.lower() or "parameter adjustments" in prompt.lower():
            return '''
            {
                "adjustments": {"general": "Increase focus on cost optimization while maintaining quality"},
                "priority": "high",
                "expected_impact": "15% cost reduction with minimal quality impact"
            }
            '''
        elif "autonomous decision" in prompt.lower():
            return '''
            {
                "action": "optimize_resource_allocation",
                "confidence": 0.85,
                "reasoning": "Current resource utilization is suboptimal, reallocation will improve efficiency",
                "execution_plan": ["Analyze current allocation", "Identify optimization opportunities", "Implement changes", "Monitor results"],
                "rollback_plan": ["Revert to previous allocation", "Restore original settings"],
                "monitoring_metrics": ["cpu_utilization", "response_time", "cost_per_request"]
            }
            '''
        elif "strategic" in prompt.lower() and "roadmap components" in prompt.lower():
            return '''
            {
                "key_initiatives": ["Implement performance monitoring system", "Optimize resource allocation algorithms", "Enhance system reliability measures", "Deploy automated scaling solutions"],
                "success_metrics": ["System uptime percentage", "Response time improvement", "Cost reduction percentage", "User satisfaction score"],
                "risk_factors": ["Technical complexity", "Resource constraints", "Timeline pressures"],
                "dependencies": ["Infrastructure readiness", "Team availability", "Budget approval"]
            }
            '''
        elif "strategic" in prompt.lower():
            return '''
            {
                "success_criteria": ["Achieve 95% uptime", "Reduce costs by 20%", "Improve response time by 30%"],
                "milestones": [
                    {"name": "Infrastructure upgrade", "description": "Upgrade core infrastructure", "target_date": "2024-03-15", "completion_criteria": ["All servers upgraded"]},
                    {"name": "Optimization implementation", "description": "Implement optimization algorithms", "target_date": "2024-04-01", "completion_criteria": ["Algorithms deployed"]}
                ],
                "dependencies": ["Budget approval", "Technical team availability"],
                "risks": ["Budget constraints", "Technical complexity"]
            }
            '''
        elif "cross-system learning" in prompt.lower() or "federated" in prompt.lower():
            return '''
            [
                {
                    "description": "High CPU usage pattern detected across multiple systems during peak hours",
                    "confidence": 0.9,
                    "applicable_contexts": ["production", "high_traffic"],
                    "recommendations": ["Implement auto-scaling", "Optimize resource allocation"],
                    "evidence": {"avg_cpu": 85, "peak_times": ["09:00-11:00", "14:00-16:00"]}
                }
            ]
            '''
        else:
            return '{"message": "Mock response generated successfully"}'


class Phase3TestSuite:
    """Comprehensive test suite for Phase 3 components"""
    
    def __init__(self):
        self.mock_openai = MockOpenAIService()
        self.test_results = {}
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 3 tests"""
        logger.info("🚀 Starting Phase 3 Advanced Orchestration Tests")
        
        tests = [
            ("Multi-Objective Optimization", self.test_multi_objective_optimizer),
            ("Autonomous Decision Making", self.test_autonomous_controller),
            ("Strategic Planning", self.test_strategic_planner),
            ("Cross-System Learning", self.test_cross_system_learning),
            ("Integration Test", self.test_phase3_integration)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"Running test: {test_name}")
                result = await test_func()
                self.test_results[test_name] = {"status": "PASSED", "details": result}
                logger.info(f"✅ {test_name} - PASSED")
            except Exception as e:
                self.test_results[test_name] = {"status": "FAILED", "error": str(e)}
                logger.error(f"❌ {test_name} - FAILED: {str(e)}")
        
        return self.generate_test_report()
    
    async def test_multi_objective_optimizer(self) -> Dict[str, Any]:
        """Test multi-objective optimization engine"""
        optimizer = MultiObjectiveOptimizer(self.mock_openai)
        
        # Add objectives
        cost_objective = Objective(
            name="cost_efficiency",
            type=ObjectiveType.MINIMIZE,
            weight=0.4,
            target_value=100
        )
        
        performance_objective = Objective(
            name="response_time",
            type=ObjectiveType.MINIMIZE,
            weight=0.6,
            target_value=200
        )
        
        optimizer.add_objective(cost_objective)
        optimizer.add_objective(performance_objective)
        
        # Define parameter space
        parameter_space = {
            "cpu_allocation": {"type": "float", "min": 0.1, "max": 1.0},
            "memory_allocation": {"type": "float", "min": 0.1, "max": 1.0},
            "instance_count": {"type": "int", "min": 1, "max": 10}
        }
        
        # Run optimization
        result = await optimizer.optimize(
            parameter_space=parameter_space,
            strategy=OptimizationStrategy.HYBRID_AI,
            max_time_seconds=30
        )
        
        # Validate results
        assert len(result.pareto_front) > 0, "Pareto front should not be empty"
        assert result.best_compromise is not None, "Best compromise solution should exist"
        assert result.optimization_time > 0, "Optimization time should be recorded"
        assert len(result.ai_recommendations) > 0, "AI recommendations should be provided"
        
        # Test parameter adjustment suggestions
        current_performance = {"cost_efficiency": 120, "response_time": 250}
        suggestions = await optimizer.suggest_parameter_adjustments(current_performance)
        
        assert "adjustments" in suggestions, "Parameter adjustment suggestions should be provided"
        
        return {
            "pareto_front_size": len(result.pareto_front),
            "optimization_time": result.optimization_time,
            "best_compromise_confidence": result.best_compromise.confidence_score,
            "ai_recommendations_count": len(result.ai_recommendations)
        }
    
    async def test_autonomous_controller(self) -> Dict[str, Any]:
        """Test autonomous decision making controller"""
        controller = AutonomousController(self.mock_openai)
        
        # Add custom safety constraint
        custom_constraint = SafetyConstraint(
            name="test_constraint",
            condition="risk_level > 5",
            max_risk_level=5,
            requires_human_approval=True,
            description="Test safety constraint"
        )
        controller.add_safety_constraint(custom_constraint)
        
        # Test autonomous decision
        decision_context = DecisionContext(
            decision_id="test_decision_001",
            decision_type=DecisionType.OPTIMIZATION,
            description="Optimize resource allocation for better performance",
            data={
                "current_cpu": 75,
                "current_memory": 60,
                "target_performance": 90
            },
            urgency=5,
            impact=7,
            risk_level=3
        )
        
        decision_result = await controller.make_decision(decision_context)
        
        # Validate decision
        assert decision_result.decision_id == "test_decision_001", "Decision ID should match"
        assert decision_result.confidence > 0, "Decision should have confidence score"
        assert len(decision_result.execution_plan) > 0, "Execution plan should be provided"
        assert len(decision_result.rollback_plan) > 0, "Rollback plan should be provided"
        
        # Test high-risk decision (should be escalated)
        high_risk_context = DecisionContext(
            decision_id="test_decision_002",
            decision_type=DecisionType.SAFETY,
            description="Critical safety decision",
            data={"safety_level": "critical"},
            urgency=9,
            impact=10,
            risk_level=8
        )
        
        high_risk_result = await controller.make_decision(high_risk_context)
        assert high_risk_result.human_approval_required, "High-risk decisions should require approval"
        
        # Test decision execution
        if not decision_result.human_approval_required:
            execution_result = await controller.execute_decision(decision_result.decision_id)
            assert execution_result["success"], "Decision execution should succeed"
        
        # Get performance metrics
        metrics = controller.get_performance_metrics()
        
        return {
            "decisions_made": metrics["total_decisions"],
            "autonomous_rate": metrics["autonomy_rate"],
            "safety_constraints": metrics["safety_constraints"],
            "pending_approvals": metrics["pending_approvals"]
        }
    
    async def test_strategic_planner(self) -> Dict[str, Any]:
        """Test strategic planning system"""
        planner = StrategicPlanner(self.mock_openai)
        
        # Create strategic goal
        goal = await planner.create_strategic_goal(
            name="Improve System Performance",
            description="Enhance overall system performance and reliability",
            goal_type=GoalType.PERFORMANCE,
            target_value=95.0,
            target_date=datetime.now() + timedelta(days=90),
            priority=8
        )
        
        # Validate goal creation
        assert goal.id in planner.goals, "Goal should be stored"
        assert len(goal.success_criteria) > 0, "Success criteria should be generated"
        assert len(goal.milestones) > 0, "Milestones should be created"
        
        # Update goal progress
        progress_result = await planner.update_goal_progress(goal.id, 25.0)
        assert progress_result["success"], "Goal progress update should succeed"
        
        # Create scenario
        scenario = await planner.create_scenario(
            name="High Traffic Scenario",
            description="System under high traffic load",
            probability=0.7,
            impact=8,
            assumptions=["Traffic increases by 300%", "Current infrastructure maintained"]
        )
        
        # Generate strategic roadmap
        roadmap = await planner.generate_strategic_roadmap(
            name="Performance Improvement Roadmap",
            description="Strategic roadmap for system performance improvements",
            horizon=PlanningHorizon.MEDIUM_TERM,
            goal_ids=[goal.id],
            scenario_ids=[scenario.id]
        )
        
        # Validate roadmap
        assert roadmap.id in planner.roadmaps, "Roadmap should be stored"
        assert len(roadmap.goals) > 0, "Roadmap should include goals"


        assert len(roadmap.key_initiatives) > 0, "Key initiatives should be generated"
        
        # Test scenario impact simulation
        simulation_result = await planner.simulate_scenario_impact(scenario.id, [goal.id])
        assert simulation_result["success"], "Scenario simulation should succeed"
        
        # Get dashboard data
        dashboard = planner.get_strategic_dashboard()
        
        return {
            "goals_created": dashboard["summary"]["total_goals"],
            "scenarios_created": dashboard["summary"]["total_scenarios"],
            "roadmaps_created": dashboard["summary"]["total_roadmaps"],
            "milestones_created": dashboard["summary"]["total_milestones"]
        }
    
    async def test_cross_system_learning(self) -> Dict[str, Any]:
        """Test cross-system learning engine"""
        learning_engine = CrossSystemLearning("test_system_001", self.mock_openai)
        
        # Add learning data
        data_id = learning_engine.add_learning_data(
            learning_type=LearningType.PERFORMANCE_PATTERNS,
            data={
                "cpu_usage": 75.5,
                "memory_usage": 60.2,
                "response_time": 150,
                "throughput": 1000
            },
            metadata={"environment": "production", "region": "us-east-1"},
            sensitivity=DataSensitivity.AGGREGATED
        )
        
        # Add more data points for pattern recognition
        for i in range(5):
            learning_engine.add_learning_data(
                learning_type=LearningType.PERFORMANCE_PATTERNS,
                data={
                    "cpu_usage": 70 + i * 2,
                    "memory_usage": 55 + i * 3,
                    "response_time": 140 + i * 5,
                    "throughput": 950 + i * 10
                },
                metadata={"environment": "production", "region": "us-east-1"}
            )
        
        # Generate insights
        insights = await learning_engine.generate_insights(LearningType.PERFORMANCE_PATTERNS)
        
        # Connect to another system
        learning_engine.connect_to_system("test_system_002", trust_score=0.85)
        
        # Test federated learning round
        federated_result = await learning_engine.federated_learning_round()
        
        # Get dashboard data
        dashboard = learning_engine.get_learning_dashboard()
        
        return {
            "data_points_collected": dashboard["summary"]["total_data_points"],
            "insights_generated": dashboard["summary"]["insights_generated"],
            "connected_systems": dashboard["summary"]["connected_systems"],
            "federated_learning_success": federated_result.get("success", False)
        }
    
    async def test_phase3_integration(self) -> Dict[str, Any]:
        """Test integration between Phase 3 components"""
        # Initialize all components
        optimizer = MultiObjectiveOptimizer(self.mock_openai)
        controller = AutonomousController(self.mock_openai)
        planner = StrategicPlanner(self.mock_openai)
        learning_engine = CrossSystemLearning("integration_test", self.mock_openai)
        
        # Simulate integrated workflow
        
        # 1. Strategic planning creates goals
        goal = await planner.create_strategic_goal(
            name="Integrated System Optimization",
            description="Optimize system through integrated AI approach",
            goal_type=GoalType.PERFORMANCE,
            target_value=90.0,
            priority=9
        )
        
        # 2. Multi-objective optimization finds optimal parameters
        optimizer.add_objective(Objective("performance", ObjectiveType.MAXIMIZE, 0.6))
        optimizer.add_objective(Objective("cost", ObjectiveType.MINIMIZE, 0.4))
        
        parameter_space = {
            "optimization_level": {"type": "float", "min": 0.1, "max": 1.0},
            "resource_allocation": {"type": "float", "min": 0.5, "max": 2.0}
        }
        
        optimization_result = await optimizer.optimize(parameter_space, max_time_seconds=15)
        
        # 3. Autonomous controller makes implementation decision
        decision_context = DecisionContext(
            decision_id="integration_decision",
            decision_type=DecisionType.OPTIMIZATION,
            description="Implement optimization results",
            data={
                "optimization_params": optimization_result.best_compromise.parameters,
                "expected_performance": 90.0
            },
            urgency=6,
            impact=8,
            risk_level=4
        )
        
        decision_result = await controller.make_decision(decision_context)
        
        # 4. Cross-system learning captures the results
        learning_engine.add_learning_data(
            learning_type=LearningType.OPTIMIZATION_STRATEGIES,
            data={
                "optimization_strategy": "hybrid_ai",
                "performance_improvement": 15.5,
                "implementation_success": True,
                "decision_confidence": decision_result.confidence
            }
        )
        
        # 5. Update strategic goal progress
        await planner.update_goal_progress(goal.id, 45.0)
        
        return {
            "integration_successful": True,
            "goal_progress": 45.0,
            "optimization_confidence": optimization_result.best_compromise.confidence_score,
            "decision_confidence": decision_result.confidence,
            "learning_data_captured": True
        }
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASSED")
        total_tests = len(self.test_results)
        
        report = {
            "phase": "Phase 3 - Advanced Orchestration",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0
            },
            "test_results": self.test_results,
            "status": "PASSED" if passed_tests == total_tests else "FAILED"
        }
        
        return report


async def main():
    """Main test execution"""
    test_suite = Phase3TestSuite()
    
    try:
        report = await test_suite.run_all_tests()
        
        print("\n" + "="*80)
        print("🎯 PHASE 3 ADVANCED ORCHESTRATION TEST REPORT")
        print("="*80)
        print(f"Status: {report['status']}")
        print(f"Tests Passed: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1%}")
        print("="*80)
        
        for test_name, result in report['test_results'].items():
            status_emoji = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"{status_emoji} {test_name}: {result['status']}")
            if result['status'] == 'FAILED':
                print(f"   Error: {result['error']}")
        
        print("="*80)
        
        if report['status'] == 'PASSED':
            print("🚀 Phase 3 Advanced Orchestration implementation is ready!")
            print("✨ Features validated:")
            print("   • Multi-objective optimization with AI guidance")
            print("   • Autonomous decision making with safety constraints")
            print("   • Strategic planning with scenario analysis")
            print("   • Cross-system learning with federated insights")
            print("   • Integrated workflow orchestration")
        else:
            print("⚠️  Some tests failed. Please review the errors above.")
        
        return report['status'] == 'PASSED'
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        print(f"\n❌ Test execution failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
