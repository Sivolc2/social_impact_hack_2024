import pandas as pd
import h3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_country_bounds():
    """Return geographical bounds for countries of interest"""
    return {
        'Malawi': {
            'lat_min': -17.0,
            'lat_max': -9.5,
            'lon_min': 32.0,
            'lon_max': 36.0
        },
        # These are approximate bounds - you may want to adjust them
        'Panama': {
            'lat_min': 7.0,
            'lat_max': 10.0,
            'lon_min': -83.0,
            'lon_max': -77.0
        },
        'Ethiopia': {
            'lat_min': 3.0,
            'lat_max': 15.0,
            'lon_min': 33.0,
            'lon_max': 48.0
        },
        'Libya': {
            'lat_min': 19.5,
            'lat_max': 33.0,
            'lon_min': 10.0,
            'lon_max': 25.0
        },
        'Somalia': {
            'lat_min': -1.5,
            'lat_max': 12.0,
            'lon_min': 41.0,
            'lon_max': 51.5
        }
    }

def load_ged_data(csv_path: str, country: str = None) -> pd.DataFrame:
    """Load and preprocess GED CSV data with optional country filtering"""
    logger.info(f"Loading GED data from {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Convert date columns to datetime
    df['date_start'] = pd.to_datetime(df['date_start'])
    df['year'] = df['date_start'].dt.year
    
    # Filter for years 2001-2015
    df = df[(df['year'] >= 2001) & (df['year'] <= 2015)]
    
    # Country-specific filtering
    if country:
        if country == 'Malawi':
            bounds = get_country_bounds()['Malawi']
            df = df[
                (df['latitude'] >= bounds['lat_min']) & 
                (df['latitude'] <= bounds['lat_max']) &
                (df['longitude'] >= bounds['lon_min']) & 
                (df['longitude'] <= bounds['lon_max'])
            ]
        else:
            df = df[df['country'] == country]
            
        logger.info(f"Filtered data for {country}, {len(df)} events remaining")
    
    # Ensure latitude and longitude are numeric
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Drop rows with invalid coordinates
    df = df.dropna(subset=['latitude', 'longitude'])
    
    return df

def aggregate_by_h3(df: pd.DataFrame, resolution: int = 3) -> Dict[str, Any]:
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

def convert_ged_to_h3(input_path: str, output_path: str, resolution: int = 3, country: str = None):
    """Convert GED CSV to H3-aggregated GeoJSON for specific country"""
    try:
        # Load and process data
        df = load_ged_data(input_path, country)
        
        # Modify output path to include country name if specified
        if country:
            output_path = str(Path(output_path).parent / f"ged_h3_{country.lower()}.geojson")
        
        # Aggregate by H3
        geojson = aggregate_by_h3(df, resolution)
        
        # Add country to metadata
        if country:
            geojson['metadata']['country'] = country
            geojson['metadata']['bounds'] = get_country_bounds()[country]
        
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
    parser.add_argument('--resolution', type=int, default=3,
                      help='H3 resolution (0-15)')
    parser.add_argument('--country', choices=['Panama', 'Malawi', 'Ethiopia', 'Libya', 'Somalia'],
                      help='Country to filter data for')
    
    args = parser.parse_args()
    
    # Process each country if none specified, otherwise process only the specified country
    if args.country:
        convert_ged_to_h3(args.input, args.output, args.resolution, args.country)
    else:
        for country in ['Panama', 'Malawi', 'Ethiopia', 'Libya', 'Somalia']:
            convert_ged_to_h3(args.input, args.output, args.resolution, country)
