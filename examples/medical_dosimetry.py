#!/usr/bin/env python
"""
Medical Dosimetry Example
=========================

Simulates a proton therapy treatment with dose calculation.
"""

import httpx
import asyncio
import json

API_BASE = "http://localhost:8000/api/v1"


async def main():
    """Run a proton therapy dosimetry simulation."""
    
    async with httpx.AsyncClient(timeout=60) as client:
        
        # 1. Create water phantom geometry
        print("Creating patient phantom geometry...")
        
        geometry = {
            "name": "patient_phantom",
            "description": "Simplified patient water phantom for proton therapy",
            "world": {
                "half_x": 500,
                "half_y": 500,
                "half_z": 500,
                "material": "G4_AIR"
            },
            "volumes": [
                # Patient body (simplified as water box)
                {
                    "name": "body",
                    "solid": {
                        "type": "box",
                        "half_x": 150,
                        "half_y": 200,
                        "half_z": 300
                    },
                    "material": "G4_WATER",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "is_sensitive": True
                },
                # Target volume (tumor)
                {
                    "name": "tumor",
                    "solid": {
                        "type": "sphere",
                        "inner_radius": 0,
                        "outer_radius": 30
                    },
                    "material": "G4_WATER",
                    "position": {"x": 0, "y": 0, "z": 100},
                    "is_sensitive": True
                }
            ]
        }
        
        response = await client.post(f"{API_BASE}/geometry", json=geometry)
        response.raise_for_status()
        print(f"Created geometry: {response.json()}")
        
        # 2. Configure medical physics
        print("\nConfiguring medical physics...")
        
        physics = {
            "physics_list": "QGSP_BIC",
            "em_physics": "option4",
            "default_cut": 0.1,  # 0.1 mm for better accuracy
            "enable_radioactive_decay": False
        }
        
        response = await client.post(
            f"{API_BASE}/physics?name=proton_therapy",
            json=physics
        )
        response.raise_for_status()
        print(f"Created physics config: {response.json()}")
        
        # 3. Configure proton beam
        print("\nConfiguring proton beam...")
        
        source = {
            "name": "proton_beam",
            "particle": "proton",
            "energy": {
                "distribution": "gaussian",
                "value": 150.0,  # 150 MeV protons
                "sigma": 1.5    # 1% energy spread
            },
            "direction": {
                "distribution": "directed",
                "direction": {"x": 0, "y": 0, "z": 1}
            },
            "position": {
                "distribution": "plane",
                "center": {"x": 0, "y": 0, "z": -400},
                "half_x": 5.0,  # 10mm beam spot
                "half_y": 5.0
            },
            "number_of_particles": 1
        }
        
        response = await client.post(f"{API_BASE}/sources", json=source)
        response.raise_for_status()
        print(f"Created source: {response.json()}")
        
        # 4. Create and run simulation
        print("\nCreating simulation...")
        
        simulation_request = {
            "simulation": {
                "name": "proton_therapy_dose",
                "description": "150 MeV proton beam dose calculation",
                "num_events": 5000,
                "output_every_n_events": 500,
                "num_threads": 4
            },
            "geometry_id": "patient_phantom",
            "physics_id": "proton_therapy",
            "source_id": "proton_beam"
        }
        
        response = await client.post(
            f"{API_BASE}/simulations",
            json=simulation_request
        )
        response.raise_for_status()
        job = response.json()
        simulation_id = job["id"]
        print(f"Created simulation: {simulation_id}")
        
        # 5. Start and monitor
        print("\nStarting simulation...")
        response = await client.post(
            f"{API_BASE}/simulations/{simulation_id}/start"
        )
        
        # Poll for progress
        while True:
            await asyncio.sleep(2)
            
            response = await client.get(
                f"{API_BASE}/simulations/{simulation_id}/progress"
            )
            progress = response.json()
            
            status = progress.get("status")
            pct = progress.get("progress_percent", 0)
            
            print(f"\rStatus: {status}, Progress: {pct:.1f}%", end="")
            
            if status in ["completed", "failed", "cancelled"]:
                print()
                break
        
        # 6. Analyze results
        if status == "completed":
            print("\n\nAnalyzing results...")
            
            # Get detector results
            response = await client.get(
                f"{API_BASE}/results/{simulation_id}/detectors"
            )
            detectors = response.json()
            
            print("\nDose Summary:")
            for det in detectors.get("detectors", []):
                print(f"\n  {det['name']}:")
                print(f"    Total hits: {det['total_hits']}")
                print(f"    Energy deposited: {det['total_energy_deposit']:.4f} MeV")
                print(f"    Mean per event: {det['mean_energy_per_event']:.4f} MeV")
            
            # Get energy histogram
            response = await client.get(
                f"{API_BASE}/results/{simulation_id}/histogram/energy_deposit?bins=50"
            )
            
            if response.status_code == 200:
                hist = response.json()
                print(f"\nEnergy deposit histogram:")
                print(f"  Entries: {hist.get('entries')}")
                print(f"  Mean: {hist.get('mean', 0):.4f} MeV")
                print(f"  Std Dev: {hist.get('std_dev', 0):.4f} MeV")


if __name__ == "__main__":
    print("=" * 60)
    print("Geant4 API - Medical Proton Therapy Dosimetry Example")
    print("=" * 60)
    print()
    
    asyncio.run(main())

