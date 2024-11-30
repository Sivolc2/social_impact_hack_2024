import pytest
from app.services.catalog_llm import CatalogAgent
from app.services.catalog import DataCatalog

@pytest.fixture
def mock_catalog():
    class MockDataCatalog(DataCatalog):
        def __init__(self):
            self.datasets = {
                "datasets_available": [
                    {
                        "id": "dataset-001",
                        "name": "Temperature Data",
                        "description": "Global temperature measurements",
                        "temporal_range": "2000-2023",
                        "spatial_resolution": "1km"
                    },
                    {
                        "id": "dataset-002",
                        "name": "Rainfall Data",
                        "description": "Precipitation measurements",
                        "temporal_range": "2010-2023",
                        "spatial_resolution": "500m"
                    }
                ]
            }
        
        def _load_datasets(self):
            return self.datasets

    return MockDataCatalog()

@pytest.fixture
def catalog_agent(mock_catalog):
    return CatalogAgent(mock_catalog)

def test_extract_dataset_suggestions(catalog_agent):
    # Test response with dataset references
    llm_response = """
    For your temperature analysis:
    
    [Dataset ID: dataset-001] The Temperature Data would be perfect for this analysis 
    since it covers global measurements. This dataset provides high resolution data 
    at 1km scale.
    
    You might also want to consider [Dataset ID: dataset-002] for understanding 
    precipitation patterns in the region.
    """
    
    suggestions = catalog_agent.extract_dataset_suggestions(llm_response)
    
    assert len(suggestions) == 2
    assert suggestions[0]["id"] == "dataset-001"
    assert suggestions[0]["name"] == "Temperature Data"
    assert "perfect for this analysis" in suggestions[0]["relevance_context"]
    
    assert suggestions[1]["id"] == "dataset-002"
    assert suggestions[1]["name"] == "Rainfall Data"

def test_extract_dataset_suggestions_no_matches(catalog_agent):
    llm_response = "No relevant datasets found for your query."
    suggestions = catalog_agent.extract_dataset_suggestions(llm_response)
    assert len(suggestions) == 0

def test_extract_dataset_suggestions_invalid_id(catalog_agent):
    llm_response = "[Dataset ID: invalid-id] This dataset doesn't exist"
    suggestions = catalog_agent.extract_dataset_suggestions(llm_response)
    assert len(suggestions) == 0

def test_extract_relevance_context(catalog_agent):
    llm_response = """First sentence. 
    [Dataset ID: dataset-001] is relevant because of X. 
    Some other text. 
    More about dataset-001 and its usefulness.
    Unrelated sentence."""
    
    context = catalog_agent._extract_relevance_context(llm_response, "dataset-001")
    assert "relevant because of X" in context
    assert "its usefulness" in context
    assert "Unrelated sentence" not in context 