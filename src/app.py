from flask import Flask, render_template, jsonify, url_for, request, Response, stream_with_context, send_from_directory
from flask_cors import CORS
from src.services.map_service import MapService
from src.services.dataset_service import DatasetService
from src.services.data_agent import DataAgent
from dotenv import load_dotenv
import os
from datetime import datetime
import traceback
from werkzeug.utils import secure_filename
import json
import logging
from pydantic import BaseModel
import asyncio
from functools import wraps
from .services.analysis_agent import AnalysisAgent

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Define the models that were previously imported
class DataRequest(BaseModel):
    question: str
    context: dict = None

class DataResponse(BaseModel):
    data_summary: str
    source_url: str
    confidence_score: float
    methodology_notes: str = ""

# Load environment variables
load_dotenv()

# Add this after load_dotenv()
if not os.getenv('ANTHROPIC_API_KEY'):
    logger.warning("ANTHROPIC_API_KEY not found in environment variables")

def validate_environment():
    required_vars = ['MAPBOX_API_KEY', 'ANTHROPIC_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise EnvironmentError(error_msg)

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)
CORS(app)

# Validate environment variables
validate_environment()

map_service = MapService()
dataset_service = DatasetService()

# Helper function to run async code in Flask
def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

# Initialize agents
try:
    data_agent = DataAgent()
    asyncio.run(data_agent.initialize("data/knowledge_base.json"))
    analysis_agent = AnalysisAgent()
    logger.info("Agents initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize agents: {str(e)}")
    raise

# Debug log for API key presence
logger.debug(f"ANTHROPIC_API_KEY present: {'ANTHROPIC_API_KEY' in os.environ}")

def validate_mapbox_token(token):
    if not token:
        return False
    if token == 'your_actual_mapbox_token_here':
        return False
    if not token.startswith('pk.eyJ1'):  # Basic format check for public tokens
        return False
    return True

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    message_history = data.get('history', [])
    current_mode = data.get('mode', 'data')
    
    def generate():
        try:
            if current_mode == 'data':
                response = asyncio.run(data_agent.process_query(user_message))
                if response.get('error'):
                    yield f"data: {json.dumps({'chunk': response['response'], 'error': True})}\n\n"
                else:
                    yield f"data: {json.dumps({'chunk': response['response']})}\n\n"
            else:
                for chunk in analysis_agent.stream_analysis(user_message):
                    if chunk:
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}")
            error_message = "I apologize, but I'm having trouble connecting to my knowledge base. Please check the API configuration."
            yield f"data: {json.dumps({'chunk': error_message, 'error': True})}\n\n"
    
    return Response(
        stream_with_context(generate()), 
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Content-Type': 'text/event-stream',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/export-data', methods=['GET'])
@async_route
async def export_data():
    try:
        recommendations = await data_agent.get_dataset_recommendations()
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    mapbox_token = os.getenv('MAPBOX_API_KEY')
    if not validate_mapbox_token(mapbox_token):
        logger.error("Invalid MAPBOX_API_KEY configuration")
        return "Error: Invalid Mapbox token configuration. Please check your .env file.", 500
    return render_template('base.html', mapbox_token=mapbox_token)

@app.route('/api/map/base')
def get_base_map():
    return jsonify(map_service.get_base_map_config())

@app.route('/api/map/policy/water_management')
def get_water_management_policy():
    try:
        timestamp_str = request.args.get('timestamp')
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()
            
        # Load the SDG sample data with the timestamp
        data = map_service.load_sdg_sample()
        
        # Update the features with time-based patterns
        if data and 'features' in data:
            for feature in data['features']:
                h3_index = feature['properties']['h3_index']
                pattern = map_service._generate_cell_pattern(h3_index, timestamp)
                
                # Debug log for color values
                logger.debug(f"Generated color for hex {h3_index}: {pattern.get('color')}")
                
                # Ensure color is present and valid
                if 'color' not in pattern or not pattern['color'].startswith('#'):
                    pattern['color'] = '#ff0000'  # Default to red if invalid
                    
                feature['properties'].update(pattern)
        
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in get_water_management_policy: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process_hypothesis', methods=['POST'])
def process_hypothesis():
    data = request.get_json()
    hypothesis = data.get('hypothesis')
    
    if not hypothesis:
        return jsonify({'error': 'No hypothesis provided'}), 400
        
    result = data_agent.process_hypothesis_query(hypothesis)
    return jsonify(result)

@app.route('/send-to-map', methods=['POST'])
def send_to_map():
    try:
        dataset_service = DatasetService()
        datasets = dataset_service.load_all_geojson_datasets()
        
        # Ensure each dataset has the required structure
        formatted_datasets = []
        for dataset in datasets:
            if isinstance(dataset, dict) and 'data' in dataset:
                # Ensure data has features array
                if not isinstance(dataset['data'], dict):
                    dataset['data'] = {'features': []}
                if 'features' not in dataset['data']:
                    dataset['data']['features'] = []
                formatted_datasets.append(dataset)
        
        return jsonify({
            'status': 'success',
            'datasets': formatted_datasets
        })
    except Exception as e:
        error_msg = f"Error in send_to_map: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'status': 'error',
            'error': error_msg
        }), 500

@app.route('/api/datasets/<dataset_id>/map', methods=['GET'])
def get_dataset_map(dataset_id):
    try:
        dataset_service = DatasetService()
        map_data = dataset_service.load_dataset_for_map(dataset_id)
        return jsonify(map_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analysis', methods=['POST'])
async def handle_analysis():
    try:
        data = request.get_json()
        question = data.get('question')
        
        # Get current map context if available
        context = session.get('map_context', {})
        
        response = await analysis_agent.process_query(question, context)
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in analysis endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/initial-prompt', methods=['GET'])
def get_initial_prompt():
    try:
        prompts_dir = os.path.join(os.path.dirname(__file__), "services", "prompts")
        with open(os.path.join(prompts_dir, "initial_prompt.txt"), "r") as f:
            initial_prompt = f.read().strip()
        return jsonify({
            'status': 'success',
            'prompt': initial_prompt
        })
    except Exception as e:
        logger.error(f"Error loading initial prompt: {str(e)}")
        return jsonify({
            'status': 'error',
            'prompt': 'Hello! I\'m an expert environmental data analyst assistant. How can I help you today?'
        })

# Add this route to serve GeoJSON data
@app.route('/api/dataset/sdg-15-3-1')
def get_sdg_data():
    try:
        # Load the GeoJSON file
        with open('data/sdg_panama_sample.geojson', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'Dataset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add a general route to serve data files
@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory('data', filename)

# Add this new route
@app.route('/api/datasets/map', methods=['GET'])
def get_all_datasets_map():
    try:
        dataset_service = DatasetService()
        datasets = dataset_service.load_all_geojson_datasets()
        return jsonify({
            'status': 'success',
            'datasets': datasets
        })
    except Exception as e:
        logger.error(f"Error loading datasets: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add this new route
@app.route('/api/datasets/deserts')
def get_deserts():
    try:
        data = dataset_service.get_deserts_data()
        if data:
            return jsonify(data)
        return jsonify({'error': 'Desert data not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=9002)
