from uagents import Agent, Context, Model
from dataclasses import dataclass
from openai import AsyncOpenAI
import os
from typing import Dict, List

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
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def generate_insights(self, question: str, focus_area: str, data_summary: str, source_url: str) -> Dict:
        prompt = f"""
        Analyze this data and question about UNCCD goals:
        Question: {question}
        Focus Area: {focus_area}
        Data Summary: {data_summary}
        Source: {source_url}
        
        Provide comprehensive analysis with:
        1. Key insights derived from the data
        2. Actionable recommendations
        3. Confidence level in the analysis
        4. Notable limitations or assumptions
        
        Return a JSON with:
        - key_insights (list of strings)
        - recommendations (list of strings)
        - confidence_level (0-1)
        - analysis_notes (string)
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content

@insights_agent.on_message(model=InsightsRequest, replies=InsightsResponse)
async def handle_insights_request(ctx: Context, sender: str, request: InsightsRequest) -> None:
    ctx.logger.info(f"Received insights request for focus area: {request.focus_area}")
    
    try:
        # Initialize analyzer
        analyzer = InsightsAnalyzer()
        
        # Generate insights
        analysis_result = await analyzer.generate_insights(
            request.question,
            request.focus_area,
            request.data_summary,
            request.source_url
        )
        
        # Parse the JSON response
        result_dict = eval(analysis_result)
        
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
