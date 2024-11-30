from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import map, chat
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Geospatial Framework API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
logger.debug("Initializing routers...")
app.include_router(map.router, prefix="/api/map", tags=["map"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
logger.debug("Routers initialized")

@app.get("/")
async def root():
    return {"message": "Geospatial Framework API"} 