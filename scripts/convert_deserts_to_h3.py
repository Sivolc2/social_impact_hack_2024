import geopandas as gpd
import h3
import json
import logging
from pathlib import Path
from shapely.geometry import shape, mapping
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_desert_data(geojson_path: str) -> gpd.GeoDataFrame:
    """Load and preprocess desert GeoJSON data"""
    logger.info(f"Loading desertification data from {geojson_path}")
    
    try:
        gdf = gpd.read_file(geojson_path)
        logger.info(f"Loaded {len(gdf)} features")
        return gdf
    except Exception as e:
        logger.error(f"Error loading desert data: {e}")
        raise

def aggregate_by_h3(gdf: gpd.GeoDataFrame, resolution: int = 3) -> Dict[str, Any]:
    """Aggregate desert data by H3 cells"""
    logger.info(f"Aggregating data using H3 resolution {resolution}")
    
    # Convert to EPSG:4326 if needed
    if gdf.crs != 'EPSG:4326':
        gdf = gdf.to_crs(epsg=4326)
    
    # Pre-filter with Somalia boundary
    from utils.geo_filter import load_country_boundary
    somalia_boundary = load_country_boundary('Somalia')
    somalia_gdf = gpd.GeoDataFrame(geometry=[somalia_boundary], crs='EPSG:4326')
    gdf = gpd.overlay(gdf, somalia_gdf, how='intersection')
    logger.info(f"Filtered to {len(gdf)} features intersecting Somalia")
    
    # Collect all H3 cells
    h3_cells = set()  # Use set to avoid duplicates
    for idx, row in gdf.iterrows():
        try:
            # Convert polygon to GeoJSON format and extract coordinates
            geojson = mapping(row.geometry)
            coords = geojson['coordinates'][0]  # Get exterior ring coordinates
            
            # Get H3 cells for this polygon
            cells = h3.polyfill_polygon(coords, resolution)
            h3_cells.update(cells)
            
        except Exception as e:
            logger.warning(f"Error processing feature {idx}: {e}")
            logger.debug(f"Geometry type: {row.geometry.geom_type}")
            continue
    
    logger.info(f"Generated {len(h3_cells)} unique H3 cells")
    
    # Create features for each H3 cell
    features = []
    for h3_index in h3_cells:
        try:
            # Get hexagon boundary
            boundary = h3.cell_to_boundary(h3_index)
            hex_polygon = gpd.GeoDataFrame(
                geometry=[gpd.GeoSeries([shape({
                    'type': 'Polygon',
                    'coordinates': [[[vertex[1], vertex[0]] for vertex in boundary]]
                })])[0]], 
                crs='EPSG:4326'
            )
            
            # Intersect with original data
            intersection = gpd.overlay(gdf, hex_polygon, how='intersection')
            
            if not intersection.empty:
                # Calculate metrics for the hexagon
                metrics = {
                    'desertification_index': float(intersection['DI'].mean()) if 'DI' in intersection.columns else None,
                    'desertification_index2': float(intersection['DI2'].mean()) if 'DI2' in intersection.columns else None,
                    'land_suitability': intersection['LU_Suitabi'].mode().iloc[0] if 'LU_Suitabi' in intersection.columns else None,
                    'degradation_type': intersection['Deg_Type_1'].mode().iloc[0] if 'Deg_Type_1' in intersection.columns else None,
                    'degradation_condition': intersection['Deg_Condit'].mode().iloc[0] if 'Deg_Condit' in intersection.columns else None,
                    'area_km2': float(intersection.geometry.area.sum() / 1_000_000)  # Convert to km²
                }
                
                # Create feature
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[[vertex[1], vertex[0]] for vertex in boundary]]
                    },
                    'properties': {
                        'h3_index': h3_index,
                        'metrics': metrics
                    }
                }
                features.append(feature)
                
        except Exception as e:
            logger.warning(f"Error processing H3 cell {h3_index}: {e}")
            continue
    
    logger.info(f"Created {len(features)} features with metrics")
    
    # Create GeoJSON structure
    geojson = {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'dataset': 'Somalia Desertification Data',
            'cell_count': len(features),
            'h3_resolution': resolution,
            'metrics': {
                'desertification_index': {
                    'name': 'Desertification Index',
                    'description': 'Primary desertification index',
                },
                'desertification_index2': {
                    'name': 'Secondary Desertification Index',
                    'description': 'Secondary measure of desertification',
                },
                'area_km2': {
                    'name': 'Area',
                    'description': 'Area covered in square kilometers',
                    'unit': 'km²'
                }
            }
        }
    }
    
    return geojson

def convert_deserts_to_h3(input_path: str, output_path: str, resolution: int = 3):
    """Convert desert GeoJSON to H3-aggregated GeoJSON"""
    try:
        # Load and process data
        gdf = load_desert_data(input_path)
        
        # Aggregate by H3
        geojson = aggregate_by_h3(gdf, resolution)
        
        # Save output
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f)
        
        logger.info(f"Successfully saved H3 aggregated data to {output_path}")
        
    except Exception as e:
        logger.error(f"Error converting desert data to H3: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert desert GeoJSON to H3-aggregated GeoJSON')
    parser.add_argument('--input', default='scripts/data/deserts_somalia_raw.geojson',
                      help='Input desert GeoJSON file path')
    parser.add_argument('--output', default='data/deserts_h3_somalia.geojson',
                      help='Output GeoJSON file path')
    parser.add_argument('--resolution', type=int, default=3,
                      help='H3 resolution (0-15)')
    
    args = parser.parse_args()
    convert_deserts_to_h3(args.input, args.output, args.resolution) 