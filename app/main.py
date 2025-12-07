"""
Geant4 Real-Time API - Main Application
=======================================

A FastAPI-based REST API wrapper for Geant4 Monte Carlo simulations
with WebSocket support for real-time data streaming.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from loguru import logger
import sys

from app.config import settings, setup_geant4_environment
from app.api import api_router


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level
)

if settings.log_file:
    logger.add(settings.log_file, rotation="10 MB", retention="7 days")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Geant4 API server...")
    setup_geant4_environment()
    logger.info(f"Results directory: {settings.results_path}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Geant4 API server...")


# Create FastAPI application
app = FastAPI(
    title="Geant4 Real-Time API",
    redirect_slashes=False,  # Prevent 307 redirects for trailing slashes
    description="""
## Geant4 Monte Carlo Simulation API

A RESTful API for running Geant4 particle physics simulations with real-time 
WebSocket streaming support.

### Features

- **Geometry Configuration**: Define detector geometries via API
- **Physics Selection**: Choose from standard Geant4 physics lists
- **Particle Sources**: Configure particle guns and GPS sources
- **Real-Time Streaming**: WebSocket updates during simulation
- **Results Analysis**: Histograms, summaries, and data export

### Quick Start

1. Create a simulation configuration
2. Start the simulation
3. Connect to WebSocket for real-time updates
4. Retrieve results when complete

### WebSocket

Connect to `/ws/simulations/{simulation_id}` for real-time updates.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Geant4 API</title>
        <style>
            body {
                font-family: 'Segoe UI', system-ui, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #eee;
                min-height: 100vh;
            }
            h1 { 
                color: #00d4ff; 
                border-bottom: 2px solid #00d4ff;
                padding-bottom: 10px;
            }
            h2 { color: #ff6b6b; }
            a { 
                color: #4ecdc4; 
                text-decoration: none;
            }
            a:hover { text-decoration: underline; }
            .card {
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
                backdrop-filter: blur(10px);
            }
            code {
                background: rgba(0,212,255,0.2);
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Fira Code', monospace;
            }
            .endpoint {
                display: flex;
                align-items: center;
                margin: 10px 0;
            }
            .method {
                background: #4ecdc4;
                color: #1a1a2e;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 10px;
                font-size: 12px;
            }
            .method.post { background: #ff6b6b; }
            .method.ws { background: #ffd93d; }
        </style>
    </head>
    <body>
        <h1>⚛️ Geant4 Real-Time API</h1>
        
        <div class="card">
            <h2>📚 Documentation</h2>
            <p>
                <a href="/docs">📖 Interactive API Docs (Swagger)</a><br>
                <a href="/redoc">📘 ReDoc Documentation</a>
            </p>
        </div>
        
        <div class="card">
            <h2>🚀 Quick Start</h2>
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/v1/simulations/quick-start/water_phantom</code>
            </div>
            <p>Start a quick simulation using a predefined template.</p>
        </div>
        
        <div class="card">
            <h2>🔌 Key Endpoints</h2>
            <div class="endpoint">
                <span class="method">GET</span>
                <code>/api/v1/simulations</code> - List simulations
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/v1/simulations</code> - Create simulation
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/v1/simulations/{id}/start</code> - Start simulation
            </div>
            <div class="endpoint">
                <span class="method ws">WS</span>
                <code>/ws/simulations/{id}</code> - Real-time updates
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <code>/api/v1/results/{id}</code> - Get results
            </div>
        </div>
        
        <div class="card">
            <h2>📦 Templates</h2>
            <div class="endpoint">
                <span class="method">GET</span>
                <code>/api/v1/geometry/templates</code>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <code>/api/v1/physics/templates</code>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <code>/api/v1/sources/templates</code>
            </div>
        </div>
        
        <div class="card">
            <h2>ℹ️ Version</h2>
            <p>API Version: 1.0.0</p>
            <p>Powered by FastAPI + Geant4</p>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "geant4_available": False  # Will be True when Geant4 bindings are loaded
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )

