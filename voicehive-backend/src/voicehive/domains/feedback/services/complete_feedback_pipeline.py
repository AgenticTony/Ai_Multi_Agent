"""
Complete Feedback Pipeline - Orchestrates the entire feedback loop
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from voicehive.domains.feedback.services.vertex.vertex_feedback_service import VertexFeedbackService
from voicehive.domains.agents.services.prompt_agent import PromptAgent
from voicehive.domains.agents.services.gatekeeper_supervisor import (
    SupervisorAgent as GatekeeperSupervisor
)
from voicehive.domains.prompts.services.prompt_manager import PromptManager
from voicehive.services.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class CompleteFeedbackPipeline:
    """
    Orchestrates the complete feedback loop:
    1. Analyze calls with Vertex Feedback Service
    2. Generate candidate prompt with Prompt Agent
    3. Evaluate and approve with Supervisor Agent
    4. Deploy to production
    """

    def __init__(self):
        self.feedback_service = VertexFeedbackService()
        self.openai_service = OpenAIService()
        self.prompt_manager = PromptManager()
        self.prompt_agent = PromptAgent(self.openai_service)
        self.supervisor_agent = GatekeeperSupervisor(self.openai_service, self.prompt_manager)

    async def run_complete_pipeline(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete feedback pipeline
        
        Args:
            date: Optional date string (YYYY-MM-DD), defaults to yesterday
            
        Returns:
            Pipeline results summary
        """
        if not date:
            yesterday = datetime.now() - timedelta(days=1)
            date = yesterday.strftime("%Y-%m-%d")

        logger.info(f"Starting complete feedback pipeline for date: {date}")

        results = {
            "date": date,
            "pipeline_start": datetime.now().isoformat(),
            "stages": {},
            "success": False
        }
        
        try:
            # Stage 1: Analyze calls
            logger.info("Stage 1: Analyzing calls")
            feedback_summary = await self.feedback_service.analyze_daily_transcripts(date)
            
            results["stages"]["analysis"] = {
                "success": feedback_summary is not None,
                "calls_analyzed": feedback_summary.total_calls_analyzed if feedback_summary else 0
            }
            
            if not feedback_summary or feedback_summary.total_calls_analyzed == 0:
                logger.warning(f"No calls analyzed for date: {date}")
                results["stages"]["analysis"]["error"] = "No calls analyzed"
                return self._complete_results(results)
                
            # Save feedback to file
            await self.feedback_service.save_feedback_to_file(feedback_summary)
            
            # Stage 2: Generate candidate prompt
            logger.info("Stage 2: Generating candidate prompt")
            current_prompt = self.prompt_manager.get_current_prompt()
            
            if not current_prompt:
                logger.error("Failed to get current prompt")
                results["stages"]["prompt_generation"] = {
                    "success": False,
                    "error": "Failed to get current prompt"
                }
                return self._complete_results(results)
                
            # Convert feedback summary to format expected by prompt agent
            feedback_data = {
                "pending_improvements": feedback_summary.recommended_prompt_changes
            }
            
            candidate_prompt = await self.prompt_agent.generate_candidate_prompt(
                current_prompt, feedback_data
            )
            
            results["stages"]["prompt_generation"] = {
                "success": candidate_prompt is not None,
                "version": (
                    candidate_prompt.get("metadata", {}).get("version", "unknown")
                    if candidate_prompt else None
                )
            }
            
            if not candidate_prompt:
                logger.warning("No candidate prompt generated")
                results["stages"]["prompt_generation"]["error"] = "No candidate prompt generated"
                return self._complete_results(results)
                
            # Stage 3: Evaluate candidate prompt
            logger.info("Stage 3: Evaluating candidate prompt")
            evaluation_results = await self.supervisor_agent.evaluate_candidate_prompt(
                candidate_prompt, current_prompt
            )
            
            results["stages"]["evaluation"] = {
                "success": True,
                "approved": evaluation_results.get("approved", False),
                "reasons": evaluation_results.get("reasons", [])
            }
            
            # Stage 4: Deploy if approved
            if evaluation_results.get("approved", False):
                logger.info("Stage 4: Deploying approved prompt")
                deployment_success = await self.supervisor_agent.approve_and_deploy(
                    candidate_prompt, evaluation_results
                )
                
                results["stages"]["deployment"] = {
                    "success": deployment_success,
                    "version": candidate_prompt.get("metadata", {}).get("version", "unknown")
                }
                
                if deployment_success:
                    results["success"] = True
                    version = candidate_prompt.get('metadata', {}).get('version', 'unknown')
                    logger.info(f"Successfully deployed new prompt version: {version}")
                else:
                    results["stages"]["deployment"]["error"] = "Deployment failed"
            else:
                logger.info("Candidate prompt not approved, skipping deployment")
                results["stages"]["deployment"] = {
                    "success": True,
                    "skipped": True,
                    "reason": "Candidate not approved"
                }
                
            return self._complete_results(results)
                
        except Exception as e:
            logger.error(f"Error in feedback pipeline: {str(e)}")
            results["error"] = str(e)
            return self._complete_results(results)
    
    async def run_analysis_only(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Run only the analysis stage of the pipeline"""
        if not date:
            yesterday = datetime.now() - timedelta(days=1)
            date = yesterday.strftime("%Y-%m-%d")
            
        logger.info(f"Running analysis-only pipeline for date: {date}")
        
        results = {
            "date": date,
            "pipeline_start": datetime.now().isoformat(),
            "mode": "analysis_only",
            "success": False
        }
        
        try:
            feedback_summary = await self.feedback_service.analyze_daily_transcripts(date)
            
            if feedback_summary and feedback_summary.total_calls_analyzed > 0:
                await self.feedback_service.save_feedback_to_file(feedback_summary)
                results["success"] = True
                results["calls_analyzed"] = feedback_summary.total_calls_analyzed
                results["improvements_found"] = len(feedback_summary.recommended_prompt_changes)
            else:
                results["error"] = "No calls analyzed"
                
            return self._complete_results(results)
            
        except Exception as e:
            logger.error(f"Error in analysis-only pipeline: {str(e)}")
            results["error"] = str(e)
            return self._complete_results(results)
    
    async def run_simulation_only(
        self, candidate_prompt: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run only the simulation/evaluation stage"""
        logger.info("Running simulation-only pipeline")
        
        results = {
            "pipeline_start": datetime.now().isoformat(),
            "mode": "simulation_only",
            "success": False
        }
        
        try:
            current_prompt = self.prompt_manager.get_current_prompt()
            
            if not current_prompt:
                results["error"] = "Failed to get current prompt"
                return self._complete_results(results)
            
            if not candidate_prompt:
                # Generate a test candidate prompt
                feedback_data = {"pending_improvements": []}
                candidate_prompt = await self.prompt_agent.generate_candidate_prompt(
                    current_prompt, feedback_data
                )
            
            if candidate_prompt:
                evaluation_results = await self.supervisor_agent.evaluate_candidate_prompt(
                    candidate_prompt, current_prompt
                )
                
                results["success"] = True
                results["evaluation"] = evaluation_results
            else:
                results["error"] = "Failed to generate candidate prompt"
                
            return self._complete_results(results)
            
        except Exception as e:
            logger.error(f"Error in simulation-only pipeline: {str(e)}")
            results["error"] = str(e)
            return self._complete_results(results)
    
    def _complete_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Complete the results with pipeline end time"""
        results["pipeline_end"] = datetime.now().isoformat()
        return results


async def run_pipeline(date: Optional[str] = None) -> Dict[str, Any]:
    """Run the complete feedback pipeline"""
    pipeline = CompleteFeedbackPipeline()
    return await pipeline.run_complete_pipeline(date)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Get date from command line args if provided
    import sys
    date = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run the pipeline
    results = asyncio.run(run_pipeline(date))
    
    # Print results
    import json
    print(json.dumps(results, indent=2))
