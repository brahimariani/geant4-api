"""
Geant4 Configuration API endpoints.

Endpoints for configuring the Geant4 installation and managing
the connection to real Geant4 executables.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.simulation_engine import simulation_engine


router = APIRouter()


class Geant4Config(BaseModel):
    """Geant4 configuration request."""
    install_path: Optional[str] = Field(
        default=None,
        description="Path to Geant4 installation directory"
    )
    data_path: Optional[str] = Field(
        default=None,
        description="Path to Geant4 data files directory"
    )
    executable_path: Optional[str] = Field(
        default=None,
        description="Path to compiled Geant4 application executable"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "install_path": "C:/Geant4/geant4-v11.2.0-install",
                "data_path": "C:/Geant4/geant4-v11.2.0-install/share/Geant4/data",
                "executable_path": "C:/Geant4/my_app/build/Release/geant4api.exe"
            }
        }


@router.get("/status")
async def get_geant4_status():
    """
    Get current Geant4 configuration status.
    
    Returns information about:
    - Whether Geant4 is configured
    - Installation paths
    - Verification results
    - Whether real simulations can be run
    """
    return simulation_engine.get_geant4_status()


@router.post("/configure")
async def configure_geant4(config: Geant4Config):
    """
    Configure Geant4 installation paths.
    
    This must be called before running real Geant4 simulations.
    
    **Windows Example:**
    ```json
    {
      "install_path": "C:/Geant4/geant4-v11.2.0-install",
      "executable_path": "C:/path/to/your/geant4app.exe"
    }
    ```
    
    **Linux Example:**
    ```json
    {
      "install_path": "/opt/geant4/geant4-v11.2.0-install",
      "executable_path": "/home/user/geant4app/build/geant4api"
    }
    ```
    """
    result = simulation_engine.configure_geant4(
        install_path=config.install_path,
        data_path=config.data_path,
        executable_path=config.executable_path
    )
    
    return result


@router.get("/verify")
async def verify_geant4():
    """
    Verify Geant4 installation.
    
    Checks:
    - Installation path exists
    - Data files are present
    - Environment variables can be set
    - Executable exists and is accessible
    """
    status = simulation_engine.get_geant4_status()
    verification = status.get("verification", {})
    
    if not verification.get("valid", False):
        return {
            "status": "error",
            "message": "Geant4 verification failed",
            "issues": verification.get("issues", []),
            "warnings": verification.get("warnings", []),
            "info": verification.get("info", {})
        }
    
    return {
        "status": "ok",
        "message": "Geant4 installation verified",
        "warnings": verification.get("warnings", []),
        "info": verification.get("info", {})
    }


@router.get("/environment")
async def get_environment():
    """
    Get the environment variables that will be set for Geant4.
    
    Useful for debugging environment issues.
    """
    from app.core.geant4_executor import Geant4Environment
    from app.config import settings
    
    env = Geant4Environment(
        install_path=settings.geant4_install_path,
        data_path=settings.geant4_data_path
    )
    
    geant4_env = env.setup()
    
    # Filter to only Geant4-related variables
    g4_vars = {
        k: v for k, v in geant4_env.items()
        if k.startswith("G4") or k.startswith("GEANT4") or k == "PATH" or k == "LD_LIBRARY_PATH"
    }
    
    return {
        "environment_variables": g4_vars,
        "data_variables": Geant4Environment.DATA_VARS
    }


@router.get("/build-instructions")
async def get_build_instructions():
    """
    Get instructions for building the Geant4 API application.
    """
    return {
        "title": "Building the Geant4 API Application",
        "prerequisites": [
            "Geant4 11.x installed (https://geant4.web.cern.ch/)",
            "CMake 3.16 or higher",
            "C++ compiler (MSVC on Windows, GCC/Clang on Linux/Mac)"
        ],
        "steps": {
            "windows": [
                "1. Open Developer Command Prompt for VS",
                "2. Set Geant4 environment:",
                "   call C:\\Geant4\\geant4-v11.2.0-install\\bin\\geant4.bat",
                "3. Create build directory:",
                "   cd app/core/geant4_app",
                "   mkdir build && cd build",
                "4. Configure with CMake:",
                "   cmake .. -G \"Visual Studio 17 2022\" -A x64",
                "5. Build:",
                "   cmake --build . --config Release",
                "6. Executable will be at: build/Release/geant4api.exe"
            ],
            "linux": [
                "1. Source Geant4 environment:",
                "   source /opt/geant4/geant4-v11.2.0-install/bin/geant4.sh",
                "2. Create build directory:",
                "   cd app/core/geant4_app",
                "   mkdir build && cd build",
                "3. Configure with CMake:",
                "   cmake ..",
                "4. Build:",
                "   make -j$(nproc)",
                "5. Executable will be at: build/geant4api"
            ]
        },
        "configuration": {
            "description": "After building, configure the API to use your executable:",
            "endpoint": "POST /api/v1/geant4/configure",
            "example": {
                "install_path": "C:/Geant4/geant4-v11.2.0-install",
                "executable_path": "C:/path/to/geant4api.exe"
            }
        }
    }

