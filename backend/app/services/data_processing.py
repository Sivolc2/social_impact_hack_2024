import h3
import json
import geopandas as gpd
from shapely.geometry import shape, mapping
from pathlib import Path

class DataProcessor:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"

    def load_geojson(self, filename: str) -> dict:
        file_path = self.data_dir / filename
        with open(file_path) as f:
            return json.load(f)

    @staticmethod
    def geometry_to_h3(geometry: dict, resolution: int = 9) -> list:
        """Convert a GeoJSON geometry to H3 hexagons"""
        geom = shape(geometry)
        polygons = []
        if geom.geom_type == 'MultiPolygon':
            polygons.extend(geom.geoms)
        else:
            polygons.append(geom)
        
        h3_hexagons = set()
        for polygon in polygons:
            points = h3.polyfill(
                mapping(polygon),
                resolution,
                geo_json_conformant=True
            )
            h3_hexagons.update(points)
        
        return list(h3_hexagons)

    def process_geospatial_data(self, filename: str, resolution: int = 9):
        """Process GeoJSON file into H3 hexagons"""
        try:
            geojson_data = self.load_geojson(filename)
            
            all_hexagons = []
            for feature in geojson_data['features']:
                hexagons = self.geometry_to_h3(
                    feature['geometry'],
                    resolution
                )
                all_hexagons.extend(hexagons)
            
            # Convert H3 indexes to GeoJSON
            hex_features = []
            for h3_index in all_hexagons:
                boundary = h3.h3_to_geo_boundary(h3_index, geo_json=True)
                hex_features.append({
                    "type": "Feature",
                    "properties": {
                        "h3_index": h3_index,
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [boundary]
                    }
                })
            
            return {
                "type": "FeatureCollection",
                "features": hex_features
            }
            
        except Exception as e:
            raise Exception(f"Error processing geospatial data: {str(e)}") 