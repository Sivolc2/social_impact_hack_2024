from flask import Flask, render_template, jsonify
from src.services.map_service import MapService
from src.services.data_agent import DataAgent
from src.services.dataset_service import DatasetService
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
map_service = MapService()
data_agent = DataAgent()
dataset_service = DatasetService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/map/base')
def get_base_map():
    """Return base map configuration"""
    return jsonify(map_service.create_base_map())

@app.route('/api/map/update_view', methods=['POST'])
def update_map_view():
    # Implementation for updating map view
    pass

@app.route('/api/data/layers', methods=['GET'])
def get_available_layers():
    # Implementation for getting available layers
    pass

if __name__ == '__main__':
    app.run(debug=True) 