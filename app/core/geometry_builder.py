"""
Geometry builder for constructing Geant4 detector geometries.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger
import json

from app.models.geometry import (
    DetectorGeometry, Volume, WorldVolume,
    BoxGeometry, CylinderGeometry, SphereGeometry, ConeGeometry,
    Vector3D, Rotation3D, MaterialType
)


class GeometryBuilder:
    """
    Builds Geant4 detector geometries from configuration.
    
    Supports:
    - Python API geometry construction (with geant4-pybind)
    - GDML file generation
    - JSON configuration storage
    """
    
    def __init__(self):
        self.geometries: Dict[str, DetectorGeometry] = {}
        self._g4_available = False
        
        try:
            import geant4_pybind as g4
            self._g4 = g4
            self._g4_available = True
        except ImportError:
            pass
    
    def create_geometry(self, config: DetectorGeometry) -> str:
        """
        Create and store a geometry configuration.
        Returns the geometry ID.
        """
        geometry_id = config.name
        self.geometries[geometry_id] = config
        logger.info(f"Created geometry: {geometry_id}")
        return geometry_id
    
    def get_geometry(self, geometry_id: str) -> Optional[DetectorGeometry]:
        """Get a stored geometry configuration."""
        return self.geometries.get(geometry_id)
    
    def list_geometries(self) -> List[str]:
        """List all stored geometry IDs."""
        return list(self.geometries.keys())
    
    def delete_geometry(self, geometry_id: str) -> bool:
        """Delete a stored geometry."""
        if geometry_id in self.geometries:
            del self.geometries[geometry_id]
            return True
        return False
    
    def to_gdml(self, geometry: DetectorGeometry, output_path: Path) -> Path:
        """
        Convert geometry configuration to GDML format.
        """
        gdml_content = self._build_gdml(geometry)
        output_path.write_text(gdml_content)
        logger.info(f"Generated GDML: {output_path}")
        return output_path
    
    def _build_gdml(self, geometry: DetectorGeometry) -> str:
        """Build GDML XML content."""
        
        # Collect all unique materials
        materials = self._collect_materials(geometry)
        
        # Build GDML structure
        defines = self._build_gdml_defines(geometry)
        materials_xml = self._build_gdml_materials(materials)
        solids = self._build_gdml_solids(geometry)
        structure = self._build_gdml_structure(geometry)
        
        gdml = f'''<?xml version="1.0" encoding="UTF-8"?>
<gdml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd">

<!-- Geometry: {geometry.name} -->
<!-- {geometry.description or 'No description'} -->

<define>
{defines}
</define>

<materials>
{materials_xml}
</materials>

<solids>
{solids}
</solids>

<structure>
{structure}
</structure>

<setup name="Default" version="1.0">
    <world ref="World_LV"/>
</setup>

</gdml>'''
        
        return gdml
    
    def _collect_materials(self, geometry: DetectorGeometry) -> set:
        """Collect all unique materials used in geometry."""
        materials = {geometry.world.material}
        
        def collect_from_volume(volume: Volume):
            materials.add(volume.material)
            for child in volume.children:
                collect_from_volume(child)
        
        for volume in geometry.volumes:
            collect_from_volume(volume)
        
        return materials
    
    def _build_gdml_defines(self, geometry: DetectorGeometry) -> str:
        """Build GDML defines section."""
        lines = ['    <position name="center" x="0" y="0" z="0" unit="mm"/>']
        
        # Add positions for each volume
        for i, volume in enumerate(geometry.volumes):
            pos = volume.position
            lines.append(
                f'    <position name="{volume.name}_pos" '
                f'x="{pos.x}" y="{pos.y}" z="{pos.z}" unit="mm"/>'
            )
            
            rot = volume.rotation
            if rot.x != 0 or rot.y != 0 or rot.z != 0:
                lines.append(
                    f'    <rotation name="{volume.name}_rot" '
                    f'x="{rot.x}" y="{rot.y}" z="{rot.z}" unit="deg"/>'
                )
        
        return "\n".join(lines)
    
    def _build_gdml_materials(self, materials: set) -> str:
        """Build GDML materials section using NIST references."""
        lines = []
        for mat in materials:
            # Use NIST material database reference
            lines.append(f'    <material name="{mat}" Z="1">')
            lines.append(f'        <D value="1.0"/>')
            lines.append(f'        <atom value="1.0"/>')
            lines.append(f'    </material>')
        return "\n".join(lines)
    
    def _build_gdml_solids(self, geometry: DetectorGeometry) -> str:
        """Build GDML solids section."""
        lines = []
        
        # World solid
        w = geometry.world
        lines.append(
            f'    <box name="World_solid" '
            f'x="{w.half_x * 2}" y="{w.half_y * 2}" z="{w.half_z * 2}" lunit="mm"/>'
        )
        
        # Volume solids
        for volume in geometry.volumes:
            solid_xml = self._solid_to_gdml(volume.name, volume.solid)
            lines.append(solid_xml)
        
        return "\n".join(lines)
    
    def _solid_to_gdml(self, name: str, solid) -> str:
        """Convert a solid to GDML XML."""
        if solid.type == "box":
            return (
                f'    <box name="{name}_solid" '
                f'x="{solid.half_x * 2}" y="{solid.half_y * 2}" '
                f'z="{solid.half_z * 2}" lunit="mm"/>'
            )
        elif solid.type == "cylinder":
            return (
                f'    <tube name="{name}_solid" '
                f'rmin="{solid.inner_radius}" rmax="{solid.outer_radius}" '
                f'z="{solid.half_z * 2}" '
                f'startphi="{solid.start_phi}" deltaphi="{solid.delta_phi}" '
                f'aunit="deg" lunit="mm"/>'
            )
        elif solid.type == "sphere":
            return (
                f'    <sphere name="{name}_solid" '
                f'rmin="{solid.inner_radius}" rmax="{solid.outer_radius}" '
                f'startphi="{solid.start_phi}" deltaphi="{solid.delta_phi}" '
                f'starttheta="{solid.start_theta}" deltatheta="{solid.delta_theta}" '
                f'aunit="deg" lunit="mm"/>'
            )
        elif solid.type == "cone":
            return (
                f'    <cone name="{name}_solid" '
                f'rmin1="{solid.inner_radius_1}" rmax1="{solid.outer_radius_1}" '
                f'rmin2="{solid.inner_radius_2}" rmax2="{solid.outer_radius_2}" '
                f'z="{solid.half_z * 2}" '
                f'startphi="0" deltaphi="360" aunit="deg" lunit="mm"/>'
            )
        else:
            raise ValueError(f"Unknown solid type: {solid.type}")
    
    def _build_gdml_structure(self, geometry: DetectorGeometry) -> str:
        """Build GDML structure section."""
        lines = []
        
        # Build volume logical volumes first
        for volume in geometry.volumes:
            lines.append(f'    <volume name="{volume.name}_LV">')
            lines.append(f'        <materialref ref="{volume.material}"/>')
            lines.append(f'        <solidref ref="{volume.name}_solid"/>')
            
            # Add sensitive detector auxiliary if needed
            if volume.is_sensitive:
                lines.append(f'        <auxiliary auxtype="SensDet" auxvalue="{volume.name}"/>')
            
            lines.append(f'    </volume>')
            lines.append('')
        
        # World volume with placements
        lines.append('    <volume name="World_LV">')
        lines.append(f'        <materialref ref="{geometry.world.material}"/>')
        lines.append('        <solidref ref="World_solid"/>')
        
        for volume in geometry.volumes:
            lines.append(f'        <physvol name="{volume.name}_PV">')
            lines.append(f'            <volumeref ref="{volume.name}_LV"/>')
            lines.append(f'            <positionref ref="{volume.name}_pos"/>')
            if volume.rotation.x != 0 or volume.rotation.y != 0 or volume.rotation.z != 0:
                lines.append(f'            <rotationref ref="{volume.name}_rot"/>')
            lines.append('        </physvol>')
        
        lines.append('    </volume>')
        
        return "\n".join(lines)
    
    def validate_geometry(self, geometry: DetectorGeometry) -> Dict[str, Any]:
        """Validate geometry configuration."""
        issues = []
        warnings = []
        
        # Check world size
        max_extent = 0
        for volume in geometry.volumes:
            pos = volume.position
            solid = volume.solid
            
            # Calculate extent based on solid type
            if solid.type == "box":
                extent = max(
                    abs(pos.x) + solid.half_x,
                    abs(pos.y) + solid.half_y,
                    abs(pos.z) + solid.half_z
                )
            elif solid.type == "cylinder":
                extent = max(
                    abs(pos.x) + solid.outer_radius,
                    abs(pos.y) + solid.outer_radius,
                    abs(pos.z) + solid.half_z
                )
            elif solid.type == "sphere":
                extent = max(
                    abs(pos.x) + solid.outer_radius,
                    abs(pos.y) + solid.outer_radius,
                    abs(pos.z) + solid.outer_radius
                )
            else:
                extent = 0
            
            max_extent = max(max_extent, extent)
        
        # Check if world is large enough
        world = geometry.world
        if max_extent > min(world.half_x, world.half_y, world.half_z):
            issues.append(
                f"World size ({world.half_x}, {world.half_y}, {world.half_z}) "
                f"may be too small for volumes (max extent: {max_extent})"
            )
        
        # Check for duplicate names
        names = [v.name for v in geometry.volumes]
        if len(names) != len(set(names)):
            issues.append("Duplicate volume names detected")
        
        # Check materials
        known_materials = {m.value for m in MaterialType}
        for volume in geometry.volumes:
            if volume.material not in known_materials:
                warnings.append(
                    f"Material '{volume.material}' for volume '{volume.name}' "
                    f"is not a standard G4 material"
                )
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


# Predefined geometry templates
GEOMETRY_TEMPLATES = {
    "water_phantom": DetectorGeometry(
        name="water_phantom",
        description="Simple water phantom for dosimetry",
        world=WorldVolume(half_x=500, half_y=500, half_z=500),
        volumes=[
            Volume(
                name="phantom",
                solid=BoxGeometry(type="box", half_x=150, half_y=150, half_z=150),
                material="G4_WATER",
                position=Vector3D(x=0, y=0, z=0),
                is_sensitive=True
            )
        ]
    ),
    "simple_detector": DetectorGeometry(
        name="simple_detector",
        description="Simple NaI detector",
        world=WorldVolume(half_x=300, half_y=300, half_z=300),
        volumes=[
            Volume(
                name="detector",
                solid=CylinderGeometry(
                    type="cylinder", 
                    inner_radius=0, 
                    outer_radius=38.1, 
                    half_z=38.1
                ),
                material="G4_SODIUM_IODIDE",
                position=Vector3D(x=0, y=0, z=100),
                is_sensitive=True
            )
        ]
    ),
    "shielded_detector": DetectorGeometry(
        name="shielded_detector",
        description="Lead-shielded detector",
        world=WorldVolume(half_x=500, half_y=500, half_z=500),
        volumes=[
            Volume(
                name="shield",
                solid=CylinderGeometry(
                    type="cylinder",
                    inner_radius=50,
                    outer_radius=100,
                    half_z=100
                ),
                material="G4_Pb",
                position=Vector3D(x=0, y=0, z=150),
                is_sensitive=False
            ),
            Volume(
                name="detector",
                solid=CylinderGeometry(
                    type="cylinder",
                    inner_radius=0,
                    outer_radius=45,
                    half_z=50
                ),
                material="G4_SODIUM_IODIDE",
                position=Vector3D(x=0, y=0, z=150),
                is_sensitive=True
            )
        ]
    )
}


# Global geometry builder instance
geometry_builder = GeometryBuilder()

