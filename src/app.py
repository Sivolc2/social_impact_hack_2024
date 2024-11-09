from flask import Flask, jsonify, request
from src.services.data_agent import DataAgent
from src.services.map_service import MapService
from src.services.dataset_service import DatasetService

app = Flask(__name__)

data_agent = DataAgent()
map_service = MapService()
dataset_service = DatasetService()

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'status': 'online',
        'available_endpoints': [
            '/api/chat',
            '/api/datasets',
            '/api/map/layers'
        ]
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with the data agent"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    return jsonify(data_agent.process_message(message))

@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    """Get available datasets"""
    return jsonify(dataset_service.get_available_datasets())

@app.route('/api/map/layers', methods=['GET'])
def get_map_layers():
    """Get available map layers"""
    return jsonify(map_service.get_available_layers())

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 