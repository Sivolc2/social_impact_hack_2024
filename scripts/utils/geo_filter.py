import geopandas as gpd
from shapely.geometry import shape, Point, Polygon
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_country_boundary(country: str) -> Polygon:
    """Load country boundary from geoBoundaries file"""
    if country.lower() == 'somalia':
        boundary_path = Path("scripts/data/geoBoundaries-SOM-ADM2-all/geoBoundaries-SOM-ADM2.geojson").resolve()
    else:
        raise ValueError(f"Boundary data not available for {country}")
    
    try:
        # Check if file exists
        if not boundary_path.exists():
            raise FileNotFoundError(f"Boundary file not found at {boundary_path}")
            
        # Read the GeoJSON file
        gdf = gpd.read_file(str(boundary_path))
        
        # Dissolve all administrative boundaries into a single polygon
        country_boundary = gdf.dissolve().geometry.iloc[0]
        logger.info(f"Successfully loaded boundary for {country}")
        return country_boundary
    except Exception as e:
        logger.error(f"Error loading boundary for {country}: {e}")
        raise

def filter_geojson_by_country(geojson: dict, country: str) -> dict:
    """Filter GeoJSON features that intersect with country boundary"""
    try:
        # Load country boundary
        country_boundary = load_country_boundary(country)
        
        # Filter features
        filtered_features = []
        for feature in geojson['features']:
            # Convert feature geometry to shape
            feature_shape = shape(feature['geometry'])
            
            # Check if feature intersects with country boundary
            if feature_shape.intersects(country_boundary):
                filtered_features.append(feature)
        
        # Create new GeoJSON with filtered features
        filtered_geojson = geojson.copy()
        filtered_geojson['features'] = filtered_features
        
        # Update metadata if it exists
        if 'metadata' in filtered_geojson:
            filtered_geojson['metadata']['cell_count'] = len(filtered_features)
            filtered_geojson['metadata']['country'] = country
        
        logger.info(f"Filtered GeoJSON to {len(filtered_features)} features for {country}")
        return filtered_geojson
    
    except Exception as e:
        logger.error(f"Error filtering GeoJSON for {country}: {e}")
        raise