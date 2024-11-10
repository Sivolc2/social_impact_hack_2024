from typing import Dict, List, Optional
import logging
import anthropic
from anthropic import Anthropic
import os

logger = logging.getLogger(__name__)

class AnalysisAgent:
    def __init__(self):
        """Initialize the analysis agent with Claude"""
        self.conversation_history: List[Dict] = []
        
        # Initialize Claude
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = Anthropic(api_key=api_key)
        
        # Load analysis prompt
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the system prompt for analysis mode"""
        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        
        try:
            with open(os.path.join(prompts_dir, "analysis_prompt.txt"), "r") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error loading analysis prompt: {str(e)}")
            raise

    async def process_query(self, query: str, context: Optional[Dict] = None) -> Dict:
        """Process an analysis query using Claude"""
        try:
            # Include region context if available
            context_str = ""
            if context and 'region' in context:
                context_str = f"\nRegion context: {context['region']}"
            
            # Create message
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=self.system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"{query}{context_str}"
                }]
            )
            
            response_text = message.content[0].text if message and message.content else "No response generated"
            
            # Store in conversation history
            self.conversation_history.append({
                'query': query,
                'response': response_text,
                'context': context
            })
            
            return {
                'response': response_text,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error processing analysis query: {str(e)}")
            return {
                'response': f"I apologize, but I encountered an error analyzing your request: {str(e)}",
                'status': 'error'
            }

    def get_conversation_history(self) -> List[Dict]:
        """Return the conversation history"""
        return self.conversation_history

    async def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = [] 