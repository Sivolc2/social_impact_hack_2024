from flask import Flask, render_template, jsonify, url_for, request
from src.services.map_service import MapService
from src.services.dataset_service import DatasetService
from dotenv import load_dotenv
import os
from datetime import datetime
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__, 
    static_folder='static',  # Add static folder configuration
    template_folder='templates'
)
map_service = MapService()
dataset_service = DatasetService()

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/api/map/base')
def get_base_map():
    """Return base map configuration"""
    return jsonify(map_service.get_base_map_config())

@app.route('/api/map/policy/water_management')
def get_policy_data():
    try:
        # Get timestamp from query parameter or use current time
        timestamp_str = request.args.get('timestamp')
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()
        
        # Example coordinates for Sub-Saharan Africa
        center_lat = 8.7832
        center_lng = 34.5085
        
        data = map_service.generate_hexagon_data(center_lat, center_lng, timestamp)
        
        # Validate data before returning
        if not data or not data.get('features'):
            app.logger.error("Generated data is empty or invalid")
            return jsonify({"error": "Failed to generate valid data"}), 500
            
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Error generating policy data: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/map/update_view', methods=['POST'])
def update_map_view():
    # Implementation for updating map view
    pass

@app.route('/api/data/layers', methods=['GET'])
def get_available_layers():
    # Implementation for getting available layers
    pass

@app.route('/api/export-data', methods=['GET'])
def export_data():
    try:
        # Get current map data from your data service
        data = data_agent.get_current_data()  # You'll need to implement this method
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.debug = True
    
    app.run() 