import pydeck as pdk
import pandas as pd
import geopandas as gpd
from typing import Dict, Any, List
import os
import json

class MapService:
    def __init__(self):
        # You should set this in your environment variables
        self.mapbox_api_key = os.getenv('MAPBOX_API_KEY', '')
        self.default_view_state = pdk.ViewState(
            latitude=48.8566,  # Paris coordinates for better initial view
            longitude=2.3522,
            zoom=11,
            pitch=0,
            bearing=0
        )
        self.active_layers = []

    def create_base_map(self) -> Dict[str, Any]:
        """Create a base map with default settings"""
        # Use proper Mapbox style URL
        mapbox_style = "mapbox://styles/mapbox/light-v11"
        
        deck = pdk.Deck(
            map_provider="mapbox",
            map_style=mapbox_style,
            initial_view_state=self.default_view_state,
            layers=[],
            api_keys={"mapbox": self.mapbox_api_key}
        )
        
        # Convert to dictionary instead of JSON string
        return {
            "initialViewState": {
                "latitude": self.default_view_state.latitude,
                "longitude": self.default_view_state.longitude,
                "zoom": self.default_view_state.zoom,
                "pitch": self.default_view_state.pitch,
                "bearing": self.default_view_state.bearing
            },
            "layers": [],
            "mapStyle": mapbox_style,
            "mapProvider": "mapbox"
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
        self.default_view_state.latitude = latitude
        self.default_view_state.longitude = longitude
        if zoom:
            self.default_view_state.zoom = zoom
        return self.default_view_state.to_json()