import h3
import json
import numpy as np
from datetime import datetime
import logging
import random
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_trend(values):
    """Calculate trend direction and confidence"""
    if len(values) < 2:
        return 'Stable', 0.0
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(range(len(values)), values)
    
    confidence = abs(r_value)  # Use R-value as confidence measure
    
    if abs(slope) < 0.01:
        return 'Stable', confidence
    elif slope > 0:
        return 'Improving', confidence
    else:
        return 'Degrading', confidence

def calculate_change_rate(values):
    """Calculate annual rate of change"""
    if len(values) < 2:
        return 0.0
    
    total_change = values[-1] - values[0]
    years = len(values) - 1
    return (total_change / years) * 100

def generate_panama_sdg_data():
    """Generate multidimensional SDG 15.3.1 data for Panama using H3 grid for years 2001-2015"""
    
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
            'color_scale': ['#2ecc71', '#e74c3c']  # Green to Red
        },
        'soil_organic_carbon': {
            'name': 'Soil Organic Carbon',
            'description': 'Soil organic carbon content',
            'unit': 'tons/ha',
            'color_scale': ['#fff7fb', '#023858']
        },
        'vegetation_cover': {
            'name': 'Vegetation Cover',
            'description': 'Percentage of vegetation cover',
            'unit': '%',
            'color_scale': ['#ffffe5', '#004529']
        },
        'biodiversity_index': {
            'name': 'Biodiversity Index',
            'description': 'Species diversity index',
            'unit': 'index',
            'color_scale': ['#ffffcc', '#800026']
        }
    }
    
    features = []
    center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
    center_lng = (bounds['min_lng'] + bounds['max_lng']) / 2

    # Generate yearly timestamps from 2001 to 2015
    years = range(2001, 2016)  # 2001 to 2015 inclusive
    timestamps = [datetime(year, 1, 1) for year in years]
    
    logger.info(f"Generating data for {len(timestamps)} years between 2001 and 2015")
    
    # Store historical values for each hexagon
    hexagon_history = {hex_id: {metric: [] for metric in metrics.keys()} 
                      for hex_id in hexagons}
    
    # Generate data for each hexagon at each year
    for hex_id in hexagons:
        cell_center = h3.cell_to_latlng(hex_id)
        boundary = h3.cell_to_boundary(hex_id)
        coordinates = [[[vertex[1], vertex[0]] for vertex in boundary]]
        coordinates[0].append(coordinates[0][0])
        
        # Base values for this hexagon
        dist_from_center = np.sqrt(
            (cell_center[0] - center_lat)**2 + 
            (cell_center[1] - center_lng)**2
        )
        base_random = np.random.normal(0, 0.1)
        
        # Generate data for each year
        for year_idx, timestamp in enumerate(timestamps):
            # Add temporal variation factor (gradual change over years)
            time_progress = year_idx / (len(timestamps) - 1)  # 0 to 1
            temporal_factor = np.sin(time_progress * 2 * np.pi) * 0.2
            
            metric_values = {}
            for metric in metrics.keys():
                random_factor = base_random + np.random.normal(0, 0.05)
                value = min(1.0, max(0.0,
                    0.3 + # base value
                    0.4 * (1 - dist_from_center/3) + # distance effect
                    temporal_factor + # temporal variation
                    random_factor # random variation
                ))
                
                # Scale values according to metric type
                if metric == 'soil_organic_carbon':
                    value = value * 150  # 0-150 tons/ha
                elif metric == 'vegetation_cover':
                    value = value * 100  # 0-100%
                elif metric == 'biodiversity_index':
                    value = value * 10  # 0-10 index
                
                # Store value in history
                hexagon_history[hex_id][metric].append(value)
                
                # Calculate additional statistics if we have enough history
                if year_idx > 0:
                    trend, confidence = calculate_trend(hexagon_history[hex_id][metric])
                    change_rate = calculate_change_rate(hexagon_history[hex_id][metric])
                    
                    # Add statistical values to metrics
                    metric_values[metric] = float(value)
                    metric_values[f"{metric}_trend"] = trend
                    metric_values[f"{metric}_confidence"] = float(confidence)
                    metric_values["change_rate"] = float(change_rate)
                    metric_values["trend"] = trend
                    metric_values["confidence_score"] = float(confidence)
                else:
                    metric_values[metric] = float(value)
                    metric_values[f"{metric}_trend"] = "Insufficient Data"
                    metric_values[f"{metric}_confidence"] = 0.0
                    metric_values["change_rate"] = 0.0
                    metric_values["trend"] = "Insufficient Data"
                    metric_values["confidence_score"] = 0.0
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': coordinates
                },
                'properties': {
                    'h3_index': hex_id,
                    'metrics': metric_values,
                    'timestamp': timestamp.isoformat(),
                    'year': timestamp.year
                }
            }
            features.append(feature)
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'dataset': 'SDG 15.3.1 Land Degradation',
            'region': 'Panama',
            'cell_count': len(hexagons),
            'year_count': len(years),
            'h3_resolution': resolution,
            'temporal_range': {
                'start': timestamps[0].isoformat(),
                'end': timestamps[-1].isoformat(),
                'interval': 'yearly'
            },
            'bounds': bounds,
            'metrics': metrics
        }
    }
    
    output_path = 'data/sdg_panama_sample.geojson'
    with open(output_path, 'w') as f:
        json.dump(geojson, f)
    
    logger.info(f"Saved dataset to {output_path} with {len(features)} total features across {len(years)} years")
    return output_path

if __name__ == "__main__":
    generate_panama_sdg_data()