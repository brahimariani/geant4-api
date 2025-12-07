# Running the B2a Tracker Example

This guide explains how to run the **B2a Tracker Simulation** - a Geant4 example with a Lead target and 5 Xenon gas tracking chambers.

---

## B2a Geometry (Built into the executable)

| Component | Material | Description |
|-----------|----------|-------------|
| Target | G4_Pb (Lead) | 5 cm cylinder |
| Chambers (x5) | G4_Xe (Xenon) | Tracker chambers |
| World | G4_AIR | Air-filled world |

> **Note:** The B2a geometry is **hardcoded in C++** (DetectorConstruction.cc), not configurable via API. The API only controls the **particle source** and **number of events**.

---

## Option 1: Run B2a Directly (Recommended for Testing)

Run the B2a executable directly with a macro file:

```bash
# Navigate to B2a directory
cd /home/vgate/Documents/geant4-api/app/core/geant4_app/B2a

# Create macro file (if not exists)
cat > run.mac << 'EOF'
# B2a Example - 3 GeV Proton Beam
/control/verbose 0
/run/verbose 1
/run/initialize

/gps/particle proton
/gps/ene/mono 3 GeV
/gps/pos/centre 0. 0. -250. cm
/gps/direction 0 0 1

/run/beamOn 100
EOF

# Run the executable
./build/exampleB2a run.mac
```

### Expected Output

```
========================================
 Geant4 B2a Example - API Mode
 Tracker Simulation
========================================

Materials defined:
  Target: G4_Pb
  Chamber: G4_Xe

Geometry parameters:
  World extent: 3.36 m
  Target length: 5 cm
  Number of chambers: 5

========================================
### Run 0 starts.
    Number of events: 100
========================================

>>> Event 0 | Hits: 42 | Total Edep: 123.45 keV
>>> Event 1 | Hits: 38 | Total Edep: 98.76 keV
...
```

---

## Option 2: Run B2a via REST API

### Step 1: Start the API Server

```bash
# Terminal 1
cd /home/vgate/Documents/geant4-api
source venv/bin/activate
source /home/vgate/Software/Geant4/install/bin/geant4.sh
python run.py
```

### Step 2: Configure Geant4 Executable

```bash
# Terminal 2
curl -X POST http://localhost:8000/api/v1/geant4/configure \
  -H "Content-Type: application/json" \
  -d '{
    "executable_path": "/home/vgate/Documents/geant4-api/app/core/geant4_app/B2a/build/exampleB2a"
  }'
```

### Step 3: Create B2a Simulation

```bash
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "simulation": {
      "name": "b2a_tracker_simulation",
      "description": "B2a Tracker - 3 GeV proton beam on Lead target",
      "num_events": 100,
      "output_every_n_events": 10
    },
    "source": {
      "name": "proton_beam",
      "particle": "proton",
      "energy": {"distribution": "mono", "value": 3000},
      "direction": {"distribution": "directed", "direction": {"x": 0, "y": 0, "z": 1}},
      "position": {"distribution": "point", "center": {"x": 0, "y": 0, "z": -2500}}
    }
  }'
```

**Response:**
```json
{
  "id": "abc123-def456-...",
  "name": "b2a_tracker_simulation",
  "status": "pending",
  ...
}
```

### Step 4: Start the Simulation

```bash
# Replace {simulation_id} with the actual ID from Step 3
curl -X POST http://localhost:8000/api/v1/simulations/{simulation_id}/start
```

### Step 5: Monitor Progress

```bash
# Check progress via REST
curl http://localhost:8000/api/v1/simulations/{simulation_id}/progress

# Or monitor via WebSocket (real-time)
websocat ws://localhost:8000/ws/simulations/{simulation_id}
```

### Step 6: Get Results

```bash
curl http://localhost:8000/api/v1/results/{simulation_id}/summary
```

---

## Option 3: Run Different Particle Beams

### Gamma Beam (100 MeV)

```bash
# Direct execution
cat > run_gamma.mac << 'EOF'
/run/initialize
/gps/particle gamma
/gps/ene/mono 100 MeV
/gps/pos/centre 0. 0. -250. cm
/gps/direction 0 0 1
/run/beamOn 500
EOF

./build/exampleB2a run_gamma.mac
```

### Electron Beam (500 MeV)

```bash
# Direct execution
cat > run_electron.mac << 'EOF'
/run/initialize
/gps/particle e-
/gps/ene/mono 500 MeV
/gps/pos/centre 0. 0. -250. cm
/gps/direction 0 0 1
/run/beamOn 200
EOF

./build/exampleB2a run_electron.mac
```

### Via API (Gamma)

```bash
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "simulation": {
      "name": "b2a_gamma_test",
      "num_events": 500
    },
    "source": {
      "particle": "gamma",
      "energy": {"distribution": "mono", "value": 100},
      "position": {"center": {"x": 0, "y": 0, "z": -2500}}
    }
  }'
```

---

## Complete Test Script

Save this as `test_b2a.sh`:

```bash
#!/bin/bash
# test_b2a.sh - Complete B2a API Test

API="http://localhost:8000/api/v1"

echo "=== B2a Tracker Simulation Test ==="
echo

# 1. Configure executable
echo "1. Configuring Geant4..."
curl -s -X POST "$API/geant4/configure" \
  -H "Content-Type: application/json" \
  -d '{"executable_path": "/home/vgate/Documents/geant4-api/app/core/geant4_app/B2a/build/exampleB2a"}' \
  | python3 -m json.tool
echo

# 2. Create simulation
echo "2. Creating B2a simulation..."
RESPONSE=$(curl -s -X POST "$API/simulations" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation": {"name": "b2a_test", "num_events": 50},
    "source": {"particle": "proton", "energy": {"value": 3000}}
  }')

SIM_ID=$(echo $RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Simulation ID: $SIM_ID"
echo

# 3. Start
echo "3. Starting simulation..."
curl -s -X POST "$API/simulations/$SIM_ID/start" | python3 -m json.tool
echo

# 4. Monitor
echo "4. Monitoring progress..."
while true; do
    STATUS=$(curl -s "$API/simulations/$SIM_ID/progress" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'], d.get('progress_percent',0))")
    echo "   $STATUS"
    
    if [[ "$STATUS" == *"completed"* ]] || [[ "$STATUS" == *"failed"* ]]; then
        break
    fi
    sleep 2
done
echo

# 5. Results
echo "5. Results:"
curl -s "$API/results/$SIM_ID/summary" | python3 -m json.tool

echo
echo "=== Done ==="
```

Run it:
```bash
chmod +x test_b2a.sh
./test_b2a.sh
```

---

## Troubleshooting

### "Cannot open macro file"

```bash
# Make sure you're in the right directory
cd /home/vgate/Documents/geant4-api/app/core/geant4_app/B2a
./build/exampleB2a run.mac  # NOT ../run.mac
```

### "Geant4 libraries not found"

```bash
# Source Geant4 environment first
source /home/vgate/Software/Geant4/install/bin/geant4.sh
./build/exampleB2a run.mac
```

### API returns "simulation mode" instead of real Geant4

```bash
# Make sure executable is configured
curl http://localhost:8000/api/v1/geant4/status

# Reconfigure if needed
curl -X POST http://localhost:8000/api/v1/geant4/configure \
  -H "Content-Type: application/json" \
  -d '{"executable_path": "/home/vgate/Documents/geant4-api/app/core/geant4_app/B2a/build/exampleB2a"}'
```

