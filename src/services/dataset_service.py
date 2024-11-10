import json
import logging
from typing import Dict, Any, Optional
from .map_service import MapService

logger = logging.getLogger(__name__)

class DatasetService:
    def __init__(self):
        self.map_service = MapService()
        self.available_datasets = self._load_available_datasets()

    def _load_available_datasets(self) -> Dict[str, Any]:
        """Load available datasets from knowledge base"""
        try:
            with open('data/knowledge_base.json', 'r') as f:
                data = json.load(f)
                return {dataset['id']: dataset for dataset in data['datasets_available']}
        except Exception as e:
            logger.error(f"Error loading datasets: {e}")
            return {}

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset by ID"""
        if dataset_id not in self.available_datasets:
            return None
        return self.available_datasets[dataset_id]

    def load_dataset_for_map(self, dataset_id: str) -> Dict[str, Any]:
        """Load dataset and prepare it for map visualization"""
        if dataset_id == "sdg-15-3-1":
            return self.map_service.load_sdg_sample()
        # Add other dataset handlers here
        return {"error": "Dataset not found"}