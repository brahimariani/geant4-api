/**
 * Geant4 API Application - Main
 * =============================
 * Generic Geant4 application controlled by REST API via macro files.
 * Supports GPS particle source, GDML geometry, and CSV/JSON output.
 */

#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4UIExecutive.hh"
#include "G4VisExecutive.hh"
#include "G4GDMLParser.hh"

#include "DetectorConstruction.hh"
#include "ActionInitialization.hh"

#include "FTFP_BERT.hh"
#include "QGSP_BERT.hh"
#include "QGSP_BIC.hh"
#include "Shielding.hh"
#include "G4EmStandardPhysics_option4.hh"

#include <iostream>
#include <string>

void PrintUsage() {
    G4cerr << "Usage: geant4api [options] [macro.mac]" << G4endl;
    G4cerr << "Options:" << G4endl;
    G4cerr << "  -g, --gdml <file>    Load geometry from GDML file" << G4endl;
    G4cerr << "  -p, --physics <name> Physics list (FTFP_BERT, QGSP_BERT, QGSP_BIC, Shielding)" << G4endl;
    G4cerr << "  -t, --threads <n>    Number of threads (for MT build)" << G4endl;
    G4cerr << "  -o, --output <dir>   Output directory" << G4endl;
    G4cerr << "  -v, --vis            Enable visualization" << G4endl;
    G4cerr << "  -i, --interactive    Interactive mode" << G4endl;
    G4cerr << "  -h, --help           Print this help" << G4endl;
}

int main(int argc, char** argv) {
    // Parse command line arguments
    G4String macroFile = "";
    G4String gdmlFile = "";
    G4String physicsName = "FTFP_BERT";
    G4String outputDir = ".";
    G4int nThreads = 1;
    G4bool useVis = false;
    G4bool interactive = false;
    
    for (int i = 1; i < argc; i++) {
        G4String arg = argv[i];
        
        if (arg == "-h" || arg == "--help") {
            PrintUsage();
            return 0;
        }
        else if (arg == "-g" || arg == "--gdml") {
            if (i + 1 < argc) gdmlFile = argv[++i];
        }
        else if (arg == "-p" || arg == "--physics") {
            if (i + 1 < argc) physicsName = argv[++i];
        }
        else if (arg == "-t" || arg == "--threads") {
            if (i + 1 < argc) nThreads = std::stoi(argv[++i]);
        }
        else if (arg == "-o" || arg == "--output") {
            if (i + 1 < argc) outputDir = argv[++i];
        }
        else if (arg == "-v" || arg == "--vis") {
            useVis = true;
        }
        else if (arg == "-i" || arg == "--interactive") {
            interactive = true;
        }
        else if (arg[0] != '-') {
            macroFile = arg;
        }
    }
    
    // Create run manager
    auto* runManager = G4RunManagerFactory::CreateRunManager(
        G4RunManagerType::Default
    );
    
    #ifdef G4MULTITHREADED
    if (nThreads > 1) {
        runManager->SetNumberOfThreads(nThreads);
        G4cout << "Using " << nThreads << " threads" << G4endl;
    }
    #endif
    
    // Detector construction
    DetectorConstruction* detector = nullptr;
    if (!gdmlFile.empty()) {
        G4cout << "Loading geometry from GDML: " << gdmlFile << G4endl;
        detector = new DetectorConstruction(gdmlFile);
    } else {
        detector = new DetectorConstruction();
    }
    runManager->SetUserInitialization(detector);
    
    // Physics list
    G4VModularPhysicsList* physicsList = nullptr;
    if (physicsName == "QGSP_BERT") {
        physicsList = new QGSP_BERT;
    }
    else if (physicsName == "QGSP_BIC") {
        physicsList = new QGSP_BIC;
    }
    else if (physicsName == "Shielding") {
        physicsList = new Shielding;
    }
    else {
        physicsList = new FTFP_BERT;
    }
    runManager->SetUserInitialization(physicsList);
    
    // User actions
    runManager->SetUserInitialization(new ActionInitialization(outputDir));
    
    // Visualization
    G4VisManager* visManager = nullptr;
    if (useVis) {
        visManager = new G4VisExecutive;
        visManager->Initialize();
    }
    
    // UI manager
    G4UImanager* UImanager = G4UImanager::GetUIpointer();
    
    if (!macroFile.empty()) {
        // Batch mode
        G4cout << "Executing macro: " << macroFile << G4endl;
        G4String command = "/control/execute ";
        UImanager->ApplyCommand(command + macroFile);
    }
    
    if (interactive) {
        // Interactive mode
        G4UIExecutive* ui = new G4UIExecutive(argc, argv);
        if (useVis) {
            UImanager->ApplyCommand("/control/execute vis.mac");
        }
        ui->SessionStart();
        delete ui;
    }
    
    // Cleanup
    if (visManager) delete visManager;
    delete runManager;
    
    return 0;
}

