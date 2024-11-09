class MapService:
    def __init__(self):
        self.active_layers = []
        
    def get_available_layers(self):
        """Get list of available map layers"""
        return [
            {
                'id': 'green_coverage',
                'name': 'Green Coverage',
                'type': 'geojson',
                'visible': True
            }
        ]
    
    def update_layer_state(self, layer_id, state):
        """Update layer visibility and properties"""
        pass 