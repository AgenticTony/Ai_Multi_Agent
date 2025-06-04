import logging
from typing import List
from openai import OpenAI

from app.config.settings import settings
from app.models.vapi import ConversationMessage
from app.utils.exceptions import OpenAIServiceError

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        
    async def generate_response(self, system_prompt: str, conversation_history: List[ConversationMessage]) -> str:
        """
        Generate a response using OpenAI GPT
        
        Args:
            system_prompt: The system prompt for the AI
            conversation_history: List of conversation messages
            
        Returns:
            Generated response text
        """
        try:
            # Prepare messages for OpenAI API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Generate response
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature,
                timeout=settings.response_timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            raise OpenAIServiceError(f"Failed to generate response: {str(e)}")
