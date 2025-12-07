# CMakeLists.txt for Geant4 B2a Example (API-compatible version)
# ==============================================================
# Based on: https://github.com/Geant4/geant4/tree/master/examples/basic/B2/B2a
# Modified for REST API integration with real-time output

cmake_minimum_required(VERSION 3.16...3.27)
project(B2a_API VERSION 1.0.0)

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
set(PROJECT_SRC
    ${PROJECT_SOURCE_DIR}/src/ActionInitialization.cc
    ${PROJECT_SOURCE_DIR}/src/DetectorConstruction.cc
    ${PROJECT_SOURCE_DIR}/src/DetectorMessenger.cc
    ${PROJECT_SOURCE_DIR}/src/EventAction.cc
    ${PROJECT_SOURCE_DIR}/src/PrimaryGeneratorAction.cc
    ${PROJECT_SOURCE_DIR}/src/RunAction.cc
    ${PROJECT_SOURCE_DIR}/src/SteppingAction.cc
    ${PROJECT_SOURCE_DIR}/src/TrackerHit.cc
    ${PROJECT_SOURCE_DIR}/src/TrackerSD.cc
)

# Executable
add_executable(exampleB2a exampleB2a.cc ${PROJECT_SRC})

# Include directories
target_include_directories(exampleB2a PRIVATE 
    ${PROJECT_SOURCE_DIR}/include
    ${Geant4_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(exampleB2a ${Geant4_LIBRARIES})

# Install
install(TARGETS exampleB2a DESTINATION bin)

# Copy macros
file(GLOB MACRO_FILES ${PROJECT_SOURCE_DIR}/*.mac)
file(COPY ${MACRO_FILES} DESTINATION ${PROJECT_BINARY_DIR})

# Print configuration
message(STATUS "")
message(STATUS "=== B2a API Example Configuration ===")
message(STATUS "Geant4 version: ${Geant4_VERSION}")
message(STATUS "Geant4 dir: ${Geant4_DIR}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "")

