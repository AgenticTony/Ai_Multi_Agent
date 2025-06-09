"""
Supervisor Agent - Responsible for evaluating, testing, and approving prompt changes
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

from voicehive.services.ai.openai_service import OpenAIService
from voicehive.domains.prompts.services.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """
    The Supervisor Agent evaluates candidate prompts through simulation,
    safety checks, and performance analysis before approving them for production.
    """
    
    def __init__(self, 
                 openai_service: OpenAIService,
                 prompt_manager: PromptManager):
        self.openai_service = openai_service
        self.prompt_manager = prompt_manager
        self.safety_checks = [
            self._check_harmful_content,
            self._check_tool_calling_syntax,
            self._check_prompt_length,
            self._check_instruction_preservation
        ]
        
    async def evaluate_candidate_prompt(self, 
                                       candidate_prompt: Dict[str, Any],
                                       current_prompt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a candidate prompt through simulation and safety checks
        
        Args:
            candidate_prompt: The candidate prompt to evaluate
            current_prompt: The current production prompt
            
        Returns:
            Evaluation results with approval decision
        """
        evaluation_results = {
            "prompt_id": candidate_prompt.get("metadata", {}).get("version", "unknown"),
            "evaluation_timestamp": datetime.now().isoformat(),
            "safety_checks": {},
            "simulation_results": {},
            "approved": False,
            "reasons": []
        }
        
        # Run safety checks
        all_safety_passed = True
        for check in self.safety_checks:
            check_name = check.__name__.replace("_check_", "")
            passed, reason = await check(candidate_prompt, current_prompt)
            evaluation_results["safety_checks"][check_name] = {
                "passed": passed,
                "reason": reason
            }
            if not passed:
                all_safety_passed = False
                evaluation_results["reasons"].append(f"Failed safety check: {check_name} - {reason}")
        
        # If safety checks pass, run simulations
        if all_safety_passed:
            simulation_passed, simulation_results = await self._run_simulations(candidate_prompt, current_prompt)
            evaluation_results["simulation_results"] = simulation_results
            
            if not simulation_passed:
                evaluation_results["reasons"].append("Failed simulation tests")
            else:
                # All checks passed
                evaluation_results["approved"] = True
                evaluation_results["reasons"].append("All safety checks and simulations passed")
        
        return evaluation_results
    
    async def approve_and_deploy(self, 
                                candidate_prompt: Dict[str, Any], 
                                evaluation_results: Dict[str, Any]) -> bool:
        """
        Approve and deploy a candidate prompt if evaluation passed
        
        Args:
            candidate_prompt: The candidate prompt to deploy
            evaluation_results: The evaluation results
            
        Returns:
            True if deployment successful, False otherwise
        """
        if not evaluation_results.get("approved", False):
            logger.warning(f"Cannot deploy unapproved prompt: {candidate_prompt.get('metadata', {}).get('version', 'unknown')}")
            return False
            
        try:
            # Update metadata
            candidate_prompt["metadata"]["status"] = "active"
            candidate_prompt["metadata"]["approved_timestamp"] = datetime.now().isoformat()
            
            # Save as new version using the prompt manager
            version = candidate_prompt["metadata"]["version"]
            base_version = candidate_prompt["metadata"].get("based_on_version", "v1.0")
            
            # Create the new version
            new_version = self.prompt_manager.create_new_version(
                base_version=base_version,
                changes={"prompt": candidate_prompt},
                rationale=f"Supervisor approved deployment of {version}"
            )
            
            if new_version:
                # Activate the new version
                success = self.prompt_manager.activate_version(new_version)
                if success:
                    logger.info(f"Successfully deployed new prompt version: {new_version}")
                    return True
                else:
                    logger.error(f"Failed to activate new prompt version: {new_version}")
                    return False
            else:
                logger.error(f"Failed to create new prompt version from: {version}")
                return False
                
        except Exception as e:
            logger.error(f"Error deploying candidate prompt: {str(e)}")
            return False
    
    async def _run_simulations(self, 
                              candidate_prompt: Dict[str, Any],
                              current_prompt: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Run simulations with problematic transcripts"""
        # Get recent problematic transcripts
        test_cases = await self._get_test_transcripts()
        
        if not test_cases:
            logger.warning("No test transcripts found for simulation")
            return False, {"error": "No test transcripts available"}
            
        simulation_results = {
            "total_cases": len(test_cases),
            "improved_cases": 0,
            "regression_cases": 0,
            "neutral_cases": 0,
            "case_details": []
        }
        
        for case in test_cases:
            # Simulate with both prompts
            current_response = await self._simulate_response(current_prompt, case["transcript"])
            candidate_response = await self._simulate_response(candidate_prompt, case["transcript"])
            
            # Compare responses
            comparison = await self._compare_responses(
                case["transcript"], 
                current_response, 
                candidate_response
            )
            
            simulation_results["case_details"].append({
                "case_id": case["id"],
                "comparison_result": comparison["result"],
                "improvement_score": comparison["score"],
                "reasoning": comparison["reasoning"]
            })
            
            # Update counters
            if comparison["result"] == "improved":
                simulation_results["improved_cases"] += 1
            elif comparison["result"] == "regression":
                simulation_results["regression_cases"] += 1
            else:
                simulation_results["neutral_cases"] += 1
        
        # Determine if simulation passed
        passed = (
            simulation_results["improved_cases"] > simulation_results["regression_cases"] and
            simulation_results["regression_cases"] <= 1  # Allow at most 1 regression
        )
        
        return passed, simulation_results
    
    async def _get_test_transcripts(self) -> List[Dict[str, Any]]:
        """Get problematic transcripts for testing"""
        # In production, this would query Mem0 for recent problematic calls
        # For now, return a simplified test set
        return [
            {
                "id": "test_case_1",
                "transcript": "Customer: I'm not sure if this is worth the money.\nAgent: We offer great value for the price.",
                "issue": "price_objection"
            },
            {
                "id": "test_case_2",
                "transcript": "Customer: I need to think about it.\nAgent: I understand. When would be a good time to follow up?",
                "issue": "hesitation"
            }
        ]
    
    async def _simulate_response(self, prompt: Dict[str, Any], transcript: str) -> str:
        """Simulate agent response with given prompt"""
        try:
            # Extract the last customer message
            customer_lines = [line for line in transcript.split('\n') if line.startswith('Customer:')]
            if not customer_lines:
                return "No customer message found"
                
            last_customer_message = customer_lines[-1].replace('Customer:', '').strip()
            
            # Create simulation prompt
            system_content = json.dumps(prompt)
            
            # Get response from OpenAI
            response = await self.openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": last_customer_message}
                ],
                model="gpt-4",
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in simulation: {str(e)}")
            return f"Simulation error: {str(e)}"

    async def _compare_responses(self,
                                transcript: str,
                                current_response: str,
                                candidate_response: str) -> Dict[str, Any]:
        """Compare responses and determine if there's improvement"""
        comparison_prompt = f"""
TRANSCRIPT:
{transcript}

CURRENT RESPONSE:
{current_response}

CANDIDATE RESPONSE:
{candidate_response}

Compare these two responses and determine if the candidate response is an improvement.
Focus on:
1. Addressing the customer's concern
2. Persuasiveness and empathy
3. Effectiveness at moving toward booking an appointment
4. Professionalism and clarity

Return a JSON with:
- "result": "improved", "regression", or "neutral"
- "score": 1-10 rating of improvement (10 being significant improvement)
- "reasoning": Brief explanation of your assessment
"""

        response = await self.openai_service.chat_completion(
            messages=[
                {"role": "system", "content": "You are an expert evaluator of sales conversations."},
                {"role": "user", "content": comparison_prompt}
            ],
            model="gpt-4",
            temperature=0.3
        )

        # Parse response
        try:
            content = response.choices[0].message.content
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {
                    "result": "neutral",
                    "score": 5,
                    "reasoning": "Failed to parse comparison result"
                }

        except Exception:
            return {
                "result": "neutral",
                "score": 5,
                "reasoning": "Error comparing responses"
            }

    async def _check_harmful_content(self,
                                    candidate_prompt: Dict[str, Any],
                                    current_prompt: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for harmful content in the prompt"""
        forbidden_terms = [
            "bypass", "ignore", "disregard instructions",
            "harmful", "unethical", "illegal"
        ]

        prompt_str = json.dumps(candidate_prompt).lower()

        for term in forbidden_terms:
            if term in prompt_str:
                return False, f"Prompt contains forbidden term: {term}"

        return True, "No harmful content detected"

    async def _check_tool_calling_syntax(self,
                                       candidate_prompt: Dict[str, Any],
                                       current_prompt: Dict[str, Any]) -> Tuple[bool, str]:
        """Check that tool calling syntax is preserved"""
        # This is a simplified check - in production would be more thorough
        current_tools = self._extract_tools(current_prompt)
        candidate_tools = self._extract_tools(candidate_prompt)

        if len(current_tools) > len(candidate_tools):
            return False, f"Candidate prompt is missing tools: {set(current_tools) - set(candidate_tools)}"

        return True, "Tool calling syntax preserved"

    def _extract_tools(self, prompt: Dict[str, Any]) -> List[str]:
        """Extract tool names from prompt"""
        # Simplified extraction - would be more robust in production
        prompt_str = json.dumps(prompt)
        tools = []

        # Look for common tool patterns
        if "function_call" in prompt_str:
            tools.append("function_call")
        if "book_appointment" in prompt_str:
            tools.append("book_appointment")
        if "check_availability" in prompt_str:
            tools.append("check_availability")

        return tools

    async def _check_prompt_length(self,
                                 candidate_prompt: Dict[str, Any],
                                 current_prompt: Dict[str, Any]) -> Tuple[bool, str]:
        """Check that prompt length is reasonable"""
        max_length = 4000  # Characters

        candidate_length = len(json.dumps(candidate_prompt))

        if candidate_length > max_length:
            return False, f"Prompt too long: {candidate_length} chars (max {max_length})"

        return True, "Prompt length acceptable"

    async def _check_instruction_preservation(self,
                                            candidate_prompt: Dict[str, Any],
                                            current_prompt: Dict[str, Any]) -> Tuple[bool, str]:
        """Check that core instructions are preserved"""
        # This would be more sophisticated in production
        core_elements = [
            "appointment", "booking", "schedule",
            "wellness", "services", "consultation"
        ]

        current_str = json.dumps(current_prompt).lower()
        candidate_str = json.dumps(candidate_prompt).lower()

        for element in core_elements:
            if element in current_str and element not in candidate_str:
                return False, f"Core instruction element missing: {element}"

        return True, "Core instructions preserved"
