from flask import Flask, render_template, jsonify, url_for
from src.services.map_service import MapService
from src.services.dataset_service import DatasetService
from src.services.policy_service import PolicyService
from dotenv import load_dotenv
import os

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

@app.route('/api/map/policy/<policy_id>')
def get_policy_data(policy_id):
    try:
        policy_data = map_service.get_policy_data(policy_id)
        if policy_data is None:
            return jsonify({"error": "Policy not found"}), 404
        return jsonify(policy_data)
    except Exception as e:
        print(f"Error processing policy data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/map/update_view', methods=['POST'])
def update_map_view():
    # Implementation for updating map view
    pass

@app.route('/api/data/layers', methods=['GET'])
def get_available_layers():
    # Implementation for getting available layers
    pass

if __name__ == '__main__':
    app.debug = True
    app.run() 