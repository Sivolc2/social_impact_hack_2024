import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

class DatasetService:
    def __init__(self):
        self.datasets = self._load_sample_data()
        
    def _load_sample_data(self):
        """Load sample dataset"""
        # Create sample points in San Francisco
        data = {
            'id': range(5),
            'name': ['Park A', 'Park B', 'Park C', 'Park D', 'Park E'],
            'geometry': [
                Point(-122.4194, 37.7749),  # San Francisco
                Point(-122.4099, 37.7850),
                Point(-122.4369, 37.7720),
                Point(-122.4784, 37.7775),
                Point(-122.4071, 37.7835),
            ],
            'green_score': [85, 92, 78, 95, 88]
        }
        
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame(data)
        
        # Convert to format Kepler.gl expects
        return {
            'green_spaces': {
                'fields': [
                    {'name': 'id', 'type': 'integer'},
                    {'name': 'name', 'type': 'string'},
                    {'name': 'latitude', 'type': 'real'},
                    {'name': 'longitude', 'type': 'real'},
                    {'name': 'green_score', 'type': 'real'}
                ],
                'rows': [
                    [row.id, row.name, row.geometry.y, row.geometry.x, row.green_score]
                    for idx, row in gdf.iterrows()
                ]
            }
        }
    
    def get_available_datasets(self):
        """Get list of available datasets"""
        return [
            {
                'id': 'green_spaces',
                'name': 'Green Spaces',
                'data': self.datasets['green_spaces']
            }
        ]