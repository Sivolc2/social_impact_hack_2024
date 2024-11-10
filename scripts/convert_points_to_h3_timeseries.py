import json
import h3
from datetime import datetime
from pathlib import Path
import logging
from utils.geo_filter import filter_geojson_by_country

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_point_geojson(input_path: str) -> dict:
    """Load point-based GeoJSON file"""
    with open(input_path, 'r') as f:
        return json.load(f)

def convert_to_h3_timeseries(point_geojson: dict, start_year: int = 2001, end_year: int = 2015) -> dict:
    """Convert point-based GeoJSON to H3-based timeseries GeoJSON"""
    
    # Get unique H3 cells and their values
    h3_values = {}
    for feature in point_geojson['features']:
        h3_index = feature['properties']['h3_cell']
        value = feature['properties']['value']
        h3_values[h3_index] = value

    # Create features for each H3 cell for each year
    features = []
    years = range(start_year, end_year + 1)
    
    for h3_index, value in h3_values.items():
        # Get cell boundary
        try:
            boundary = h3.cell_to_boundary(h3_index)
            # Convert to GeoJSON coordinate format (lon, lat) and close the polygon
            coordinates = [[[vertex[1], vertex[0]] for vertex in boundary]]
            coordinates[0].append(coordinates[0][0])
            
            # Create a feature for each year
            for year in years:
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': coordinates
                    },
                    'properties': {
                        'h3_index': h3_index,
                        'year': year,
                        'timestamp': datetime(year, 1, 1).isoformat(),
                        'metrics': {
                            'desertification': value
                        }
                    }
                }
                features.append(feature)
                
        except Exception as e:
            logger.warning(f"Error processing H3 cell {h3_index}: {e}")
            continue

    # Create output GeoJSON structure
    output_geojson = {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'dataset': 'Desertification Data',
            'cell_count': len(h3_values),
            'year_count': len(years),
            'h3_resolution': 3,
            'temporal_range': {
                'start': min(years),
                'end': max(years),
                'interval': 'yearly'
            },
            'metrics': {
                'desertification': {
                    'name': 'Desertification',
                    'description': 'Desertification indicator value',
                    'unit': 'binary'
                }
            }
        }
    }
    
    return output_geojson

def convert_points_to_h3_timeseries(input_path: str, output_path: str, country: str = None):
    """Main function to convert point GeoJSON to H3 timeseries GeoJSON"""
    try:
        # Load input data
        point_geojson = load_point_geojson(input_path)
        
        # Filter by country if specified
        if country:
            point_geojson = filter_geojson_by_country(point_geojson, country)
        
        # Convert to H3 timeseries format
        h3_geojson = convert_to_h3_timeseries(point_geojson)
        
        # Modify output path to include country name if specified
        if country:
            output_path = str(Path(output_path).parent / f"{Path(output_path).stem}_{country.lower()}{Path(output_path).suffix}")
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save output
        with open(output_path, 'w') as f:
            json.dump(h3_geojson, f)
            
        logger.info(f"Successfully converted and saved H3 timeseries data to {output_path}")
        
    except Exception as e:
        logger.error(f"Error converting points to H3 timeseries: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert point GeoJSON to H3 timeseries GeoJSON')
    parser.add_argument('--input', required=True,
                      help='Input point GeoJSON file path')
    parser.add_argument('--output', required=True,
                      help='Output H3 timeseries GeoJSON file path')
    parser.add_argument('--country', choices=['Somalia'],  # Add more countries as boundary data becomes available
                      help='Country to filter data for')
    
    args = parser.parse_args()
    
    convert_points_to_h3_timeseries(args.input, args.output, args.country)