from typing import List
import os
from dotenv import load_dotenv
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import requests
from typing import Optional

class VectorDB:
    def __init__(self):
        # Initialize the sentence transformer model
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.texts = []

    def add_text(self, *texts: List[str]):
        """Add texts to the vector store"""
        self.texts = texts
        # Convert texts to embeddings
        embeddings = self.encoder.encode(texts)
        # Initialize FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        # Add vectors to the index
        self.index.add(np.array(embeddings).astype('float32'))

    def search(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Search for similar texts given a query"""
        # Convert query to embedding
        query_embedding = self.encoder.encode([query])
        # Search in FAISS index
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), k)
        
        # Return results with distances
        results = [(self.texts[idx], dist) for idx, dist in zip(indices[0], distances[0])]
        return results

class Completions:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv('FETCH_ACCESS_TOKEN')
        if not self.api_key:
            raise ValueError("FETCH_ACCESS_TOKEN not found in environment variables")
            
        self.base_url = "https://api.fetch.ai/chat/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat(self, message: str, context: Optional[List[str]] = None) -> str:
        """Send a chat message to Fetch.ai endpoint"""
        payload = {
            "message": message,
            "context": context if context else []
        }
        
        response = requests.post(
            f"{self.base_url}/completions",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["response"]

# Example usage:
if __name__ == "__main__":
    # Initialize vector store
    vector_store = VectorDB()
    
    # Add some example texts
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language",
    ]
    vector_store.add_text(*texts)
    
    # Query the vector store
    query = "What is AI?"
    results = vector_store.search(query)
        
    # Print results
    for text, distance in results:
        print(f"Text: {text}")
        print(f"Distance: {distance}\n")

    # Example of using FetchAIChat
    completions = Completions()
    try:
        response = completions.chat("What is artificial intelligence?")
        print("\nFetch.ai Response:")
        print(response)
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Fetch.ai: {e}")
