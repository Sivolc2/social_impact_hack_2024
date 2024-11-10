import h3
import json
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_panama_sdg_data():
    """Generate multidimensional SDG 15.3.1 data for Panama using H3 grid"""
    
    # Panama's approximate bounding box
    bounds = {
        'min_lat': 7.2,
        'max_lat': 9.6,
        'min_lng': -83.0,
        'max_lng': -77.2
    }
    
    resolution = 6
    hexagons = set()
    
    # Generate base hexagons covering Panama
    for lat in np.arange(bounds['min_lat'], bounds['max_lat'], 0.1):
        for lng in np.arange(bounds['min_lng'], bounds['max_lng'], 0.1):
            hex_id = h3.latlng_to_cell(lat, lng, resolution)
            hexagons.add(hex_id)
    
    logger.info(f"Generated {len(hexagons)} hexagons covering Panama")
    
    # Define multiple dimensions/metrics
    metrics = {
        'land_degradation': {
            'name': 'Land Degradation',
            'description': 'Degree of land degradation',
            'unit': 'index',
            'color_scale': ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']  # Green to Red
        },
        'soil_organic_carbon': {
            'name': 'Soil Organic Carbon',
            'description': 'Soil organic carbon content',
            'unit': 'tons/ha',
            'color_scale': ['#fff7fb', '#023858']  # Light to Dark Blue
        },
        'vegetation_cover': {
            'name': 'Vegetation Cover',
            'description': 'Percentage of vegetation cover',
            'unit': '%',
            'color_scale': ['#ffffe5', '#004529']  # Light to Dark Green
        },
        'biodiversity_index': {
            'name': 'Biodiversity Index',
            'description': 'Species diversity index',
            'unit': 'index',
            'color_scale': ['#ffffcc', '#800026']  # Light Yellow to Dark Red
        }
    }
    
    features = []
    center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
    center_lng = (bounds['min_lng'] + bounds['max_lng']) / 2
    
    for hex_id in hexagons:
        try:
            cell_center = h3.cell_to_latlng(hex_id)
            boundary = h3.cell_to_boundary(hex_id)
            coordinates = [[[vertex[1], vertex[0]] for vertex in boundary]]
            coordinates[0].append(coordinates[0][0])
            
            # Generate correlated but distinct values for each metric
            dist_from_center = np.sqrt(
                (cell_center[0] - center_lat)**2 + 
                (cell_center[1] - center_lng)**2
            )
            
            base_random = np.random.normal(0, 0.1)
            metric_values = {}
            
            # Generate somewhat correlated values for each metric
            for metric in metrics.keys():
                random_factor = base_random + np.random.normal(0, 0.05)
                value = min(1.0, max(0.0,
                    0.3 + # base value
                    0.4 * (1 - dist_from_center/3) + # distance effect
                    random_factor # random variation
                ))
                
                # Scale values according to metric type
                if metric == 'soil_organic_carbon':
                    value = value * 150  # 0-150 tons/ha
                elif metric == 'vegetation_cover':
                    value = value * 100  # 0-100%
                elif metric == 'biodiversity_index':
                    value = value * 10  # 0-10 index
                
                metric_values[metric] = float(value)
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': coordinates
                },
                'properties': {
                    'h3_index': hex_id,
                    'metrics': metric_values,
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
            'bounds': bounds,
            'metrics': metrics
        }
    }
    
    output_path = 'data/sdg_panama_sample.geojson'
    with open(output_path, 'w') as f:
        json.dump(geojson, f)
    
    logger.info(f"Saved dataset to {output_path}")
    return output_path

if __name__ == "__main__":
    generate_panama_sdg_data() 