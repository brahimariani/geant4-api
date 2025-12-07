"""
Particle source builder for Geant4 primary generators.
"""

from typing import Dict, Optional, List, Any
from loguru import logger

from app.models.particle import (
    ParticleSource, ParticleType, EnergyDistribution,
    AngularDistribution, PositionDistribution,
    EnergyConfig, DirectionConfig, PositionConfig,
    Vector3D, IonConfig, RadioactiveSource
)


class SourceBuilder:
    """
    Builds Geant4 particle source configurations.
    
    Generates GPS (General Particle Source) macro commands.
    """
    
    def __init__(self):
        self.sources: Dict[str, ParticleSource] = {}
    
    def create_source(self, config: ParticleSource) -> str:
        """Create and store a particle source configuration."""
        source_id = config.name
        self.sources[source_id] = config
        logger.info(f"Created particle source: {source_id}")
        return source_id
    
    def get_source(self, source_id: str) -> Optional[ParticleSource]:
        """Get a stored source configuration."""
        return self.sources.get(source_id)
    
    def list_sources(self) -> List[str]:
        """List all stored source IDs."""
        return list(self.sources.keys())
    
    def delete_source(self, source_id: str) -> bool:
        """Delete a stored source."""
        if source_id in self.sources:
            del self.sources[source_id]
            return True
        return False
    
    def to_gps_commands(self, config: ParticleSource) -> List[str]:
        """
        Convert source configuration to GPS macro commands.
        """
        commands = [
            "# Particle source configuration",
            f"# Source: {config.name}",
            "",
            "# Particle type",
            f"/gps/particle {config.particle}",
            f"/gps/number {config.number_of_particles}",
            "",
        ]
        
        # Energy configuration
        commands.extend(self._energy_commands(config.energy))
        
        # Position configuration
        commands.extend(self._position_commands(config.position))
        
        # Direction configuration
        commands.extend(self._direction_commands(config.direction))
        
        return commands
    
    def _energy_commands(self, energy: EnergyConfig) -> List[str]:
        """Generate GPS energy commands."""
        commands = ["# Energy"]
        
        if energy.distribution == EnergyDistribution.MONO:
            commands.append(f"/gps/ene/type Mono")
            commands.append(f"/gps/ene/mono {energy.value} MeV")
            
        elif energy.distribution == EnergyDistribution.GAUSSIAN:
            commands.append(f"/gps/ene/type Gauss")
            commands.append(f"/gps/ene/mono {energy.value} MeV")
            if energy.sigma:
                commands.append(f"/gps/ene/sigma {energy.sigma} MeV")
                
        elif energy.distribution == EnergyDistribution.FLAT:
            commands.append(f"/gps/ene/type Lin")
            if energy.min_energy is not None and energy.max_energy is not None:
                commands.append(f"/gps/ene/min {energy.min_energy} MeV")
                commands.append(f"/gps/ene/max {energy.max_energy} MeV")
            commands.append(f"/gps/ene/gradient 0")
            commands.append(f"/gps/ene/intercept 1")
            
        elif energy.distribution == EnergyDistribution.EXPONENTIAL:
            commands.append(f"/gps/ene/type Exp")
            commands.append(f"/gps/ene/ezero {energy.value} MeV")
            
        elif energy.distribution == EnergyDistribution.POWER_LAW:
            commands.append(f"/gps/ene/type Pow")
            commands.append(f"/gps/ene/alpha -2")  # Default power law index
            if energy.min_energy is not None and energy.max_energy is not None:
                commands.append(f"/gps/ene/min {energy.min_energy} MeV")
                commands.append(f"/gps/ene/max {energy.max_energy} MeV")
        
        commands.append("")
        return commands
    
    def _position_commands(self, position: PositionConfig) -> List[str]:
        """Generate GPS position commands."""
        commands = ["# Position"]
        center = position.center
        
        if position.distribution == PositionDistribution.POINT:
            commands.append(f"/gps/pos/type Point")
            commands.append(
                f"/gps/pos/centre {center.x} {center.y} {center.z} mm"
            )
            
        elif position.distribution == PositionDistribution.PLANE:
            commands.append(f"/gps/pos/type Plane")
            commands.append(f"/gps/pos/shape Rectangle")
            commands.append(
                f"/gps/pos/centre {center.x} {center.y} {center.z} mm"
            )
            if position.half_x and position.half_y:
                commands.append(f"/gps/pos/halfx {position.half_x} mm")
                commands.append(f"/gps/pos/halfy {position.half_y} mm")
                
        elif position.distribution == PositionDistribution.SURFACE:
            commands.append(f"/gps/pos/type Surface")
            if position.radius:
                commands.append(f"/gps/pos/shape Sphere")
                commands.append(f"/gps/pos/radius {position.radius} mm")
            commands.append(
                f"/gps/pos/centre {center.x} {center.y} {center.z} mm"
            )
            
        elif position.distribution == PositionDistribution.VOLUME:
            commands.append(f"/gps/pos/type Volume")
            if position.radius:
                commands.append(f"/gps/pos/shape Sphere")
                commands.append(f"/gps/pos/radius {position.radius} mm")
            elif position.half_x and position.half_y and position.half_z:
                commands.append(f"/gps/pos/shape Para")
                commands.append(f"/gps/pos/halfx {position.half_x} mm")
                commands.append(f"/gps/pos/halfy {position.half_y} mm")
                commands.append(f"/gps/pos/halfz {position.half_z} mm")
            commands.append(
                f"/gps/pos/centre {center.x} {center.y} {center.z} mm"
            )
        
        commands.append("")
        return commands
    
    def _direction_commands(self, direction: DirectionConfig) -> List[str]:
        """Generate GPS direction commands."""
        commands = ["# Direction"]
        
        if direction.distribution == AngularDistribution.DIRECTED:
            d = direction.direction
            commands.append(
                f"/gps/direction {d.x} {d.y} {d.z}"
            )
            
        elif direction.distribution == AngularDistribution.ISOTROPIC:
            commands.append(f"/gps/ang/type iso")
            
        elif direction.distribution == AngularDistribution.COSINE:
            commands.append(f"/gps/ang/type cos")
            
        elif direction.distribution == AngularDistribution.CONE:
            commands.append(f"/gps/ang/type focused")
            d = direction.direction
            commands.append(
                f"/gps/ang/focuspoint {d.x} {d.y} {d.z} mm"
            )
            if direction.cone_angle:
                commands.append(f"/gps/ang/maxtheta {direction.cone_angle} deg")
        
        commands.append("")
        return commands
    
    def get_particle_info(self, particle: str) -> Dict[str, Any]:
        """Get information about a particle type."""
        info = {
            "e-": {
                "name": "Electron",
                "pdg": 11,
                "mass_mev": 0.511,
                "charge": -1,
                "lifetime": "stable"
            },
            "e+": {
                "name": "Positron",
                "pdg": -11,
                "mass_mev": 0.511,
                "charge": +1,
                "lifetime": "stable"
            },
            "gamma": {
                "name": "Gamma (Photon)",
                "pdg": 22,
                "mass_mev": 0,
                "charge": 0,
                "lifetime": "stable"
            },
            "proton": {
                "name": "Proton",
                "pdg": 2212,
                "mass_mev": 938.272,
                "charge": +1,
                "lifetime": "stable"
            },
            "neutron": {
                "name": "Neutron",
                "pdg": 2112,
                "mass_mev": 939.565,
                "charge": 0,
                "lifetime": "881.5 s"
            },
            "mu-": {
                "name": "Muon (negative)",
                "pdg": 13,
                "mass_mev": 105.658,
                "charge": -1,
                "lifetime": "2.2 µs"
            },
            "alpha": {
                "name": "Alpha particle",
                "pdg": 1000020040,
                "mass_mev": 3727.379,
                "charge": +2,
                "lifetime": "stable"
            },
            "pi+": {
                "name": "Pion (positive)",
                "pdg": 211,
                "mass_mev": 139.570,
                "charge": +1,
                "lifetime": "26 ns"
            },
            "pi-": {
                "name": "Pion (negative)",
                "pdg": -211,
                "mass_mev": 139.570,
                "charge": -1,
                "lifetime": "26 ns"
            },
        }
        
        return info.get(particle, {
            "name": particle,
            "pdg": None,
            "mass_mev": None,
            "charge": None,
            "lifetime": "unknown"
        })
    
    def validate_source(self, config: ParticleSource) -> Dict[str, Any]:
        """Validate source configuration."""
        issues = []
        warnings = []
        
        # Check particle type
        known_particles = {p.value for p in ParticleType}
        if config.particle not in known_particles:
            warnings.append(
                f"Particle '{config.particle}' is not a recognized type. "
                "Make sure it's a valid Geant4 particle name."
            )
        
        # Check energy
        if config.energy.value <= 0:
            issues.append("Energy must be positive")
        
        if config.energy.value > 1e9:
            warnings.append(
                f"Very high energy ({config.energy.value} MeV). "
                "Ensure physics list supports this energy range."
            )
        
        # Check Gaussian distribution
        if config.energy.distribution == EnergyDistribution.GAUSSIAN:
            if not config.energy.sigma:
                warnings.append("Gaussian energy distribution without sigma specified")
        
        # Check flat distribution
        if config.energy.distribution == EnergyDistribution.FLAT:
            if config.energy.min_energy is None or config.energy.max_energy is None:
                issues.append(
                    "Flat energy distribution requires min_energy and max_energy"
                )
        
        # Check direction normalization
        d = config.direction.direction
        mag = (d.x**2 + d.y**2 + d.z**2) ** 0.5
        if abs(mag - 1.0) > 0.01 and mag > 0:
            warnings.append(
                f"Direction vector ({d.x}, {d.y}, {d.z}) is not normalized "
                f"(magnitude = {mag:.3f})"
            )
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }


# Predefined source templates
SOURCE_TEMPLATES = {
    "gamma_1mev": ParticleSource(
        name="gamma_1mev",
        particle="gamma",
        energy=EnergyConfig(
            distribution=EnergyDistribution.MONO,
            value=1.0
        ),
        direction=DirectionConfig(
            distribution=AngularDistribution.DIRECTED,
            direction=Vector3D(x=0, y=0, z=1)
        ),
        position=PositionConfig(
            distribution=PositionDistribution.POINT,
            center=Vector3D(x=0, y=0, z=-100)
        )
    ),
    "electron_beam": ParticleSource(
        name="electron_beam",
        particle="e-",
        energy=EnergyConfig(
            distribution=EnergyDistribution.GAUSSIAN,
            value=6.0,
            sigma=0.1
        ),
        direction=DirectionConfig(
            distribution=AngularDistribution.DIRECTED,
            direction=Vector3D(x=0, y=0, z=1)
        ),
        position=PositionConfig(
            distribution=PositionDistribution.PLANE,
            center=Vector3D(x=0, y=0, z=-200),
            half_x=5.0,
            half_y=5.0
        )
    ),
    "proton_therapy": ParticleSource(
        name="proton_therapy",
        particle="proton",
        energy=EnergyConfig(
            distribution=EnergyDistribution.MONO,
            value=200.0  # 200 MeV protons
        ),
        direction=DirectionConfig(
            distribution=AngularDistribution.DIRECTED,
            direction=Vector3D(x=0, y=0, z=1)
        ),
        position=PositionConfig(
            distribution=PositionDistribution.PLANE,
            center=Vector3D(x=0, y=0, z=-300),
            half_x=10.0,
            half_y=10.0
        )
    ),
    "isotropic_neutron": ParticleSource(
        name="isotropic_neutron",
        particle="neutron",
        energy=EnergyConfig(
            distribution=EnergyDistribution.FLAT,
            value=1.0,
            min_energy=0.001,
            max_energy=10.0
        ),
        direction=DirectionConfig(
            distribution=AngularDistribution.ISOTROPIC
        ),
        position=PositionConfig(
            distribution=PositionDistribution.POINT,
            center=Vector3D(x=0, y=0, z=0)
        )
    ),
    "co60_source": ParticleSource(
        name="co60_source",
        particle="gamma",
        energy=EnergyConfig(
            distribution=EnergyDistribution.MONO,
            value=1.25  # Average of 1.17 and 1.33 MeV
        ),
        direction=DirectionConfig(
            distribution=AngularDistribution.ISOTROPIC
        ),
        position=PositionConfig(
            distribution=PositionDistribution.POINT,
            center=Vector3D(x=0, y=0, z=0)
        )
    )
}


# Global source builder instance
source_builder = SourceBuilder()

