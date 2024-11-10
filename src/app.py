from flask import Flask, render_template, jsonify, url_for, request, Response
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

# Initialize the agent
try:
    agent = DataAgent()
    asyncio.run(agent.initialize("data/knowledge_base.txt"))
    logging.info("Data agent initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize DataAgent: {str(e)}")
    raise

# Initialize both agents
data_agent = DataAgent()
analysis_agent = AnalysisAgent()

@app.route('/chat', methods=['POST'])
@async_route
async def chat():
    try:
        data = request.json
        question = data.get('question')
        mode = data.get('mode', 'data')  # Get the current mode
        context = data.get('context', {})
        
        logging.debug(f"Processing {mode} query: {question}")
        
        if mode == 'data':
            # Process query through data agent with summary
            response = await agent.process_query(question, context, include_summary=True)
        else:
            # Process through analysis agent without summary
            response = await analysis_agent.process_query(question, context)
            # Convert analysis response to match expected format
            response = {
                'response': response.get('response', ''),
                'summary_table': '',  # No summary table for analysis mode
                'status': response.get('status', 'error')
            }
        
        logging.debug(f"Got response: {response}")
        
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'response': f"Error: {str(e)}",
            'summary_table': '',
            'status': 'error'
        }), 500

@app.route('/api/export-data', methods=['GET'])
@async_route
async def export_data():
    try:
        recommendations = await agent.get_dataset_recommendations()
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
        
    result = agent.process_hypothesis_query(hypothesis)
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

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=9001)