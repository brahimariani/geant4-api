"""
Simulation results API endpoints.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
from pathlib import Path

from app.models.results import (
    SimulationResults, AnalysisResult, HistogramData
)
from app.core.result_collector import result_collector
from app.core.simulation_engine import simulation_engine


router = APIRouter()


@router.get("", response_model=List[str])
@router.get("/", response_model=List[str], include_in_schema=False)
async def list_results():
    """List all simulations with saved results."""
    return result_collector.list_simulations()


@router.get("/{simulation_id}", response_model=SimulationResults)
async def get_results(simulation_id: str):
    """
    Get complete results for a simulation.
    """
    # Check if simulation exists
    job = simulation_engine.get_simulation_status(simulation_id)
    
    # Try to get from engine first (for completed simulations)
    if job:
        results = await simulation_engine.get_results(simulation_id)
        if results:
            return results
    
    # Try to load from file
    results = result_collector.load_results(simulation_id)
    if not results:
        raise HTTPException(404, f"Results for simulation '{simulation_id}' not found")
    
    return results


@router.get("/{simulation_id}/summary")
async def get_results_summary(simulation_id: str):
    """
    Get summary statistics for a simulation.
    """
    results = result_collector.load_results(simulation_id)
    if not results:
        raise HTTPException(404, f"Results for simulation '{simulation_id}' not found")
    
    return {
        "simulation_id": simulation_id,
        "simulation_name": results.simulation_name,
        "num_events": results.num_events,
        "elapsed_time": results.elapsed_time,
        "events_per_second": results.events_per_second,
        "total_energy_deposited": results.total_energy_deposited,
        "detectors": [
            {
                "name": d.name,
                "hits": d.total_hits,
                "total_energy": d.total_energy_deposit,
                "mean_energy_per_event": d.mean_energy_per_event
            }
            for d in results.detector_summaries
        ],
        "particle_statistics": results.particle_statistics
    }


@router.get("/{simulation_id}/detectors")
async def get_detector_results(simulation_id: str):
    """Get per-detector results."""
    results = result_collector.load_results(simulation_id)
    if not results:
        raise HTTPException(404, f"Results for simulation '{simulation_id}' not found")
    
    return {
        "simulation_id": simulation_id,
        "detectors": [d.model_dump() for d in results.detector_summaries]
    }


@router.get("/{simulation_id}/hits")
async def get_hits(
    simulation_id: str,
    detector: Optional[str] = None,
    particle: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0
):
    """
    Get hit data from a simulation.
    
    - **detector**: Filter by detector name
    - **particle**: Filter by particle type
    - **limit**: Maximum number of hits to return
    - **offset**: Offset for pagination
    """
    results = result_collector.load_results(simulation_id)
    if not results:
        raise HTTPException(404, f"Results for simulation '{simulation_id}' not found")
    
    if not results.hits:
        return {"simulation_id": simulation_id, "hits": [], "total": 0}
    
    hits = results.hits
    
    # Apply filters
    if detector:
        hits = [h for h in hits if h.detector_name == detector]
    if particle:
        hits = [h for h in hits if h.particle_name == particle]
    
    total = len(hits)
    hits = hits[offset:offset + limit]
    
    return {
        "simulation_id": simulation_id,
        "hits": [h.model_dump() for h in hits],
        "total": total,
        "offset": offset,
        "limit": limit
    }


@router.get("/{simulation_id}/analysis", response_model=AnalysisResult)
async def get_analysis(
    simulation_id: str,
    analysis_type: str = "standard"
):
    """
    Generate analysis results with histograms.
    """
    analysis = result_collector.generate_analysis(simulation_id, analysis_type)
    if not analysis:
        raise HTTPException(404, f"Cannot generate analysis for '{simulation_id}'")
    
    return analysis


@router.get("/{simulation_id}/histogram/{hist_name}")
async def get_histogram(
    simulation_id: str,
    hist_name: str,
    bins: int = 100
):
    """
    Get a specific histogram from results.
    """
    results = result_collector.load_results(simulation_id)
    if not results:
        raise HTTPException(404, f"Results for simulation '{simulation_id}' not found")
    
    # Generate histogram based on name
    if hist_name == "energy_deposit" and results.hits:
        data = [h.energy_deposit for h in results.hits]
        hist = result_collector.create_histogram(
            data,
            name="energy_deposit",
            title="Energy Deposit Distribution",
            x_label="Energy (MeV)",
            bins=bins
        )
        return hist.model_dump()
    
    elif hist_name == "position_z" and results.hits:
        data = [h.position_z for h in results.hits]
        hist = result_collector.create_histogram(
            data,
            name="position_z",
            title="Hit Position Z Distribution",
            x_label="Z Position (mm)",
            bins=bins
        )
        return hist.model_dump()
    
    else:
        raise HTTPException(
            404, 
            f"Histogram '{hist_name}' not available. "
            "Available: energy_deposit, position_z"
        )


@router.get("/{simulation_id}/export/json")
async def export_json(simulation_id: str):
    """Export results as JSON file."""
    results = result_collector.load_results(simulation_id)
    if not results:
        raise HTTPException(404, f"Results for simulation '{simulation_id}' not found")
    
    return Response(
        content=results.model_dump_json(indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={simulation_id}_results.json"
        }
    )


@router.get("/{simulation_id}/export/csv")
async def export_csv(simulation_id: str):
    """Export hits as CSV file."""
    import tempfile
    
    results = result_collector.load_results(simulation_id)
    if not results:
        raise HTTPException(404, f"Results for simulation '{simulation_id}' not found")
    
    if not results.hits:
        raise HTTPException(400, "No hits data available for export")
    
    # Create temp file
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.csv', 
        delete=False
    ) as f:
        csv_path = Path(f.name)
    
    result_collector.export_csv(simulation_id, csv_path)
    
    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=f"{simulation_id}_hits.csv"
    )


@router.delete("/{simulation_id}")
async def delete_results(simulation_id: str):
    """Delete simulation results."""
    results_path = result_collector.results_path / simulation_id
    
    if not results_path.exists():
        raise HTTPException(404, f"Results for simulation '{simulation_id}' not found")
    
    import shutil
    shutil.rmtree(results_path)
    
    return {"message": f"Results for simulation '{simulation_id}' deleted"}


@router.get("/{simulation_id}/live")
async def get_live_stats(simulation_id: str):
    """
    Get live statistics for a running simulation.
    
    Returns current aggregated statistics without waiting for completion.
    """
    stats = result_collector.get_current_stats(simulation_id)
    if not stats:
        raise HTTPException(
            404, 
            f"No live stats for simulation '{simulation_id}'. "
            "Simulation may not be running or collecting results."
        )
    
    return {
        "simulation_id": simulation_id,
        "live": True,
        **stats
    }

