from uagents import Agent, Context, Model
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re
import requests
import os
import time
import json

#mailbox = e5170687-619b-49df-bb01-159fa4610bfa

# Import models from other agents
from data_agent import DataRequest, DataResponse
from insights_agent import InsightsRequest, InsightsResponse

router_agent = Agent(
    name="router_agent",
    seed="router_seed_456",
    port=8002,
    endpoint=["http://localhost:8002"]
)

# Request/Response models for REST endpoint
class QueryRequest(Model):
    question: str

class QueryResponse(Model):
    insights: List[str]
    recommendations: List[str]
    confidence_level: float
    source_url: str
    analysis_notes: str

# Fetch.ai API Configuration
FAUNA_URL = 'https://accounts.fetch.ai'
TOKEN_URL = f'{FAUNA_URL}/v1/tokens'
CLIENT_ID = 'agentverse'
SCOPE = 'av'

class QueryAnalyzer:
    def __init__(self):
        self.access_token = f"Bearer {os.getenv('FETCH_ACCESS_TOKEN')}"

    async def analyze_query(self, question: str) -> tuple[str, str, str]:
        """Analyze query using Fetch.ai to determine type, focus area, and category."""

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
        Analyze this question about UNCCD goals and desertification:
        "{question}"

        Classify the question into:
        1. Query type: either 'data' (for statistical/numerical questions) or 'insights' (for analytical/explanatory questions)
        2. Focus area: one of 'policy', 'trends', 'impacts', or 'solutions'
        3. Data category: one of 'land_degradation', 'drought', or 'population'

        Respond in JSON format with these three classifications.
        """

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

        time.sleep(3)  # Wait for processing

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

        # Parse response
        try:
            if response.get('agent_response'):
                analysis = json.loads(response['agent_response'][0])
                return (
                    analysis.get('query_type', 'insights'),
                    analysis.get('focus_area', 'trends'),
                    analysis.get('data_category', 'land_degradation')
                )
        except Exception as e:
            ctx.logger.error(f"Error parsing query analysis: {str(e)}")

        # Default values if analysis fails
        return 'insights', 'trends', 'land_degradation'

# Replace the existing determine_query_type and determine_data_category functions
# with the QueryAnalyzer class instance
query_analyzer = QueryAnalyzer()

@router_agent.on_rest_post("/query", QueryRequest, QueryResponse)
async def handle_user_query(ctx: Context, req: QueryRequest) -> QueryResponse:
    try:
        # Use the analyzer to determine query characteristics
        query_type, focus_area, data_category = await query_analyzer.analyze_query(req.question)

        if query_type == 'data':
            data_response = await ctx.send(
                "data_agent",
                DataRequest(msg=req.question, data_category=data_category)
            )

            insights_response = await ctx.send(
                "insights_agent",
                InsightsRequest(
                    question=req.question,
                    focus_area=focus_area,
                    data_summary=data_response.data_summary,
                    source_url=data_response.source_url
                )
            )

            return QueryResponse(
                insights=insights_response.key_insights,
                recommendations=insights_response.recommendations,
                confidence_level=min(data_response.confidence_score, insights_response.confidence_level),
                source_url=data_response.source_url,
                analysis_notes=f"Data methodology: {data_response.methodology_notes}\nAnalysis notes: {insights_response.analysis_notes}"
            )
        else:
            # For insight-focused queries, still get some basic data first
            data_category = determine_data_category(req.question)
            data_response = await ctx.send(
                "data_agent",
                DataRequest(msg=req.question, data_category=data_category)
            )

            insights_response = await ctx.send(
                "insights_agent",
                InsightsRequest(
                    question=req.question,
                    focus_area=focus_area,
                    data_summary=data_response.data_summary,
                    source_url=data_response.source_url
                )
            )

            return QueryResponse(
                insights=insights_response.key_insights,
                recommendations=insights_response.recommendations,
                confidence_level=insights_response.confidence_level,
                source_url=data_response.source_url,
                analysis_notes=insights_response.analysis_notes
            )

    except Exception as e:
        ctx.logger.error(f"Error processing query: {str(e)}")
        return QueryResponse(
            insights=["Error processing query"],
            recommendations=["Please try again with a different question"],
            confidence_level=0.0,
            source_url="",
            analysis_notes=f"Error during processing: {str(e)}"
        )

if __name__ == "__main__":
    router_agent.run()
