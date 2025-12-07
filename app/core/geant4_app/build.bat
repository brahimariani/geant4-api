@echo off
REM Build script for Geant4 API Application (Windows)
REM ===================================================

echo Geant4 API Application Builder
echo ===============================
echo.

REM Check for Geant4 environment
if "%GEANT4_INSTALL%"=="" (
    echo ERROR: GEANT4_INSTALL environment variable not set.
    echo Please run the Geant4 environment setup script first:
    echo   call C:\Geant4\geant4-v11.2.0-install\bin\geant4.bat
    exit /b 1
)

echo Geant4 found at: %GEANT4_INSTALL%

REM Create build directory
if not exist build mkdir build
cd build

REM Configure with CMake
echo.
echo Configuring with CMake...
cmake .. -G "Visual Studio 17 2022" -A x64 ^
    -DCMAKE_PREFIX_PATH="%GEANT4_INSTALL%" ^
    -DWITH_GEANT4_UIVIS=OFF

if %ERRORLEVEL% NEQ 0 (
    echo CMake configuration failed!
    exit /b 1
)

REM Build
echo.
echo Building...
cmake --build . --config Release --parallel

if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    exit /b 1
)

echo.
echo Build successful!
echo Executable: %CD%\Release\geant4api.exe
echo.
echo To use with the API, configure with:
echo   POST /api/v1/geant4/configure
echo   {"executable_path": "%CD%\Release\geant4api.exe"}

