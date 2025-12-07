"""
API routes for Geant4 REST API.
"""

from fastapi import APIRouter
from .simulations import router as simulations_router
from .geometry import router as geometry_router
from .physics import router as physics_router
from .sources import router as sources_router
from .results import router as results_router
from .websocket import router as websocket_router
from .geant4 import router as geant4_router

# Main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(
    simulations_router, 
    prefix="/simulations", 
    tags=["Simulations"]
)
api_router.include_router(
    geometry_router, 
    prefix="/geometry", 
    tags=["Geometry"]
)
api_router.include_router(
    physics_router, 
    prefix="/physics", 
    tags=["Physics"]
)
api_router.include_router(
    sources_router, 
    prefix="/sources", 
    tags=["Particle Sources"]
)
api_router.include_router(
    results_router, 
    prefix="/results", 
    tags=["Results"]
)
api_router.include_router(
    websocket_router, 
    prefix="/ws", 
    tags=["WebSocket"]
)
api_router.include_router(
    geant4_router,
    prefix="/geant4",
    tags=["Geant4 Configuration"]
)

