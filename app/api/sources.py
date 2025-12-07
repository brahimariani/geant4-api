"""
Particle source configuration API endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from app.models.particle import (
    ParticleSource, ParticleType, EnergyDistribution,
    AngularDistribution, PositionDistribution
)
from app.core.source_builder import (
    source_builder, SourceBuilder, SOURCE_TEMPLATES
)


router = APIRouter()


@router.get("", response_model=List[str])
@router.get("/", response_model=List[str], include_in_schema=False)
async def list_sources():
    """List all saved particle source configurations."""
    return source_builder.list_sources()


@router.get("/templates", response_model=Dict[str, Any])
async def list_templates():
    """List available source templates."""
    return {
        name: {
            "particle": source.particle,
            "energy": source.energy.value,
            "energy_unit": "MeV",
            "distribution": source.energy.distribution.value
        }
        for name, source in SOURCE_TEMPLATES.items()
    }


@router.get("/templates/{template_name}", response_model=ParticleSource)
async def get_template(template_name: str):
    """Get a source template configuration."""
    if template_name not in SOURCE_TEMPLATES:
        raise HTTPException(404, f"Template '{template_name}' not found")
    return SOURCE_TEMPLATES[template_name]


@router.get("/particles")
async def list_particles():
    """List available particle types with properties."""
    return [
        {
            "name": p.name,
            "value": p.value,
            "info": source_builder.get_particle_info(p.value)
        }
        for p in ParticleType
    ]


@router.get("/particles/{particle_name}")
async def get_particle_info(particle_name: str):
    """Get detailed information about a particle type."""
    info = source_builder.get_particle_info(particle_name)
    if not info.get("pdg"):
        # Try to find in enum
        for p in ParticleType:
            if p.value == particle_name or p.name.lower() == particle_name.lower():
                info = source_builder.get_particle_info(p.value)
                break
    
    return info


@router.get("/energy-distributions")
async def list_energy_distributions():
    """List available energy distribution types."""
    descriptions = {
        EnergyDistribution.MONO: "Monoenergetic - single energy value",
        EnergyDistribution.GAUSSIAN: "Gaussian distribution around mean energy",
        EnergyDistribution.FLAT: "Flat/uniform distribution between min and max",
        EnergyDistribution.EXPONENTIAL: "Exponential decay spectrum",
        EnergyDistribution.POWER_LAW: "Power law spectrum",
        EnergyDistribution.USER_DEFINED: "User-defined spectrum from file"
    }
    
    return [
        {
            "name": d.name,
            "value": d.value,
            "description": descriptions.get(d, "")
        }
        for d in EnergyDistribution
    ]


@router.get("/angular-distributions")
async def list_angular_distributions():
    """List available angular distribution types."""
    descriptions = {
        AngularDistribution.ISOTROPIC: "Uniform in all directions (4π)",
        AngularDistribution.DIRECTED: "Single direction (pencil beam)",
        AngularDistribution.COSINE: "Cosine-law distribution",
        AngularDistribution.CONE: "Cone around a direction",
        AngularDistribution.USER_DEFINED: "User-defined angular distribution"
    }
    
    return [
        {
            "name": d.name,
            "value": d.value,
            "description": descriptions.get(d, "")
        }
        for d in AngularDistribution
    ]


@router.get("/position-distributions")
async def list_position_distributions():
    """List available position distribution types."""
    descriptions = {
        PositionDistribution.POINT: "Point source at a single location",
        PositionDistribution.PLANE: "Distributed on a plane (rectangle)",
        PositionDistribution.SURFACE: "Distributed on a surface (sphere, etc.)",
        PositionDistribution.VOLUME: "Distributed within a volume"
    }
    
    return [
        {
            "name": d.name,
            "value": d.value,
            "description": descriptions.get(d, "")
        }
        for d in PositionDistribution
    ]


@router.post("", response_model=Dict[str, str])
@router.post("/", response_model=Dict[str, str], include_in_schema=False)
async def create_source(source: ParticleSource):
    """
    Create and save a new particle source configuration.
    """
    # Validate
    validation = source_builder.validate_source(source)
    if not validation["valid"]:
        raise HTTPException(400, {
            "message": "Source validation failed",
            "issues": validation["issues"],
            "warnings": validation["warnings"]
        })
    
    source_id = source_builder.create_source(source)
    
    return {
        "source_id": source_id,
        "message": f"Source '{source_id}' created",
        "warnings": validation["warnings"] if validation["warnings"] else None
    }


@router.get("/{source_id}", response_model=ParticleSource)
async def get_source(source_id: str):
    """Get a saved source configuration."""
    source = source_builder.get_source(source_id)
    if not source:
        raise HTTPException(404, f"Source '{source_id}' not found")
    return source


@router.delete("/{source_id}")
async def delete_source(source_id: str):
    """Delete a saved source configuration."""
    if not source_builder.delete_source(source_id):
        raise HTTPException(404, f"Source '{source_id}' not found")
    return {"message": f"Source '{source_id}' deleted"}


@router.post("/{source_id}/validate")
async def validate_source_config(source_id: str):
    """Validate a saved source configuration."""
    source = source_builder.get_source(source_id)
    if not source:
        raise HTTPException(404, f"Source '{source_id}' not found")
    
    return source_builder.validate_source(source)


@router.post("/validate")
async def validate_source(source: ParticleSource):
    """Validate a source configuration without saving."""
    return source_builder.validate_source(source)


@router.get("/{source_id}/gps")
async def export_gps_commands(source_id: str):
    """
    Export source configuration as GPS (General Particle Source) macro commands.
    """
    source = source_builder.get_source(source_id)
    if not source:
        raise HTTPException(404, f"Source '{source_id}' not found")
    
    commands = source_builder.to_gps_commands(source)
    
    return {
        "source_id": source_id,
        "gps_commands": commands
    }

