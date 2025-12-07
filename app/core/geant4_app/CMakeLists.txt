# CMakeLists.txt for Geant4 API Application
# ==========================================
# A generic Geant4 application that can be controlled via macro files
# and produces output suitable for the REST API

cmake_minimum_required(VERSION 3.16...3.27)
project(Geant4API VERSION 1.0.0)

# Find Geant4
option(WITH_GEANT4_UIVIS "Build with Geant4 UI and Vis drivers" OFF)

if(WITH_GEANT4_UIVIS)
  find_package(Geant4 REQUIRED ui_all vis_all)
else()
  find_package(Geant4 REQUIRED)
endif()

# Setup Geant4 include directories and compile definitions
include(${Geant4_USE_FILE})

# Source files
set(SOURCES
    src/main.cc
    src/ActionInitialization.cc
    src/DetectorConstruction.cc
    src/PrimaryGeneratorAction.cc
    src/RunAction.cc
    src/EventAction.cc
    src/SteppingAction.cc
    src/SensitiveDetector.cc
    src/Analysis.cc
)

set(HEADERS
    include/ActionInitialization.hh
    include/DetectorConstruction.hh
    include/PrimaryGeneratorAction.hh
    include/RunAction.hh
    include/EventAction.hh
    include/SteppingAction.hh
    include/SensitiveDetector.hh
    include/Analysis.hh
)

# Executable
add_executable(geant4api ${SOURCES} ${HEADERS})

# Include directories
target_include_directories(geant4api PRIVATE 
    ${PROJECT_SOURCE_DIR}/include
    ${Geant4_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(geant4api ${Geant4_LIBRARIES})

# Install
install(TARGETS geant4api DESTINATION bin)

# Copy macros
file(GLOB MACRO_FILES ${PROJECT_SOURCE_DIR}/macros/*.mac)
file(COPY ${MACRO_FILES} DESTINATION ${PROJECT_BINARY_DIR})

# Print configuration
message(STATUS "Geant4 found: ${Geant4_DIR}")
message(STATUS "Geant4 version: ${Geant4_VERSION}")

