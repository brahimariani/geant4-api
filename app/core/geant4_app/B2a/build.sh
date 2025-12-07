#!/bin/bash
# Build script for B2a Example (Linux/Mac)
# ========================================

echo ""
echo "============================================="
echo "  Geant4 B2a Example - Build Script"
echo "============================================="
echo ""

# Check for Geant4 environment
if [ -z "$Geant4_DIR" ] && [ -z "$G4INSTALL" ]; then
    echo "WARNING: Geant4 environment may not be set."
    echo "Consider running: source /path/to/geant4-install/bin/geant4.sh"
    echo ""
fi

# Create build directory
mkdir -p build
cd build

# Configure with CMake
echo ""
echo "[1/2] Configuring with CMake..."
echo ""
cmake .. -DCMAKE_BUILD_TYPE=Release

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: CMake configuration failed!"
    echo ""
    echo "Make sure you have:"
    echo "  1. Geant4 installed and environment set"
    echo "  2. CMake 3.16+ installed"
    echo "  3. GCC/Clang compiler installed"
    exit 1
fi

# Build
echo ""
echo "[2/2] Building..."
echo ""
make -j$(nproc)

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Build failed!"
    exit 1
fi

echo ""
echo "============================================="
echo "  BUILD SUCCESSFUL!"
echo "============================================="
echo ""
echo "Executable location:"
echo "  $(pwd)/exampleB2a"
echo ""
echo "To test the build, run:"
echo "  ./exampleB2a ../run.mac"
echo ""
echo "To configure the API to use this executable:"
echo '  POST http://localhost:8000/api/v1/geant4/configure'
echo '  {'
echo "    \"executable_path\": \"$(pwd)/exampleB2a\""
echo '  }'
echo ""

