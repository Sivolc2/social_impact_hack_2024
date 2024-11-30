from typing import List, Dict, Optional
import re
import logging
from .catalog import DataCatalog

logger = logging.getLogger(__name__)

class CatalogAgent:
    def __init__(self, catalog: DataCatalog):
        self.catalog = catalog

    async def process_query(self, query: str) -> Dict:
        """
        Process a natural language query and return matching datasets
        Returns a dict with interpretation, matches, and dataset details
        """
        try:
            # Initialize response structure
            result = {
                "interpretation": "",
                "dataset_ids": [],
                "confidence": {},
                "reasoning": {},
                "datasets": []
            }
            
            # Get dataset details for any found matches
            datasets = self.catalog.get_all_datasets()
            for dataset in datasets:
                dataset_id = dataset["id"]
                # Add basic confidence and reasoning (this would be enhanced by LLM)
                result["confidence"][dataset_id] = 0.0
                result["reasoning"][dataset_id] = ""
                
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    def extract_dataset_suggestions(self, llm_response: str) -> List[Dict]:
        """
        Parse LLM response to extract dataset suggestions
        Returns a list of suggested datasets with their details
        """
        suggested_datasets = []
        
        try:
            # Extract dataset IDs using regex pattern [Dataset ID: xxx]
            dataset_ids = re.findall(r'\[Dataset ID:\s*([^\]]+)\]', llm_response)
            
            # Get full dataset details for each suggested ID
            for dataset_id in dataset_ids:
                dataset_id = dataset_id.strip()
                dataset = self.catalog.get_dataset_by_id(dataset_id)
                if dataset:
                    # Extract relevance context for this dataset
                    relevance_context = self._extract_relevance_context(llm_response, dataset_id)
                    
                    suggested_datasets.append({
                        "id": dataset_id,
                        "name": dataset.get("name"),
                        "description": dataset.get("description"),
                        "temporal_range": dataset.get("temporal_range"),
                        "spatial_resolution": dataset.get("spatial_resolution"),
                        "relevance_context": relevance_context
                    })
                else:
                    logger.warning(f"Dataset ID not found in catalog: {dataset_id}")
            
        except Exception as e:
            logger.error(f"Error extracting dataset suggestions: {str(e)}")
        
        return suggested_datasets

    def _extract_relevance_context(self, llm_response: str, dataset_id: str) -> str:
        """
        Extract the context around why a dataset was suggested
        Returns the relevant sentences containing the dataset ID and surrounding context
        """
        try:
            # Split into sentences (basic implementation)
            sentences = re.split(r'[.!?]+\s+', llm_response)
            relevant_sentences = []
            
            # Find sentences containing the dataset ID and include surrounding context
            for i, sentence in enumerate(sentences):
                if dataset_id in sentence:
                    # Include previous sentence for context if available
                    if i > 0:
                        relevant_sentences.append(sentences[i-1])
                    relevant_sentences.append(sentence)
                    # Include next sentence for context if available
                    if i < len(sentences) - 1:
                        relevant_sentences.append(sentences[i+1])
                    
            return ' '.join(relevant_sentences).strip()
            
        except Exception as e:
            logger.error(f"Error extracting relevance context: {str(e)}")
            return ""
