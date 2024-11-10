from typing import List, Dict
import numpy as np
from pathlib import Path
import json
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import pickle
import os

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_dir: str = 'cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.embeddings_path = self.cache_dir / 'embeddings.npy'
        self.documents_path = self.cache_dir / 'documents.pkl'
        self.hash_path = self.cache_dir / 'knowledge_base_hash.txt'
        
        try:
            self.encoder = SentenceTransformer(model_name)
            logger.info("Successfully initialized SentenceTransformer")
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformer: {str(e)}")
            raise RuntimeError(f"Could not initialize vector store: {str(e)}")
            
        self.documents: List[Dict] = []
        self.embeddings = None

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _save_cache(self, knowledge_base_path: str):
        """Save embeddings, documents, and file hash to cache"""
        # Save embeddings
        np.save(self.embeddings_path, self.embeddings)
        
        # Save documents
        with open(self.documents_path, 'wb') as f:
            pickle.dump(self.documents, f)
            
        # Save knowledge base hash
        with open(self.hash_path, 'w') as f:
            f.write(self._compute_file_hash(knowledge_base_path))
            
        logger.info("Cached vector store data saved")

    def _load_cache(self) -> bool:
        """Load cached embeddings and documents if they exist"""
        try:
            if (self.embeddings_path.exists() and 
                self.documents_path.exists()):
                self.embeddings = np.load(self.embeddings_path)
                with open(self.documents_path, 'rb') as f:
                    self.documents = pickle.load(f)
                logger.info("Loaded vector store from cache")
                return True
        except Exception as e:
            logger.error(f"Error loading cache: {str(e)}")
        return False

    def _is_cache_valid(self, knowledge_base_path: str) -> bool:
        """Check if cache is valid by comparing file hashes"""
        if not self.hash_path.exists():
            return False
            
        with open(self.hash_path, 'r') as f:
            cached_hash = f.read().strip()
            
        current_hash = self._compute_file_hash(knowledge_base_path)
        return cached_hash == current_hash

    def add_documents(self, documents: List[Dict[str, str]], knowledge_base_path: str = None):
        """
        Add documents to the vector store
        documents: List of dicts with 'content' and 'metadata' keys
        knowledge_base_path: Path to knowledge base file for caching
        """
        if knowledge_base_path and self._is_cache_valid(knowledge_base_path):
            if self._load_cache():
                logger.info("Using cached vector store")
                return
        
        logger.info(f"Adding {len(documents)} documents to vector store")
        self.documents = documents  # Replace existing documents
        texts = [doc['content'] for doc in documents]
        
        # Create embeddings
        self.embeddings = self.encoder.encode(texts)
        logger.info(f"Created embeddings of shape {self.embeddings.shape}")
        
        # Save to cache if knowledge_base_path provided
        if knowledge_base_path:
            self._save_cache(knowledge_base_path)
            
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