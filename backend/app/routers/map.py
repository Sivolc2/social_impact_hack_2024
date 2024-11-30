from fastapi import APIRouter, HTTPException, Query
from app.services.data_processing import DataProcessor
from typing import Optional

router = APIRouter()
processor = DataProcessor()

@router.get("/data")
async def get_map_data(
    filename: str = Query("sample.geojson", description="GeoJSON file to process"),
    resolution: Optional[int] = Query(9, ge=0, le=15, description="H3 resolution (0-15)")
):
    try:
        result = processor.process_geospatial_data(filename, resolution)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/raw")
async def get_raw_geojson(
    filename: str = Query("sample.geojson", description="GeoJSON file to fetch")
):
    try:
        result = processor.load_geojson(filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 