from uagents import Agent, Context, Model
from dataclasses import dataclass
from typing import Dict, List
import requests
import json
import os
import time

# Fetch.ai API Configuration
FAUNA_URL = 'https://accounts.fetch.ai'
TOKEN_URL = f'{FAUNA_URL}/v1/tokens'
CLIENT_ID = 'agentverse'
SCOPE = 'av'

insights_agent = Agent(
    name="insights_agent",
    seed="insights_seed_123",
    port=8001,
    endpoint="http://127.0.0.1:8001/insights_request"
)

@dataclass
class InsightsRequest(Model):
    question: str
    focus_area: str  # e.g., 'policy', 'trends', 'impacts', 'solutions'
    data_summary: str
    source_url: str

@dataclass
class InsightsResponse(Model):
    key_insights: List[str]
    recommendations: List[str]
    confidence_level: float
    analysis_notes: str

class InsightsAnalyzer:
    def __init__(self):
        self.access_token = f"Bearer {os.getenv('FETCH_ACCESS_TOKEN')}"
    
    async def generate_insights(self, question: str, focus_area: str, data_summary: str, source_url: str) -> Dict:
        # Create chat session
        session_data = {
            "email": os.getenv('FETCH_EMAIL'),
            "requestedModel": "talkative-01"
        }
        
        session_response = requests.post(
            "https://agentverse.ai/v1beta1/engine/chat/sessions",
            json=session_data,
            headers={"Authorization": self.access_token}
        ).json()
        
        session_id = session_response.get('session_id')
        
        # Prepare analysis prompt
        prompt = f"""
        Analyze this data and question about UNCCD goals:
        Question: {question}
        Focus Area: {focus_area}
        Data Summary: {data_summary}
        Source: {source_url}
        
        Provide comprehensive analysis with:
        1. Key insights derived from the data
        2. Actionable recommendations
        3. Confidence level in the analysis (0-1)
        4. Notable limitations or assumptions
        
        Respond in JSON format with these fields:
        - key_insights (list of strings)
        - recommendations (list of strings)
        - confidence_level (float between 0-1)
        - analysis_notes (string)
        """
        
        # Send analysis request
        message_data = {
            "payload": {
                "type": "user_message",
                "user_message": prompt,
                "session_id": session_id
            }
        }
        
        # Send message
        requests.post(
            f"https://agentverse.ai/v1beta1/engine/chat/sessions/{session_id}/submit",
            json=message_data,
            headers={"Authorization": self.access_token}
        )
        
        time.sleep(5)  # Wait for processing
        
        # Get analysis response
        response = requests.get(
            f"https://agentverse.ai/v1beta1/engine/chat/sessions/{session_id}/responses",
            headers={"Authorization": self.access_token}
        ).json()
        
        # Stop session
        requests.post(
            f"https://agentverse.ai/v1beta1/engine/chat/sessions/{session_id}/submit",
            json={"payload": {"type": "stop"}},
            headers={"Authorization": self.access_token}
        )
        
        # Parse and return response
        if response.get('agent_response'):
            try:
                return json.loads(response['agent_response'][0])
            except json.JSONDecodeError:
                # Fallback if response isn't proper JSON
                return {
                    'key_insights': ["Error: Could not parse response"],
                    'recommendations': ["Please try again"],
                    'confidence_level': 0.0,
                    'analysis_notes': "Error parsing response from AI"
                }
        
        return {
            'key_insights': ["Error: No response received"],
            'recommendations': ["Please try again"],
            'confidence_level': 0.0,
            'analysis_notes': "No response from AI service"
        }

@insights_agent.on_message(model=InsightsRequest, replies=InsightsResponse)
async def handle_insights_request(ctx: Context, sender: str, request: InsightsRequest) -> None:
    ctx.logger.info(f"Received insights request for focus area: {request.focus_area}")
    
    try:
        # Initialize analyzer
        analyzer = InsightsAnalyzer()
        
        # Generate insights
        result_dict = await analyzer.generate_insights(
            request.question,
            request.focus_area,
            request.data_summary,
            request.source_url
        )
        
        return InsightsResponse(
            key_insights=result_dict['key_insights'],
            recommendations=result_dict['recommendations'],
            confidence_level=result_dict['confidence_level'],
            analysis_notes=result_dict['analysis_notes']
        )
                
    except Exception as e:
        ctx.logger.error(f"Error processing insights request: {str(e)}")
        return InsightsResponse(
            key_insights=["Error processing request"],
            recommendations=["Please try again with different parameters"],
            confidence_level=0.0,
            analysis_notes=f"Error during processing: {str(e)}"
        )

if __name__ == "__main__":
    insights_agent.run()
