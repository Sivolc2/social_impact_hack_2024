from flask import Flask, render_template, jsonify, url_for, request, Response, stream_with_context
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

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)
CORS(app)

map_service = MapService()
dataset_service = DatasetService()

logging.basicConfig(level=logging.DEBUG)

# Helper function to run async code in Flask
def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

# Initialize agents
try:
    data_agent = DataAgent()
    asyncio.run(data_agent.initialize("data/knowledge_base.txt"))
    analysis_agent = AnalysisAgent()
    logging.info("Agents initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize agents: {str(e)}")
    raise

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    message_history = data.get('history', [])
    current_mode = data.get('mode', 'data')  # Get the current mode from the request
    
    def generate():
        try:
            if current_mode == 'data':
                # Use data agent for data mode
                response = asyncio.run(data_agent.process_query(user_message))
                yield f"data: {json.dumps({'chunk': response['response']})}\n\n"
            else:
                # Use analysis agent for analysis mode
                for chunk in analysis_agent.stream_analysis(user_message):
                    if chunk:  # Only yield non-empty chunks
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}")
            yield f"data: {json.dumps({'chunk': f'Error: {str(e)}'})}\n\n"
    
    return Response(
        stream_with_context(generate()), 
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Content-Type': 'text/event-stream',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
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
        data = request.get_json()
        messages = data.get('messages', [])
        
        # Process the conversation history
        # You can add your logic here to analyze the messages and determine what to show on the map
        
        # For now, just return a success response
        return jsonify({
            'status': 'success',
            'message': 'Conversation processed for map visualization',
            # Add any additional data you want to send back to update the map
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=9001)