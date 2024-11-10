from typing import Dict, List, Optional
import logging
import anthropic
from anthropic import Anthropic
import os
import time
from time import sleep

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
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()

        self._last_request_time = 0
        self._request_interval = 1.0  # Minimum time between requests in seconds

    def _load_system_prompt(self) -> str:
        """Load the system prompt for analysis mode"""
        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        
        try:
            with open(os.path.join(prompts_dir, "analysis_prompt.txt"), "r") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error loading analysis prompt: {str(e)}")
            raise

    def stream_analysis(self, user_message):
        """Stream the analysis response from Claude with rate limiting"""
        try:
            # Add rate limiting
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._request_interval:
                sleep(self._request_interval - time_since_last)
            
            self._last_request_time = time.time()

            # Create messages array with conversation history
            messages = [{"role": msg["role"], "content": msg["content"]} 
                       for msg in self.conversation_history]
            messages.append({"role": "user", "content": user_message})

            with self.client.messages.stream(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                system=self.system_prompt,
                messages=messages
            ) as stream:
                response_content = ""
                for message in stream:
                    if hasattr(message, 'type'):
                        if message.type == 'content_block_delta':
                            if hasattr(message, 'delta') and hasattr(message.delta, 'text'):
                                if message.delta.text:
                                    response_content += message.delta.text
                                    yield message.delta.text
                        elif message.type == 'message_delta':
                            if hasattr(message, 'delta') and hasattr(message.delta, 'text'):
                                if message.delta.text:
                                    response_content += message.delta.text
                                    yield message.delta.text

                # Store the complete conversation
                self.conversation_history.append({
                    "role": "user",
                    "content": user_message
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_content
                })
                    
        except Exception as e:
            logger.error(f"Error in stream_analysis: {str(e)}")
            yield f"Error: {str(e)}"

    async def process_query(self, query: str, context: Optional[Dict] = None) -> Dict:
        """Process an analysis query using Claude"""
        try:
            # Include region context if available
            context_str = ""
            if context and 'region' in context:
                context_str = f"\nRegion context: {context['region']}"
            
            # Create messages array with conversation history
            messages = [{"role": msg["role"], "content": msg["content"]} 
                       for msg in self.conversation_history]
            messages.append({
                "role": "user", 
                "content": f"{query}{context_str}"
            })
            
            # Create message
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=self.system_prompt,
                messages=messages
            )
            
            response_text = message.content[0].text if message and message.content else "No response generated"
            
            # Store in conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': f"{query}{context_str}"
            })
            self.conversation_history.append({
                'role': 'assistant',
                'content': response_text
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