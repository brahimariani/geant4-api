# Geant4 REST API - Ubuntu Server Installation Guide

Complete guide for installing and running the Geant4 REST API on Ubuntu Server with an existing Geant4 installation.

---

## Prerequisites

- Ubuntu Server 20.04/22.04/24.04
- Geant4 11.x already installed
- Python 3.10 or higher
- CMake 3.16+
- GCC/G++ compiler

---

## 1. Verify Geant4 Installation

First, verify your Geant4 installation:

```bash
# Check if Geant4 environment script exists
ls /opt/geant4/geant4-v11.*/bin/geant4.sh

# Or check common installation paths
ls /usr/local/geant4/bin/geant4.sh
ls ~/geant4/bin/geant4.sh

# Source the Geant4 environment (adjust path to your installation)
source /opt/geant4/geant4-v11.2.0-install/bin/geant4.sh

# Verify Geant4 is available
which geant4-config
geant4-config --version
```

**Note your Geant4 installation path** - you'll need it later.

---

## 2. Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install build tools (for compiling the Geant4 example)
sudo apt install -y build-essential cmake

# Optional: Install Redis for background task queue
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

---

## 3. Clone/Setup the Project

```bash
# Navigate to your preferred directory
cd /opt  # or ~/projects or wherever you want

# If cloning from git:
# git clone https://github.com/your-repo/geant4-api.git

# Or if copying existing files:
# Copy the geant4-api folder to this location

cd geant4-api
```

---

## 4. Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

## 5. Build the B2a Geant4 Example

```bash
# Source Geant4 environment (IMPORTANT!)
source /opt/geant4/geant4-v11.2.0-install/bin/geant4.sh

# Navigate to B2a example
cd app/core/geant4_app/B2a

# Create build directory
mkdir -p build && cd build

# Configure with CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build (use all available cores)
make -j$(nproc)

# Verify the executable was created
ls -la exampleB2a

# Test it works (should run and exit cleanly)
./exampleB2a ../run.mac

# Note the full path to the executable
echo "Executable path: $(pwd)/exampleB2a"
```

**Save the executable path** - you'll need it to configure the API.

---

## 6. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cd /opt/geant4-api  # or your project directory

cat > .env << 'EOF'
# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
RELOAD=false

# Geant4 Settings (adjust paths to your installation)
GEANT4_INSTALL_PATH=/opt/geant4/geant4-v11.2.0-install
GEANT4_DATA_PATH=/opt/geant4/geant4-v11.2.0-install/share/Geant4/data
GEANT4_USE_SUBPROCESS=true

# Redis (optional, for background tasks)
REDIS_URL=redis://localhost:6379/0

# Database
DATABASE_URL=sqlite+aiosqlite:///./simulations.db

# Simulation Settings
MAX_CONCURRENT_SIMULATIONS=4
SIMULATION_TIMEOUT=3600
RESULTS_PATH=./results

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/geant4_api.log
EOF
```

---

## 7. Create Required Directories

```bash
mkdir -p results logs
```

---

## 8. Start the API Server

### Option A: Direct Start (Development/Testing)

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Source Geant4 environment
source /opt/geant4/geant4-v11.2.0-install/bin/geant4.sh

# Start the server
python run.py
```

### Option B: Using systemd (Production)

Create a systemd service file:

```bash
sudo cat > /etc/systemd/system/geant4-api.service << 'EOF'
[Unit]
Description=Geant4 REST API Server
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/geant4-api
Environment="PATH=/opt/geant4-api/venv/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/opt/geant4-api/.env

# Source Geant4 environment
ExecStartPre=/bin/bash -c 'source /opt/geant4/geant4-v11.2.0-install/bin/geant4.sh'

ExecStart=/opt/geant4-api/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start the service:

```bash
# Set correct ownership
sudo chown -R www-data:www-data /opt/geant4-api

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable geant4-api

# Start the service
sudo systemctl start geant4-api

# Check status
sudo systemctl status geant4-api

# View logs
sudo journalctl -u geant4-api -f
```

---

## 9. Configure the API to Use Your Geant4 Executable

Once the server is running, configure it to use your built B2a executable:

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/geant4/configure \
  -H "Content-Type: application/json" \
  -d '{
    "install_path": "/opt/geant4/geant4-v11.2.0-install",
    "data_path": "/opt/geant4/geant4-v11.2.0-install/share/Geant4/data",
    "executable_path": "/opt/geant4-api/app/core/geant4_app/B2a/build/exampleB2a"
  }'
```

Verify the configuration:

```bash
curl http://localhost:8000/api/v1/geant4/status | python3 -m json.tool
```

---

## 10. Test the API

### Health Check

```bash
curl http://localhost:8000/health
```

### Create and Run a Simulation

```bash
# Create a quick-start simulation
curl -X POST "http://localhost:8000/api/v1/simulations/quick-start/water_phantom?num_events=100" \
  -H "Content-Type: application/json" | python3 -m json.tool

# Note the simulation_id from the response

# Start the simulation (replace {simulation_id} with actual ID)
curl -X POST http://localhost:8000/api/v1/simulations/{simulation_id}/start

# Check progress
curl http://localhost:8000/api/v1/simulations/{simulation_id}/progress | python3 -m json.tool

# Get results when complete
curl http://localhost:8000/api/v1/results/{simulation_id} | python3 -m json.tool
```

### WebSocket Test (Real-time Updates)

```bash
# Install websocat if not available
sudo apt install -y websocat

# Or use pip
pip install websocket-client

# Connect to WebSocket
websocat ws://localhost:8000/ws/simulations/{simulation_id}
```

---

## 11. Access the API Documentation

Open in your browser:

- **Swagger UI**: http://your-server-ip:8000/docs
- **ReDoc**: http://your-server-ip:8000/redoc
- **API Info**: http://your-server-ip:8000/

---

## 12. Firewall Configuration (if needed)

```bash
# Allow port 8000
sudo ufw allow 8000/tcp

# Or for nginx reverse proxy, allow HTTP/HTTPS
sudo ufw allow 'Nginx Full'
```

---

## 13. Optional: Nginx Reverse Proxy

For production, use Nginx as a reverse proxy:

```bash
sudo apt install -y nginx

sudo cat > /etc/nginx/sites-available/geant4-api << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # or server IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/geant4-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Troubleshooting

### Geant4 Libraries Not Found

```bash
# Make sure to source Geant4 environment before starting
source /opt/geant4/geant4-v11.2.0-install/bin/geant4.sh

# Add to your .bashrc for persistence
echo 'source /opt/geant4/geant4-v11.2.0-install/bin/geant4.sh' >> ~/.bashrc
```

### CMake Can't Find Geant4

```bash
# Set Geant4_DIR explicitly
export Geant4_DIR=/opt/geant4/geant4-v11.2.0-install/lib/Geant4-11.2.0

# Then run cmake
cmake .. -DCMAKE_BUILD_TYPE=Release
```

### Permission Denied on Results Directory

```bash
sudo chown -R $USER:$USER /opt/geant4-api/results
chmod 755 /opt/geant4-api/results
```

### Port Already in Use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill it or use a different port
# In .env, change PORT=8080
```

### Check Logs

```bash
# API logs
tail -f /opt/geant4-api/logs/geant4_api.log

# systemd logs
sudo journalctl -u geant4-api -f
```

---

## Quick Reference Commands

```bash
# Start API (development)
source venv/bin/activate
source /opt/geant4/geant4-v11.2.0-install/bin/geant4.sh
python run.py

# Start API (production)
sudo systemctl start geant4-api

# Stop API
sudo systemctl stop geant4-api

# Restart API
sudo systemctl restart geant4-api

# View logs
sudo journalctl -u geant4-api -f

# Check status
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/geant4/status
```

---

## Project Structure

```
/opt/geant4-api/
├── app/
│   ├── api/                 # REST API endpoints
│   ├── core/
│   │   ├── geant4_app/
│   │   │   └── B2a/         # B2a Geant4 example
│   │   │       └── build/   # Built executable here
│   │   ├── simulation_engine.py
│   │   └── geant4_executor.py
│   └── models/
├── results/                  # Simulation results
├── logs/                     # Log files
├── venv/                     # Python virtual environment
├── .env                      # Configuration
├── requirements.txt
└── run.py                    # Entry point
```

---

## Support

- **API Documentation**: http://localhost:8000/docs
- **Geant4 Documentation**: https://geant4.web.cern.ch/docs/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

