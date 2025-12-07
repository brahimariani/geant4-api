@echo off
REM Build script for B2a Example (Windows)
REM =======================================

echo.
echo =============================================
echo   Geant4 B2a Example - Build Script
echo =============================================
echo.

REM Check for Geant4 environment
if "%Geant4_DIR%"=="" (
    echo WARNING: Geant4_DIR not set.
    echo Please ensure Geant4 is properly installed and run:
    echo   call "C:\path\to\geant4-install\bin\geant4.bat"
    echo.
    echo Attempting to continue anyway...
)

REM Create build directory
if not exist build mkdir build
cd build

REM Configure with CMake
echo.
echo [1/2] Configuring with CMake...
echo.
cmake .. -G "Visual Studio 17 2022" -A x64

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: CMake configuration failed!
    echo.
    echo Make sure you have:
    echo   1. Geant4 installed and environment set
    echo   2. Visual Studio 2022 installed
    echo   3. CMake 3.16+ installed
    exit /b 1
)

REM Build
echo.
echo [2/2] Building...
echo.
cmake --build . --config Release --parallel

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Build failed!
    exit /b 1
)

echo.
echo =============================================
echo   BUILD SUCCESSFUL!
echo =============================================
echo.
echo Executable location:
echo   %CD%\Release\exampleB2a.exe
echo.
echo To test the build, run:
echo   Release\exampleB2a.exe ..\run.mac
echo.
echo To configure the API to use this executable:
echo   POST http://localhost:8000/api/v1/geant4/configure
echo   {
echo     "executable_path": "%CD%\Release\exampleB2a.exe"
echo   }
echo.

