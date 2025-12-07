"""
Particle source models for primary generator configuration.
"""

from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum


class ParticleType(str, Enum):
    """Common particle types in Geant4."""
    # Leptons
    ELECTRON = "e-"
    POSITRON = "e+"
    MUON_MINUS = "mu-"
    MUON_PLUS = "mu+"
    
    # Photons
    GAMMA = "gamma"
    OPTICAL_PHOTON = "opticalphoton"
    
    # Hadrons
    PROTON = "proton"
    NEUTRON = "neutron"
    PION_PLUS = "pi+"
    PION_MINUS = "pi-"
    PION_ZERO = "pi0"
    KAON_PLUS = "kaon+"
    KAON_MINUS = "kaon-"
    
    # Ions
    ALPHA = "alpha"
    DEUTERON = "deuteron"
    TRITON = "triton"
    HE3 = "He3"
    CARBON12 = "GenericIon"
    
    # Generic
    GEANTINO = "geantino"
    CHARGED_GEANTINO = "chargedgeantino"


class EnergyDistribution(str, Enum):
    """Energy distribution types."""
    MONO = "mono"
    GAUSSIAN = "gaussian"
    FLAT = "flat"
    EXPONENTIAL = "exponential"
    POWER_LAW = "power_law"
    USER_DEFINED = "user_defined"


class AngularDistribution(str, Enum):
    """Angular distribution types."""
    ISOTROPIC = "isotropic"
    DIRECTED = "directed"
    COSINE = "cosine"
    CONE = "cone"
    USER_DEFINED = "user_defined"


class PositionDistribution(str, Enum):
    """Position distribution types."""
    POINT = "point"
    PLANE = "plane"
    SURFACE = "surface"
    VOLUME = "volume"


class Vector3D(BaseModel):
    """3D vector for positions and directions."""
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)
    z: float = Field(default=0.0)


class EnergyConfig(BaseModel):
    """Energy configuration for particle source."""
    distribution: EnergyDistribution = Field(
        default=EnergyDistribution.MONO,
        description="Energy distribution type"
    )
    value: float = Field(..., description="Energy value in MeV")
    sigma: Optional[float] = Field(
        default=None, 
        description="Standard deviation for Gaussian (MeV)"
    )
    min_energy: Optional[float] = Field(
        default=None,
        description="Minimum energy for flat distribution (MeV)"
    )
    max_energy: Optional[float] = Field(
        default=None,
        description="Maximum energy for flat distribution (MeV)"
    )


class DirectionConfig(BaseModel):
    """Direction configuration for particle source."""
    distribution: AngularDistribution = Field(
        default=AngularDistribution.DIRECTED,
        description="Angular distribution type"
    )
    direction: Vector3D = Field(
        default_factory=lambda: Vector3D(x=0, y=0, z=1),
        description="Direction vector (for directed)"
    )
    cone_angle: Optional[float] = Field(
        default=None,
        description="Half-angle for cone distribution (degrees)"
    )


class PositionConfig(BaseModel):
    """Position configuration for particle source."""
    distribution: PositionDistribution = Field(
        default=PositionDistribution.POINT,
        description="Position distribution type"
    )
    center: Vector3D = Field(
        default_factory=Vector3D,
        description="Center position (mm)"
    )
    half_x: Optional[float] = Field(default=None, description="Half-X for plane/volume")
    half_y: Optional[float] = Field(default=None, description="Half-Y for plane/volume")
    half_z: Optional[float] = Field(default=None, description="Half-Z for plane/volume")
    radius: Optional[float] = Field(default=None, description="Radius for surface/volume")


class ParticleSource(BaseModel):
    """Complete particle source configuration."""
    name: str = Field(default="primary", description="Source name")
    particle: str = Field(default="gamma", description="Particle type")
    energy: EnergyConfig = Field(..., description="Energy configuration")
    direction: DirectionConfig = Field(
        default_factory=DirectionConfig,
        description="Direction configuration"
    )
    position: PositionConfig = Field(
        default_factory=PositionConfig,
        description="Position configuration"
    )
    number_of_particles: int = Field(
        default=1,
        description="Particles per event"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "gamma_source",
                "particle": "gamma",
                "energy": {"distribution": "mono", "value": 1.0},
                "direction": {
                    "distribution": "directed",
                    "direction": {"x": 0, "y": 0, "z": 1}
                },
                "position": {
                    "distribution": "point",
                    "center": {"x": 0, "y": 0, "z": -100}
                },
                "number_of_particles": 1
            }
        }


class IonConfig(BaseModel):
    """Configuration for ion particles."""
    z: int = Field(..., description="Atomic number")
    a: int = Field(..., description="Mass number")
    charge: Optional[int] = Field(default=None, description="Charge state")
    excitation_energy: float = Field(
        default=0.0, 
        description="Excitation energy (keV)"
    )


class RadioactiveSource(BaseModel):
    """Radioactive source configuration."""
    name: str = Field(..., description="Source name")
    ion: IonConfig = Field(..., description="Ion configuration")
    activity: float = Field(..., description="Activity in Bq")
    position: PositionConfig = Field(
        default_factory=PositionConfig,
        description="Position configuration"
    )
    confined_to_volume: Optional[str] = Field(
        default=None,
        description="Confine to named volume"
    )

