from typing import List, Dict, Optional, Callable
import numpy as np
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize vector store with a sentence transformer model"""
        try:
            self.encoder = SentenceTransformer(model_name)
            logger.info("Successfully initialized SentenceTransformer")
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformer: {str(e)}")
            raise RuntimeError(f"Could not initialize vector store: {str(e)}")
            
        self.documents = []
        self.embeddings = None

    def add_documents(self, documents: List[Dict[str, str]]):
        """Add text chunks to the vector store"""
        logger.info(f"Adding {len(documents)} text chunks to vector store")
        
        # Store documents with their raw content
        self.documents = documents
        
        # Create embeddings for the document content
        texts = [doc['content'] for doc in documents]
        self.embeddings = self.encoder.encode(texts)
        
        logger.info(f"Created embeddings of shape {self.embeddings.shape}")

    def search_by_metadata(self, filters: Dict[str, str]) -> List[Dict]:
        """Search documents by metadata fields"""
        matching_docs = []
        
        for idx, doc in enumerate(self.documents):
            metadata = doc.get('metadata', {})
            if all(metadata.get(k) == v for k, v in filters.items()):
                matching_docs.append({
                    'document': doc,
                    'score': 1.0  # Exact metadata match
                })
        
        return matching_docs

    def similarity_search(self, query: str, k: int = 3, filter: Optional[Callable] = None) -> List[Dict]:
        """Search for similar documents"""
        # Create query embedding
        query_embedding = self.encoder.encode([query])[0]
        
        # Calculate similarities
        similarities = cosine_similarity(
            [query_embedding], 
            self.embeddings
        )[0]
        
        # Get document indices sorted by similarity
        doc_scores = list(enumerate(similarities))
        
        # Apply metadata filter if provided
        if filter:
            doc_scores = [
                (i, score) for i, score in doc_scores 
                if filter(self.documents[i])
            ]
        
        # Sort by score
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k documents with their scores
        results = []
        for idx, score in doc_scores[:k]:
            doc = self.documents[idx]
            
            # Include metadata in results
            results.append({
                'document': doc,
                'score': float(score),
                'metadata': doc.get('metadata', {})
            })
        
        return results

    def get_relevant_context(self, query: str, max_docs: int = 3) -> str:
        """
        Get relevant context as a formatted string for RAG
        """
        similar_docs = self.similarity_search(query, k=max_docs)
        
        if not similar_docs:
            return "No relevant information found in the knowledge base."
            
        context = "Relevant information from knowledge base:\n\n"
        for i, doc in enumerate(similar_docs, 1):
            content = doc['document']['content']
            metadata = doc['document'].get('metadata', {})
            score = doc['score']
            
            context += f"[{i}] {content}\n"
            if metadata:
                context += f"Source: {metadata.get('source', 'Unknown')}\n"
                if 'temporal_range' in metadata:
                    context += f"Time Range: {metadata['temporal_range']}\n"
            context += f"Relevance: {score:.2f}\n\n"
            
        return context