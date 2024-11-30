from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging
import anthropic
from anthropic import Anthropic
import os
from time import sleep
import time
from .catalog import DataCatalog
from .catalog_llm import CatalogAgent
import asyncio

logger = logging.getLogger(__name__)

class DataAgent:
    def __init__(self):
        """Initialize the data agent with Claude and catalog"""
        self.conversation_history: List[Dict] = []
        self.catalog = DataCatalog()
        self.catalog_agent = CatalogAgent(self.catalog)
        
        # Initialize Claude
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")
        try:
            self.client = Anthropic(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {str(e)}")
            self.client = None
        
        # Load prompts
        self.prompts = self._load_prompts()
        self._last_request_time = 0
        self._request_interval = 1.0

    def _load_prompts(self) -> Dict[str, str]:
        """Load system prompt template"""
        prompts_dir = Path(__file__).parent / "prompts"
        try:
            with open(prompts_dir / "system_prompt.txt", "r") as f:
                return {"system": f.read().strip()}
        except Exception as e:
            logger.error(f"Error loading prompts: {str(e)}")
            return {"system": "You are an environmental data analysis assistant."}

    def _format_dataset_suggestions(self, datasets: List[Dict]) -> str:
        """Format dataset suggestions for the LLM context"""
        if not datasets:
            return "No matching datasets found."
            
        suggestions = "Relevant datasets:\n\n"
        for dataset in datasets:
            suggestions += f"""- {dataset['name']}
  ID: {dataset['id']}
  Time Range: {dataset['temporal_range']}
  Resolution: {dataset['spatial_resolution']}
  Description: {dataset['description']}\n\n"""
            
        return suggestions

    async def get_dataset_suggestions(self, query: str) -> Dict:
        """
        Process user query and return structured dataset suggestions
        """
        response_text = ""
        async for chunk in self.stream_query(query):
            response_text += chunk
            
        # Extract structured suggestions using CatalogAgent
        suggested_datasets = self.catalog_agent.extract_dataset_suggestions(response_text)
        
        return {
            "query": query,
            "suggested_datasets": suggested_datasets,
            "raw_response": response_text
        }

    async def stream_query(self, query: str):
        """Stream the response from Claude with dataset suggestions"""
        try:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._request_interval:
                await asyncio.sleep(self._request_interval - time_since_last)
            
            self._last_request_time = time.time()

            # Create a condensed version of the catalog for context
            condensed_catalog = [
                {
                    "id": d["id"],
                    "name": d["name"],
                    "description": d["description"][:100] + "..." if len(d["description"]) > 100 else d["description"],
                    "temporal_range": d["temporal_range"],
                    "spatial_resolution": d["spatial_resolution"]
                }
                for d in self.catalog.get_all_datasets()
            ]

            context = f"""Available datasets:

{json.dumps(condensed_catalog, indent=2)}

Query: {query}

Please analyze the query and suggest the most relevant datasets from the catalog. For each suggestion:
1. Reference the dataset using [Dataset ID: dataset-id] format
2. Explain why it's relevant to the query
3. Highlight key temporal and spatial characteristics
4. Limit to the top 3 most relevant datasets"""

            # Create the message using the non-streaming API
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=self.prompts["system"],
                messages=[{"role": "user", "content": context}]
            )

            # Get the response content
            content = response.content[0].text
            chunk_size = 4  # Smaller chunks for more natural streaming
            
            # Yield the content in chunks with proper SSE formatting
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                # Format as Server-Sent Event
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.02)  # Slightly longer delay for more natural streaming

            # Send end marker
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in stream_query: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"

    async def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []

class LLMService:
    @staticmethod
    def process_message(message: str):
        # Placeholder for LLM processing
        return f"Processed: {message}" 