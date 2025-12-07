"""
Result collector for aggregating and storing simulation results.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from app.models.results import (
    SimulationResults, HitData, TrajectoryData,
    EventSummary, DetectorSummary, ScoringResult,
    HistogramData, AnalysisResult
)


class ResultCollector:
    """
    Collects, aggregates, and stores simulation results.
    
    Features:
    - Real-time hit accumulation
    - Histogram generation
    - Statistical analysis
    - Multiple export formats
    """
    
    def __init__(self, results_path: str = "./results"):
        self.results_path = Path(results_path)
        self.results_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage for active simulations
        self._active_collectors: Dict[str, Dict[str, Any]] = {}
    
    def create_collector(self, simulation_id: str):
        """Initialize a new result collector for a simulation."""
        self._active_collectors[simulation_id] = {
            "hits": [],
            "trajectories": [],
            "event_summaries": [],
            "energy_deposits": {},  # detector_name -> list of deposits
            "particle_counts": {},
            "start_time": datetime.utcnow(),
            "events_processed": 0
        }
        logger.info(f"Created result collector for simulation {simulation_id}")
    
    def add_hit(self, simulation_id: str, hit: Dict[str, Any]):
        """Add a hit to the collector."""
        if simulation_id not in self._active_collectors:
            self.create_collector(simulation_id)
        
        collector = self._active_collectors[simulation_id]
        collector["hits"].append(hit)
        
        # Update aggregates
        detector = hit.get("detector_name", "unknown")
        energy = hit.get("energy_deposit", 0)
        
        if detector not in collector["energy_deposits"]:
            collector["energy_deposits"][detector] = []
        collector["energy_deposits"][detector].append(energy)
        
        # Count particles
        particle = hit.get("particle_name", "unknown")
        collector["particle_counts"][particle] = \
            collector["particle_counts"].get(particle, 0) + 1
    
    def add_hits_batch(self, simulation_id: str, hits: List[Dict[str, Any]]):
        """Add multiple hits at once."""
        for hit in hits:
            self.add_hit(simulation_id, hit)
    
    def add_trajectory(self, simulation_id: str, trajectory: Dict[str, Any]):
        """Add a trajectory to the collector."""
        if simulation_id not in self._active_collectors:
            self.create_collector(simulation_id)
        
        self._active_collectors[simulation_id]["trajectories"].append(trajectory)
    
    def add_event_summary(self, simulation_id: str, summary: Dict[str, Any]):
        """Add an event summary."""
        if simulation_id not in self._active_collectors:
            self.create_collector(simulation_id)
        
        collector = self._active_collectors[simulation_id]
        collector["event_summaries"].append(summary)
        collector["events_processed"] += 1
    
    def get_current_stats(self, simulation_id: str) -> Dict[str, Any]:
        """Get current statistics for an active simulation."""
        if simulation_id not in self._active_collectors:
            return {}
        
        collector = self._active_collectors[simulation_id]
        
        stats = {
            "events_processed": collector["events_processed"],
            "total_hits": len(collector["hits"]),
            "particle_counts": collector["particle_counts"],
            "detectors": {}
        }
        
        # Detector statistics
        for detector, deposits in collector["energy_deposits"].items():
            if deposits:
                stats["detectors"][detector] = {
                    "hits": len(deposits),
                    "total_energy": sum(deposits),
                    "mean_energy": np.mean(deposits),
                    "max_energy": max(deposits)
                }
        
        return stats
    
    def finalize(self, simulation_id: str) -> SimulationResults:
        """
        Finalize collection and generate results.
        """
        if simulation_id not in self._active_collectors:
            raise ValueError(f"No collector found for {simulation_id}")
        
        collector = self._active_collectors[simulation_id]
        end_time = datetime.utcnow()
        elapsed = (end_time - collector["start_time"]).total_seconds()
        
        # Generate detector summaries
        detector_summaries = []
        total_energy = 0
        
        for detector, deposits in collector["energy_deposits"].items():
            if deposits:
                total_dep = sum(deposits)
                total_energy += total_dep
                
                events = collector["events_processed"] or 1
                mean_per_event = total_dep / events
                std_per_event = np.std(deposits) if len(deposits) > 1 else 0
                
                detector_summaries.append(DetectorSummary(
                    name=detector,
                    total_hits=len(deposits),
                    total_energy_deposit=total_dep,
                    mean_energy_per_event=mean_per_event,
                    std_energy_per_event=float(std_per_event),
                    hit_efficiency=len(deposits) / events if events > 0 else 0
                ))
        
        # Create results object
        results = SimulationResults(
            simulation_id=simulation_id,
            simulation_name=f"sim_{simulation_id[:8]}",
            completed_at=end_time,
            num_events=collector["events_processed"],
            elapsed_time=elapsed,
            events_per_second=collector["events_processed"] / elapsed if elapsed > 0 else 0,
            random_seed=0,
            total_energy_deposited=total_energy,
            detector_summaries=detector_summaries,
            primary_particles_generated=collector["events_processed"],
            total_secondaries_created=sum(collector["particle_counts"].values()),
            particle_statistics=collector["particle_counts"],
            hits=[HitData(**h) for h in collector["hits"][:1000]] if collector["hits"] else None,
        )
        
        # Save to file
        self._save_results(simulation_id, results)
        
        # Cleanup
        del self._active_collectors[simulation_id]
        
        return results
    
    def _save_results(self, simulation_id: str, results: SimulationResults):
        """Save results to file."""
        sim_path = self.results_path / simulation_id
        sim_path.mkdir(parents=True, exist_ok=True)
        
        # Save JSON summary
        summary_path = sim_path / "results.json"
        summary_path.write_text(results.model_dump_json(indent=2))
        
        logger.info(f"Saved results to {summary_path}")
    
    def load_results(self, simulation_id: str) -> Optional[SimulationResults]:
        """Load results from file."""
        results_file = self.results_path / simulation_id / "results.json"
        
        if not results_file.exists():
            return None
        
        data = json.loads(results_file.read_text())
        return SimulationResults(**data)
    
    def create_histogram(
        self,
        data: List[float],
        name: str,
        title: str,
        x_label: str,
        bins: int = 100,
        x_range: Optional[tuple] = None
    ) -> HistogramData:
        """Create a histogram from data."""
        if not data:
            return HistogramData(
                name=name,
                title=title,
                x_label=x_label,
                y_label="Counts",
                bins=bins,
                x_min=0,
                x_max=1,
                bin_edges=[0, 1],
                bin_contents=[0],
                entries=0
            )
        
        if x_range:
            hist, edges = np.histogram(data, bins=bins, range=x_range)
        else:
            hist, edges = np.histogram(data, bins=bins)
        
        return HistogramData(
            name=name,
            title=title,
            x_label=x_label,
            y_label="Counts",
            bins=bins,
            x_min=float(edges[0]),
            x_max=float(edges[-1]),
            bin_edges=edges.tolist(),
            bin_contents=hist.tolist(),
            bin_errors=[np.sqrt(h) for h in hist],
            entries=len(data),
            mean=float(np.mean(data)),
            std_dev=float(np.std(data))
        )
    
    def generate_analysis(
        self,
        simulation_id: str,
        analysis_type: str = "standard"
    ) -> Optional[AnalysisResult]:
        """Generate analysis results with histograms."""
        results = self.load_results(simulation_id)
        if not results:
            return None
        
        histograms = []
        
        # Energy deposit histogram (if hits available)
        if results.hits:
            energy_data = [h.energy_deposit for h in results.hits]
            histograms.append(self.create_histogram(
                energy_data,
                name="edep_hist",
                title="Energy Deposit Distribution",
                x_label="Energy (MeV)",
                bins=100
            ))
        
        # Summary statistics
        summary_stats = {
            "total_events": results.num_events,
            "total_energy": results.total_energy_deposited,
            "particles": results.particle_statistics,
            "event_rate": results.events_per_second
        }
        
        return AnalysisResult(
            simulation_id=simulation_id,
            analysis_type=analysis_type,
            histograms=histograms,
            summary_stats=summary_stats
        )
    
    def export_csv(self, simulation_id: str, output_path: Path) -> Path:
        """Export hits to CSV format."""
        results = self.load_results(simulation_id)
        if not results or not results.hits:
            raise ValueError("No hits data to export")
        
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'event_id', 'track_id', 'particle_name', 'detector_name',
                'position_x', 'position_y', 'position_z',
                'energy_deposit', 'kinetic_energy', 'global_time'
            ])
            writer.writeheader()
            
            for hit in results.hits:
                writer.writerow({
                    'event_id': hit.event_id,
                    'track_id': hit.track_id,
                    'particle_name': hit.particle_name,
                    'detector_name': hit.detector_name,
                    'position_x': hit.position_x,
                    'position_y': hit.position_y,
                    'position_z': hit.position_z,
                    'energy_deposit': hit.energy_deposit,
                    'kinetic_energy': hit.kinetic_energy,
                    'global_time': hit.global_time
                })
        
        logger.info(f"Exported CSV to {output_path}")
        return output_path
    
    def list_simulations(self) -> List[str]:
        """List all simulation IDs with saved results."""
        return [
            d.name for d in self.results_path.iterdir()
            if d.is_dir() and (d / "results.json").exists()
        ]


# Global result collector instance
result_collector = ResultCollector()

