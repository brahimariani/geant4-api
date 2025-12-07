"""
Physics configuration models for Geant4 simulations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PhysicsListType(str, Enum):
    """Pre-built Geant4 physics lists."""
    # Standard EM
    FTFP_BERT = "FTFP_BERT"
    FTFP_BERT_HP = "FTFP_BERT_HP"
    QGSP_BERT = "QGSP_BERT"
    QGSP_BERT_HP = "QGSP_BERT_HP"
    QGSP_BIC = "QGSP_BIC"
    QGSP_BIC_HP = "QGSP_BIC_HP"
    
    # Shielding
    SHIELDING = "Shielding"
    SHIELDING_LEQ = "ShieldingLEND"
    
    # Medical
    QGSP_BIC_EMY = "QGSP_BIC_EMY"
    
    # Low energy EM
    LIVERMORE = "G4EmLivermorePhysics"
    PENELOPE = "G4EmPenelopePhysics"
    
    # Custom/minimal
    CUSTOM = "Custom"


class EMPhysicsOption(str, Enum):
    """Electromagnetic physics options."""
    STANDARD = "standard"
    OPTION1 = "option1"
    OPTION2 = "option2"
    OPTION3 = "option3"
    OPTION4 = "option4"
    LIVERMORE = "livermore"
    PENELOPE = "penelope"
    DNA = "dna"


class ProductionCut(BaseModel):
    """Production cut configuration."""
    gamma: float = Field(default=1.0, description="Gamma cut (mm)")
    electron: float = Field(default=1.0, description="Electron cut (mm)")
    positron: float = Field(default=1.0, description="Positron cut (mm)")
    proton: float = Field(default=1.0, description="Proton cut (mm)")


class RegionCut(BaseModel):
    """Region-specific production cuts."""
    region_name: str = Field(..., description="Region name")
    volumes: List[str] = Field(..., description="Volumes in this region")
    cuts: ProductionCut = Field(..., description="Production cuts for region")


class StepLimiter(BaseModel):
    """Step limiter configuration."""
    max_step: float = Field(..., description="Maximum step size (mm)")
    volumes: Optional[List[str]] = Field(
        default=None,
        description="Apply to specific volumes only"
    )


class PhysicsConfig(BaseModel):
    """Complete physics configuration."""
    physics_list: PhysicsListType = Field(
        default=PhysicsListType.FTFP_BERT,
        description="Reference physics list"
    )
    em_physics: EMPhysicsOption = Field(
        default=EMPhysicsOption.STANDARD,
        description="EM physics option"
    )
    
    # Cuts
    default_cut: float = Field(
        default=1.0,
        description="Default production cut (mm)"
    )
    production_cuts: Optional[ProductionCut] = Field(
        default=None,
        description="Global production cuts"
    )
    region_cuts: List[RegionCut] = Field(
        default_factory=list,
        description="Region-specific cuts"
    )
    
    # Step limiters
    step_limiters: List[StepLimiter] = Field(
        default_factory=list,
        description="Step limiter configurations"
    )
    
    # Process toggles
    enable_decay: bool = Field(default=True, description="Enable decay physics")
    enable_radioactive_decay: bool = Field(
        default=False, 
        description="Enable radioactive decay"
    )
    enable_optical: bool = Field(
        default=False, 
        description="Enable optical physics"
    )
    enable_hadronic: bool = Field(
        default=True, 
        description="Enable hadronic physics"
    )
    
    # Energy thresholds
    low_energy_limit: float = Field(
        default=0.001,
        description="Low energy limit (MeV)"
    )
    high_energy_limit: float = Field(
        default=100000.0,
        description="High energy limit (MeV)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "physics_list": "FTFP_BERT",
                "em_physics": "standard",
                "default_cut": 1.0,
                "enable_decay": True,
                "enable_radioactive_decay": False
            }
        }


class ScoringType(str, Enum):
    """Types of scoring quantities."""
    ENERGY_DEPOSIT = "energy_deposit"
    DOSE = "dose"
    DOSE_WEIGHTED = "dose_weighted"
    FLUX = "flux"
    CURRENT = "current"
    TRACK_LENGTH = "track_length"
    N_STEP = "n_step"
    N_SECONDARY = "n_secondary"
    CHARGE = "charge"


class ScoringMesh(BaseModel):
    """Scoring mesh configuration."""
    name: str = Field(..., description="Mesh name")
    scoring_type: ScoringType = Field(..., description="Quantity to score")
    
    # Mesh dimensions
    x_bins: int = Field(default=100, description="Number of X bins")
    y_bins: int = Field(default=100, description="Number of Y bins")
    z_bins: int = Field(default=100, description="Number of Z bins")
    
    # Mesh size (mm)
    half_x: float = Field(..., description="Half-size in X (mm)")
    half_y: float = Field(..., description="Half-size in Y (mm)")
    half_z: float = Field(..., description="Half-size in Z (mm)")
    
    # Position
    center_x: float = Field(default=0.0, description="Center X (mm)")
    center_y: float = Field(default=0.0, description="Center Y (mm)")
    center_z: float = Field(default=0.0, description="Center Z (mm)")
    
    # Filtering
    particle_filter: Optional[List[str]] = Field(
        default=None,
        description="Filter by particle types"
    )
    energy_filter_min: Optional[float] = Field(
        default=None,
        description="Minimum energy filter (MeV)"
    )
    energy_filter_max: Optional[float] = Field(
        default=None,
        description="Maximum energy filter (MeV)"
    )

