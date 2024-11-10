import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from .map_service import MapService

logger = logging.getLogger(__name__)

class DatasetService:
    def __init__(self):
        self.map_service = MapService()
        self.available_datasets = self._load_available_datasets()
        self.geojson_cache = {}

    def _load_available_datasets(self) -> Dict[str, Any]:
        """Load available datasets from knowledge base"""
        try:
            with open('data/knowledge_base.json', 'r') as f:
                data = json.load(f)
                return {dataset['id']: dataset for dataset in data['datasets_available']}
        except Exception as e:
            logger.error(f"Error loading datasets: {e}")
            return {}

    def load_all_geojson_datasets(self) -> List[Dict[str, Any]]:
        """Load all GeoJSON files from the data directory"""
        try:
            data_dir = Path('data')
            datasets = []
            
            # Load each GeoJSON file
            for geojson_file in data_dir.glob('*.geojson'):
                try:
                    if geojson_file.name not in self.geojson_cache:
                        with open(geojson_file, 'r') as f:
                            data = json.load(f)
                            self.geojson_cache[geojson_file.name] = data
                    
                    datasets.append({
                        'id': geojson_file.stem,
                        'data': self.geojson_cache[geojson_file.name]
                    })
                    logger.info(f"Loaded dataset: {geojson_file.name}")
                except Exception as e:
                    logger.error(f"Error loading {geojson_file}: {e}")
                    continue
            
            return datasets
            
        except Exception as e:
            logger.error(f"Error loading GeoJSON datasets: {e}")
            return []

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset by ID"""
        if dataset_id not in self.available_datasets:
            return None
        return self.available_datasets[dataset_id]

    def load_dataset_for_map(self, dataset_id: str) -> Dict[str, Any]:
        """Load dataset and prepare it for map visualization"""
        try:
            # Try to load from GeoJSON files first
            data_path = Path('data') / f"{dataset_id}.geojson"
            if data_path.exists():
                if dataset_id not in self.geojson_cache:
                    with open(data_path, 'r') as f:
                        data = json.load(f)
                        self.geojson_cache[dataset_id] = data
                return self.geojson_cache[dataset_id]
            
            # Fallback to legacy loading method
            if dataset_id == "sdg-15-3-1":
                data = self.map_service.load_sdg_sample()
                if not data or not data.get('features'):
                    logger.error("No features found in SDG sample data")
                    return {"error": "No data available"}
                return data
            
            logger.warning(f"Unknown dataset ID: {dataset_id}")
            return {"error": "Dataset not found"}
            
        except Exception as e:
            logger.error(f"Error loading dataset {dataset_id}: {e}")
            return {"error": f"Error loading dataset: {str(e)}"}