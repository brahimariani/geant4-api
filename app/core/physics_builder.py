"""
Physics list builder for Geant4 simulations.
"""

from typing import Dict, Optional, List, Any
from loguru import logger

from app.models.physics import (
    PhysicsConfig, PhysicsListType, EMPhysicsOption,
    ProductionCut, RegionCut, StepLimiter, ScoringMesh
)


class PhysicsBuilder:
    """
    Builds Geant4 physics configurations.
    
    Handles:
    - Reference physics list selection
    - EM physics options
    - Production cuts
    - Scoring meshes
    """
    
    def __init__(self):
        self.physics_configs: Dict[str, PhysicsConfig] = {}
        self._g4_available = False
        
        try:
            import geant4_pybind as g4
            self._g4 = g4
            self._g4_available = True
        except ImportError:
            pass
    
    def create_physics(self, config: PhysicsConfig, name: str) -> str:
        """Create and store a physics configuration."""
        self.physics_configs[name] = config
        logger.info(f"Created physics config: {name}")
        return name
    
    def get_physics(self, name: str) -> Optional[PhysicsConfig]:
        """Get a stored physics configuration."""
        return self.physics_configs.get(name)
    
    def list_physics(self) -> List[str]:
        """List all stored physics configurations."""
        return list(self.physics_configs.keys())
    
    def delete_physics(self, name: str) -> bool:
        """Delete a stored physics configuration."""
        if name in self.physics_configs:
            del self.physics_configs[name]
            return True
        return False
    
    def to_macro_commands(self, config: PhysicsConfig) -> List[str]:
        """
        Convert physics configuration to Geant4 macro commands.
        """
        commands = [
            "# Physics configuration",
            f"# Physics list: {config.physics_list.value}",
        ]
        
        # Production cuts
        commands.append(f"/run/setCut {config.default_cut} mm")
        
        if config.production_cuts:
            cuts = config.production_cuts
            commands.extend([
                f"/run/setCutForAGivenParticle gamma {cuts.gamma} mm",
                f"/run/setCutForAGivenParticle e- {cuts.electron} mm",
                f"/run/setCutForAGivenParticle e+ {cuts.positron} mm",
                f"/run/setCutForAGivenParticle proton {cuts.proton} mm",
            ])
        
        # Region cuts
        for region_cut in config.region_cuts:
            commands.append(f"# Region: {region_cut.region_name}")
            commands.append(f"/run/setCutForRegion {region_cut.region_name} {region_cut.cuts.gamma} mm")
        
        # Step limiters
        for limiter in config.step_limiters:
            if limiter.volumes:
                for vol in limiter.volumes:
                    commands.append(f"/process/setMaxStep {limiter.max_step} mm {vol}")
        
        return commands
    
    def get_physics_list_info(self, list_type: PhysicsListType) -> Dict[str, Any]:
        """Get information about a physics list."""
        info = {
            PhysicsListType.FTFP_BERT: {
                "name": "FTFP_BERT",
                "description": "Fritiof + Bertini cascade. Good for HEP.",
                "energy_range": "0 - 100 TeV",
                "best_for": ["High energy physics", "LHC experiments"],
                "em_physics": "Standard EM",
                "hadronic": "FTFP + Bertini"
            },
            PhysicsListType.FTFP_BERT_HP: {
                "name": "FTFP_BERT_HP",
                "description": "FTFP_BERT with high precision neutron transport",
                "energy_range": "0 - 100 TeV",
                "best_for": ["Neutron transport", "Shielding"],
                "em_physics": "Standard EM",
                "hadronic": "FTFP + Bertini + NeutronHP"
            },
            PhysicsListType.QGSP_BERT: {
                "name": "QGSP_BERT",
                "description": "Quark-gluon string + Bertini cascade",
                "energy_range": "0 - 100 TeV",
                "best_for": ["General purpose", "Calorimetry"],
                "em_physics": "Standard EM",
                "hadronic": "QGSP + Bertini"
            },
            PhysicsListType.QGSP_BIC: {
                "name": "QGSP_BIC",
                "description": "Quark-gluon string + Binary cascade",
                "energy_range": "0 - 100 TeV",
                "best_for": ["Proton therapy", "Nuclear physics"],
                "em_physics": "Standard EM",
                "hadronic": "QGSP + Binary"
            },
            PhysicsListType.SHIELDING: {
                "name": "Shielding",
                "description": "Optimized for shielding calculations",
                "energy_range": "0 - 100 TeV",
                "best_for": ["Shielding design", "Radiation protection"],
                "em_physics": "Standard EM",
                "hadronic": "FTFP + Bertini + HP"
            },
            PhysicsListType.LIVERMORE: {
                "name": "G4EmLivermorePhysics",
                "description": "Low energy EM based on Livermore data",
                "energy_range": "250 eV - 100 GeV",
                "best_for": ["X-ray applications", "Low energy"],
                "em_physics": "Livermore",
                "hadronic": "None (EM only)"
            },
            PhysicsListType.PENELOPE: {
                "name": "G4EmPenelopePhysics",
                "description": "Low energy EM based on PENELOPE",
                "energy_range": "100 eV - 1 GeV",
                "best_for": ["Medical physics", "Microdosimetry"],
                "em_physics": "Penelope",
                "hadronic": "None (EM only)"
            },
        }
        
        return info.get(list_type, {
            "name": list_type.value,
            "description": "Custom physics list",
            "energy_range": "Unknown",
            "best_for": [],
            "em_physics": "Unknown",
            "hadronic": "Unknown"
        })
    
    def recommend_physics_list(
        self,
        application: str,
        energy_mev: float,
        particles: List[str]
    ) -> PhysicsListType:
        """
        Recommend a physics list based on application parameters.
        """
        application = application.lower()
        
        # Medical physics
        if any(x in application for x in ["medical", "therapy", "dosimetry"]):
            if energy_mev < 10:
                return PhysicsListType.PENELOPE
            elif "proton" in particles or "ion" in particles:
                return PhysicsListType.QGSP_BIC
            else:
                return PhysicsListType.QGSP_BERT
        
        # Shielding
        if any(x in application for x in ["shielding", "radiation protection"]):
            return PhysicsListType.SHIELDING
        
        # X-ray / low energy
        if any(x in application for x in ["xray", "x-ray", "fluorescence"]):
            return PhysicsListType.LIVERMORE
        
        # Neutron transport
        if "neutron" in particles:
            return PhysicsListType.FTFP_BERT_HP
        
        # High energy physics
        if energy_mev > 10000 or any(x in application for x in ["hep", "collider"]):
            return PhysicsListType.FTFP_BERT
        
        # Default
        return PhysicsListType.FTFP_BERT
    
    def validate_physics(self, config: PhysicsConfig) -> Dict[str, Any]:
        """Validate physics configuration."""
        issues = []
        warnings = []
        
        # Check cut values
        if config.default_cut < 0.001:
            warnings.append(
                f"Very small default cut ({config.default_cut} mm) may cause "
                "slow simulation"
            )
        
        if config.default_cut > 100:
            warnings.append(
                f"Large default cut ({config.default_cut} mm) may cause "
                "inaccurate results"
            )
        
        # Check energy limits
        if config.low_energy_limit >= config.high_energy_limit:
            issues.append(
                f"Low energy limit ({config.low_energy_limit}) must be less than "
                f"high energy limit ({config.high_energy_limit})"
            )
        
        # Check for HP physics with radioactive decay
        if config.enable_radioactive_decay:
            if config.physics_list not in [
                PhysicsListType.FTFP_BERT_HP,
                PhysicsListType.QGSP_BERT_HP,
                PhysicsListType.QGSP_BIC_HP,
                PhysicsListType.SHIELDING
            ]:
                warnings.append(
                    "Radioactive decay is enabled but physics list doesn't include "
                    "high precision (HP) physics. Consider using a *_HP variant."
                )
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


# Predefined physics templates
PHYSICS_TEMPLATES = {
    "standard": PhysicsConfig(
        physics_list=PhysicsListType.FTFP_BERT,
        em_physics=EMPhysicsOption.STANDARD,
        default_cut=1.0
    ),
    "medical": PhysicsConfig(
        physics_list=PhysicsListType.QGSP_BIC,
        em_physics=EMPhysicsOption.OPTION4,
        default_cut=0.1,
        enable_radioactive_decay=False
    ),
    "shielding": PhysicsConfig(
        physics_list=PhysicsListType.SHIELDING,
        em_physics=EMPhysicsOption.STANDARD,
        default_cut=1.0,
        enable_radioactive_decay=True
    ),
    "low_energy": PhysicsConfig(
        physics_list=PhysicsListType.LIVERMORE,
        em_physics=EMPhysicsOption.LIVERMORE,
        default_cut=0.01,
        low_energy_limit=0.00025  # 250 eV
    )
}


# Global physics builder instance
physics_builder = PhysicsBuilder()

