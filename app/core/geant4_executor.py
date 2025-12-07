"""
Real Geant4 Executor
====================

Interfaces with actual Geant4 installations to run simulations.
Supports:
- Running compiled Geant4 applications
- Generating and executing macro files
- Parsing output (ROOT, CSV, ASCII)
- Environment setup for Geant4
"""

import asyncio
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, AsyncGenerator, Callable
from datetime import datetime
from loguru import logger

from app.config import settings


class Geant4Environment:
    """Manages Geant4 environment variables and paths."""
    
    # Standard Geant4 data environment variables
    DATA_VARS = [
        "G4NEUTRONHPDATA",
        "G4LEDATA",
        "G4LEVELGAMMADATA",
        "G4RADIOACTIVEDATA",
        "G4PARTICLEXSDATA",
        "G4PIIDATA",
        "G4REALSURFACEDATA",
        "G4SAIDXSDATA",
        "G4ABLADATA",
        "G4INCLDATA",
        "G4ENSDFSTATEDATA",
        "G4TENDLDATA",
    ]
    
    def __init__(
        self,
        install_path: Optional[str] = None,
        data_path: Optional[str] = None
    ):
        self.install_path = Path(install_path) if install_path else None
        self.data_path = Path(data_path) if data_path else None
        self._env: Dict[str, str] = {}
        
    def setup(self) -> Dict[str, str]:
        """
        Set up Geant4 environment variables.
        Returns the environment dict to use for subprocess calls.
        """
        env = os.environ.copy()
        
        if self.install_path:
            # Add Geant4 bin to PATH
            bin_path = self.install_path / "bin"
            if bin_path.exists():
                env["PATH"] = str(bin_path) + os.pathsep + env.get("PATH", "")
            
            # Add lib to library path
            lib_path = self.install_path / "lib"
            if lib_path.exists():
                if os.name == 'nt':  # Windows
                    env["PATH"] = str(lib_path) + os.pathsep + env.get("PATH", "")
                else:  # Linux/Mac
                    env["LD_LIBRARY_PATH"] = str(lib_path) + os.pathsep + env.get("LD_LIBRARY_PATH", "")
        
        # Set data paths
        if self.data_path and self.data_path.exists():
            env["GEANT4_DATA_DIR"] = str(self.data_path)
            
            # Auto-detect data directories
            for data_dir in self.data_path.iterdir():
                if data_dir.is_dir():
                    name = data_dir.name
                    # Map directory names to environment variables
                    if "G4NEUTRONHP" in name or "NeutronHP" in name:
                        env["G4NEUTRONHPDATA"] = str(data_dir)
                    elif "G4EMLOW" in name or "G4LEDATA" in name:
                        env["G4LEDATA"] = str(data_dir)
                    elif "PhotonEvaporation" in name:
                        env["G4LEVELGAMMADATA"] = str(data_dir)
                    elif "RadioactiveDecay" in name:
                        env["G4RADIOACTIVEDATA"] = str(data_dir)
                    elif "G4PARTICLEXS" in name:
                        env["G4PARTICLEXSDATA"] = str(data_dir)
                    elif "G4PII" in name:
                        env["G4PIIDATA"] = str(data_dir)
                    elif "RealSurface" in name:
                        env["G4REALSURFACEDATA"] = str(data_dir)
                    elif "G4SAIDDATA" in name:
                        env["G4SAIDXSDATA"] = str(data_dir)
                    elif "G4ABLA" in name:
                        env["G4ABLADATA"] = str(data_dir)
                    elif "G4INCL" in name:
                        env["G4INCLDATA"] = str(data_dir)
                    elif "G4ENSDFSTATE" in name:
                        env["G4ENSDFSTATEDATA"] = str(data_dir)
                    elif "G4TENDL" in name:
                        env["G4TENDLDATA"] = str(data_dir)
        
        self._env = env
        return env
    
    def verify(self) -> Dict[str, Any]:
        """Verify Geant4 installation."""
        issues = []
        warnings = []
        info = {}
        
        if self.install_path:
            if not self.install_path.exists():
                issues.append(f"Install path does not exist: {self.install_path}")
            else:
                info["install_path"] = str(self.install_path)
                
                # Check for geant4-config
                config_script = self.install_path / "bin" / "geant4-config"
                if os.name == 'nt':
                    config_script = self.install_path / "bin" / "geant4-config.bat"
                
                if config_script.exists():
                    info["config_script"] = str(config_script)
                else:
                    warnings.append("geant4-config not found")
        else:
            issues.append("No Geant4 install path configured")
        
        if self.data_path:
            if not self.data_path.exists():
                issues.append(f"Data path does not exist: {self.data_path}")
            else:
                info["data_path"] = str(self.data_path)
                # Count data directories
                data_dirs = [d for d in self.data_path.iterdir() if d.is_dir()]
                info["data_directories"] = len(data_dirs)
        else:
            warnings.append("No Geant4 data path configured")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "info": info
        }


class Geant4Executor:
    """
    Executes real Geant4 simulations.
    """
    
    def __init__(
        self,
        executable_path: Optional[str] = None,
        install_path: Optional[str] = None,
        data_path: Optional[str] = None
    ):
        self.executable_path = Path(executable_path) if executable_path else None
        self.environment = Geant4Environment(install_path, data_path)
        self._process: Optional[asyncio.subprocess.Process] = None
        
    async def run_simulation(
        self,
        macro_file: Path,
        work_dir: Path,
        output_callback: Optional[Callable[[str], None]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run a Geant4 simulation with the given macro file.
        
        Yields progress updates as the simulation runs.
        """
        if not self.executable_path or not self.executable_path.exists():
            raise ValueError(f"Geant4 executable not found: {self.executable_path}")
        
        # Setup environment
        env = self.environment.setup()
        
        # Build command
        cmd = [str(self.executable_path), str(macro_file)]
        
        logger.info(f"Starting Geant4: {' '.join(cmd)}")
        logger.info(f"Working directory: {work_dir}")
        
        yield {
            "event_type": "status",
            "data": {"status": "starting", "message": "Launching Geant4 process..."}
        }
        
        # Start process
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(work_dir),
            env=env
        )
        
        yield {
            "event_type": "status",
            "data": {"status": "running", "message": "Geant4 process started", "pid": self._process.pid}
        }
        
        # Parse output in real-time
        events_completed = 0
        events_total = 0
        start_time = datetime.now()
        
        async for line in self._read_output():
            # Parse Geant4 output for progress
            parsed = self._parse_output_line(line)
            
            if parsed:
                if parsed.get("type") == "run_start":
                    events_total = parsed.get("events", 0)
                    yield {
                        "event_type": "progress",
                        "data": {
                            "events_completed": 0,
                            "events_total": events_total,
                            "progress_percent": 0,
                            "message": f"Starting run with {events_total} events"
                        }
                    }
                
                elif parsed.get("type") == "event":
                    events_completed = parsed.get("event_id", 0) + 1
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = events_completed / elapsed if elapsed > 0 else 0
                    remaining = (events_total - events_completed) / rate if rate > 0 else None
                    
                    yield {
                        "event_type": "progress",
                        "data": {
                            "events_completed": events_completed,
                            "events_total": events_total,
                            "progress_percent": (events_completed / events_total * 100) if events_total > 0 else 0,
                            "elapsed_time": elapsed,
                            "estimated_remaining": remaining,
                            "event_rate": rate
                        }
                    }
                
                elif parsed.get("type") == "hit":
                    yield {
                        "event_type": "hit",
                        "data": parsed
                    }
            
            # Forward output for logging
            if output_callback:
                output_callback(line)
        
        # Wait for process to complete
        return_code = await self._process.wait()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if return_code == 0:
            yield {
                "event_type": "completed",
                "data": {
                    "status": "completed",
                    "return_code": return_code,
                    "total_events": events_completed,
                    "elapsed_time": elapsed,
                    "events_per_second": events_completed / elapsed if elapsed > 0 else 0
                }
            }
        else:
            yield {
                "event_type": "error",
                "data": {
                    "status": "failed",
                    "return_code": return_code,
                    "message": f"Geant4 exited with code {return_code}"
                }
            }
    
    async def _read_output(self) -> AsyncGenerator[str, None]:
        """Read process output line by line."""
        if not self._process or not self._process.stdout:
            return
        
        while True:
            line = await self._process.stdout.readline()
            if not line:
                break
            yield line.decode('utf-8', errors='replace').strip()
    
    def _parse_output_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse Geant4 output line for relevant information."""
        
        # Match event processing output
        # Common formats:
        # ">>> Event 100" or "Event: 100" or "Processing event 100"
        event_patterns = [
            r">>> Event\s+(\d+)",
            r"Event:\s*(\d+)",
            r"Processing event\s+(\d+)",
            r"---> Event\s+(\d+)",
        ]
        
        for pattern in event_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return {"type": "event", "event_id": int(match.group(1))}
        
        # Match run start
        # "Run 0 starts" or "/run/beamOn 1000"
        run_patterns = [
            r"Run\s+\d+\s+starts.*?(\d+)\s+events",
            r"/run/beamOn\s+(\d+)",
            r"Number of events\s*[=:]\s*(\d+)",
        ]
        
        for pattern in run_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return {"type": "run_start", "events": int(match.group(1))}
        
        # Match hit data (customize based on your application output)
        # Example: "Hit: detector=phantom edep=0.523 MeV pos=(10.2, 5.1, 100.3)"
        hit_pattern = r"Hit:\s*detector=(\w+)\s+edep=([\d.]+)"
        match = re.search(hit_pattern, line, re.IGNORECASE)
        if match:
            return {
                "type": "hit",
                "detector": match.group(1),
                "energy_deposit": float(match.group(2))
            }
        
        return None
    
    async def terminate(self):
        """Terminate the running process."""
        if self._process:
            self._process.terminate()
            await self._process.wait()
            self._process = None
    
    async def kill(self):
        """Kill the running process immediately."""
        if self._process:
            self._process.kill()
            await self._process.wait()
            self._process = None


class MacroGenerator:
    """Generates Geant4 macro files from API configurations."""
    
    @staticmethod
    def generate_full_macro(
        geometry_config: Optional[Dict] = None,
        physics_config: Optional[Dict] = None,
        source_config: Optional[Dict] = None,
        simulation_config: Optional[Dict] = None,
        gdml_file: Optional[str] = None
    ) -> str:
        """Generate a complete Geant4 macro file."""
        lines = [
            "# ============================================",
            "# Geant4 Macro - Auto-generated by Geant4 API",
            f"# Generated: {datetime.now().isoformat()}",
            "# ============================================",
            "",
        ]
        
        # Verbosity settings
        sim = simulation_config or {}
        verbose = sim.get("verbose_level", 0)
        tracking_verbose = sim.get("tracking_verbose", 0)
        
        lines.extend([
            "# Verbosity",
            f"/control/verbose {verbose}",
            f"/run/verbose {verbose}",
            f"/event/verbose {verbose}",
            f"/tracking/verbose {tracking_verbose}",
            "",
        ])
        
        # GDML geometry loading (if provided)
        if gdml_file:
            lines.extend([
                "# Geometry from GDML",
                f'# /persistency/gdml/read {gdml_file}',
                "",
            ])
        
        # Physics cuts
        if physics_config:
            physics = physics_config
            default_cut = physics.get("default_cut", 1.0)
            lines.extend([
                "# Physics cuts",
                f"/run/setCut {default_cut} mm",
                "",
            ])
            
            # Production cuts by particle
            if physics.get("production_cuts"):
                cuts = physics["production_cuts"]
                lines.append("/run/setCutForAGivenParticle gamma {:.4f} mm".format(cuts.get("gamma", 1.0)))
                lines.append("/run/setCutForAGivenParticle e- {:.4f} mm".format(cuts.get("electron", 1.0)))
                lines.append("/run/setCutForAGivenParticle e+ {:.4f} mm".format(cuts.get("positron", 1.0)))
                lines.append("/run/setCutForAGivenParticle proton {:.4f} mm".format(cuts.get("proton", 1.0)))
                lines.append("")
        
        # Initialize run manager
        lines.extend([
            "# Initialize",
            "/run/initialize",
            "",
        ])
        
        # Particle source (GPS)
        if source_config:
            source = source_config
            particle = source.get("particle", "gamma")
            
            lines.extend([
                "# Particle source (GPS)",
                f"/gps/particle {particle}",
            ])
            
            # Energy
            energy = source.get("energy", {})
            distribution = energy.get("distribution", "mono")
            energy_value = energy.get("value", 1.0)
            
            if distribution == "mono":
                lines.append("/gps/ene/type Mono")
                lines.append(f"/gps/ene/mono {energy_value} MeV")
            elif distribution == "gaussian":
                lines.append("/gps/ene/type Gauss")
                lines.append(f"/gps/ene/mono {energy_value} MeV")
                sigma = energy.get("sigma", energy_value * 0.01)
                lines.append(f"/gps/ene/sigma {sigma} MeV")
            elif distribution == "flat":
                lines.append("/gps/ene/type Lin")
                lines.append(f"/gps/ene/min {energy.get('min_energy', 0.1)} MeV")
                lines.append(f"/gps/ene/max {energy.get('max_energy', 10.0)} MeV")
                lines.append("/gps/ene/gradient 0")
                lines.append("/gps/ene/intercept 1")
            
            # Position
            position = source.get("position", {})
            pos_dist = position.get("distribution", "point")
            center = position.get("center", {"x": 0, "y": 0, "z": 0})
            
            if pos_dist == "point":
                lines.append("/gps/pos/type Point")
            elif pos_dist == "plane":
                lines.append("/gps/pos/type Plane")
                lines.append("/gps/pos/shape Rectangle")
                if position.get("half_x"):
                    lines.append(f"/gps/pos/halfx {position['half_x']} mm")
                if position.get("half_y"):
                    lines.append(f"/gps/pos/halfy {position['half_y']} mm")
            elif pos_dist == "volume":
                lines.append("/gps/pos/type Volume")
                lines.append("/gps/pos/shape Para")
            
            lines.append(f"/gps/pos/centre {center.get('x', 0)} {center.get('y', 0)} {center.get('z', 0)} mm")
            
            # Direction
            direction = source.get("direction", {})
            dir_dist = direction.get("distribution", "directed")
            dir_vec = direction.get("direction", {"x": 0, "y": 0, "z": 1})
            
            if dir_dist == "directed":
                lines.append(f"/gps/direction {dir_vec.get('x', 0)} {dir_vec.get('y', 0)} {dir_vec.get('z', 1)}")
            elif dir_dist == "isotropic":
                lines.append("/gps/ang/type iso")
            elif dir_dist == "cone":
                lines.append("/gps/ang/type focused")
                lines.append(f"/gps/ang/focuspoint {dir_vec.get('x', 0)} {dir_vec.get('y', 0)} {dir_vec.get('z', 0)} mm")
                if direction.get("cone_angle"):
                    lines.append(f"/gps/ang/maxtheta {direction['cone_angle']} deg")
            
            lines.append("")
        
        # Run simulation
        num_events = sim.get("num_events", 1000)
        
        # Optional: output commands (depends on your application)
        lines.extend([
            "# Output settings",
            "# /analysis/setFileName output",
            "# /analysis/h1/set 1 100 0. 10. MeV",
            "",
        ])
        
        lines.extend([
            "# Start simulation",
            f"/run/beamOn {num_events}",
            "",
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def save_macro(content: str, path: Path) -> Path:
        """Save macro content to file."""
        path.write_text(content)
        logger.info(f"Saved macro to {path}")
        return path


class OutputParser:
    """Parses Geant4 output files (ROOT, CSV, ASCII)."""
    
    @staticmethod
    def parse_csv(file_path: Path) -> List[Dict[str, Any]]:
        """Parse CSV output file."""
        import csv
        
        results = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric values
                parsed_row = {}
                for key, value in row.items():
                    try:
                        parsed_row[key] = float(value)
                    except (ValueError, TypeError):
                        parsed_row[key] = value
                results.append(parsed_row)
        
        return results
    
    @staticmethod
    def parse_ascii_histogram(file_path: Path) -> Dict[str, Any]:
        """Parse ASCII histogram file from Geant4 analysis."""
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Parse header
        header = {}
        data = []
        in_data = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                # Parse header comments
                if '=' in line:
                    key, value = line.split('=', 1)
                    header[key.strip('# ')] = value.strip()
                continue
            
            # Data line
            parts = line.split()
            if len(parts) >= 2:
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    data.append({"x": x, "y": y})
                except ValueError:
                    continue
        
        return {
            "header": header,
            "data": data
        }
    
    @staticmethod
    def find_output_files(work_dir: Path, patterns: List[str] = None) -> Dict[str, List[Path]]:
        """Find output files in working directory."""
        if patterns is None:
            patterns = ["*.csv", "*.root", "*.txt", "*.dat"]
        
        files = {}
        for pattern in patterns:
            matched = list(work_dir.glob(pattern))
            if matched:
                ext = pattern.replace("*", "")
                files[ext] = matched
        
        return files


# Global executor instance (configure with actual paths)
geant4_executor = Geant4Executor(
    executable_path=settings.geant4_install_path + "/bin/your_app" if settings.geant4_install_path else None,
    install_path=settings.geant4_install_path,
    data_path=settings.geant4_data_path
)

