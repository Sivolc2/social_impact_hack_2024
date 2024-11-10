from typing import Dict, List, Optional
from .vector_store import VectorStore
from pathlib import Path
import json
import logging
import asyncio
import anthropic
from anthropic import Anthropic
import os
from .summary_agent import SummaryAgent

logger = logging.getLogger(__name__)

class DataAgent:
    def __init__(self):
        """Initialize the data agent with vector store and Claude"""
        self.vector_store = VectorStore()
        self.conversation_history: List[Dict] = []
        self.confidence_threshold = 0.7
        
        # Initialize Claude
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = Anthropic(api_key=api_key)
        
        # Load prompts
        self.prompts = self._load_prompts()
        
        # Add summary agent
        self.summary_agent = SummaryAgent()

    def _load_prompts(self) -> Dict[str, str]:
        """Load all prompt templates from files"""
        prompts_dir = Path(__file__).parent / "prompts"
        prompts = {}
        
        try:
            # Load system prompt
            with open(prompts_dir / "system_prompt.txt", "r") as f:
                prompts["system"] = f.read().strip()
                
            # Load hypothesis prompt
            with open(prompts_dir / "hypothesis_prompt.txt", "r") as f:
                prompts["hypothesis"] = f.read().strip()
                
            # Load query prompt
            with open(prompts_dir / "query_prompt.txt", "r") as f:
                prompts["query"] = f.read().strip()
                
            logger.info("Successfully loaded all prompts")
            return prompts
            
        except Exception as e:
            logger.error(f"Error loading prompts: {str(e)}")
            raise RuntimeError(f"Failed to load prompts: {str(e)}")

    async def initialize(self, knowledge_base_path: str = "data/knowledge_base.txt"):
        """Initialize the agent with knowledge base"""
        try:
            await self.load_knowledge_base(knowledge_base_path)
            logger.info("Data agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize data agent: {str(e)}")
            raise

    async def load_knowledge_base(self, knowledge_base_path: str):
        """Load and index the knowledge base from text file"""
        path = Path(knowledge_base_path)
        
        if not path.exists():
            logger.warning(f"Knowledge base not found at {path}")
            return
            
        try:
            with open(path, 'r') as f:
                content = f.read()
                
            # Split content into dataset blocks
            dataset_blocks = content.split('[DATASET]')[1:]  # Skip empty first split
            
            formatted_docs = []
            for block in dataset_blocks:
                # Parse dataset block
                lines = block.strip().split('\n')
                dataset = {}
                
                current_field = None
                current_value = []
                
                for line in lines:
                    if ':' in line and not line.startswith(' '):
                        # Save previous field if it exists
                        if current_field:
                            dataset[current_field.lower()] = '\n'.join(current_value).strip()
                            current_value = []
                        
                        # Start new field
                        field, value = line.split(':', 1)
                        current_field = field.strip()
                        current_value.append(value.strip())
                    else:
                        # Continue previous field
                        if current_field:
                            current_value.append(line.strip())
                
                # Save last field
                if current_field:
                    dataset[current_field.lower()] = '\n'.join(current_value).strip()
                
                # Format document for vector store
                if dataset:
                    formatted_docs.append({
                        'content': dataset.get('text', dataset.get('description', '')),
                        'metadata': {
                            'source': dataset.get('source', ''),
                            'category': dataset.get('category', ''),
                            'dataset_id': dataset.get('id', ''),
                            'name': dataset.get('name', ''),
                            'temporal_range': dataset.get('temporal_range', ''),
                            'spatial_resolution': dataset.get('spatial_resolution', ''),
                            'variables': dataset.get('variables', '').split(', ')
                        }
                    })
            
            self.vector_store.add_documents(formatted_docs, knowledge_base_path=str(path))
            logger.info(f"Loaded {len(formatted_docs)} documents into vector store")
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            raise

    def _format_context(self, documents: List[Dict]) -> str:
        """Format retrieved documents into context for Claude"""
        context = "Relevant information from our database:\n\n"
        for i, doc in enumerate(documents, 1):
            content = doc['document']['content']
            source = doc['document']['metadata'].get('source', 'Unknown source')
            confidence = doc['score']
            context += f"{i}. {content}\n"
            context += f"   Source: {source}\n"
            context += f"   Confidence: {confidence:.2f}\n\n"
        return context

    async def process_query(self, query: str, context: Optional[Dict] = None, include_summary: bool = False) -> Dict:
        """Process a user query using Claude and vector store"""
        try:
            # Search for relevant documents in vector store
            similar_docs = self.vector_store.similarity_search(query, k=3)
            confident_docs = [doc for doc in similar_docs if doc['score'] >= self.confidence_threshold]
            doc_context = self._format_context(confident_docs)
            
            # Use query prompt template
            formatted_prompt = self.prompts["query"].format(
                context=doc_context,
                query=query
            )
            
            # Create message synchronously
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=self.prompts["system"],
                messages=[{
                    "role": "user",
                    "content": formatted_prompt
                }]
            )
            
            # Extract response text from message
            response_text = message.content[0].text if message and message.content else "No response generated"
            
            # Generate summary table only if include_summary is True
            summary_table = ''
            if include_summary:
                summary_table = await self.summary_agent.create_summary_table(response_text)
                summary_table = self.summary_agent.format_html_table(summary_table)
            
            return {
                'response': response_text,
                'summary_table': summary_table,
                'confidence': confident_docs[0]['score'] if confident_docs else 0.5,
                'supporting_docs': confident_docs,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'response': f"I apologize, but I encountered an error processing your request: {str(e)}",
                'summary_table': '',
                'confidence': 0.0,
                'supporting_docs': [],
                'status': 'error'
            }

    async def get_dataset_recommendations(self) -> List[Dict]:
        """Get dataset recommendations based on conversation history"""
        if not self.conversation_history:
            return []
            
        # Get recent queries
        recent_queries = [
            conv['query']
            for conv in self.conversation_history[-3:]
        ]
        
        # Search for relevant datasets
        recommendations = []
        for query in recent_queries:
            docs = self.vector_store.similarity_search(query, k=2)
            for doc in docs:
                dataset_id = doc['document']['metadata'].get('dataset_id')
                if dataset_id and doc['score'] > 0.6:
                    recommendations.append({
                        'dataset_id': dataset_id,
                        'relevance_score': doc['score'],
                        'description': doc['document']['content']
                    })
                    
        return recommendations

    def get_conversation_history(self) -> List[Dict]:
        """Return the conversation history"""
        return self.conversation_history

    async def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []

    async def process_hypothesis_query(self, query: str) -> Dict:
        """
        Process a hypothesis query and return relevant datasets and unavailable data.
        Uses vector store to find relevant datasets from knowledge base.
        """
        try:
            # Search for relevant datasets in vector store
            similar_docs = self.vector_store.similarity_search(query, k=3)
            
            response = {
                "relevant_datasets": [],
                "unavailable_data": [],
                "suggestions": []
            }
            
            # Process matching documents
            for doc in similar_docs:
                if doc['score'] >= self.confidence_threshold:
                    dataset_info = doc['document']['metadata']
                    if dataset_info.get('category') == 'dataset':
                        response["relevant_datasets"].append({
                            "name": dataset_info.get('name'),
                            "description": doc['document']['content'],
                            "source": dataset_info.get('source'),
                            "temporal_range": dataset_info.get('temporal_range'),
                            "confidence_score": doc['score']
                        })
            
            # Add suggestions for potential data gaps
            if not response["relevant_datasets"]:
                response["suggestions"].append({
                    "type": "Data Gap",
                    "message": "No directly relevant datasets found. Consider expanding search criteria."
                })
                
                # Use Claude to suggest potential useful datasets
                suggestion_prompt = f"""Based on the hypothesis: "{query}"
                What types of environmental data would be most useful but are not currently available?
                Please suggest 1-2 specific types of data."""
                
                suggestion_response = await self._get_claude_suggestions(suggestion_prompt)
                if suggestion_response:
                    response["unavailable_data"].extend(suggestion_response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing hypothesis query: {str(e)}")
            return {
                "relevant_datasets": [],
                "unavailable_data": [],
                "suggestions": [{"type": "Error", "message": str(e)}]
            }

    async def _get_claude_suggestions(self, query: str) -> List[Dict]:
        """Get suggestions for unavailable but useful data from Claude"""
        try:
            # Use hypothesis prompt template
            formatted_prompt = self.prompts["hypothesis"].format(query=query)
            
            # Create message synchronously
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": formatted_prompt
                }]
            )
            
            # Extract response text from message
            response_text = message.content[0].text if message and message.content else ""
            
            # Parse Claude's response into structured suggestions
            suggestions = []
            for line in response_text.split('\n'):
                if line.strip():
                    suggestions.append({
                        "type": "Suggested Dataset",
                        "reason": line.strip()
                    })
            return suggestions[:2]  # Return top 2 suggestions
            
        except Exception as e:
            logger.error(f"Error getting Claude suggestions: {str(e)}")
            return []

    def get_available_datasets(self) -> List[Dict]:
        """Return list of all available datasets from vector store"""
        try:
            # Search for all documents with category 'dataset'
            all_datasets = self.vector_store.search_by_metadata({"category": "dataset"})
            
            return [{
                "name": doc['document']['metadata'].get('name'),
                "description": doc['document']['content'],
                "source": doc['document']['metadata'].get('source'),
                "temporal_range": doc['document']['metadata'].get('temporal_range')
            } for doc in all_datasets]
            
        except Exception as e:
            logger.error(f"Error getting available datasets: {str(e)}")
            return []
