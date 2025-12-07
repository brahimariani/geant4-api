"""
Simulation management API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger

from app.models.simulation import (
    SimulationConfig, SimulationRequest, SimulationJob, 
    SimulationStatus, SimulationProgress
)
from app.models.geometry import DetectorGeometry
from app.models.physics import PhysicsConfig
from app.models.particle import ParticleSource
from app.core.simulation_engine import simulation_engine
from app.core.geometry_builder import geometry_builder, GEOMETRY_TEMPLATES
from app.core.physics_builder import physics_builder, PHYSICS_TEMPLATES
from app.core.source_builder import source_builder, SOURCE_TEMPLATES


router = APIRouter()


@router.get("", response_model=List[SimulationJob])
@router.get("/", response_model=List[SimulationJob], include_in_schema=False)
async def list_simulations(
    status: Optional[SimulationStatus] = None
):
    """
    List all simulations.
    
    Optionally filter by status.
    """
    jobs = simulation_engine.list_simulations()
    
    if status:
        jobs = [j for j in jobs if j.status == status]
    
    return jobs


@router.post("", response_model=SimulationJob)
@router.post("/", response_model=SimulationJob, include_in_schema=False)
async def create_simulation(request: SimulationRequest):
    """
    Create a new simulation.
    
    You can either:
    - Reference saved configurations by ID (geometry_id, physics_id, source_id)
    - Provide inline configurations (geometry, physics, source)
    """
    # Resolve geometry
    geometry = None
    if request.geometry:
        geometry = DetectorGeometry(**request.geometry) if isinstance(request.geometry, dict) else request.geometry
    elif request.geometry_id:
        geometry = geometry_builder.get_geometry(request.geometry_id)
        if not geometry:
            raise HTTPException(404, f"Geometry '{request.geometry_id}' not found")
    
    # Resolve physics
    physics = None
    if request.physics:
        physics = PhysicsConfig(**request.physics) if isinstance(request.physics, dict) else request.physics
    elif request.physics_id:
        physics = physics_builder.get_physics(request.physics_id)
        if not physics:
            raise HTTPException(404, f"Physics config '{request.physics_id}' not found")
    
    # Resolve source
    source = None
    if request.source:
        source = ParticleSource(**request.source) if isinstance(request.source, dict) else request.source
    elif request.source_id:
        source = source_builder.get_source(request.source_id)
        if not source:
            raise HTTPException(404, f"Source '{request.source_id}' not found")
    
    # Create simulation job
    job = await simulation_engine.create_simulation(
        config=request.simulation,
        geometry=geometry,
        physics=physics,
        source=source
    )
    
    return job


@router.post("/{simulation_id}/start")
async def start_simulation(
    simulation_id: str,
    background_tasks: BackgroundTasks
):
    """
    Start a simulation.
    
    The simulation runs asynchronously. Use WebSocket endpoint
    `/ws/simulations/{simulation_id}` to receive real-time updates.
    """
    job = simulation_engine.get_simulation_status(simulation_id)
    if not job:
        raise HTTPException(404, f"Simulation '{simulation_id}' not found")
    
    if job.status not in [SimulationStatus.PENDING, SimulationStatus.PAUSED]:
        raise HTTPException(
            400, 
            f"Cannot start simulation in status '{job.status}'"
        )
    
    # Start simulation in background
    async def run_simulation():
        async for event in simulation_engine.start_simulation(simulation_id):
            # Events are handled by WebSocket subscribers
            pass
    
    background_tasks.add_task(run_simulation)
    
    return {
        "message": f"Simulation {simulation_id} started",
        "status": "starting",
        "websocket_url": f"/ws/simulations/{simulation_id}"
    }


@router.post("/{simulation_id}/pause")
async def pause_simulation(simulation_id: str):
    """Pause a running simulation."""
    success = await simulation_engine.pause_simulation(simulation_id)
    if not success:
        raise HTTPException(400, "Could not pause simulation")
    return {"message": "Simulation paused", "status": "paused"}


@router.post("/{simulation_id}/resume")
async def resume_simulation(simulation_id: str):
    """Resume a paused simulation."""
    success = await simulation_engine.resume_simulation(simulation_id)
    if not success:
        raise HTTPException(400, "Could not resume simulation")
    return {"message": "Simulation resumed", "status": "running"}


@router.post("/{simulation_id}/cancel")
async def cancel_simulation(simulation_id: str):
    """Cancel a simulation."""
    success = await simulation_engine.cancel_simulation(simulation_id)
    if not success:
        raise HTTPException(400, "Could not cancel simulation")
    return {"message": "Simulation cancelled", "status": "cancelled"}


@router.get("/{simulation_id}", response_model=SimulationJob)
async def get_simulation(simulation_id: str):
    """Get simulation status and details."""
    job = simulation_engine.get_simulation_status(simulation_id)
    if not job:
        raise HTTPException(404, f"Simulation '{simulation_id}' not found")
    return job


@router.get("/{simulation_id}/progress", response_model=SimulationProgress)
async def get_simulation_progress(simulation_id: str):
    """Get current simulation progress."""
    job = simulation_engine.get_simulation_status(simulation_id)
    if not job:
        raise HTTPException(404, f"Simulation '{simulation_id}' not found")
    
    elapsed = 0.0
    if job.started_at:
        from datetime import datetime
        elapsed = (datetime.utcnow() - job.started_at).total_seconds()
    
    progress_pct = (job.events_completed / job.events_total * 100) if job.events_total > 0 else 0
    rate = job.events_completed / elapsed if elapsed > 0 else None
    remaining = (job.events_total - job.events_completed) / rate if rate else None
    
    return SimulationProgress(
        simulation_id=simulation_id,
        status=job.status,
        events_completed=job.events_completed,
        events_total=job.events_total,
        progress_percent=progress_pct,
        elapsed_time=elapsed,
        estimated_remaining=remaining,
        current_event_rate=rate
    )


@router.delete("/{simulation_id}")
async def delete_simulation(simulation_id: str):
    """Delete a simulation and its results."""
    job = simulation_engine.get_simulation_status(simulation_id)
    if not job:
        raise HTTPException(404, f"Simulation '{simulation_id}' not found")
    
    # Cancel if running
    if job.status == SimulationStatus.RUNNING:
        await simulation_engine.cancel_simulation(simulation_id)
    
    # Remove from active simulations
    if simulation_id in simulation_engine.active_simulations:
        del simulation_engine.active_simulations[simulation_id]
    
    return {"message": f"Simulation {simulation_id} deleted"}


# Quick start endpoint with templates
@router.post("/quick-start/{template_name}")
async def quick_start_simulation(
    template_name: str,
    num_events: int = 1000,
    background_tasks: BackgroundTasks = None
):
    """
    Quick-start a simulation using predefined templates.
    
    Available templates:
    - water_phantom: Gamma in water phantom
    - simple_detector: NaI detector
    - shielded_detector: Lead-shielded detector
    """
    # Get templates
    geometry = GEOMETRY_TEMPLATES.get(template_name)
    physics = PHYSICS_TEMPLATES.get("standard")
    source = SOURCE_TEMPLATES.get("gamma_1mev")
    
    if not geometry:
        available = list(GEOMETRY_TEMPLATES.keys())
        raise HTTPException(
            404, 
            f"Template '{template_name}' not found. Available: {available}"
        )
    
    # Create config
    config = SimulationConfig(
        name=f"{template_name}_quick",
        description=f"Quick-start simulation using {template_name} template",
        num_events=num_events,
        output_every_n_events=max(1, num_events // 10)
    )
    
    # Create and start
    job = await simulation_engine.create_simulation(
        config=config,
        geometry=geometry,
        physics=physics,
        source=source
    )
    
    return {
        "simulation_id": job.id,
        "name": job.name,
        "status": job.status,
        "message": f"Created quick-start simulation. Use POST /simulations/{job.id}/start to begin.",
        "websocket_url": f"/ws/simulations/{job.id}"
    }

