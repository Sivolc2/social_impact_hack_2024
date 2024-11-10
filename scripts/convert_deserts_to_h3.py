import geopandas as gpd
import pandas as pd
import h3
import json
import logging
from pathlib import Path
from datetime import datetime
from shapely.geometry import shape, mapping
from typing import Dict, Any

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_desert_data(geojson_path: str) -> gpd.GeoDataFrame:
    """Load and preprocess desert GeoJSON data"""
    logger.info(f"Loading desertification data from {geojson_path}")
    
    try:
        gdf = gpd.read_file(geojson_path)
        
        # Convert relevant columns to appropriate types
        if 'DI' in gdf.columns:
            gdf['DI'] = pd.to_numeric(gdf['DI'], errors='coerce')
        if 'DI2' in gdf.columns:
            gdf['DI2'] = pd.to_numeric(gdf['DI2'], errors='coerce')
            
        return gdf
    except Exception as e:
        logger.error(f"Error loading desert data: {e}")
        raise

def aggregate_by_h3(gdf: gpd.GeoDataFrame, resolution: int = 3) -> Dict[str, Any]:
    """Aggregate desert data by H3 cells"""
    logger.info(f"Aggregating data using H3 resolution {resolution}")
    
    features = []
    hexagon_data = {}
    
    # Debug info about input data
    logger.debug(f"Input GeoDataFrame CRS: {gdf.crs}")
    logger.debug(f"Number of input features: {len(gdf)}")
    logger.debug(f"Geometry types: {gdf.geometry.geom_type.unique()}")
    
    # First convert to EPSG:4326 if not already
    if gdf.crs != 'EPSG:4326':
        gdf = gdf.to_crs(epsg=4326)
        logger.debug("Converted GeoDataFrame to EPSG:4326")
    
    # Get Somalia boundary first
    from utils.geo_filter import load_country_boundary
    somalia_boundary = load_country_boundary('Somalia')
    logger.debug(f"Loaded Somalia boundary: {somalia_boundary.wkt[:100]}...")
    
    # Ensure boundary is also in EPSG:4326
    somalia_gdf = gpd.GeoDataFrame(geometry=[somalia_boundary], crs='EPSG:4326')
    
    # Pre-filter the data to Somalia's boundary
    gdf = gpd.overlay(gdf, somalia_gdf, how='intersection')
    logger.debug(f"Pre-filtered to {len(gdf)} features intersecting Somalia")
    
    # Process each geometry in the GeoDataFrame
    for idx, row in gdf.iterrows():
        geom = row.geometry
        try:
            # Handle MultiPolygon vs Polygon
            if geom.geom_type == 'MultiPolygon':
                polygons = [p for p in geom.geoms]
            else:
                polygons = [geom]
            
            logger.debug(f"Processing feature {idx} with {len(polygons)} polygons")
            
            for poly in polygons:
                # Get exterior coordinates and any interior (holes) coordinates
                exterior_coords = [[coord[0], coord[1]] for coord in poly.exterior.coords[:-1]]  # Skip last point (duplicate)
                interior_coords = []
                for interior in poly.interiors:
                    interior_coords.append([[coord[0], coord[1]] for coord in interior.coords[:-1]])
                
                # Create polygon in h3 format - note the nested array structure
                h3_polygon = {
                    'type': 'Polygon',
                    'coordinates': [exterior_coords] + interior_coords
                }
                
                try:
                    # Get H3 cells covering this polygon
                    h3_cells = h3.polygon_to_cells(h3_polygon, resolution)
                    logger.debug(f"Generated {len(h3_cells)} H3 cells for polygon")
                except Exception as e:
                    logger.warning(f"Error generating H3 cells: {e}")
                    logger.debug(f"Polygon coordinates: {h3_polygon}")
                    continue
                
                for h3_index in h3_cells:
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
            logger.warning(f"Error processing geometry {idx}: {str(e)}")
            logger.debug(f"Problematic geometry: {geom.wkt[:100]}...")
            continue
    
    logger.info(f"Generated {len(features)} H3 features")
    
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