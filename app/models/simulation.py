"""
Simulation configuration and status models.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid


class SimulationStatus(str, Enum):
    """Simulation execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationMode(str, Enum):
    """Simulation execution mode."""
    BATCH = "batch"
    INTERACTIVE = "interactive"
    VISUALIZATION = "visualization"


class OutputFormat(str, Enum):
    """Output data format."""
    JSON = "json"
    CSV = "csv"
    ROOT = "root"
    HDF5 = "hdf5"
    NUMPY = "numpy"


class SimulationConfig(BaseModel):
    """Complete simulation configuration."""
    name: str = Field(..., description="Simulation name")
    description: Optional[str] = Field(default=None, description="Description")
    
    # Number of events
    num_events: int = Field(default=1000, description="Number of events to simulate")
    
    # Execution settings
    mode: SimulationMode = Field(
        default=SimulationMode.BATCH,
        description="Execution mode"
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed (None for auto)"
    )
    num_threads: int = Field(
        default=1,
        description="Number of worker threads"
    )
    
    # Output settings
    output_format: OutputFormat = Field(
        default=OutputFormat.JSON,
        description="Output data format"
    )
    output_every_n_events: int = Field(
        default=100,
        description="Stream results every N events"
    )
    save_trajectories: bool = Field(
        default=False,
        description="Save particle trajectories"
    )
    save_secondaries: bool = Field(
        default=True,
        description="Save secondary particle info"
    )
    
    # Verbosity
    verbose_level: int = Field(
        default=0,
        description="Geant4 verbosity (0-5)"
    )
    tracking_verbose: int = Field(
        default=0,
        description="Tracking verbosity"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "gamma_in_water",
                "description": "1 MeV gamma in water phantom",
                "num_events": 10000,
                "mode": "batch",
                "num_threads": 4,
                "output_format": "json",
                "output_every_n_events": 100
            }
        }


class SimulationRequest(BaseModel):
    """Full simulation request combining all configurations."""
    simulation: SimulationConfig = Field(..., description="Simulation settings")
    geometry_id: Optional[str] = Field(
        default=None,
        description="Reference to saved geometry config"
    )
    geometry: Optional[Any] = Field(
        default=None,
        description="Inline geometry configuration"
    )
    physics_id: Optional[str] = Field(
        default=None,
        description="Reference to saved physics config"
    )
    physics: Optional[Any] = Field(
        default=None,
        description="Inline physics configuration"
    )
    source_id: Optional[str] = Field(
        default=None,
        description="Reference to saved source config"
    )
    source: Optional[Any] = Field(
        default=None,
        description="Inline source configuration"
    )
    scoring_meshes: List[Any] = Field(
        default_factory=list,
        description="Scoring mesh configurations"
    )


class SimulationProgress(BaseModel):
    """Real-time simulation progress update."""
    simulation_id: str
    status: SimulationStatus
    events_completed: int = 0
    events_total: int = 0
    progress_percent: float = 0.0
    elapsed_time: float = 0.0
    estimated_remaining: Optional[float] = None
    current_event_rate: Optional[float] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SimulationJob(BaseModel):
    """Simulation job record."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: SimulationStatus = SimulationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Configuration references
    config: SimulationConfig
    geometry_config: Optional[Dict[str, Any]] = None
    physics_config: Optional[Dict[str, Any]] = None
    source_config: Optional[Dict[str, Any]] = None
    
    # Progress tracking
    events_completed: int = 0
    events_total: int = 0
    
    # Results
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "test_simulation",
                "status": "running",
                "events_completed": 5000,
                "events_total": 10000
            }
        }

