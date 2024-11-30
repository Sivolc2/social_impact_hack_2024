import pytest
from unittest.mock import Mock, patch
import json
from app.services.data_agent import DataAgent
from app.services.catalog import DataCatalog
import time
import asyncio

@pytest.fixture
def mock_anthropic():
    with patch('anthropic.Anthropic') as mock:
        yield mock

@pytest.fixture
def mock_catalog():
    catalog = Mock(spec=DataCatalog)
    catalog.get_all_datasets.return_value = [
        {
            "id": "dataset-001",
            "name": "Test Dataset",
            "description": "Test description",
            "temporal_range": "2020-2023",
            "spatial_resolution": "1km"
        }
    ]
    return catalog

@pytest.fixture
def data_agent(mock_anthropic, mock_catalog):
    with patch('app.services.data_agent.DataCatalog', return_value=mock_catalog):
        agent = DataAgent()
        return agent

@pytest.mark.asyncio
async def test_get_dataset_suggestions(data_agent):
    # Mock the stream_query method to return a predefined response
    async def mock_stream(*args, **kwargs):
        response = """Based on your query, I recommend:
        [Dataset ID: dataset-001] This dataset is perfect for your needs."""
        for chunk in response.split():
            yield chunk + " "
    
    data_agent.stream_query = mock_stream
    
    result = await data_agent.get_dataset_suggestions("test query")
    
    assert result["query"] == "test query"
    assert len(result["suggested_datasets"]) > 0
    assert "dataset-001" in result["raw_response"]

def test_format_dataset_suggestions(data_agent):
    datasets = [
        {
            "id": "test-001",
            "name": "Test Dataset",
            "temporal_range": "2020-2023",
            "spatial_resolution": "1km",
            "description": "Test description"
        }
    ]
    
    formatted = data_agent._format_dataset_suggestions(datasets)
    assert "Test Dataset" in formatted
    assert "test-001" in formatted
    assert "2020-2023" in formatted

def test_format_dataset_suggestions_empty(data_agent):
    formatted = data_agent._format_dataset_suggestions([])
    assert formatted == "No matching datasets found."

@pytest.mark.asyncio
async def test_stream_query_rate_limiting(data_agent):
    """Test that requests are rate limited"""
    # Mock the client.messages.stream to return a simple async generator
    async def mock_stream(*args, **kwargs):
        class MockMessage:
            def __init__(self, text):
                self.type = "content_block_delta"
                self.delta = Mock(text=text)
        
        yield MockMessage("Test response")
    
    # Create a mock async context manager
    class MockStreamContextManager:
        async def __aenter__(self):
            return mock_stream()
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    # Patch the client's stream method
    data_agent.client.messages.stream = Mock(return_value=MockStreamContextManager())
    
    # First request
    responses = []
    async for chunk in data_agent.stream_query("test"):
        responses.append(chunk)
    
    # Immediate second request should be delayed
    start_time = time.time()
    async for chunk in data_agent.stream_query("test"):
        responses.append(chunk)
    
    duration = time.time() - start_time
    assert duration >= data_agent._request_interval

def test_load_prompts(data_agent):
    prompts = data_agent._load_prompts()
    assert "system" in prompts
    assert isinstance(prompts["system"], str) 