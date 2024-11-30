from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from app.services.data_agent import DataAgent
from app.services.catalog_llm import CatalogAgent
from app.services.catalog import DataCatalog
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
agent = DataAgent()
catalog = DataCatalog()
catalog_llm = CatalogAgent(catalog)

class ChatMessage(BaseModel):
    message: str

class DatasetMatch(BaseModel):
    dataset_id: str
    confidence: float
    reasoning: str

class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str
    temporal_range: str
    spatial_resolution: str
    source: str
    category: str
    variables: List[str]
    availability: str
    text: Optional[str] = None
    relevance_context: Optional[str] = None

class CatalogResponse(BaseModel):
    interpretation: str
    matches: List[DatasetMatch]
    datasets: List[DatasetResponse]

@router.post("/catalog/query")
async def query_catalog(message: str = Body(..., embed=True)) -> CatalogResponse:
    """Query the catalog using LLM interpretation"""
    try:
        result = await catalog_llm.process_query(message)
        
        matches = [
            DatasetMatch(
                dataset_id=dataset_id,
                confidence=result["confidence"][dataset_id],
                reasoning=result["reasoning"][dataset_id]
            )
            for dataset_id in result["dataset_ids"]
        ]
        
        return CatalogResponse(
            interpretation=result["interpretation"],
            matches=matches,
            datasets=result["datasets"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message")
async def send_message(chat_message: ChatMessage) -> StreamingResponse:
    try:
        return StreamingResponse(
            agent.stream_query(chat_message.message),
            media_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'text/event-stream',
                'X-Accel-Buffering': 'no'  # Disable buffering in Nginx if you're using it
            }
        )
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets")
async def get_datasets(query: Optional[str] = None) -> List[DatasetResponse]:
    """Get available datasets, optionally filtered by search query"""
    try:
        if query:
            datasets = catalog.search_datasets(query)
        else:
            datasets = catalog.get_all_datasets()
            
        return [DatasetResponse(**dataset) for dataset in datasets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str) -> DatasetResponse:
    """Get details for a specific dataset"""
    try:
        dataset = catalog.get_dataset_by_id(dataset_id)
        if not dataset:
            logger.warning(f"Dataset not found: {dataset_id}")
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        
        try:
            # Create a copy of the dataset with all required fields
            dataset_response = DatasetResponse(
                id=dataset["id"],
                name=dataset["name"],
                description=dataset["description"],
                temporal_range=dataset["temporal_range"],
                spatial_resolution=dataset["spatial_resolution"],
                source=dataset["source"],
                category=dataset["category"],
                variables=dataset["variables"],
                availability=dataset["availability"],
                text=dataset.get("text"),
                relevance_context=""
            )
            return dataset_response
            
        except KeyError as ke:
            logger.error(f"Missing required field in dataset {dataset_id}: {ke}")
            raise HTTPException(
                status_code=500, 
                detail=f"Dataset {dataset_id} is missing required field: {ke}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dataset {dataset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear")
async def clear_conversation():
    try:
        await agent.clear_conversation()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 