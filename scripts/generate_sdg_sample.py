import h3
import json
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_panama_sdg_data():
    """Generate sample SDG 15.3.1 data for Panama using H3 grid"""
    
    # Panama's approximate bounding box
    bounds = {
        'min_lat': 7.2,
        'max_lat': 9.6,
        'min_lng': -83.0,
        'max_lng': -77.2
    }
    
    # Use H3 resolution 6 for reasonable cell size
    resolution = 6
    
    # Generate base hexagons covering Panama
    hexagons = set()
    for lat in np.arange(bounds['min_lat'], bounds['max_lat'], 0.1):
        for lng in np.arange(bounds['min_lng'], bounds['max_lng'], 0.1):
            hex_id = h3.latlng_to_cell(lat, lng, resolution)
            hexagons.add(hex_id)
    
    logger.info(f"Generated {len(hexagons)} hexagons covering Panama")
    
    # Create features with simulated land degradation data
    features = []
    
    # Parameters for generating realistic patterns
    center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
    center_lng = (bounds['min_lng'] + bounds['max_lng']) / 2
    
    for hex_id in hexagons:
        try:
            # Get cell center
            cell_center = h3.cell_to_latlng(hex_id)
            
            # Generate realistic degradation patterns
            # Distance from center affects degradation (simulating higher degradation near urban areas)
            dist_from_center = np.sqrt(
                (cell_center[0] - center_lat)**2 + 
                (cell_center[1] - center_lng)**2
            )
            
            # Add some random variation
            random_factor = np.random.normal(0, 0.1)
            
            # Calculate degradation value (0-1 scale)
            # Higher values indicate more degradation
            degradation_value = min(1.0, max(0.0,
                0.3 + # base degradation
                0.4 * (1 - dist_from_center/3) + # distance effect
                random_factor # random variation
            ))
            
            # Calculate component values
            productivity_trend = -0.5 * degradation_value + random_factor
            soil_carbon = 100 * (1 - degradation_value) + np.random.normal(0, 5)
            
            # Get boundary coordinates
            boundary = h3.cell_to_boundary(hex_id)
            coordinates = [[[vertex[1], vertex[0]] for vertex in boundary]]
            coordinates[0].append(coordinates[0][0])  # Close the polygon
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': coordinates
                },
                'properties': {
                    'h3_index': hex_id,
                    'degradation_value': float(degradation_value),
                    'productivity_trend': float(productivity_trend),
                    'soil_carbon': float(soil_carbon),
                    'timestamp': datetime.now().isoformat()
                }
            }
            features.append(feature)
            
        except Exception as e:
            logger.warning(f"Error processing hexagon {hex_id}: {e}")
            continue
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'dataset': 'SDG 15.3.1 Land Degradation',
            'region': 'Panama',
            'cell_count': len(features),
            'h3_resolution': resolution,
            'generated_at': datetime.now().isoformat(),
            'bounds': bounds
        }
    }
    
    # Save to file
    output_path = 'data/sdg_panama_sample.geojson'
    with open(output_path, 'w') as f:
        json.dump(geojson, f)
    
    logger.info(f"Saved dataset to {output_path}")
    return output_path

if __name__ == "__main__":
    generate_panama_sdg_data() 