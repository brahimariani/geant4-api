/**
 * Run Action Implementation
 */

#include "RunAction.hh"
#include "Analysis.hh"

#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4AccumulableManager.hh"

RunAction::RunAction(const G4String& outputDir)
    : G4UserRunAction(),
      fOutputDir(outputDir),
      fEdep(0.),
      fEdep2(0.)
{
    // Register accumulables
    G4AccumulableManager* accumulableManager = G4AccumulableManager::Instance();
    accumulableManager->RegisterAccumulable(fEdep);
    accumulableManager->RegisterAccumulable(fEdep2);
}

RunAction::~RunAction() {}

void RunAction::BeginOfRunAction(const G4Run* run) {
    // Reset accumulables
    G4AccumulableManager* accumulableManager = G4AccumulableManager::Instance();
    accumulableManager->Reset();
    
    // Initialize analysis
    Analysis* analysis = Analysis::Instance();
    analysis->SetOutputDirectory(fOutputDir);
    analysis->Book();
    
    G4cout << "### Run " << run->GetRunID() << " starts." << G4endl;
    G4cout << "    Output directory: " << fOutputDir << G4endl;
}

void RunAction::EndOfRunAction(const G4Run* run) {
    G4int nofEvents = run->GetNumberOfEvent();
    if (nofEvents == 0) return;
    
    // Merge accumulables
    G4AccumulableManager* accumulableManager = G4AccumulableManager::Instance();
    accumulableManager->Merge();
    
    // Calculate statistics
    G4double edep = fEdep;
    G4double edep2 = fEdep2;
    G4double rms = edep2 - edep*edep/nofEvents;
    if (rms > 0.) rms = std::sqrt(rms);
    else rms = 0.;
    
    // Print results
    if (IsMaster()) {
        G4cout << G4endl
               << "--------------------End of Run------------------------------" << G4endl
               << " Total energy deposited: " << G4BestUnit(edep, "Energy") << G4endl
               << " Mean energy per event:  " << G4BestUnit(edep/nofEvents, "Energy")
               << " +/- " << G4BestUnit(rms/nofEvents, "Energy") << G4endl
               << "------------------------------------------------------------" << G4endl;
    }
    
    // Save analysis output
    Analysis* analysis = Analysis::Instance();
    analysis->Save();
}

void RunAction::AddEdep(G4double edep) {
    fEdep += edep;
    fEdep2 += edep * edep;
}

