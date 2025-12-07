"""
Geometry configuration API endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models.geometry import DetectorGeometry, MaterialType
from app.core.geometry_builder import (
    geometry_builder, GeometryBuilder, GEOMETRY_TEMPLATES
)


router = APIRouter()


@router.get("", response_model=List[str])
@router.get("/", response_model=List[str], include_in_schema=False)
async def list_geometries():
    """List all saved geometry configurations."""
    return geometry_builder.list_geometries()


@router.get("/templates", response_model=Dict[str, Any])
async def list_templates():
    """List available geometry templates."""
    return {
        name: {
            "name": geom.name,
            "description": geom.description,
            "volumes": len(geom.volumes)
        }
        for name, geom in GEOMETRY_TEMPLATES.items()
    }


@router.get("/templates/{template_name}", response_model=DetectorGeometry)
async def get_template(template_name: str):
    """Get a geometry template configuration."""
    if template_name not in GEOMETRY_TEMPLATES:
        raise HTTPException(404, f"Template '{template_name}' not found")
    return GEOMETRY_TEMPLATES[template_name]


@router.get("/materials")
async def list_materials():
    """List available predefined materials."""
    return [
        {
            "name": m.name,
            "value": m.value,
            "description": _material_description(m)
        }
        for m in MaterialType
    ]


def _material_description(mat: MaterialType) -> str:
    """Get description for material."""
    descriptions = {
        MaterialType.VACUUM: "Perfect vacuum (galactic)",
        MaterialType.AIR: "Standard air at STP",
        MaterialType.WATER: "Liquid water (H2O)",
        MaterialType.ALUMINUM: "Pure aluminum",
        MaterialType.COPPER: "Pure copper",
        MaterialType.LEAD: "Pure lead (common shielding)",
        MaterialType.IRON: "Pure iron",
        MaterialType.TUNGSTEN: "Pure tungsten",
        MaterialType.CONCRETE: "Standard concrete",
        MaterialType.TISSUE_SOFT: "Soft tissue (ICRP)",
        MaterialType.BONE: "Compact bone (ICRU)",
        MaterialType.SILICON: "Pure silicon",
        MaterialType.GERMANIUM: "Pure germanium",
        MaterialType.SODIUM_IODIDE: "NaI scintillator",
        MaterialType.BGO: "BGO scintillator",
        MaterialType.CESIUM_IODIDE: "CsI scintillator",
        MaterialType.PLASTIC_SCINTILLATOR: "Plastic scintillator",
    }
    return descriptions.get(mat, "")


@router.post("", response_model=Dict[str, str])
@router.post("/", response_model=Dict[str, str], include_in_schema=False)
async def create_geometry(geometry: DetectorGeometry):
    """
    Create and save a new geometry configuration.
    
    The geometry can be referenced in simulations by its name.
    """
    # Validate
    validation = geometry_builder.validate_geometry(geometry)
    if not validation["valid"]:
        raise HTTPException(400, {
            "message": "Geometry validation failed",
            "issues": validation["issues"],
            "warnings": validation["warnings"]
        })
    
    geometry_id = geometry_builder.create_geometry(geometry)
    
    return {
        "geometry_id": geometry_id,
        "message": f"Geometry '{geometry_id}' created",
        "warnings": validation["warnings"] if validation["warnings"] else None
    }


@router.get("/{geometry_id}", response_model=DetectorGeometry)
async def get_geometry(geometry_id: str):
    """Get a saved geometry configuration."""
    geometry = geometry_builder.get_geometry(geometry_id)
    if not geometry:
        raise HTTPException(404, f"Geometry '{geometry_id}' not found")
    return geometry


@router.delete("/{geometry_id}")
async def delete_geometry(geometry_id: str):
    """Delete a saved geometry configuration."""
    if not geometry_builder.delete_geometry(geometry_id):
        raise HTTPException(404, f"Geometry '{geometry_id}' not found")
    return {"message": f"Geometry '{geometry_id}' deleted"}


@router.post("/{geometry_id}/validate")
async def validate_geometry_config(geometry_id: str):
    """Validate a saved geometry configuration."""
    geometry = geometry_builder.get_geometry(geometry_id)
    if not geometry:
        raise HTTPException(404, f"Geometry '{geometry_id}' not found")
    
    return geometry_builder.validate_geometry(geometry)


@router.post("/validate")
async def validate_geometry(geometry: DetectorGeometry):
    """Validate a geometry configuration without saving."""
    return geometry_builder.validate_geometry(geometry)


@router.get("/{geometry_id}/gdml")
async def export_gdml(geometry_id: str):
    """
    Export geometry to GDML format.
    
    Returns the GDML XML content.
    """
    geometry = geometry_builder.get_geometry(geometry_id)
    if not geometry:
        raise HTTPException(404, f"Geometry '{geometry_id}' not found")
    
    from pathlib import Path
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".gdml", delete=False) as f:
        gdml_path = Path(f.name)
    
    geometry_builder.to_gdml(geometry, gdml_path)
    gdml_content = gdml_path.read_text()
    gdml_path.unlink()
    
    return Response(
        content=gdml_content,
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename={geometry_id}.gdml"
        }
    )


@router.post("/{geometry_id}/copy")
async def copy_geometry(geometry_id: str, new_name: str):
    """Create a copy of a geometry with a new name."""
    geometry = geometry_builder.get_geometry(geometry_id)
    if not geometry:
        raise HTTPException(404, f"Geometry '{geometry_id}' not found")
    
    # Create copy with new name
    new_geometry = geometry.model_copy(deep=True)
    new_geometry.name = new_name
    
    new_id = geometry_builder.create_geometry(new_geometry)
    
    return {
        "geometry_id": new_id,
        "message": f"Geometry copied to '{new_id}'"
    }

