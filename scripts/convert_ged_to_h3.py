import pandas as pd
import h3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_ged_data(csv_path: str) -> pd.DataFrame:
    """Load and preprocess GED CSV data"""
    logger.info(f"Loading GED data from {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Convert date columns to datetime
    df['date_start'] = pd.to_datetime(df['date_start'])
    df['year'] = df['date_start'].dt.year
    
    # Filter for years 2001-2015
    df = df[(df['year'] >= 2001) & (df['year'] <= 2015)]
    logger.info(f"Filtered data to years 2001-2015, {len(df)} events remaining")
    
    # Ensure latitude and longitude are numeric
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Drop rows with invalid coordinates
    df = df.dropna(subset=['latitude', 'longitude'])
    
    return df

def aggregate_by_h3(df: pd.DataFrame, resolution: int = 6) -> Dict[str, Any]:
    """Aggregate GED data by H3 cells and year"""
    logger.info(f"Aggregating data using H3 resolution {resolution}")
    
    # Initialize storage for features
    features = []
    hexagon_data = {}
    
    # Fixed year range
    years = list(range(2001, 2016))  # 2001 to 2015 inclusive
    
    # Process each row
    for _, row in df.iterrows():
        try:
            # Get H3 index for the location
            h3_index = h3.latlng_to_cell(row['latitude'], row['longitude'], resolution)
            year = int(row['year'])
            
            # Create key for year and h3 combination
            key = (h3_index, year)
            
            if key not in hexagon_data:
                hexagon_data[key] = {
                    'incident_count': 0,
                    'deaths_total': 0,
                    'deaths_civilians': 0,
                    'deaths_military': 0,
                    'countries': set(),
                    'types_of_violence': set()
                }
            
            # Aggregate data
            data = hexagon_data[key]
            data['incident_count'] += 1
            data['deaths_total'] += row['best'] if pd.notna(row['best']) else 0
            data['deaths_civilians'] += row['deaths_civilians'] if pd.notna(row['deaths_civilians']) else 0
            data['deaths_military'] += (
                (row['deaths_a'] if pd.notna(row['deaths_a']) else 0) + 
                (row['deaths_b'] if pd.notna(row['deaths_b']) else 0)
            )
            data['countries'].add(row['country'])
            data['types_of_violence'].add(str(row['type_of_violence']))
            
        except Exception as e:
            logger.warning(f"Error processing row: {e}")
            continue
    
    # Get all unique H3 cells
    unique_h3_cells = set(h3_index for h3_index, _ in hexagon_data.keys())
    
    # Create features for each hexagon for all years (including years with no events)
    for h3_index in unique_h3_cells:
        for year in years:
            key = (h3_index, year)
            
            # Get data if exists, otherwise use empty data
            data = hexagon_data.get(key, {
                'incident_count': 0,
                'deaths_total': 0,
                'deaths_civilians': 0,
                'deaths_military': 0,
                'countries': set(),
                'types_of_violence': set()
            })
            
            try:
                # Get cell boundary
                boundary = h3.cell_to_boundary(h3_index)
                coordinates = [[[vertex[1], vertex[0]] for vertex in boundary]]
                coordinates[0].append(coordinates[0][0])  # Close the polygon
                
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
                            'incident_count': data['incident_count'],
                            'deaths_total': data['deaths_total'],
                            'deaths_civilians': data['deaths_civilians'],
                            'deaths_military': data['deaths_military'],
                            'countries': list(data['countries']),
                            'types_of_violence': list(data['types_of_violence'])
                        }
                    }
                }
                features.append(feature)
                
            except Exception as e:
                logger.warning(f"Error creating feature for {h3_index}: {e}")
                continue
    
    # Create GeoJSON structure
    geojson = {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'dataset': 'UCDP Georeferenced Event Dataset',
            'cell_count': len(unique_h3_cells),
            'year_count': len(years),
            'h3_resolution': resolution,
            'temporal_range': {
                'start': min(years),
                'end': max(years),
                'interval': 'yearly'
            },
            'metrics': {
                'incident_count': {
                    'name': 'Incident Count',
                    'description': 'Number of conflict events',
                    'unit': 'count'
                },
                'deaths_total': {
                    'name': 'Total Deaths',
                    'description': 'Total number of deaths',
                    'unit': 'count'
                },
                'deaths_civilians': {
                    'name': 'Civilian Deaths',
                    'description': 'Number of civilian deaths',
                    'unit': 'count'
                },
                'deaths_military': {
                    'name': 'Military Deaths',
                    'description': 'Number of military deaths (side A + side B)',
                    'unit': 'count'
                }
            }
        }
    }
    
    return geojson

def convert_ged_to_h3(input_path: str, output_path: str, resolution: int = 6):
    """Convert GED CSV to H3-aggregated GeoJSON"""
    try:
        # Load and process data
        df = load_ged_data(input_path)
        
        # Aggregate by H3
        geojson = aggregate_by_h3(df, resolution)
        
        # Save output
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f)
        
        logger.info(f"Successfully saved H3 aggregated data to {output_path}")
        
    except Exception as e:
        logger.error(f"Error converting GED to H3: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert GED CSV to H3-aggregated GeoJSON')
    parser.add_argument('--input', default='preprocessing/data/GEDEvent_v24_1.csv',
                      help='Input GED CSV file path')
    parser.add_argument('--output', default='data/ged_h3_aggregated.geojson',
                      help='Output GeoJSON file path')
    parser.add_argument('--resolution', type=int, default=6,
                      help='H3 resolution (0-15)')
    
    args = parser.parse_args()
    convert_ged_to_h3(args.input, args.output, args.resolution) 