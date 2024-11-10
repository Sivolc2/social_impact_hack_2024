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
        try:
            if dataset_id == "sdg-15-3-1":
                data = self.map_service.load_sdg_sample()
                if not data or not data.get('features'):
                    logger.error("No features found in SDG sample data")
                    return {"error": "No data available"}
                
                # Ensure metrics are properly structured in properties
                for feature in data['features']:
                    if isinstance(feature.get('properties', {}).get('metrics'), str):
                        # If metrics is a string, parse it
                        try:
                            feature['properties']['metrics'] = json.loads(feature['properties']['metrics'])
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse metrics JSON for feature {feature.get('properties', {}).get('h3_index')}")
                    
                    # Ensure all required metrics exist with default values
                    if 'metrics' not in feature['properties']:
                        feature['properties']['metrics'] = {}
                    
                    metrics = feature['properties']['metrics']
                    for metric in ['land_degradation', 'soil_organic_carbon', 'vegetation_cover', 'biodiversity_index']:
                        if metric not in metrics:
                            metrics[metric] = 0.0
                
                logger.info(f"Loaded SDG dataset with {len(data['features'])} features")
                return data
            
            # Add other dataset handlers here
            logger.warning(f"Unknown dataset ID: {dataset_id}")
            return {"error": "Dataset not found"}
            
        except Exception as e:
            logger.error(f"Error loading dataset {dataset_id}: {e}")
            return {"error": f"Error loading dataset: {str(e)}"}