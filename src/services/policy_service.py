import h3
import json
import random
import math
from typing import Dict, List

class PolicyService:
    def __init__(self):
        # H3 resolution (0-15). Resolution 6 gives cells ~36km² which is good for regional view
        self.h3_resolution = 6

    def generate_water_management_policy_data(self) -> Dict:
        # Multiple center points for different clusters
        centers = [
            (8.7832, 34.5085),    # Original center
            (12.5, 36.2),         # North cluster
            (5.2, 31.8),          # Southwest cluster
            (7.9, 38.2)           # Southeast cluster
        ]
        
        # Generate impact data for each hexagon
        policy_data = {
            "type": "FeatureCollection",
            "features": []
        }
        
        # Impact metrics with more varied colors
        impact_levels = {
            "critical": {"color": "#ff1744", "weight": 0.9},    # Deep Red
            "high": {"color": "#ff4444", "weight": 0.7},        # Red
            "medium-high": {"color": "#ff8a65", "weight": 0.5}, # Orange-Red
            "medium": {"color": "#ffbb33", "weight": 0.4},      # Orange
            "medium-low": {"color": "#79c879", "weight": 0.3},  # Light Green
            "low": {"color": "#00C851", "weight": 0.2},         # Green
            "minimal": {"color": "#00e676", "weight": 0.1}      # Bright Green
        }

        # Process each center
        processed_hexagons = set()
        
        for center_lat, center_lng in centers:
            center_hex = h3.latlng_to_cell(center_lat, center_lng, self.h3_resolution)
            
            # Random radius between 5 and 12 for each cluster
            radius = random.randint(5, 12)
            affected_hexagons = h3.grid_disk(center_hex, radius)
            
            for hex_id in affected_hexagons:
                if hex_id not in processed_hexagons:
                    processed_hexagons.add(hex_id)
                    
                    # Convert H3 index to polygon coordinates
                    boundary = h3.cell_to_boundary(hex_id)
                    polygon_coords = [[coord[1], coord[0]] for coord in boundary]
                    polygon_coords.append(polygon_coords[0])
                    
                    # Calculate distance from center for this specific cluster
                    distance = h3.grid_distance(center_hex, hex_id)
                    
                    # Add some randomness to impact levels
                    random_factor = random.uniform(0.8, 1.2)
                    normalized_distance = (distance * random_factor) / radius
                    
                    # Determine impact level with more variation
                    if normalized_distance <= 0.2:
                        impact = "critical"
                    elif normalized_distance <= 0.35:
                        impact = "high"
                    elif normalized_distance <= 0.5:
                        impact = "medium-high"
                    elif normalized_distance <= 0.65:
                        impact = "medium"
                    elif normalized_distance <= 0.8:
                        impact = "medium-low"
                    elif normalized_distance <= 0.9:
                        impact = "low"
                    else:
                        impact = "minimal"
                    
                    # Add random variation to metrics
                    base_hectares = 500
                    base_communities = 12
                    base_efficiency = 85
                    
                    random_multiplier = random.uniform(0.7, 1.3)
                    weight = impact_levels[impact]["weight"] * random_multiplier
                    
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "h3_index": str(hex_id),
                            "impact_level": impact,
                            "color": impact_levels[impact]["color"],
                            "metrics": {
                                "hectares_restored": round(base_hectares * weight),
                                "communities_affected": round(base_communities * weight),
                                "cost_efficiency": f"{round(base_efficiency * weight)}%"
                            }
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [polygon_coords]
                        }
                    }
                    policy_data["features"].append(feature)
        
        return policy_data

    def get_water_management_policy(self) -> Dict:
        """Returns the water management policy data for Sub-Saharan Africa"""
        return self.generate_water_management_policy_data()