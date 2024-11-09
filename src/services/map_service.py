import pydeck as pdk
import pandas as pd
import geopandas as gpd
from typing import Dict, Any, List
import os
import json
from .policy_service import PolicyService

class MapService:
    def __init__(self):
        self.policy_service = PolicyService()
        # Define default view state
        self.default_view_state = {
            "latitude": 8.7832,
            "longitude": 34.5085,
            "zoom": 4,
            "pitch": 45,
            "bearing": 0
        }

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