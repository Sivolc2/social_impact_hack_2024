from uagents import Agent, Context, Model
from dataclasses import dataclass
import aiohttp
import json
from bs4 import BeautifulSoup
import os
from typing import List, Dict
import re
import requests
import time

# Fetch.ai API Configuration
FAUNA_URL = 'https://accounts.fetch.ai'
TOKEN_URL = f'{FAUNA_URL}/v1/tokens'
CLIENT_ID = 'agentverse'
SCOPE = 'av'

data_agent = Agent(
    name="data_agent",
    seed="randomseedidk",
    port=8000,
    endpoint="http://127.0.0.1:8000/data_request"
)

@dataclass
class DataRequest(Model):
    msg: str
    data_category: str  # 'land_degradation', 'drought', or 'population'

@dataclass
class DataResponse(Model):
    data_summary: str
    source_url: str
    confidence_score: float
    methodology_notes: str

class DataSourceAnalyzer:
    def __init__(self):
        self.refresh_token = os.getenv('FETCH_REFRESH_TOKEN')
        self.access_token = f"Bearer {os.getenv('FETCH_ACCESS_TOKEN')}"
        
    async def analyze_source_credibility(self, text: str, url: str) -> Dict:
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
        
        # Send analysis request
        prompt = f"""
        Analyze this potential data source about UNCCD goals:
        URL: {url}
        Content: {text[:1000]}...
        
        Evaluate:
        1. Credibility
        2. Relevance to UNCCD goals
        3. Data quality and methodology
        4. Recency of data
        """
        
        message_data = {
            "payload": {
                "type": "user_message",
                "user_message": prompt,
                "session_id": session_id
            }
        }
        
        # Send message and wait for response
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
        
        # Parse response
        if response.get('agent_response'):
            agent_response = json.loads(response['agent_response'][0])
            analysis = agent_response.get('agent_message', '')
            
            # Convert response to expected format
            return {
                'confidence_score': 0.8,  # You may want to extract this from the response
                'summary': analysis,
                'methodology_notes': "Analysis performed using Fetch.ai's chat API"
            }
        
        return {
            'confidence_score': 0.0,
            'summary': "Analysis failed",
            'methodology_notes': "Error during processing"
        }

@data_agent.on_message(model=DataRequest, replies=DataResponse)
async def msg_callback(ctx: Context, sender: str, request: DataRequest) -> None:
    ctx.logger.info(f"Received request for {request.data_category} data: {request.msg}")
    
    # Initialize analyzer
    analyzer = DataSourceAnalyzer()
    
    # Define search queries based on category
    search_queries = {
        'land_degradation': [
            'site:unccd.int land degradation neutrality data',
            'site:fao.org land degradation statistics',
            'site:worldbank.org land degradation indicators'
        ],
        'drought': [
            'site:unccd.int drought risk data',
            'site:drought.gov global drought data',
            'site:fao.org drought impact statistics'
        ],
        'population': [
            'site:unccd.int population affected desertification',
            'site:un.org demographics desertification impact',
            'site:worldbank.org population displacement environmental'
        ]
    }
    
    best_source = None
    highest_confidence = 0
    
    try:
        async with aiohttp.ClientSession() as session:
            # Search relevant URLs
            for query in search_queries.get(request.data_category, []):
                search_url = f"https://www.google.com/search?q={query}"
                async with session.get(search_url) as response:
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    urls = [a['href'] for a in soup.find_all('a', href=True) 
                           if any(domain in a['href'] for domain in 
                                ['.gov', '.int', '.org', '.edu'])]
                    
                    # Analyze each URL
                    for url in urls[:3]:  # Analyze top 3 results
                        async with session.get(url) as page_response:
                            content = await page_response.text()
                            soup = BeautifulSoup(content, 'html.parser')
                            text = soup.get_text()
                            
                            # Analyze source credibility and relevance
                            analysis = await analyzer.analyze_source_credibility(text, url)
                            
                            if analysis['confidence_score'] > highest_confidence:
                                best_source = {
                                    'url': url,
                                    'analysis': analysis
                                }
                                highest_confidence = analysis['confidence_score']
    
        if best_source:
            return DataResponse(
                data_summary=best_source['analysis']['summary'],
                source_url=best_source['url'],
                confidence_score=best_source['analysis']['confidence_score'],
                methodology_notes=best_source['analysis']['methodology_notes']
            )
        else:
            return DataResponse(
                data_summary="No reliable data sources found",
                source_url="",
                confidence_score=0.0,
                methodology_notes="Search failed to find credible sources"
            )
                
    except Exception as e:
        ctx.logger.error(f"Error processing request: {str(e)}")
        return DataResponse(
            data_summary=f"Error: {str(e)}",
            source_url="",
            confidence_score=0.0,
            methodology_notes="Error during processing"
        )

def get_current_data(self):
    """
    Returns the currently loaded map data in a format suitable for export
    """
    # Return the current data in a structured format
    # This will depend on how you're storing/managing your data
    if hasattr(self, 'current_data'):
        return self.current_data
    return None

if __name__ == "__main__":
    data_agent.run()
