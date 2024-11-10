from typing import Dict, List, Optional
from .vector_store import VectorStore
from pathlib import Path
import json
import logging
import asyncio
import anthropic
from anthropic import Anthropic
import os

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
        
        # System prompt for environmental data analysis
        self.system_prompt = """You are an expert environmental data analyst assistant. 
        Your role is to help users understand environmental data, particularly focusing on:
        - Land degradation and soil health
        - Forest coverage and deforestation
        - Climate impact assessment
        - Environmental policy analysis
        
        When responding:
        1. Be precise with data interpretations
        2. Cite sources when available
        3. Explain confidence levels in your analysis
        4. Suggest related datasets when relevant
        5. Use scientific terminology appropriately
        """

    async def initialize(self, knowledge_base_path: str = "data/knowledge_base.json"):
        """Initialize the agent with knowledge base"""
        try:
            await self.load_knowledge_base(knowledge_base_path)
            logger.info("Data agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize data agent: {str(e)}")
            raise

    async def load_knowledge_base(self, knowledge_base_path: str):
        """Load and index the knowledge base"""
        path = Path(knowledge_base_path)
        
        if not path.exists():
            logger.warning(f"Knowledge base not found at {path}")
            return
            
        with open(path, 'r') as f:
            documents = json.load(f)
            
        formatted_docs = [
            {
                'content': doc['text'],
                'metadata': {
                    'source': doc.get('source', ''),
                    'category': doc.get('category', ''),
                    'dataset_id': doc.get('dataset_id', '')
                }
            }
            for doc in documents
        ]
        
        self.vector_store.add_documents(formatted_docs)

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

    async def process_query(self, 
                          query: str, 
                          context: Optional[Dict] = None) -> Dict:
        """
        Process a user query using Claude and vector store
        """
        # Get relevant documents
        similar_docs = self.vector_store.similarity_search(query, k=3)
        
        # Filter by confidence threshold
        confident_docs = [
            doc for doc in similar_docs 
            if doc['score'] >= self.confidence_threshold
        ]
        
        # Format context from retrieved documents
        doc_context = self._format_context(confident_docs)
        
        try:
            logger.debug(f"Sending query to Claude: {query}")
            logger.debug(f"With context: {doc_context}")
            
            # Get response from Claude with correct message format
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                system=self.system_prompt,  # System prompt goes here instead
                messages=[
                    {
                        "role": "user",
                        "content": f"""Context: {doc_context}

Question: {query}

Please provide a detailed response that:
1. Directly answers the question
2. References relevant data points from the context
3. Explains your confidence level
4. Suggests related areas to explore"""
                    }
                ]
            )
            
            logger.debug(f"Got response from Claude: {response}")
            
            claude_response = response.content[0].text
            
            logger.debug(f"Extracted text: {claude_response}")
            
            # Format final response
            result = {
                'response': claude_response,
                'confidence': confident_docs[0]['score'] if confident_docs else 0.5,
                'supporting_docs': confident_docs,
                'status': 'success',
                'metadata': {
                    'source': confident_docs[0]['document']['metadata'].get('source') if confident_docs else None,
                    'category': confident_docs[0]['document']['metadata'].get('category') if confident_docs else None,
                    'dataset_id': confident_docs[0]['document']['metadata'].get('dataset_id') if confident_docs else None
                }
            }

        except Exception as e:
            logger.error(f"Error getting response from Claude: {str(e)}")
            result = {
                'response': "I apologize, but I encountered an error processing your request.",
                'confidence': 0.0,
                'supporting_docs': [],
                'status': 'error',
                'metadata': {}
            }

        # Update conversation history
        self.conversation_history.append({
            'query': query,
            'response': result,
            'context': context
        })

        return result

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
