"""
Models for simulation results and analysis.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class HitData(BaseModel):
    """Single detector hit data."""
    detector_name: str
    event_id: int
    track_id: int
    parent_id: int
    particle_name: str
    particle_pdg: int
    
    # Position
    position_x: float  # mm
    position_y: float  # mm
    position_z: float  # mm
    
    # Local position (in detector coordinates)
    local_x: Optional[float] = None
    local_y: Optional[float] = None
    local_z: Optional[float] = None
    
    # Momentum
    momentum_x: float  # MeV/c
    momentum_y: float  # MeV/c
    momentum_z: float  # MeV/c
    
    # Energy
    kinetic_energy: float  # MeV
    energy_deposit: float  # MeV
    
    # Time
    global_time: float  # ns
    local_time: float  # ns
    
    # Track info
    step_number: int
    track_length: float  # mm


class TrajectoryPoint(BaseModel):
    """Single point in a particle trajectory."""
    x: float
    y: float
    z: float
    t: float  # time in ns
    kinetic_energy: float  # MeV
    momentum_direction: List[float]  # unit vector


class TrajectoryData(BaseModel):
    """Complete particle trajectory."""
    event_id: int
    track_id: int
    parent_id: int
    particle_name: str
    particle_pdg: int
    initial_energy: float  # MeV
    points: List[TrajectoryPoint]
    process_name: str  # Creation process
    end_process: Optional[str] = None  # Process that stopped the track


class EventSummary(BaseModel):
    """Summary data for a single event."""
    event_id: int
    num_primaries: int
    num_secondaries: int
    
    # Total energy deposits per detector
    energy_deposits: Dict[str, float]
    
    # Particle counts
    particle_counts: Dict[str, int]
    
    # Primary particle info
    primary_particle: str
    primary_energy: float
    primary_direction: List[float]


class DetectorSummary(BaseModel):
    """Summary statistics for a detector."""
    name: str
    total_hits: int
    total_energy_deposit: float  # MeV
    mean_energy_per_event: float
    std_energy_per_event: float
    hit_efficiency: float  # fraction of events with hits


class ScoringResult(BaseModel):
    """Scoring mesh results."""
    mesh_name: str
    scoring_type: str
    
    # Mesh dimensions
    x_bins: int
    y_bins: int
    z_bins: int
    
    # Bin edges (mm)
    x_edges: List[float]
    y_edges: List[float]
    z_edges: List[float]
    
    # Data (flattened 3D array, row-major order)
    data: List[float]
    
    # Statistics
    total: float
    mean: float
    max_value: float
    min_value: float


class SimulationResults(BaseModel):
    """Complete simulation results."""
    simulation_id: str
    simulation_name: str
    completed_at: datetime
    
    # Run info
    num_events: int
    elapsed_time: float  # seconds
    events_per_second: float
    random_seed: int
    
    # Summary statistics
    total_energy_deposited: float  # MeV
    detector_summaries: List[DetectorSummary]
    
    # Particle statistics
    primary_particles_generated: int
    total_secondaries_created: int
    particle_statistics: Dict[str, int]
    
    # Detailed data (if requested)
    hits: Optional[List[HitData]] = None
    trajectories: Optional[List[TrajectoryData]] = None
    event_summaries: Optional[List[EventSummary]] = None
    scoring_results: Optional[List[ScoringResult]] = None


class StreamingEvent(BaseModel):
    """Real-time streaming event data."""
    event_type: str  # "progress", "event", "hit", "summary", "error"
    simulation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]


class HistogramData(BaseModel):
    """Histogram data for visualization."""
    name: str
    title: str
    x_label: str
    y_label: str
    bins: int
    x_min: float
    x_max: float
    bin_edges: List[float]
    bin_contents: List[float]
    bin_errors: Optional[List[float]] = None
    underflow: float = 0.0
    overflow: float = 0.0
    entries: int = 0
    mean: Optional[float] = None
    std_dev: Optional[float] = None


class AnalysisResult(BaseModel):
    """Analysis results container."""
    simulation_id: str
    analysis_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    histograms: List[HistogramData] = Field(default_factory=list)
    summary_stats: Dict[str, Any] = Field(default_factory=dict)
    custom_data: Dict[str, Any] = Field(default_factory=dict)

