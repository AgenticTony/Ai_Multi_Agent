"""
Enhanced Roxy Agent with dynamic prompt loading
"""
import logging
from typing import Dict, Any, Optional, List

from voicehive.domains.prompts.services.prompt_manager import PromptManager
from voicehive.services.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class RoxyAgent:
    """
    Roxy Agent - Main voice assistant with dynamic prompt loading
    """
    
    def __init__(self, 
                 openai_service: OpenAIService,
                 prompt_manager: PromptManager):
        self.openai_service = openai_service
        self.prompt_manager = prompt_manager
        self.current_prompt = None
        self.prompt_version = None
        
    async def initialize(self):
        """Initialize agent by loading the latest prompt"""
        await self._load_latest_prompt()
        
    async def _load_latest_prompt(self):
        """Load the latest approved prompt version"""
        prompt_data = self.prompt_manager.get_current_prompt()
        if prompt_data:
            self.current_prompt = prompt_data
            self.prompt_version = prompt_data.version
            logger.info(f"Loaded prompt version: {self.prompt_version}")
        else:
            logger.error("Failed to load current prompt")
            raise RuntimeError("No prompt available for agent")
    
    async def handle_message(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming user message
        
        Args:
            user_message: The user's message text
            context: Conversation context including history, user data, etc.
            
        Returns:
            Response object with agent's reply and any actions
        """
        # Ensure prompt is loaded
        if not self.current_prompt:
            await self._load_latest_prompt()
            
        # Create system message from prompt
        system_message = self.current_prompt.prompt.get("system_prompt", "")
        
        # Prepare conversation history
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Add conversation history if available
        if "history" in context and context["history"]:
            messages.extend(context["history"])
            
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Get response from OpenAI
        response = await self.openai_service.chat_completion(
            messages=messages,
            model="gpt-4",
            temperature=0.7
        )
        
        # Process response
        agent_response = {
            "text": response.choices[0].message.content,
            "prompt_version": self.prompt_version,
            "actions": self._extract_actions(response.choices[0].message.content)
        }
        
        return agent_response
    
    def _extract_actions(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract any actions from the response text"""
        # This would parse function calls or action markers in the response
        # Simplified implementation for now
        actions = []
        
        if "book appointment" in response_text.lower():
            actions.append({
                "type": "book_appointment",
                "params": {}
            })
            
        if "check availability" in response_text.lower():
            actions.append({
                "type": "check_availability",
                "params": {}
            })
            
        return actions