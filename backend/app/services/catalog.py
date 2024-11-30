from typing import List, Dict, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class DataCatalog:
    def __init__(self):
        self.data_path = Path(__file__).parent.parent / "data" / "data_catalogue.json"
        self.datasets = self._load_datasets()

    def _load_datasets(self) -> Dict:
        try:
            logger.debug(f"Loading catalog from: {self.data_path}")
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                logger.debug(f"Loaded {len(data.get('datasets_available', []))} datasets")
                return data
        except Exception as e:
            logger.error(f"Error loading catalog: {str(e)}")
            return {"datasets_available": []}

    def get_dataset_by_id(self, dataset_id: str) -> Optional[Dict]:
        """Get a dataset by its ID"""
        try:
            for dataset in self.datasets.get("datasets_available", []):
                if dataset.get("id") == dataset_id:
                    logger.debug(f"Found dataset {dataset_id}: {dataset}")
                    return dataset
            logger.warning(f"Dataset not found: {dataset_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting dataset {dataset_id}: {str(e)}")
            return None

    def get_all_datasets(self) -> List[Dict]:
        """Get all available datasets"""
        return self.datasets.get("datasets_available", [])

    def search_datasets(self, query: str) -> List[Dict]:
        """Search datasets by query string"""
        query = query.lower()
        return [
            dataset for dataset in self.get_all_datasets()
            if query in dataset.get("name", "").lower() or 
               query in dataset.get("description", "").lower() or
               query in dataset.get("text", "").lower()
        ]