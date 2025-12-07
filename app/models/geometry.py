"""
Geometry models for detector construction.
"""

from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum


class MaterialType(str, Enum):
    """Common Geant4 materials."""
    VACUUM = "G4_Galactic"
    AIR = "G4_AIR"
    WATER = "G4_WATER"
    ALUMINUM = "G4_Al"
    COPPER = "G4_Cu"
    LEAD = "G4_Pb"
    IRON = "G4_Fe"
    TUNGSTEN = "G4_W"
    CONCRETE = "G4_CONCRETE"
    TISSUE_SOFT = "G4_TISSUE_SOFT_ICRP"
    BONE = "G4_BONE_COMPACT_ICRU"
    SILICON = "G4_Si"
    GERMANIUM = "G4_Ge"
    SODIUM_IODIDE = "G4_SODIUM_IODIDE"
    BGO = "G4_BGO"
    CESIUM_IODIDE = "G4_CESIUM_IODIDE"
    PLASTIC_SCINTILLATOR = "G4_PLASTIC_SC_VINYLTOLUENE"


class Vector3D(BaseModel):
    """3D vector for positions and dimensions."""
    x: float = Field(default=0.0, description="X component (mm)")
    y: float = Field(default=0.0, description="Y component (mm)")
    z: float = Field(default=0.0, description="Z component (mm)")


class Rotation3D(BaseModel):
    """3D rotation angles."""
    x: float = Field(default=0.0, description="Rotation around X (degrees)")
    y: float = Field(default=0.0, description="Rotation around Y (degrees)")
    z: float = Field(default=0.0, description="Rotation around Z (degrees)")


class BoxGeometry(BaseModel):
    """Box-shaped solid geometry."""
    type: Literal["box"] = "box"
    half_x: float = Field(..., description="Half-length in X (mm)")
    half_y: float = Field(..., description="Half-length in Y (mm)")
    half_z: float = Field(..., description="Half-length in Z (mm)")


class CylinderGeometry(BaseModel):
    """Cylindrical solid geometry."""
    type: Literal["cylinder"] = "cylinder"
    inner_radius: float = Field(default=0.0, description="Inner radius (mm)")
    outer_radius: float = Field(..., description="Outer radius (mm)")
    half_z: float = Field(..., description="Half-length in Z (mm)")
    start_phi: float = Field(default=0.0, description="Start angle (degrees)")
    delta_phi: float = Field(default=360.0, description="Angular span (degrees)")


class SphereGeometry(BaseModel):
    """Spherical solid geometry."""
    type: Literal["sphere"] = "sphere"
    inner_radius: float = Field(default=0.0, description="Inner radius (mm)")
    outer_radius: float = Field(..., description="Outer radius (mm)")
    start_phi: float = Field(default=0.0, description="Start phi (degrees)")
    delta_phi: float = Field(default=360.0, description="Delta phi (degrees)")
    start_theta: float = Field(default=0.0, description="Start theta (degrees)")
    delta_theta: float = Field(default=180.0, description="Delta theta (degrees)")


class ConeGeometry(BaseModel):
    """Conical solid geometry."""
    type: Literal["cone"] = "cone"
    inner_radius_1: float = Field(default=0.0, description="Inner radius at -z (mm)")
    outer_radius_1: float = Field(..., description="Outer radius at -z (mm)")
    inner_radius_2: float = Field(default=0.0, description="Inner radius at +z (mm)")
    outer_radius_2: float = Field(..., description="Outer radius at +z (mm)")
    half_z: float = Field(..., description="Half-length in Z (mm)")


SolidGeometry = Union[BoxGeometry, CylinderGeometry, SphereGeometry, ConeGeometry]


class Volume(BaseModel):
    """A detector volume with geometry, material, and placement."""
    name: str = Field(..., description="Unique volume name")
    solid: SolidGeometry = Field(..., description="Solid geometry definition")
    material: str = Field(..., description="Material name (e.g., G4_WATER)")
    position: Vector3D = Field(default_factory=Vector3D, description="Position")
    rotation: Rotation3D = Field(default_factory=Rotation3D, description="Rotation")
    is_sensitive: bool = Field(default=False, description="Is a sensitive detector")
    color: Optional[List[float]] = Field(
        default=None, 
        description="RGBA color [r, g, b, a] for visualization"
    )
    children: List["Volume"] = Field(
        default_factory=list, 
        description="Child volumes"
    )


class WorldVolume(BaseModel):
    """The world volume containing the entire geometry."""
    half_x: float = Field(default=1000.0, description="World half-X (mm)")
    half_y: float = Field(default=1000.0, description="World half-Y (mm)")
    half_z: float = Field(default=1000.0, description="World half-Z (mm)")
    material: str = Field(default="G4_AIR", description="World material")


class DetectorGeometry(BaseModel):
    """Complete detector geometry configuration."""
    name: str = Field(..., description="Geometry configuration name")
    description: Optional[str] = Field(default=None, description="Description")
    world: WorldVolume = Field(default_factory=WorldVolume, description="World volume")
    volumes: List[Volume] = Field(default_factory=list, description="Detector volumes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "simple_detector",
                "description": "A simple box detector",
                "world": {"half_x": 500, "half_y": 500, "half_z": 500},
                "volumes": [
                    {
                        "name": "detector",
                        "solid": {"type": "box", "half_x": 50, "half_y": 50, "half_z": 50},
                        "material": "G4_WATER",
                        "position": {"x": 0, "y": 0, "z": 100},
                        "is_sensitive": True
                    }
                ]
            }
        }


# Enable forward references for recursive Volume
Volume.model_rebuild()

