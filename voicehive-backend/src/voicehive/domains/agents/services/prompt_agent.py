"""
Prompt Agent - Responsible for synthesizing feedback into improved prompts
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from voicehive.services.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class PromptAgent:
    """
    The Prompt Agent reads feedback and intelligently synthesizes new system prompts.
    It takes the current prompt and feedback data as input and produces a candidate
    prompt that incorporates improvements while maintaining prompt integrity.
    """
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        
    async def generate_candidate_prompt(self, 
                                        current_prompt: Dict[str, Any], 
                                        feedback_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a candidate prompt based on current prompt and feedback data
        
        Args:
            current_prompt: The current active prompt structure
            feedback_data: Feedback and improvement suggestions
            
        Returns:
            A candidate prompt incorporating the improvements
        """
        try:
            # Extract relevant feedback
            recommendations = feedback_data.get("pending_improvements", [])
            if not recommendations:
                logger.info("No pending improvements found, skipping prompt generation")
                return None
                
            # Create synthesis prompt
            synthesis_prompt = self._create_synthesis_prompt(current_prompt, recommendations)
            
            # Generate improved prompt
            response = await self.openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert prompt engineer specializing in voice assistant optimization."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                model="gpt-4",
                temperature=0.3
            )
            
            # Parse the response
            candidate_prompt = self._parse_candidate_prompt(response.choices[0].message.content)
            
            # Add metadata
            candidate_prompt["metadata"] = {
                "version": f"v{self._increment_version(current_prompt.get('metadata', {}).get('version', 'v1.0'))}",
                "generated_timestamp": datetime.now().isoformat(),
                "based_on_version": current_prompt.get("metadata", {}).get("version", "v1.0"),
                "applied_recommendations": [rec.get("id") for rec in recommendations],
                "status": "candidate"
            }
            
            return candidate_prompt
            
        except Exception as e:
            logger.error(f"Error generating candidate prompt: {str(e)}")
            return None
            
    def _create_synthesis_prompt(self, current_prompt: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
        """Create a prompt for synthesizing improvements"""
        return f"""
CURRENT PROMPT:
{json.dumps(current_prompt, indent=2)}

RECOMMENDED IMPROVEMENTS:
{json.dumps(recommendations, indent=2)}

Your task is to create an improved version of the current prompt by carefully incorporating the recommended improvements.

IMPORTANT GUIDELINES:
1. Maintain the overall structure and essential elements of the original prompt
2. Integrate the improvements naturally, not as appended text
3. Ensure the prompt remains coherent and consistent in tone
4. Preserve all tool-calling syntax and functional elements
5. Focus on the high-priority recommendations first
6. Keep the prompt concise and effective

Return ONLY the complete JSON structure of the new prompt with all improvements integrated.
"""

    def _parse_candidate_prompt(self, response_text: str) -> Dict[str, Any]:
        """Parse the candidate prompt from the response"""
        try:
            # Find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse candidate prompt: {str(e)}")
            raise
            
    def _increment_version(self, version: str) -> str:
        """Increment the version number"""
        if not version.startswith('v'):
            return "v1.1"
            
        try:
            version_num = version[1:]
            major, minor = version_num.split('.')
            return f"v{major}.{int(minor) + 1}"
        except:
            return "v1.1"
