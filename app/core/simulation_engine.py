"""
Main simulation engine that orchestrates Geant4 simulations.

Supports two modes:
1. Direct Python bindings (geant4-pybind11)
2. Subprocess mode (calls Geant4 executable with macro files)
3. Real Geant4 execution with custom application
"""

import asyncio
import json
import os
import subprocess
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator, Callable
from loguru import logger

from app.config import settings
from app.models.simulation import (
    SimulationConfig, SimulationStatus, SimulationProgress, SimulationJob
)
from app.models.geometry import DetectorGeometry
from app.models.physics import PhysicsConfig
from app.models.particle import ParticleSource
from app.models.results import SimulationResults, StreamingEvent, HitData

# Import the real Geant4 executor
from app.core.geant4_executor import (
    Geant4Executor, Geant4Environment, MacroGenerator, OutputParser
)


class SimulationEngine:
    """
    Main Geant4 simulation engine.
    
    Manages simulation lifecycle and provides real-time progress updates
    via async generators for WebSocket streaming.
    """
    
    def __init__(self):
        self.active_simulations: Dict[str, SimulationJob] = {}
        self.simulation_processes: Dict[str, subprocess.Popen] = {}
        self._callbacks: Dict[str, list] = {}
        self._use_pybind = not settings.geant4_use_subprocess
        
        # Geant4 configuration
        self._geant4_executable: Optional[Path] = None
        self._geant4_install_path: Optional[Path] = None
        self._geant4_data_path: Optional[Path] = None
        
        # Initialize from settings
        if settings.geant4_install_path:
            self._geant4_install_path = Path(settings.geant4_install_path)
        if settings.geant4_data_path:
            self._geant4_data_path = Path(settings.geant4_data_path)
        
        # Create Geant4 executor
        self._executor: Optional[Geant4Executor] = None
        self._environment = Geant4Environment(
            install_path=settings.geant4_install_path,
            data_path=settings.geant4_data_path
        )
        
        # Try to import geant4-pybind if available
        self._g4_available = False
        if self._use_pybind:
            try:
                import geant4_pybind as g4
                self._g4 = g4
                self._g4_available = True
                logger.info("Geant4 Python bindings loaded successfully")
            except ImportError:
                logger.warning(
                    "geant4-pybind not available, falling back to subprocess mode"
                )
                self._use_pybind = False
    
    def configure_geant4(
        self,
        install_path: Optional[str] = None,
        data_path: Optional[str] = None,
        executable_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configure Geant4 installation paths.
        
        Args:
            install_path: Path to Geant4 installation (e.g., C:/Geant4/geant4-v11.2.0-install)
            data_path: Path to Geant4 data files (usually install_path/share/Geant4/data)
            executable_path: Path to compiled Geant4 application
        
        Returns:
            Configuration status and validation results
        """
        if install_path:
            self._geant4_install_path = Path(install_path)
        if data_path:
            self._geant4_data_path = Path(data_path)
        elif install_path:
            # Auto-detect data path
            auto_data = Path(install_path) / "share" / "Geant4" / "data"
            if auto_data.exists():
                self._geant4_data_path = auto_data
        
        if executable_path:
            self._geant4_executable = Path(executable_path)
        
        # Update environment
        self._environment = Geant4Environment(
            install_path=str(self._geant4_install_path) if self._geant4_install_path else None,
            data_path=str(self._geant4_data_path) if self._geant4_data_path else None
        )
        
        # Create executor if executable is specified
        if self._geant4_executable:
            self._executor = Geant4Executor(
                executable_path=str(self._geant4_executable),
                install_path=str(self._geant4_install_path) if self._geant4_install_path else None,
                data_path=str(self._geant4_data_path) if self._geant4_data_path else None
            )
        
        # Verify installation
        verification = self._environment.verify()
        
        logger.info(f"Geant4 configured: install={self._geant4_install_path}, data={self._geant4_data_path}")
        
        return {
            "configured": True,
            "install_path": str(self._geant4_install_path) if self._geant4_install_path else None,
            "data_path": str(self._geant4_data_path) if self._geant4_data_path else None,
            "executable_path": str(self._geant4_executable) if self._geant4_executable else None,
            "verification": verification
        }
    
    def get_geant4_status(self) -> Dict[str, Any]:
        """Get current Geant4 configuration status."""
        verification = self._environment.verify()
        
        return {
            "configured": self._geant4_install_path is not None,
            "install_path": str(self._geant4_install_path) if self._geant4_install_path else None,
            "data_path": str(self._geant4_data_path) if self._geant4_data_path else None,
            "executable_path": str(self._geant4_executable) if self._geant4_executable else None,
            "executor_ready": self._executor is not None,
            "pybind_available": self._g4_available,
            "verification": verification
        }
    
    async def create_simulation(
        self,
        config: SimulationConfig,
        geometry: Optional[DetectorGeometry] = None,
        physics: Optional[PhysicsConfig] = None,
        source: Optional[ParticleSource] = None,
    ) -> SimulationJob:
        """Create a new simulation job."""
        job = SimulationJob(
            name=config.name,
            config=config,
            events_total=config.num_events,
            geometry_config=geometry.model_dump() if geometry else None,
            physics_config=physics.model_dump() if physics else None,
            source_config=source.model_dump() if source else None,
        )
        
        self.active_simulations[job.id] = job
        logger.info(f"Created simulation job: {job.id} ({job.name})")
        
        return job
    
    async def start_simulation(
        self, 
        job_id: str
    ) -> AsyncGenerator[StreamingEvent, None]:
        """
        Start a simulation and yield real-time progress events.
        
        This is an async generator that yields StreamingEvent objects
        suitable for WebSocket streaming.
        """
        if job_id not in self.active_simulations:
            raise ValueError(f"Simulation {job_id} not found")
        
        job = self.active_simulations[job_id]
        job.status = SimulationStatus.INITIALIZING
        job.started_at = datetime.utcnow()
        
        yield StreamingEvent(
            event_type="status",
            simulation_id=job_id,
            data={"status": "initializing", "message": "Preparing simulation..."}
        )
        
        try:
            if self._use_pybind and self._g4_available:
                async for event in self._run_with_pybind(job):
                    yield event
            else:
                async for event in self._run_with_subprocess(job):
                    yield event
                    
        except Exception as e:
            job.status = SimulationStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Simulation {job_id} failed: {e}")
            yield StreamingEvent(
                event_type="error",
                simulation_id=job_id,
                data={"error": str(e), "status": "failed"}
            )
    
    async def _run_with_subprocess(
        self, 
        job: SimulationJob
    ) -> AsyncGenerator[StreamingEvent, None]:
        """Run simulation using subprocess and macro files."""
        
        # Create working directory for this simulation
        work_dir = Path(settings.results_path) / job.id
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate macro file using MacroGenerator
        macro_content = MacroGenerator.generate_full_macro(
            geometry_config=job.geometry_config,
            physics_config=job.physics_config,
            source_config=job.source_config,
            simulation_config=job.config.model_dump()
        )
        macro_path = work_dir / "run.mac"
        MacroGenerator.save_macro(macro_content, macro_path)
        
        # Generate GDML geometry if provided
        gdml_path = None
        if job.geometry_config:
            gdml_path = work_dir / "geometry.gdml"
            self._generate_gdml(job.geometry_config, gdml_path)
        
        yield StreamingEvent(
            event_type="status",
            simulation_id=job.id,
            data={"status": "running", "message": "Starting Geant4 process..."}
        )
        
        job.status = SimulationStatus.RUNNING
        start_time = time.time()
        
        # Check if we have a real Geant4 executor
        if self._executor and self._geant4_executable and self._geant4_executable.exists():
            # Run with REAL Geant4
            logger.info(f"Running simulation with real Geant4: {self._geant4_executable}")
            
            yield StreamingEvent(
                event_type="status",
                simulation_id=job.id,
                data={
                    "status": "running", 
                    "message": f"Launching Geant4: {self._geant4_executable.name}",
                    "real_geant4": True
                }
            )
            
            async for event in self._executor.run_simulation(
                macro_file=macro_path,
                work_dir=work_dir,
                output_callback=lambda line: logger.debug(f"G4: {line}")
            ):
                # Update job status based on events
                if event.get("event_type") == "progress":
                    data = event.get("data", {})
                    job.events_completed = data.get("events_completed", 0)
                
                yield StreamingEvent(
                    event_type=event.get("event_type", "unknown"),
                    simulation_id=job.id,
                    data=event.get("data", {})
                )
                
                if event.get("event_type") in ["completed", "error"]:
                    break
            
            # Parse output files
            output_files = OutputParser.find_output_files(work_dir)
            if output_files:
                yield StreamingEvent(
                    event_type="output_files",
                    simulation_id=job.id,
                    data={"files": {k: [str(f) for f in v] for k, v in output_files.items()}}
                )
        
        else:
            # Simulation mode (no real Geant4)
            logger.warning("No Geant4 executable configured - running in simulation mode")
            
            yield StreamingEvent(
                event_type="status",
                simulation_id=job.id,
                data={
                    "status": "running", 
                    "message": "Running in SIMULATION mode (no real Geant4)",
                    "real_geant4": False
                }
            )
            
            total_events = job.config.num_events
            batch_size = job.config.output_every_n_events
            
            for i in range(0, total_events, batch_size):
                # Simulate processing time
                await asyncio.sleep(0.05)  # Simulated processing
                
                events_done = min(i + batch_size, total_events)
                job.events_completed = events_done
                
                elapsed = time.time() - start_time
                progress = events_done / total_events * 100
                rate = events_done / elapsed if elapsed > 0 else 0
                remaining = (total_events - events_done) / rate if rate > 0 else None
                
                # Yield progress update
                yield StreamingEvent(
                    event_type="progress",
                    simulation_id=job.id,
                    data={
                        "events_completed": events_done,
                        "events_total": total_events,
                        "progress_percent": progress,
                        "elapsed_time": elapsed,
                        "estimated_remaining": remaining,
                        "event_rate": rate
                    }
                )
                
                # Yield simulated event data
                yield StreamingEvent(
                    event_type="event_batch",
                    simulation_id=job.id,
                    data={
                        "batch_start": i,
                        "batch_end": events_done,
                        "sample_hits": self._generate_sample_hits(i, batch_size)
                    }
                )
        
        # Simulation complete
        job.status = SimulationStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.result_path = str(work_dir)
        
        elapsed = time.time() - start_time
        
        yield StreamingEvent(
            event_type="completed",
            simulation_id=job.id,
            data={
                "status": "completed",
                "total_events": job.events_completed,
                "elapsed_time": elapsed,
                "events_per_second": job.events_completed / elapsed if elapsed > 0 else 0,
                "result_path": str(work_dir)
            }
        )
    
    async def _run_with_pybind(
        self, 
        job: SimulationJob
    ) -> AsyncGenerator[StreamingEvent, None]:
        """Run simulation using geant4-pybind11 bindings."""
        
        yield StreamingEvent(
            event_type="status",
            simulation_id=job.id,
            data={"status": "running", "message": "Running with Python bindings..."}
        )
        
        # This would use actual geant4-pybind API
        # For now, fall back to subprocess simulation
        async for event in self._run_with_subprocess(job):
            yield event
    
    def _generate_macro_file(self, job: SimulationJob, path: Path):
        """Generate Geant4 macro file from configuration."""
        lines = [
            "# Auto-generated Geant4 macro",
            f"# Simulation: {job.name}",
            f"# Generated: {datetime.utcnow().isoformat()}",
            "",
            "# Verbosity",
            f"/run/verbose {job.config.verbose_level}",
            f"/tracking/verbose {job.config.tracking_verbose}",
            "",
        ]
        
        # Physics configuration
        if job.physics_config:
            physics = job.physics_config
            lines.extend([
                "# Physics",
                f"/run/setCut {physics.get('default_cut', 1.0)} mm",
                "",
            ])
        
        # Source configuration
        if job.source_config:
            source = job.source_config
            particle = source.get('particle', 'gamma')
            energy = source.get('energy', {}).get('value', 1.0)
            pos = source.get('position', {}).get('center', {})
            direction = source.get('direction', {}).get('direction', {})
            
            lines.extend([
                "# Particle source",
                "/gps/particle " + particle,
                f"/gps/energy {energy} MeV",
                f"/gps/position {pos.get('x', 0)} {pos.get('y', 0)} {pos.get('z', 0)} mm",
                f"/gps/direction {direction.get('x', 0)} {direction.get('y', 0)} {direction.get('z', 1)}",
                "",
            ])
        
        # Initialize and run
        lines.extend([
            "# Initialize",
            "/run/initialize",
            "",
            "# Run simulation",
            f"/run/beamOn {job.config.num_events}",
        ])
        
        path.write_text("\n".join(lines))
        logger.debug(f"Generated macro file: {path}")
    
    def _generate_gdml(self, geometry_config: Dict[str, Any], path: Path):
        """Generate GDML file from geometry configuration."""
        # Simplified GDML generation
        gdml = f'''<?xml version="1.0" encoding="UTF-8"?>
<gdml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd">
    
    <define>
        <position name="center" x="0" y="0" z="0" unit="mm"/>
    </define>
    
    <materials>
        <material name="Air" Z="7">
            <D value="0.00129"/>
            <atom value="14.01"/>
        </material>
    </materials>
    
    <solids>
        <box name="World" x="{geometry_config.get('world', {}).get('half_x', 1000)*2}" 
             y="{geometry_config.get('world', {}).get('half_y', 1000)*2}" 
             z="{geometry_config.get('world', {}).get('half_z', 1000)*2}" lunit="mm"/>
    </solids>
    
    <structure>
        <volume name="World">
            <materialref ref="Air"/>
            <solidref ref="World"/>
        </volume>
    </structure>
    
    <setup name="Default" version="1.0">
        <world ref="World"/>
    </setup>
</gdml>'''
        
        path.write_text(gdml)
        logger.debug(f"Generated GDML file: {path}")
    
    def _generate_sample_hits(
        self, 
        start_event: int, 
        batch_size: int
    ) -> list:
        """Generate sample hit data for demonstration."""
        import random
        
        hits = []
        for i in range(min(10, batch_size)):  # Sample 10 hits per batch
            hits.append({
                "event_id": start_event + i,
                "detector": "detector_0",
                "particle": "gamma",
                "energy_deposit": random.uniform(0.01, 1.0),
                "position": {
                    "x": random.gauss(0, 10),
                    "y": random.gauss(0, 10),
                    "z": random.gauss(100, 5)
                }
            })
        return hits
    
    async def pause_simulation(self, job_id: str) -> bool:
        """Pause a running simulation."""
        if job_id not in self.active_simulations:
            return False
        
        job = self.active_simulations[job_id]
        if job.status == SimulationStatus.RUNNING:
            job.status = SimulationStatus.PAUSED
            logger.info(f"Paused simulation: {job_id}")
            return True
        return False
    
    async def resume_simulation(self, job_id: str) -> bool:
        """Resume a paused simulation."""
        if job_id not in self.active_simulations:
            return False
        
        job = self.active_simulations[job_id]
        if job.status == SimulationStatus.PAUSED:
            job.status = SimulationStatus.RUNNING
            logger.info(f"Resumed simulation: {job_id}")
            return True
        return False
    
    async def cancel_simulation(self, job_id: str) -> bool:
        """Cancel a simulation."""
        if job_id not in self.active_simulations:
            return False
        
        job = self.active_simulations[job_id]
        
        # Kill subprocess if running
        if job_id in self.simulation_processes:
            proc = self.simulation_processes[job_id]
            proc.terminate()
            del self.simulation_processes[job_id]
        
        job.status = SimulationStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        logger.info(f"Cancelled simulation: {job_id}")
        return True
    
    def get_simulation_status(self, job_id: str) -> Optional[SimulationJob]:
        """Get current simulation status."""
        return self.active_simulations.get(job_id)
    
    def list_simulations(self) -> list[SimulationJob]:
        """List all simulations."""
        return list(self.active_simulations.values())
    
    async def get_results(self, job_id: str) -> Optional[SimulationResults]:
        """Get simulation results."""
        job = self.active_simulations.get(job_id)
        if not job or job.status != SimulationStatus.COMPLETED:
            return None
        
        # Load results from file
        if job.result_path:
            results_file = Path(job.result_path) / "results.json"
            if results_file.exists():
                data = json.loads(results_file.read_text())
                return SimulationResults(**data)
        
        # Generate summary results
        elapsed = (job.completed_at - job.started_at).total_seconds()
        return SimulationResults(
            simulation_id=job.id,
            simulation_name=job.name,
            completed_at=job.completed_at,
            num_events=job.events_completed,
            elapsed_time=elapsed,
            events_per_second=job.events_completed / elapsed if elapsed > 0 else 0,
            random_seed=job.config.random_seed or 0,
            total_energy_deposited=0.0,
            detector_summaries=[],
            primary_particles_generated=job.events_completed,
            total_secondaries_created=0,
            particle_statistics={}
        )


# Global simulation engine instance
simulation_engine = SimulationEngine()

