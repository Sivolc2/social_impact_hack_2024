from uagents import Agent, Context, Model
from dataclasses import dataclass
from typing import List, Optional
import re

# Import models from other agents
from data_agent import DataRequest, DataResponse
from insights_agent import InsightsRequest, InsightsResponse

router_agent = Agent(
    name="router_agent",
    seed="router_seed_456",
    port=8002,
    endpoint="http://127.0.0.1:8002/submit"
)

@dataclass
class UserQuery(Model):
    question: str

@dataclass
class QueryResponse(Model):
    insights: List[str]
    recommendations: List[str]
    confidence_level: float
    source_url: str
    analysis_notes: str

def determine_query_type(question: str) -> tuple[str, str]:
    """Determine the type of query and focus area based on the question."""
    question_lower = question.lower()
    
    # Define keywords for different categories
    data_keywords = {'statistics', 'numbers', 'data', 'how many', 'what percentage'}
    insights_keywords = {'why', 'how', 'what should', 'recommend', 'analyze', 'explain'}
    
    # Define focus areas
    focus_areas = {
        'policy': {'policy', 'regulation', 'law', 'governance'},
        'trends': {'trend', 'pattern', 'change', 'over time'},
        'impacts': {'impact', 'effect', 'consequence', 'result'},
        'solutions': {'solution', 'mitigation', 'prevention', 'strategy'}
    }

    # Determine query type
    query_type = 'data' if any(keyword in question_lower for keyword in data_keywords) else 'insights'
    
    # Determine focus area
    focus_area = 'trends'  # default
    for area, keywords in focus_areas.items():
        if any(keyword in question_lower for keyword in keywords):
            focus_area = area
            break
    
    return query_type, focus_area

def determine_data_category(question: str) -> str:
    """Determine the data category based on the question."""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['degradation', 'soil', 'land']):
        return 'land_degradation'
    elif any(word in question_lower for word in ['drought', 'dry', 'water scarcity']):
        return 'drought'
    elif any(word in question_lower for word in ['population', 'people', 'communities']):
        return 'population'
    
    return 'land_degradation'  # default category

@router_agent.on_message(model=UserQuery, replies=QueryResponse)
async def handle_user_query(ctx: Context, sender: str, msg: UserQuery) -> None:
    try:
        # Determine query type and focus area
        query_type, focus_area = determine_query_type(msg.question)
        
        if query_type == 'data':
            # Get data first
            data_category = determine_data_category(msg.question)
            data_response = await ctx.send(
                "data_agent",
                DataRequest(msg=msg.question, data_category=data_category)
            )
            
            # Then get insights based on the data
            insights_response = await ctx.send(
                "insights_agent",
                InsightsRequest(
                    question=msg.question,
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
            data_category = determine_data_category(msg.question)
            data_response = await ctx.send(
                "data_agent",
                DataRequest(msg=msg.question, data_category=data_category)
            )
            
            insights_response = await ctx.send(
                "insights_agent",
                InsightsRequest(
                    question=msg.question,
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
