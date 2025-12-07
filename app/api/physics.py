"""
Physics configuration API endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from app.models.physics import PhysicsConfig, PhysicsListType, EMPhysicsOption
from app.core.physics_builder import (
    physics_builder, PhysicsBuilder, PHYSICS_TEMPLATES
)


router = APIRouter()


@router.get("", response_model=List[str])
@router.get("/", response_model=List[str], include_in_schema=False)
async def list_physics_configs():
    """List all saved physics configurations."""
    return physics_builder.list_physics()


@router.get("/templates", response_model=Dict[str, Any])
async def list_templates():
    """List available physics templates."""
    return {
        name: {
            "physics_list": config.physics_list.value,
            "em_physics": config.em_physics.value,
            "default_cut": config.default_cut
        }
        for name, config in PHYSICS_TEMPLATES.items()
    }


@router.get("/templates/{template_name}", response_model=PhysicsConfig)
async def get_template(template_name: str):
    """Get a physics template configuration."""
    if template_name not in PHYSICS_TEMPLATES:
        raise HTTPException(404, f"Template '{template_name}' not found")
    return PHYSICS_TEMPLATES[template_name]


@router.get("/physics-lists")
async def list_physics_lists():
    """
    List available Geant4 physics lists with descriptions.
    """
    return [
        physics_builder.get_physics_list_info(pl)
        for pl in PhysicsListType
    ]


@router.get("/physics-lists/{list_name}")
async def get_physics_list_info(list_name: str):
    """Get detailed information about a physics list."""
    try:
        pl_type = PhysicsListType(list_name)
    except ValueError:
        raise HTTPException(404, f"Physics list '{list_name}' not found")
    
    return physics_builder.get_physics_list_info(pl_type)


@router.get("/em-options")
async def list_em_options():
    """List available EM physics options."""
    descriptions = {
        EMPhysicsOption.STANDARD: "Standard EM physics, good for most applications",
        EMPhysicsOption.OPTION1: "EM physics with improved multiple scattering",
        EMPhysicsOption.OPTION2: "EM physics optimized for calorimetry",
        EMPhysicsOption.OPTION3: "EM physics with Goudsmit-Saunderson MSC",
        EMPhysicsOption.OPTION4: "EM physics optimized for medical applications",
        EMPhysicsOption.LIVERMORE: "Low-energy EM based on Livermore data (down to 250 eV)",
        EMPhysicsOption.PENELOPE: "Low-energy EM based on PENELOPE (down to 100 eV)",
        EMPhysicsOption.DNA: "Geant4-DNA physics for microdosimetry"
    }
    
    return [
        {
            "name": opt.name,
            "value": opt.value,
            "description": descriptions.get(opt, "")
        }
        for opt in EMPhysicsOption
    ]


@router.post("/recommend")
async def recommend_physics(
    application: str,
    energy_mev: float,
    particles: List[str]
):
    """
    Get physics list recommendation based on application.
    
    - **application**: Description of your application (e.g., "medical dosimetry", "shielding", "HEP")
    - **energy_mev**: Primary particle energy in MeV
    - **particles**: List of particle types (e.g., ["gamma", "proton"])
    """
    recommendation = physics_builder.recommend_physics_list(
        application, energy_mev, particles
    )
    
    info = physics_builder.get_physics_list_info(recommendation)
    
    return {
        "recommended": recommendation.value,
        "info": info,
        "reason": f"Best suited for {application} with {energy_mev} MeV {', '.join(particles)}"
    }


@router.post("", response_model=Dict[str, str])
@router.post("/", response_model=Dict[str, str], include_in_schema=False)
async def create_physics_config(config: PhysicsConfig, name: str):
    """
    Create and save a new physics configuration.
    """
    # Validate
    validation = physics_builder.validate_physics(config)
    if not validation["valid"]:
        raise HTTPException(400, {
            "message": "Physics validation failed",
            "issues": validation["issues"],
            "warnings": validation["warnings"]
        })
    
    physics_id = physics_builder.create_physics(config, name)
    
    return {
        "physics_id": physics_id,
        "message": f"Physics config '{physics_id}' created",
        "warnings": validation["warnings"] if validation["warnings"] else None
    }


@router.get("/{physics_id}", response_model=PhysicsConfig)
async def get_physics_config(physics_id: str):
    """Get a saved physics configuration."""
    config = physics_builder.get_physics(physics_id)
    if not config:
        raise HTTPException(404, f"Physics config '{physics_id}' not found")
    return config


@router.delete("/{physics_id}")
async def delete_physics_config(physics_id: str):
    """Delete a saved physics configuration."""
    if not physics_builder.delete_physics(physics_id):
        raise HTTPException(404, f"Physics config '{physics_id}' not found")
    return {"message": f"Physics config '{physics_id}' deleted"}


@router.post("/{physics_id}/validate")
async def validate_physics_config(physics_id: str):
    """Validate a saved physics configuration."""
    config = physics_builder.get_physics(physics_id)
    if not config:
        raise HTTPException(404, f"Physics config '{physics_id}' not found")
    
    return physics_builder.validate_physics(config)


@router.post("/validate")
async def validate_physics(config: PhysicsConfig):
    """Validate a physics configuration without saving."""
    return physics_builder.validate_physics(config)


@router.get("/{physics_id}/macro")
async def export_macro(physics_id: str):
    """
    Export physics configuration as Geant4 macro commands.
    """
    config = physics_builder.get_physics(physics_id)
    if not config:
        raise HTTPException(404, f"Physics config '{physics_id}' not found")
    
    commands = physics_builder.to_macro_commands(config)
    
    return {
        "physics_id": physics_id,
        "macro_commands": commands
    }

