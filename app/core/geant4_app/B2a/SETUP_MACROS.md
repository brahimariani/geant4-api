# B2a Example - Macro Setup Guide

If the `.mac` files are missing from your B2a directory, create them manually using the commands below.

---

## Create Macro Files

Navigate to the B2a directory:

```bash
cd /home/vgate/Documents/geant4-api/app/core/geant4_app/B2a
```

### 1. Create `run.mac` (Proton beam - 3 GeV)

```bash
cat > run.mac << 'EOF'
# Macro file for B2a example - API batch mode
# =============================================

# Verbosity
/control/verbose 0
/run/verbose 1
/event/verbose 0
/tracking/verbose 0

# Initialize
/run/initialize

# Particle source configuration via GPS
/gps/particle proton
/gps/ene/type Mono
/gps/ene/mono 3 GeV
/gps/pos/type Point
/gps/pos/centre 0. 0. -250. cm
/gps/direction 0 0 1

# Run 100 events
/run/beamOn 100
EOF
```

### 2. Create `run_gamma.mac` (Gamma beam - 100 MeV)

```bash
cat > run_gamma.mac << 'EOF'
# Macro file for B2a example - Gamma beam
# ========================================

# Verbosity
/control/verbose 0
/run/verbose 1
/event/verbose 0
/tracking/verbose 0

# Initialize
/run/initialize

# Gamma source
/gps/particle gamma
/gps/ene/type Mono
/gps/ene/mono 100 MeV
/gps/pos/type Point
/gps/pos/centre 0. 0. -250. cm
/gps/direction 0 0 1

# Run 500 events
/run/beamOn 500
EOF
```

### 3. Create `run_electron.mac` (Electron beam - 500 MeV)

```bash
cat > run_electron.mac << 'EOF'
# Macro file for B2a example - Electron beam
# ===========================================

# Verbosity
/control/verbose 0
/run/verbose 1
/event/verbose 0
/tracking/verbose 0

# Initialize
/run/initialize

# Electron beam with energy spread
/gps/particle e-
/gps/ene/type Gauss
/gps/ene/mono 500 MeV
/gps/ene/sigma 5 MeV
/gps/pos/type Plane
/gps/pos/shape Circle
/gps/pos/centre 0. 0. -250. cm
/gps/pos/radius 1. cm
/gps/direction 0 0 1

# Run 200 events
/run/beamOn 200
EOF
```

### 4. Create `init_vis.mac` (Visualization - Interactive mode)

```bash
cat > init_vis.mac << 'EOF'
# Macro file for B2a visualization initialization
# ================================================

# Verbosity
/control/verbose 2
/run/verbose 2

# Initialize kernel
/run/initialize

# Visualization (OpenGL)
/vis/open OGL 600x600-0+0

# Draw geometry
/vis/drawVolume

# Specify view angle
/vis/viewer/set/viewpointThetaPhi 90. 180.

# Draw smooth trajectories
/vis/scene/add/trajectories smooth

# Draw hits
/vis/scene/add/hits

# Superimpose events
/vis/scene/endOfEventAction accumulate

# Axes
/vis/scene/add/axes 0 0 0 1 m

# Re-establish auto refreshing
/vis/viewer/set/autoRefresh true

# Set background color
/vis/viewer/set/background white
EOF
```

---

## Run the Example

### Test with Proton Beam

```bash
cd /home/vgate/Documents/geant4-api/app/core/geant4_app/B2a/build
./exampleB2a ../run.mac
```

### Test with Gamma Beam

```bash
./exampleB2a ../run_gamma.mac
```

### Test with Electron Beam

```bash
./exampleB2a ../run_electron.mac
```

---

## Expected Output

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
  Tracker length: 480 cm
  Number of chambers: 5

========================================
### Run 0 starts.
    Number of events: 100
========================================

>>> Event 0 | Hits: 42 | Total Edep: 123.45 keV
>>> Event 1 | Hits: 38 | Total Edep: 98.76 keV
>>> Event 2 | Hits: 51 | Total Edep: 156.23 keV
...

========================================
### Run 0 ended.
    Processed events: 100
========================================
```

---

## Verify Files Were Created

```bash
ls -la *.mac
```

You should see:
```
-rw-r--r-- 1 vgate vgate  xxx  run.mac
-rw-r--r-- 1 vgate vgate  xxx  run_gamma.mac
-rw-r--r-- 1 vgate vgate  xxx  run_electron.mac
-rw-r--r-- 1 vgate vgate  xxx  init_vis.mac
```

---

## Troubleshooting

### "Can not open a macro file" Error

Make sure you're running from the correct directory:

```bash
# From build directory, use relative path
cd build
./exampleB2a ../run.mac

# Or use absolute path
./exampleB2a /home/vgate/Documents/geant4-api/app/core/geant4_app/B2a/run.mac
```

### Permission Denied

```bash
chmod +x build/exampleB2a
```

