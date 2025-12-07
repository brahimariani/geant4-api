# Geant4 Real-Time API

A Python/REST API wrapper for **Geant4** Monte Carlo simulations with real-time WebSocket streaming support.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- 🚀 **REST API** for simulation configuration and control
- 📡 **WebSocket streaming** for real-time progress and results
- 🔧 **Flexible configuration** via JSON for geometry, physics, and sources
- 📊 **Results analysis** with histograms and data export
- 🐳 **Docker support** for easy deployment
- 📚 **Auto-generated documentation** (Swagger/OpenAPI)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/geant4-api.git
cd geant4-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

### Access the API

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Overview

### Simulations

```bash
# Create a simulation
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "simulation": {
      "name": "my_simulation",
      "num_events": 10000
    },
    "geometry": {
      "name": "detector",
      "world": {"half_x": 500, "half_y": 500, "half_z": 500},
      "volumes": [{
        "name": "target",
        "solid": {"type": "box", "half_x": 50, "half_y": 50, "half_z": 50},
        "material": "G4_WATER",
        "is_sensitive": true
      }]
    },
    "source": {
      "particle": "gamma",
      "energy": {"distribution": "mono", "value": 1.0}
    }
  }'

# Start the simulation
curl -X POST http://localhost:8000/api/v1/simulations/{id}/start

# Get results
curl http://localhost:8000/api/v1/results/{id}
```

### Quick Start with Templates

```bash
# Use a predefined template
curl -X POST "http://localhost:8000/api/v1/simulations/quick-start/water_phantom?num_events=5000"
```

### WebSocket Streaming

```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws/simulations/{id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event_type);
  console.log('Progress:', data.data.progress_percent, '%');
};

// Send commands
ws.send(JSON.stringify({ command: 'pause' }));
ws.send(JSON.stringify({ command: 'resume' }));
```

## Configuration

### Geometry

Define detector geometries with boxes, cylinders, spheres, and cones:

```json
{
  "name": "my_detector",
  "world": {"half_x": 1000, "half_y": 1000, "half_z": 1000, "material": "G4_AIR"},
  "volumes": [
    {
      "name": "detector",
      "solid": {"type": "cylinder", "inner_radius": 0, "outer_radius": 50, "half_z": 100},
      "material": "G4_SODIUM_IODIDE",
      "position": {"x": 0, "y": 0, "z": 200},
      "is_sensitive": true
    }
  ]
}
```

### Physics

Select physics lists and configure production cuts:

```json
{
  "physics_list": "FTFP_BERT",
  "em_physics": "standard",
  "default_cut": 1.0,
  "enable_radioactive_decay": false
}
```

### Particle Sources

Configure particle guns and GPS sources:

```json
{
  "particle": "proton",
  "energy": {"distribution": "gaussian", "value": 200.0, "sigma": 2.0},
  "direction": {"distribution": "directed", "direction": {"x": 0, "y": 0, "z": 1}},
  "position": {"distribution": "plane", "center": {"x": 0, "y": 0, "z": -300}, "half_x": 10, "half_y": 10}
}
```

## Available Templates

### Geometry Templates
- `water_phantom` - Water phantom for dosimetry
- `simple_detector` - NaI scintillator detector
- `shielded_detector` - Lead-shielded detector

### Physics Templates
- `standard` - FTFP_BERT for general purpose
- `medical` - QGSP_BIC optimized for medical physics
- `shielding` - Shielding physics list with radioactive decay
- `low_energy` - Livermore low-energy EM physics

### Source Templates
- `gamma_1mev` - 1 MeV gamma point source
- `electron_beam` - 6 MeV electron beam
- `proton_therapy` - 200 MeV proton beam
- `isotropic_neutron` - Isotropic neutron source
- `co60_source` - Co-60 gamma source

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# With Celery worker for background tasks
docker-compose --profile full up -d
```

## Project Structure

```
geant4-api/
├── app/
│   ├── api/              # REST API endpoints
│   │   ├── geometry.py   # Geometry configuration
│   │   ├── physics.py    # Physics configuration
│   │   ├── simulations.py # Simulation management
│   │   ├── sources.py    # Particle sources
│   │   ├── results.py    # Results and analysis
│   │   └── websocket.py  # WebSocket handlers
│   ├── core/             # Core simulation logic
│   │   ├── simulation_engine.py
│   │   ├── geometry_builder.py
│   │   ├── physics_builder.py
│   │   └── source_builder.py
│   ├── models/           # Pydantic models
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI application
├── results/              # Simulation results
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `GEANT4_INSTALL_PATH` | Path to Geant4 installation | - |
| `GEANT4_USE_SUBPROCESS` | Use subprocess mode | `true` |
| `REDIS_URL` | Redis URL for task queue | `redis://localhost:6379/0` |
| `RESULTS_PATH` | Results storage path | `./results` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Integration with Geant4

The API supports two modes:

1. **Subprocess Mode** (default): Generates macro files and runs Geant4 executables
2. **Python Bindings Mode**: Uses `geant4-pybind` for direct Python integration

For production use with real Geant4 simulations, you'll need:
- Geant4 installation (11.x recommended)
- Compiled Geant4 application with your physics
- Or `geant4-pybind` Python package

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines first.

## Acknowledgments

- [Geant4 Collaboration](https://geant4.web.cern.ch/)
- [FastAPI](https://fastapi.tiangolo.com/)

