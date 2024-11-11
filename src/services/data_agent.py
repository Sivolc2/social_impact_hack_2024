from typing import Dict, List, Optional, Any
from .vector_store import VectorStore
from pathlib import Path
import json
import logging
import anthropic
from anthropic import Anthropic
import os
from .summary_agent import SummaryAgent
import time
from time import sleep

logger = logging.getLogger(__name__)

class DataAgent:
    def __init__(self):
        """Initialize the data agent with vector store and Claude"""
        self.vector_store = VectorStore()
        self.conversation_history: List[Dict] = []
        self.confidence_threshold = 0.5
        
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
        self.summary_agent = SummaryAgent()
        self._last_request_time = 0
        self._request_interval = 1.0  # Minimum time between requests in seconds

    def _load_prompts(self) -> Dict[str, str]:
        """Load system prompt template"""
        prompts_dir = Path(__file__).parent / "prompts"
        try:
            with open(prompts_dir / "system_prompt.txt", "r") as f:
                return {"system": f.read().strip()}
        except Exception as e:
            logger.error(f"Error loading prompts: {str(e)}")
            raise RuntimeError(f"Failed to load prompts: {str(e)}")

    async def initialize(self, knowledge_base_path: str = "data/knowledge_base.json"):
        """Initialize the agent with knowledge base"""
        try:
            await self.load_knowledge_base(knowledge_base_path)
            logger.info("Data agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize data agent: {str(e)}")
            raise

    async def load_knowledge_base(self, knowledge_base_path: str):
        """Load and index the knowledge base from JSON file"""
        path = Path(knowledge_base_path)
        
        if not path.exists():
            logger.error(f"Knowledge base file not found at {path}")
            raise FileNotFoundError(f"Knowledge base file not found at {path}")
            
        try:
            logger.debug(f"Attempting to read JSON from {path}")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
            
            if 'datasets_available' not in data:
                logger.error("JSON file does not contain 'datasets_available' key")
                raise ValueError("Invalid knowledge base format: missing 'datasets_available' key")
            
            # Create a special document that lists all datasets
            dataset_catalog = self._create_dataset_catalog(data['datasets_available'])
            
            # Format individual dataset documents
            formatted_docs = [dataset_catalog]  # Add catalog as first document
            for dataset in data['datasets_available']:
                formatted_docs.append(self._format_dataset_document(dataset))
            
            self.vector_store.add_documents(formatted_docs)
            logger.info(f"Successfully loaded {len(formatted_docs)} documents into vector store")
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            raise

    def _create_dataset_catalog(self, datasets: List[Dict]) -> Dict:
        """Create a special document that lists all available datasets"""
        catalog_content = "Available Environmental Datasets:\n\n"
        
        for dataset in datasets:
            catalog_content += f"""
            Dataset: {dataset.get('name', 'Unknown')}
            ID: {dataset.get('id', 'Unknown')}
            Description: {dataset.get('description', 'No description available')}
            Time Range: {dataset.get('temporal_range', 'Not specified')}
            ---
            """
        
        return {
            'content': catalog_content.strip(),
            'metadata': {
                'type': 'dataset_catalog',
                'name': 'Dataset Catalog',
                'description': 'Complete listing of available environmental datasets'
            }
        }

    def _format_dataset_document(self, dataset: Dict) -> Dict:
        """Format a single dataset into a searchable document"""
        content = f"""
        Dataset: {dataset.get('name', 'Unknown')}
        Description: {dataset.get('description', '')}
        Time Range: {dataset.get('temporal_range', '')}
        Resolution: {dataset.get('spatial_resolution', '')}
        
        {dataset.get('text', '')}
        """
        
        return {
            'content': content.strip(),
            'metadata': {
                'id': dataset.get('id'),
                'name': dataset.get('name'),
                'source': dataset.get('source'),
                'category': dataset.get('category'),
                'temporal_range': dataset.get('temporal_range'),
                'spatial_resolution': dataset.get('spatial_resolution'),
                'variables': dataset.get('variables', []),
                'type': 'dataset'
            }
        }

    def stream_query(self, query: str) -> str:
        """Stream the response from Claude with rate limiting"""
        try:
            # Add rate limiting
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._request_interval:
                sleep(self._request_interval - time_since_last)
            
            self._last_request_time = time.time()

            # Check if query is about available datasets
            if any(keyword in query.lower() for keyword in ['available', 'datasets', 'list', 'what data']):
                # Prioritize returning the dataset catalog
                catalog_docs = self.vector_store.search_by_metadata({'type': 'dataset_catalog'})
                if catalog_docs:
                    doc_context = self._format_context(catalog_docs)
                else:
                    # Fallback to regular search
                    similar_docs = self.vector_store.similarity_search(query, k=5)
                    doc_context = self._format_context(similar_docs)
            else:
                # Regular similarity search
                similar_docs = self.vector_store.similarity_search(query, k=5)
                doc_context = self._format_context(similar_docs)

            formatted_prompt = f"""Context:\n{doc_context}\n\nQuery: {query}
            
            Important: If the query is about available datasets or data sources, 
            please list them clearly with their key details like time range and description.
            For other queries about specific information, include relevant details from the context.
            
            If no relevant information is found, please state that explicitly."""

            with self.client.messages.stream(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                system=self.prompts["system"],
                messages=[{"role": "user", "content": formatted_prompt}]
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

                # Store in conversation history
                self.conversation_history.append({
                    'query': query,
                    'response': response_content,
                    'context': doc_context
                })

        except Exception as e:
            logger.error(f"Error in stream_query: {str(e)}")
            yield f"Error: {str(e)}"

    def _format_context(self, documents: List[Dict]) -> str:
        """Format retrieved documents into context for Claude"""
        if not documents:
            return "No relevant information found in the knowledge base."
            
        context = "Information from knowledge base:\n\n"
        for doc in documents:
            context += f"{doc['document']['content']}\n\n"
            
        return context

    async def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
