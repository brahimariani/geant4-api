#!/bin/bash
# Build script for Geant4 API Application (Linux/Mac)
# ===================================================

echo "Geant4 API Application Builder"
echo "==============================="
echo

# Check for Geant4 environment
if [ -z "$G4INSTALL" ] && [ -z "$GEANT4_INSTALL" ]; then
    echo "WARNING: Geant4 environment may not be set."
    echo "Consider running: source /path/to/geant4/bin/geant4.sh"
fi

# Create build directory
mkdir -p build
cd build

# Configure with CMake
echo
echo "Configuring with CMake..."
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DWITH_GEANT4_UIVIS=OFF

if [ $? -ne 0 ]; then
    echo "CMake configuration failed!"
    exit 1
fi

# Build
echo
echo "Building..."
make -j$(nproc)

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo
echo "Build successful!"
echo "Executable: $(pwd)/geant4api"
echo
echo "To use with the API, configure with:"
echo '  POST /api/v1/geant4/configure'
echo "  {\"executable_path\": \"$(pwd)/geant4api\"}"

