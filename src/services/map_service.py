import pydeck as pdk
import pandas as pd
import geopandas as gpd
from typing import Dict, Any, List
import os
import json
from .policy_service import PolicyService
import h3
import random
import numpy as np
from datetime import datetime, timedelta
import logging
import rasterio
from rasterio.warp import transform_bounds
from typing import Tuple, List

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MapService:
    def __init__(self):
        self.policy_service = PolicyService()
        # Define default view state centered on Sahara Desert
        self.default_view_state = {
            "latitude": 25.3345,
            "longitude": 15.2504,
            "zoom": 4,
            "pitch": 0,
            "bearing": 0
        }
        # Updated color scheme for better visualization of improvement
        self.impact_colors = {
            'Critical Impact': '#d32f2f',  # Darker red
            'High Impact': '#f57c00',      # Orange
            'Medium Impact': '#ffd700',     # Yellow
            'Low Impact': '#7cb342',        # Light green
            'Minimal Impact': '#2e7d32'     # Dark green
        }
        self.impact_levels = list(self.impact_colors.keys())
        logger.info("MapService initialized with %d impact levels", len(self.impact_levels))

    def get_base_map_config(self):
        """Return base map configuration"""
        return {
            "mapStyle": "mapbox://styles/mapbox/satellite-v9",
            "initialViewState": self.default_view_state
        }

    def get_policy_data(self, policy_id: str = "water_management"):
        """Get policy data for visualization"""
        try:
            if policy_id == "water_management":
                return self.policy_service.get_water_management_policy()
            return None
        except Exception as e:
            print(f"Error in get_policy_data: {str(e)}")  # For debugging
            raise e

    def create_base_map(self) -> Dict[str, Any]:
        """Create a base map with default settings"""
        return {
            "initialViewState": {
                "latitude": self.default_view_state["latitude"],
                "longitude": self.default_view_state["longitude"],
                "zoom": self.default_view_state["zoom"],
                "pitch": self.default_view_state["pitch"],
                "bearing": self.default_view_state["bearing"]
            },
            "mapStyle": "mapbox://styles/mapbox/satellite-v9",
            "projection": "globe"
        }

    def create_scatter_layer(self, data: pd.DataFrame, 
                           color_scale: List[str] = None,
                           opacity: float = 0.8,
                           radius: int = 100) -> pdk.Layer:
        """Create a scatter plot layer from DataFrame"""
        return pdk.Layer(
            'ScatterplotLayer',
            data=data,
            get_position=['longitude', 'latitude'],
            get_color=color_scale or [200, 30, 0, 160],
            get_radius=radius,
            opacity=opacity,
        )

    def create_heatmap_layer(self, data: pd.DataFrame,
                            weight_column: str,
                            opacity: float = 0.8) -> pdk.Layer:
        """Create a heatmap layer from DataFrame"""
        return pdk.Layer(
            'HeatmapLayer',
            data=data,
            get_position=['longitude', 'latitude'],
            get_weight=weight_column,
            opacity=opacity,
        )

    def update_view_state(self, latitude: float, longitude: float, 
                         zoom: int = None) -> Dict[str, Any]:
        """Update the map view state"""
        self.default_view_state["latitude"] = latitude
        self.default_view_state["longitude"] = longitude
        if zoom:
            self.default_view_state["zoom"] = zoom
        return self.default_view_state

    def _generate_cell_pattern(self, h3_index: str, timestamp: datetime) -> dict:
        """Generate dynamic impact patterns for each H3 cell based on time and location"""
        try:
            # Get cell coordinates for spatial wave effect
            cell_center = h3.cell_to_latlng(h3_index)
            
            # Use longitude for wave progression (west to east)
            base_longitude = 34.5085  # Center longitude
            longitude_diff = cell_center[1] - base_longitude
            
            # Calculate spatial phase (longitude-based)
            spatial_phase = longitude_diff * 0.5  # Adjust multiplier to control wave width
            
            # Calculate temporal phase (0-2π over the year)
            if timestamp.tzinfo is not None:
                timestamp = timestamp.replace(tzinfo=None)
            year_start = datetime(timestamp.year, 1, 1)
            days_in_year = (timestamp - year_start).days
            time_phase = (2 * np.pi * days_in_year) / 365
            
            # Combine spatial and temporal phases for wave effect
            combined_phase = time_phase + spatial_phase
            
            # Generate wave pattern (0-1)
            wave = (np.sin(combined_phase) + 1) / 2
            
            # Add some randomness (10% random variation)
            cell_seed = int(h3_index[-4:], 16)
            random.seed(cell_seed)
            random_factor = random.random() * 0.1
            
            # Make the combined factor more stable but still animated
            combined_factor = (wave * 0.3) + (random_factor * 0.1) + 0.6  # Base value of 0.6
            
            # Map to impact level with smoother transition
            simplified_impacts = [
                'Critical Impact',
                'High Impact',
                'Medium Impact',
                'Low Impact',
                'Minimal Impact'
            ]
            
            index = min(int(combined_factor * len(simplified_impacts)), len(simplified_impacts) - 1)
            impact_level = simplified_impacts[index]
            
            # Calculate metrics with more stable base values
            base_hectares = 2000
            max_additional_hectares = 2000
            hectares = int(base_hectares + combined_factor * max_additional_hectares)
            
            base_communities = 100
            max_additional_communities = 100
            communities = int(base_communities + combined_factor * max_additional_communities)
            
            base_efficiency = 80
            max_additional_efficiency = 15
            efficiency = int(base_efficiency + combined_factor * max_additional_efficiency)
            
            # Ensure impact_level is valid
            if impact_level not in self.impact_colors:
                impact_level = self.impact_levels[0]  # Use first level as default
                
            # Always return a valid hex color
            color = self.impact_colors[impact_level]
            if not color.startswith('#'):
                color = '#' + color
                
            return {
                'impact_level': impact_level,
                'color': color,  # Ensure this is a valid hex color
                'metrics': {
                    'hectares_restored': hectares,
                    'communities_affected': communities,
                    'cost_efficiency': f"{efficiency}%"
                }
            }
        except Exception as e:
            logger.error(f"Error in _generate_cell_pattern for hex {h3_index}: {str(e)}")
            # Return a valid default color
            return {
                'impact_level': self.impact_levels[0],
                'color': '#ff0000',  # Fallback to red
                'metrics': {
                    'hectares_restored': 1000,
                    'communities_affected': 50,
                    'cost_efficiency': "70%"
                }
            }

    def generate_hexagon_data(self, center_lat: float, center_lng: float, timestamp: datetime) -> dict:
        """Generate GeoJSON with dynamic H3 cell data"""
        try:
            logger.debug(f"Generating hexagon data for lat={center_lat}, lng={center_lng}, time={timestamp}")
            
            # Generate base hexagon grid using updated H3 functions
            resolution = 5
            center_hex = h3.latlng_to_cell(center_lat, center_lng, resolution)
            # Use grid_disk instead of grid_ring to include center cell
            hexagons = h3.grid_disk(center_hex, 2)  # Changed from grid_ring
            logger.debug(f"Generated {len(hexagons)} hexagons")
            
            features = []
            for hex_id in hexagons:
                try:
                    # Get cell pattern for this timestamp
                    cell_data = self._generate_cell_pattern(hex_id, timestamp)
                    
                    # Get hex boundary using updated function
                    boundary = h3.cell_to_boundary(hex_id)
                    
                    # Create properly formatted coordinates array
                    coordinates = [[[vertex[1], vertex[0]] for vertex in boundary]]
                    # Close the polygon by repeating the first point
                    coordinates[0].append(coordinates[0][0])
                    
                    feature = {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Polygon',
                            'coordinates': coordinates
                        },
                        'properties': {
                            'h3_index': hex_id,
                            'impact_level': cell_data['impact_level'],
                            'color': cell_data['color'],
                            'metrics': cell_data['metrics']
                        }
                    }
                    features.append(feature)
                    
                except Exception as e:
                    logger.error(f"Error processing hexagon {hex_id}: {str(e)}")
                    continue
            
            geojson = {
                'type': 'FeatureCollection',
                'features': features
            }
            
            # Validate GeoJSON structure
            if not features:
                raise ValueError("No features generated")
            
            logger.debug(f"Successfully generated GeoJSON with {len(features)} features")
            return geojson
            
        except Exception as e:
            logger.error(f"Error generating hexagon data: {str(e)}")
            # Return a valid but empty GeoJSON object in case of error
            return {
                'type': 'FeatureCollection',
                'features': []
            }

    def tiff_to_h3_cells(self, tiff_path: str, resolution: int = 5) -> dict:
        """Convert a TIFF file to H3 cells with values"""
        try:
            with rasterio.open(tiff_path) as dataset:
                logger.info(f"TIFF CRS: {dataset.crs}")
                bounds = dataset.bounds  # Store bounds here
                logger.info(f"TIFF Bounds: {bounds}")
                logger.info(f"TIFF Transform: {dataset.transform}")

                # Read the data and get the transformation parameters
                data = dataset.read(1)  # Read first band
                height, width = data.shape
                
                # Create arrays for row/col coordinates
                rows, cols = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
                
                # Transform pixel coordinates to lat/lon
                xs, ys = rasterio.transform.xy(dataset.transform, rows.flatten(), cols.flatten())
                xs = np.array(xs).reshape((height, width))
                ys = np.array(ys).reshape((height, width))
                
                # If the CRS is not WGS84, transform coordinates
                if str(dataset.crs).upper() != 'EPSG:4326':
                    from rasterio.warp import transform
                    from pyproj import CRS
                    
                    logger.info(f"Converting from {dataset.crs} to EPSG:4326")
                    
                    # Create transformer
                    src_crs = dataset.crs
                    dst_crs = CRS.from_epsg(4326)
                    
                    # Transform bounds to WGS84
                    bounds_lngs, bounds_lats = transform(src_crs, dst_crs, 
                        [bounds.left, bounds.right], 
                        [bounds.bottom, bounds.top])
                    bounds = rasterio.coords.BoundingBox(
                        left=min(bounds_lngs),
                        bottom=min(bounds_lats),
                        right=max(bounds_lngs),
                        top=max(bounds_lats)
                    )
                    
                    # Flatten coordinate arrays for transformation
                    xs_flat = xs.flatten()
                    ys_flat = ys.flatten()
                    
                    # Transform coordinates
                    lngs, lats = transform(src_crs, dst_crs, xs_flat, ys_flat)
                    
                    # Reshape back to grid
                    lngs = np.array(lngs).reshape((height, width))
                    lats = np.array(lats).reshape((height, width))
                    
                    logger.info(f"Transformed bounds: {bounds}")
                else:
                    lngs, lats = xs, ys
                
                # Track processed H3 indices to avoid duplicates
                processed_h3_cells = {}
                
                features = []
                for i in range(height):
                    for j in range(width):
                        if data[i, j] != dataset.nodata and not np.isnan(data[i, j]):
                            # Get coordinates for this pixel
                            lng, lat = float(lngs[i, j]), float(lats[i, j])
                            
                            # Skip if coordinates are invalid
                            if not (-180 <= lng <= 180 and -90 <= lat <= 90):
                                logger.warning(f"Invalid coordinates: lat={lat}, lng={lng}")
                                continue
                            
                            # Get H3 cell for this point
                            try:
                                h3_index = h3.latlng_to_cell(lat, lng, resolution)
                            except Exception as e:
                                logger.warning(f"Failed to create H3 cell for lat={lat}, lng={lng}: {e}")
                                continue
                            
                            # Skip if we've already processed this cell
                            if h3_index in processed_h3_cells:
                                processed_h3_cells[h3_index]['count'] += 1
                                processed_h3_cells[h3_index]['sum'] += data[i, j]
                                continue
                            
                            # Store the initial value for this cell
                            processed_h3_cells[h3_index] = {
                                'sum': data[i, j],
                                'count': 1
                            }
                            
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
                                    'value': float(data[i, j]),
                                    'raw_value': float(data[i, j])
                                }
                            }
                            features.append(feature)
                
                if not features:
                    logger.warning("No valid features generated from TIFF file")
                    return {
                        'type': 'FeatureCollection',
                        'features': [],
                        'metadata': {
                            'error': 'No valid features could be generated from the TIFF file'
                        }
                    }
                
                # Calculate final values and colors for each cell
                min_val = min(cell['sum'] / cell['count'] for cell in processed_h3_cells.values())
                max_val = max(cell['sum'] / cell['count'] for cell in processed_h3_cells.values())
                value_range = max_val - min_val if max_val != min_val else 1.0
                
                for feature in features:
                    h3_index = feature['properties']['h3_index']
                    cell_data = processed_h3_cells[h3_index]
                    avg_value = cell_data['sum'] / cell_data['count']
                    
                    # Normalize value and get color
                    normalized_value = (avg_value - min_val) / value_range
                    color = self._value_to_color(normalized_value)
                    
                    # Update feature properties
                    feature['properties'].update({
                        'value': avg_value,
                        'normalized_value': normalized_value,
                        'color': color
                    })
                
                geojson = {
                    'type': 'FeatureCollection',
                    'features': features,
                    'metadata': {
                        'min_value': float(min_val),
                        'max_value': float(max_val),
                        'cell_count': len(features),
                        'crs': str(dataset.crs),
                        'bounds': {
                            'left': float(bounds.left),
                            'right': float(bounds.right),
                            'top': float(bounds.top),
                            'bottom': float(bounds.bottom)
                        }
                    }
                }
                
                logger.info(f"Processed TIFF to {len(features)} H3 cells")
                logger.info(f"Metadata: {geojson['metadata']}")
                return geojson
                
        except Exception as e:
            logger.error(f"Error processing TIFF file: {str(e)}", exc_info=True)
            raise e

    def _value_to_color(self, normalized_value: float) -> str:
        """Convert a normalized value (0-1) to a color hex string"""
        # You can customize this color scheme
        colors = [
            '#d32f2f',  # red for low values
            '#f57c00',  # orange
            '#ffd700',  # yellow
            '#7cb342',  # light green
            '#2e7d32'   # dark green for high values
        ]
        
        index = min(int(normalized_value * len(colors)), len(colors) - 1)
        return colors[index]

    def load_sdg_sample(self) -> dict:
        """Load and process the SDG 15.3.1 sample dataset"""
        try:
            # Check if file exists
            file_path = 'data/sdg_panama_sample.geojson'
            if not os.path.exists(file_path):
                logger.error(f"SDG sample file not found at {file_path}")
                return {'type': 'FeatureCollection', 'features': []}

            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not data or 'features' not in data:
                logger.error("Invalid data format in SDG sample file")
                return {'type': 'FeatureCollection', 'features': []}

            # Update view state to center on Panama
            self.default_view_state.update({
                "latitude": 8.4,
                "longitude": -80.1,
                "zoom": 7,
                "pitch": 0,
                "bearing": 0
            })
            
            # Process features to ensure proper structure
            for feature in data['features']:
                if 'properties' not in feature:
                    feature['properties'] = {}
                
                # Handle metrics if they're stored as a string
                if isinstance(feature['properties'].get('metrics'), str):
                    try:
                        feature['properties']['metrics'] = json.loads(feature['properties']['metrics'])
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse metrics JSON for feature")
                        feature['properties']['metrics'] = {}
                
                # Ensure metrics exist
                if 'metrics' not in feature['properties']:
                    feature['properties']['metrics'] = {}
                
                metrics = feature['properties']['metrics']
                
                # Add default metrics if missing
                default_metrics = {
                    'land_degradation': 0.0,
                    'soil_organic_carbon': 0.0,
                    'vegetation_cover': 0.0,
                    'biodiversity_index': 0.0
                }
                
                for metric, default_value in default_metrics.items():
                    if metric not in metrics:
                        metrics[metric] = default_value
                
                # Add color based on land degradation (default metric)
                degradation = metrics['land_degradation']
                
                # Assign impact level and color based on degradation value
                if degradation >= 0.8:
                    impact = 'Critical Impact'
                elif degradation >= 0.6:
                    impact = 'High Impact'
                elif degradation >= 0.4:
                    impact = 'Medium Impact'
                elif degradation >= 0.2:
                    impact = 'Low Impact'
                else:
                    impact = 'Minimal Impact'
                
                feature['properties']['impact_level'] = impact
                feature['properties']['color'] = self.impact_colors[impact]
            
            logger.info(f"Successfully loaded SDG sample with {len(data['features'])} features")
            return data
            
        except Exception as e:
            logger.error(f"Error loading SDG sample data: {str(e)}", exc_info=True)
            return {
                'type': 'FeatureCollection',
                'features': []
            }
