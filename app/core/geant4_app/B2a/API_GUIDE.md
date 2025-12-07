# B2a Example - REST API Testing Guide

Complete guide for testing the Geant4 B2a tracker simulation through the REST API with real-time WebSocket streaming.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Start the API Server](#start-the-api-server)
3. [Configure Geant4 Executable](#configure-geant4-executable)
4. [Create and Run Simulations](#create-and-run-simulations)
5. [WebSocket Real-Time Streaming](#websocket-real-time-streaming)
6. [Get Results](#get-results)
7. [Python Client Example](#python-client-example)
8. [JavaScript Client Example](#javascript-client-example)
9. [Complete Workflow Example](#complete-workflow-example)

---

## Prerequisites

1. **B2a executable built:**
   ```bash
   /home/vgate/Documents/geant4-api/app/core/geant4_app/B2a/build/exampleB2a
   ```

2. **API server running:**
   ```bash
   cd /home/vgate/Documents/geant4-api
   source venv/bin/activate
   python run.py
   ```

3. **API accessible at:** `http://localhost:8000`

---

## Start the API Server

```bash
# Terminal 1: Start the API
cd /home/vgate/Documents/geant4-api
source venv/bin/activate
source /home/vgate/Software/Geant4/install/bin/geant4.sh
python run.py
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "version": "1.0.0", "geant4_available": false}
```

---

## Configure Geant4 Executable

### Check Current Status

```bash
curl http://localhost:8000/api/v1/geant4/status | python3 -m json.tool
```

### Configure B2a Executable

```bash
curl -X POST http://localhost:8000/api/v1/geant4/configure \
  -H "Content-Type: application/json" \
  -d '{
    "install_path": "/home/vgate/Software/Geant4/install",
    "data_path": "/home/vgate/Software/Geant4/install/share/Geant4/data",
    "executable_path": "/home/vgate/Documents/geant4-api/app/core/geant4_app/B2a/build/exampleB2a"
  }' | python3 -m json.tool
```

### Verify Configuration

```bash
curl http://localhost:8000/api/v1/geant4/verify | python3 -m json.tool
```

---

## Create and Run Simulations

### Method 1: Quick Start (Using Templates)

```bash
# Create a quick simulation with water_phantom template
curl -X POST "http://localhost:8000/api/v1/simulations/quick-start/water_phantom?num_events=100" \
  -H "Content-Type: application/json" | python3 -m json.tool
```

Response:
```json
{
  "simulation_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "water_phantom_quick",
  "status": "pending",
  "message": "Created quick-start simulation...",
  "websocket_url": "/ws/simulations/550e8400-e29b-41d4-a716-446655440000"
}
```

### Method 2: Custom Simulation Configuration

```bash
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "simulation": {
      "name": "b2a_proton_test",
      "description": "B2a tracker test with 3 GeV protons",
      "num_events": 100,
      "output_every_n_events": 10,
      "verbose_level": 1
    },
    "source": {
      "name": "proton_beam",
      "particle": "proton",
      "energy": {
        "distribution": "mono",
        "value": 3000
      },
      "direction": {
        "distribution": "directed",
        "direction": {"x": 0, "y": 0, "z": 1}
      },
      "position": {
        "distribution": "point",
        "center": {"x": 0, "y": 0, "z": -2500}
      }
    }
  }' | python3 -m json.tool
```

### Start the Simulation

```bash
# Replace {simulation_id} with actual ID from previous response
curl -X POST http://localhost:8000/api/v1/simulations/{simulation_id}/start \
  | python3 -m json.tool
```

### Check Progress

```bash
curl http://localhost:8000/api/v1/simulations/{simulation_id}/progress \
  | python3 -m json.tool
```

---

## WebSocket Real-Time Streaming

### Connect to WebSocket

**URL Format:**
```
ws://localhost:8000/ws/simulations/{simulation_id}
```

**Optional Query Parameters:**
- `include_hits=true` - Include hit data in event batches
- `include_trajectories=true` - Include trajectory data

### Using websocat (Command Line)

```bash
# Install websocat
sudo apt install websocat
# Or: cargo install websocat

# Connect to simulation WebSocket
websocat ws://localhost:8000/ws/simulations/{simulation_id}
```

### Using wscat (Node.js)

```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c ws://localhost:8000/ws/simulations/{simulation_id}
```

### WebSocket Event Types

| Event Type | Description |
|------------|-------------|
| `status` | Simulation status change |
| `progress` | Progress update with events completed |
| `event_batch` | Batch of processed events |
| `hit` | Individual hit data |
| `completed` | Simulation finished |
| `error` | Error occurred |
| `heartbeat` | Keep-alive ping |

### Example WebSocket Messages

**Progress Update:**
```json
{
  "event_type": "progress",
  "simulation_id": "550e8400-...",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "events_completed": 50,
    "events_total": 100,
    "progress_percent": 50.0,
    "elapsed_time": 2.5,
    "estimated_remaining": 2.5,
    "event_rate": 20.0
  }
}
```

**Completion:**
```json
{
  "event_type": "completed",
  "simulation_id": "550e8400-...",
  "data": {
    "status": "completed",
    "total_events": 100,
    "elapsed_time": 5.2,
    "events_per_second": 19.2,
    "result_path": "/path/to/results"
  }
}
```

### Send Commands via WebSocket

```json
{"command": "pause"}
{"command": "resume"}
{"command": "cancel"}
{"command": "get_status"}
```

---

## Get Results

### Get Full Results

```bash
curl http://localhost:8000/api/v1/results/{simulation_id} | python3 -m json.tool
```

### Get Summary Only

```bash
curl http://localhost:8000/api/v1/results/{simulation_id}/summary | python3 -m json.tool
```

### Get Detector Results

```bash
curl http://localhost:8000/api/v1/results/{simulation_id}/detectors | python3 -m json.tool
```

### Get Hits Data

```bash
# Get first 100 hits
curl "http://localhost:8000/api/v1/results/{simulation_id}/hits?limit=100" \
  | python3 -m json.tool

# Filter by detector
curl "http://localhost:8000/api/v1/results/{simulation_id}/hits?detector=Chamber&limit=50" \
  | python3 -m json.tool
```

### Export Results

```bash
# Export as JSON
curl http://localhost:8000/api/v1/results/{simulation_id}/export/json \
  -o results.json

# Export hits as CSV
curl http://localhost:8000/api/v1/results/{simulation_id}/export/csv \
  -o hits.csv
```

---

## Python Client Example

### Installation

```bash
pip install httpx websockets asyncio
```

### Complete Python Client

```python
#!/usr/bin/env python3
"""
B2a Simulation Client - Python Example
"""

import asyncio
import json
import httpx
import websockets

API_BASE = "http://localhost:8000/api/v1"
WS_BASE = "ws://localhost:8000/ws"


async def configure_geant4():
    """Configure Geant4 executable."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/geant4/configure",
            json={
                "install_path": "/home/vgate/Software/Geant4/install",
                "executable_path": "/home/vgate/Documents/geant4-api/app/core/geant4_app/B2a/build/exampleB2a"
            }
        )
        print("Geant4 configured:", response.json())
        return response.json()


async def create_simulation():
    """Create a new simulation."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/simulations",
            json={
                "simulation": {
                    "name": "b2a_python_test",
                    "description": "Test from Python client",
                    "num_events": 50,
                    "output_every_n_events": 10
                },
                "source": {
                    "particle": "proton",
                    "energy": {"distribution": "mono", "value": 3000},
                    "position": {"center": {"x": 0, "y": 0, "z": -2500}}
                }
            }
        )
        job = response.json()
        print(f"Created simulation: {job['id']}")
        return job['id']


async def start_simulation(simulation_id: str):
    """Start the simulation."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/simulations/{simulation_id}/start"
        )
        print("Simulation started:", response.json())


async def monitor_websocket(simulation_id: str):
    """Monitor simulation via WebSocket."""
    uri = f"{WS_BASE}/simulations/{simulation_id}"
    
    print(f"\nConnecting to WebSocket: {uri}")
    
    async with websockets.connect(uri) as ws:
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=60)
                event = json.loads(message)
                
                event_type = event.get("event_type")
                data = event.get("data", {})
                
                if event_type == "progress":
                    progress = data.get("progress_percent", 0)
                    rate = data.get("event_rate", 0)
                    print(f"\rProgress: {progress:.1f}% | Rate: {rate:.0f} events/s", end="")
                
                elif event_type == "completed":
                    print(f"\n\n✅ Simulation completed!")
                    print(f"   Total events: {data.get('total_events')}")
                    print(f"   Elapsed time: {data.get('elapsed_time'):.2f}s")
                    print(f"   Events/sec: {data.get('events_per_second'):.1f}")
                    break
                
                elif event_type == "error":
                    print(f"\n❌ Error: {data.get('error')}")
                    break
                
                elif event_type == "status":
                    print(f"Status: {data.get('status')} - {data.get('message', '')}")
                
            except asyncio.TimeoutError:
                print("\nTimeout waiting for updates")
                break


async def get_results(simulation_id: str):
    """Fetch simulation results."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/results/{simulation_id}/summary"
        )
        if response.status_code == 200:
            results = response.json()
            print("\n📊 Results Summary:")
            print(f"   Events: {results.get('num_events')}")
            print(f"   Total energy deposited: {results.get('total_energy_deposited'):.4f} MeV")
            return results
        else:
            print("Results not available yet")
            return None


async def main():
    """Run complete simulation workflow."""
    print("=" * 50)
    print("  B2a Simulation - Python Client")
    print("=" * 50)
    
    # 1. Configure Geant4 (if needed)
    # await configure_geant4()
    
    # 2. Create simulation
    simulation_id = await create_simulation()
    
    # 3. Start simulation
    await start_simulation(simulation_id)
    
    # 4. Monitor via WebSocket
    await monitor_websocket(simulation_id)
    
    # 5. Get results
    await get_results(simulation_id)


if __name__ == "__main__":
    asyncio.run(main())
```

### Run the Python Client

```bash
python3 b2a_client.py
```

---

## JavaScript Client Example

### Browser WebSocket Client

```html
<!DOCTYPE html>
<html>
<head>
    <title>B2a Simulation Monitor</title>
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #00ff88; padding: 20px; }
        .progress { width: 100%; height: 30px; background: #333; border-radius: 5px; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, #00ff88, #00d4ff); border-radius: 5px; transition: width 0.3s; }
        .log { background: #0a0a1a; padding: 10px; height: 300px; overflow-y: auto; border-radius: 5px; }
        button { background: #00ff88; color: #1a1a2e; border: none; padding: 10px 20px; cursor: pointer; margin: 5px; }
    </style>
</head>
<body>
    <h1>⚛️ B2a Simulation Monitor</h1>
    
    <div>
        <input type="text" id="simId" placeholder="Simulation ID" style="padding: 10px; width: 300px;">
        <button onclick="connect()">Connect</button>
        <button onclick="disconnect()">Disconnect</button>
    </div>
    
    <h3>Progress</h3>
    <div class="progress">
        <div class="progress-bar" id="progressBar" style="width: 0%"></div>
    </div>
    <p id="stats">Events: 0 / 0 | Rate: 0/s</p>
    
    <h3>Controls</h3>
    <button onclick="sendCommand('pause')">⏸️ Pause</button>
    <button onclick="sendCommand('resume')">▶️ Resume</button>
    <button onclick="sendCommand('cancel')">⏹️ Cancel</button>
    
    <h3>Event Log</h3>
    <div class="log" id="log"></div>

    <script>
        let ws = null;
        
        function connect() {
            const simId = document.getElementById('simId').value;
            if (!simId) { log('Enter simulation ID'); return; }
            
            ws = new WebSocket(`ws://localhost:8000/ws/simulations/${simId}`);
            
            ws.onopen = () => log('✅ Connected');
            ws.onclose = () => log('🔴 Disconnected');
            ws.onerror = (e) => log('❌ Error: ' + e);
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleEvent(data);
            };
        }
        
        function disconnect() {
            if (ws) ws.close();
        }
        
        function sendCommand(cmd) {
            if (ws) ws.send(JSON.stringify({ command: cmd }));
        }
        
        function handleEvent(event) {
            const type = event.event_type;
            const data = event.data || {};
            
            if (type === 'progress') {
                const pct = data.progress_percent || 0;
                document.getElementById('progressBar').style.width = pct + '%';
                document.getElementById('stats').textContent = 
                    `Events: ${data.events_completed} / ${data.events_total} | Rate: ${(data.event_rate || 0).toFixed(0)}/s`;
            } else if (type === 'completed') {
                log('✅ COMPLETED: ' + data.total_events + ' events in ' + data.elapsed_time.toFixed(2) + 's');
            } else if (type === 'error') {
                log('❌ ERROR: ' + (data.message || data.error));
            } else {
                log(`[${type}] ${JSON.stringify(data)}`);
            }
        }
        
        function log(msg) {
            const logEl = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            logEl.innerHTML += `[${time}] ${msg}<br>`;
            logEl.scrollTop = logEl.scrollHeight;
        }
    </script>
</body>
</html>
```

### Node.js Client

```javascript
// b2a_client.js
const WebSocket = require('ws');
const fetch = require('node-fetch');

const API_BASE = 'http://localhost:8000/api/v1';
const WS_BASE = 'ws://localhost:8000/ws';

async function createSimulation() {
    const response = await fetch(`${API_BASE}/simulations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            simulation: {
                name: 'b2a_nodejs_test',
                num_events: 50,
                output_every_n_events: 10
            },
            source: {
                particle: 'proton',
                energy: { distribution: 'mono', value: 3000 }
            }
        })
    });
    return await response.json();
}

async function startSimulation(simId) {
    await fetch(`${API_BASE}/simulations/${simId}/start`, { method: 'POST' });
}

function monitorWebSocket(simId) {
    return new Promise((resolve) => {
        const ws = new WebSocket(`${WS_BASE}/simulations/${simId}`);
        
        ws.on('message', (data) => {
            const event = JSON.parse(data);
            
            if (event.event_type === 'progress') {
                process.stdout.write(`\rProgress: ${event.data.progress_percent.toFixed(1)}%`);
            } else if (event.event_type === 'completed') {
                console.log('\n✅ Completed!');
                ws.close();
                resolve();
            }
        });
    });
}

async function main() {
    console.log('Creating simulation...');
    const job = await createSimulation();
    console.log('Simulation ID:', job.id);
    
    console.log('Starting...');
    await startSimulation(job.id);
    
    console.log('Monitoring via WebSocket...');
    await monitorWebSocket(job.id);
}

main().catch(console.error);
```

---

## Complete Workflow Example

### Step-by-Step with curl

```bash
#!/bin/bash
# complete_test.sh - Full B2a API test workflow

API="http://localhost:8000/api/v1"

echo "=== B2a API Test Workflow ==="
echo

# 1. Check API health
echo "1. Checking API health..."
curl -s $API/../health | python3 -m json.tool
echo

# 2. Check Geant4 status
echo "2. Checking Geant4 status..."
curl -s $API/geant4/status | python3 -m json.tool
echo

# 3. Create simulation
echo "3. Creating simulation..."
RESPONSE=$(curl -s -X POST "$API/simulations/quick-start/water_phantom?num_events=50")
SIM_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['simulation_id'])")
echo "Simulation ID: $SIM_ID"
echo

# 4. Start simulation
echo "4. Starting simulation..."
curl -s -X POST "$API/simulations/$SIM_ID/start" | python3 -m json.tool
echo

# 5. Poll progress
echo "5. Monitoring progress..."
while true; do
    PROGRESS=$(curl -s "$API/simulations/$SIM_ID/progress")
    STATUS=$(echo $PROGRESS | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    PCT=$(echo $PROGRESS | python3 -c "import sys, json; print(json.load(sys.stdin).get('progress_percent', 0))")
    
    echo -ne "\r   Status: $STATUS | Progress: $PCT%   "
    
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        echo
        break
    fi
    sleep 1
done
echo

# 6. Get results
echo "6. Fetching results..."
curl -s "$API/results/$SIM_ID/summary" | python3 -m json.tool
echo

echo "=== Test Complete ==="
```

Make it executable and run:
```bash
chmod +x complete_test.sh
./complete_test.sh
```

---

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/geant4/status` | Geant4 configuration status |
| POST | `/api/v1/geant4/configure` | Configure Geant4 paths |
| GET | `/api/v1/simulations` | List all simulations |
| POST | `/api/v1/simulations` | Create new simulation |
| POST | `/api/v1/simulations/{id}/start` | Start simulation |
| POST | `/api/v1/simulations/{id}/pause` | Pause simulation |
| POST | `/api/v1/simulations/{id}/resume` | Resume simulation |
| POST | `/api/v1/simulations/{id}/cancel` | Cancel simulation |
| GET | `/api/v1/simulations/{id}/progress` | Get progress |
| GET | `/api/v1/results/{id}` | Get full results |
| GET | `/api/v1/results/{id}/summary` | Get summary |
| WS | `/ws/simulations/{id}` | WebSocket stream |

---

## Troubleshooting

### WebSocket Connection Refused

```bash
# Check if API is running
curl http://localhost:8000/health

# Check firewall
sudo ufw allow 8000
```

### Simulation Stuck in "pending"

```bash
# Check if Geant4 is configured
curl http://localhost:8000/api/v1/geant4/status

# Verify executable exists
ls -la /path/to/exampleB2a
```

### No Real-Time Updates

Make sure you're using WebSocket, not polling:
```bash
# WebSocket (real-time) ✅
websocat ws://localhost:8000/ws/simulations/{id}

# Polling (slower) ⚠️
watch -n1 'curl -s http://localhost:8000/api/v1/simulations/{id}/progress'
```

