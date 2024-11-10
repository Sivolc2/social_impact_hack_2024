from typing import List, Dict
import numpy as np
from pathlib import Path
import json
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        try:
            self.encoder = SentenceTransformer(model_name)
            logger.info("Successfully initialized SentenceTransformer")
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformer: {str(e)}")
            raise RuntimeError(f"Could not initialize vector store: {str(e)}")
        self.documents: List[Dict] = []
        self.embeddings = None

    def add_documents(self, documents: List[Dict[str, str]]):
        """
        Add documents to the vector store
        documents: List of dicts with 'content' and 'metadata' keys
        """
        logger.info(f"Adding {len(documents)} documents to vector store")
        self.documents.extend(documents)
        texts = [doc['content'] for doc in documents]
        
        # Create embeddings
        new_embeddings = self.encoder.encode(texts)
        logger.info(f"Created embeddings of shape {new_embeddings.shape}")
        
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        logger.info(f"Vector store now contains {len(self.documents)} documents")

    def similarity_search(self, query: str, k: int = 3) -> List[Dict]:
        """
        Search for similar documents using cosine similarity
        """
        # 1. Convert query to vector
        query_embedding = self.encoder.encode([query])
        
        # 2. Compare with stored document vectors
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # 3. Return top k matches
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        return [
            {
                'document': self.documents[i],
                'score': float(similarities[i])
            }
            for i in top_k_indices
        ]

    def search_by_metadata(self, metadata_filter: Dict) -> List[Dict]:
        """
        Search documents by metadata fields
        metadata_filter: Dict of metadata field-value pairs to match
        """
        matching_docs = []
        
        for idx, doc in enumerate(self.documents):
            if all(doc['metadata'].get(k) == v for k, v in metadata_filter.items()):
                matching_docs.append({
                    'document': doc,
                    'score': 1.0  # Full match on metadata
                })
                
        return matching_docs