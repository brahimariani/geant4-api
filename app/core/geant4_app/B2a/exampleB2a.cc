// ********************************************************************
// * Geant4 B2a Example - Modified for REST API Integration
// * Based on: https://github.com/Geant4/geant4/tree/master/examples/basic/B2/B2a
// ********************************************************************
//
// This example simulates a simplified tracker detector with:
// - 5 tracking chambers filled with Xenon gas
// - Sensitive detectors recording particle hits
// - Real-time output for API streaming
//

#include "DetectorConstruction.hh"
#include "ActionInitialization.hh"

#include "G4RunManagerFactory.hh"
#include "G4SteppingVerbose.hh"
#include "G4UImanager.hh"
#include "G4UIExecutive.hh"
#include "G4VisExecutive.hh"

#include "FTFP_BERT.hh"

#include <iostream>

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

int main(int argc, char** argv)
{
    // Detect interactive mode (if no arguments) and define UI session
    G4UIExecutive* ui = nullptr;
    if (argc == 1) {
        ui = new G4UIExecutive(argc, argv);
    }

    // Use G4SteppingVerboseWithUnits for better output
    G4int precision = 4;
    G4SteppingVerbose::UseBestUnit(precision);

    // Construct the run manager
    auto runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Default);

    // Set mandatory initialization classes
    runManager->SetUserInitialization(new B2a::DetectorConstruction());

    // Physics list
    G4VModularPhysicsList* physicsList = new FTFP_BERT;
    physicsList->SetVerboseLevel(0);
    runManager->SetUserInitialization(physicsList);

    // User action initialization
    runManager->SetUserInitialization(new B2a::ActionInitialization());

    // Initialize visualization
    G4VisManager* visManager = nullptr;

    // Get the pointer to the User Interface manager
    G4UImanager* UImanager = G4UImanager::GetUIpointer();

    // Print banner for API
    G4cout << G4endl;
    G4cout << "========================================" << G4endl;
    G4cout << " Geant4 B2a Example - API Mode" << G4endl;
    G4cout << " Tracker Simulation" << G4endl;
    G4cout << "========================================" << G4endl;
    G4cout << G4endl;

    // Process macro or start UI session
    if (!ui) {
        // Batch mode
        G4String command = "/control/execute ";
        G4String fileName = argv[1];
        UImanager->ApplyCommand(command + fileName);
    }
    else {
        // Interactive mode
        visManager = new G4VisExecutive;
        visManager->Initialize();
        UImanager->ApplyCommand("/control/execute init_vis.mac");
        ui->SessionStart();
        delete ui;
    }

    // Job termination
    delete visManager;
    delete runManager;

    return 0;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

