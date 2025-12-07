#!/usr/bin/env python
"""
Basic Simulation Example
========================

Demonstrates how to use the Geant4 API to run a simple simulation.
"""

import httpx
import asyncio
import websockets
import json

API_BASE = "http://localhost:8000/api/v1"
WS_BASE = "ws://localhost:8000/ws"


async def main():
    """Run a basic gamma simulation in water."""
    
    async with httpx.AsyncClient() as client:
        # 1. Create simulation configuration
        print("Creating simulation...")
        
        simulation_request = {
            "simulation": {
                "name": "gamma_water_example",
                "description": "1 MeV gammas in water phantom",
                "num_events": 1000,
                "output_every_n_events": 100,
                "verbose_level": 0
            },
            "geometry": {
                "name": "water_phantom",
                "world": {
                    "half_x": 500,
                    "half_y": 500,
                    "half_z": 500,
                    "material": "G4_AIR"
                },
                "volumes": [
                    {
                        "name": "phantom",
                        "solid": {
                            "type": "box",
                            "half_x": 150,
                            "half_y": 150,
                            "half_z": 150
                        },
                        "material": "G4_WATER",
                        "position": {"x": 0, "y": 0, "z": 0},
                        "is_sensitive": True
                    }
                ]
            },
            "physics": {
                "physics_list": "FTFP_BERT",
                "default_cut": 1.0
            },
            "source": {
                "name": "gamma_source",
                "particle": "gamma",
                "energy": {
                    "distribution": "mono",
                    "value": 1.0
                },
                "direction": {
                    "distribution": "directed",
                    "direction": {"x": 0, "y": 0, "z": 1}
                },
                "position": {
                    "distribution": "point",
                    "center": {"x": 0, "y": 0, "z": -200}
                }
            }
        }
        
        response = await client.post(
            f"{API_BASE}/simulations",
            json=simulation_request
        )
        response.raise_for_status()
        job = response.json()
        
        simulation_id = job["id"]
        print(f"Created simulation: {simulation_id}")
        
        # 2. Start simulation
        print("Starting simulation...")
        response = await client.post(
            f"{API_BASE}/simulations/{simulation_id}/start"
        )
        response.raise_for_status()
        print(response.json())
        
        # 3. Connect to WebSocket for real-time updates
        print("\nConnecting to WebSocket for updates...")
        
        async with websockets.connect(
            f"{WS_BASE}/simulations/{simulation_id}"
        ) as ws:
            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=60)
                    event = json.loads(message)
                    
                    event_type = event.get("event_type")
                    data = event.get("data", {})
                    
                    if event_type == "progress":
                        progress = data.get("progress_percent", 0)
                        rate = data.get("event_rate", 0)
                        print(f"\rProgress: {progress:.1f}% ({rate:.0f} events/s)", end="")
                    
                    elif event_type == "completed":
                        print(f"\n\nSimulation completed!")
                        print(f"Total events: {data.get('total_events')}")
                        print(f"Elapsed time: {data.get('elapsed_time'):.2f}s")
                        break
                    
                    elif event_type == "error":
                        print(f"\nError: {data.get('error')}")
                        break
                    
                    elif event_type == "heartbeat":
                        pass  # Keep-alive
                    
                except asyncio.TimeoutError:
                    print("\nTimeout waiting for updates")
                    break
        
        # 4. Get results
        print("\nFetching results...")
        response = await client.get(f"{API_BASE}/results/{simulation_id}/summary")
        
        if response.status_code == 200:
            results = response.json()
            print("\nResults Summary:")
            print(f"  Events: {results.get('num_events')}")
            print(f"  Elapsed time: {results.get('elapsed_time'):.2f}s")
            print(f"  Event rate: {results.get('events_per_second'):.0f}/s")
            print(f"  Total energy deposited: {results.get('total_energy_deposited'):.4f} MeV")
        else:
            print("Results not yet available")


if __name__ == "__main__":
    print("=" * 50)
    print("Geant4 API - Basic Simulation Example")
    print("=" * 50)
    print()
    
    asyncio.run(main())

