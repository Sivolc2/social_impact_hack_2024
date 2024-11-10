from flask import Flask, render_template, jsonify, url_for, request
from flask_cors import CORS
from src.services.map_service import MapService
from src.services.dataset_service import DatasetService
from src.services.data_agent import data_agent, DataRequest, DataResponse
from dotenv import load_dotenv
import os
from datetime import datetime
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)
CORS(app)

map_service = MapService()
dataset_service = DatasetService()

def detect_category(question: str) -> str:
    question = question.lower()
    
    if any(word in question for word in ['land', 'soil', 'degradation', 'erosion']):
        return 'land_degradation'
    elif any(word in question for word in ['drought', 'water', 'rain', 'precipitation']):
        return 'drought'
    elif any(word in question for word in ['population', 'people', 'community', 'demographic']):
        return 'population'
    
    return 'land_degradation'

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/api/map/base')
def get_base_map():
    return jsonify(map_service.get_base_map_config())

@app.route('/api/map/policy/water_management')
def get_policy_data():
    try:
        timestamp_str = request.args.get('timestamp')
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()
        
        center_lat = 8.7832
        center_lng = 34.5085
        
        data = map_service.generate_hexagon_data(center_lat, center_lng, timestamp)
        
        if not data or not data.get('features'):
            app.logger.error("Generated data is empty or invalid")
            return jsonify({"error": "Failed to generate valid data"}), 500
            
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Error generating policy data: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        question = data.get('question')
        
        # Determine if it's a standardization question
        if any(word in question.lower() for word in ['standard', 'normalize', 'scale']):
            response = DataResponse(
                data_summary="The data visualization uses several standardization methods:",
                source_url="https://www.unccd.int/land-and-life/land-degradation-neutrality/overview",
                confidence_score=0.95,
                methodology_notes="""
                1. Land Degradation data: Normalized to a 0-1 scale where:
                   - 0 represents severely degraded land
                   - 0.5 represents stable land
                   - 1 represents improving land conditions
                   
                2. Drought Risk data: Standardized using a z-score method:
                   - Values are compared to historical averages
                   - Standard deviations from mean indicate severity
                   
                3. Population Impact: Per capita normalization:
                   - Raw numbers converted to percentages
                   - Adjusted for population density
                """
            ).dict()
        else:
            # Default response for other questions
            response = DataResponse(
                data_summary=f"Your question: {question}\nPlease ask about specific aspects of land degradation, drought risk, or population impact.",
                source_url="",
                confidence_score=0.8,
                methodology_notes="Try asking about data standardization, specific regions, or trends over time."
            ).dict()
        
        return jsonify({
            'insights': [
                response['data_summary'],
                f"Confidence Score: {response['confidence_score']}"
            ],
            'recommendations': [
                response['methodology_notes'],
                f"Source: {response['source_url']}"
            ]
        })
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'insights': [f"Error: {str(e)}"],
            'recommendations': ["Please try again with a different question."]
        }), 500

@app.route('/api/export-data', methods=['GET'])
def export_data():
    try:
        data = data_agent.get_current_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=9001)