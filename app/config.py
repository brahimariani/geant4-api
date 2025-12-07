"""
Configuration management for Geant4 API.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on changes")
    
    # Geant4
    geant4_install_path: Optional[str] = Field(
        default=None, 
        description="Path to Geant4 installation"
    )
    geant4_data_path: Optional[str] = Field(
        default=None,
        description="Path to Geant4 data files"
    )
    geant4_use_subprocess: bool = Field(
        default=True,
        description="Use subprocess mode instead of Python bindings"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for task queue"
    )
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./simulations.db",
        description="Database connection URL"
    )
    
    # Simulation
    max_concurrent_simulations: int = Field(
        default=4,
        description="Maximum concurrent simulations"
    )
    simulation_timeout: int = Field(
        default=3600,
        description="Simulation timeout in seconds"
    )
    results_path: str = Field(
        default="./results",
        description="Path to store simulation results"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def setup_geant4_environment():
    """Set up Geant4 environment variables."""
    if settings.geant4_install_path:
        os.environ["GEANT4_INSTALL"] = settings.geant4_install_path
        
    if settings.geant4_data_path:
        os.environ["GEANT4_DATA_DIR"] = settings.geant4_data_path
        
    # Ensure results directory exists
    Path(settings.results_path).mkdir(parents=True, exist_ok=True)

