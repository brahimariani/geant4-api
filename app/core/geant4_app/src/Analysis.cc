/**
 * Analysis Manager Implementation
 */

#include "Analysis.hh"
#include "G4SystemOfUnits.hh"

Analysis* Analysis::fInstance = nullptr;

Analysis* Analysis::Instance() {
    if (!fInstance) {
        fInstance = new Analysis();
    }
    return fInstance;
}

Analysis::Analysis()
    : fOutputDir("."),
      fBooked(false)
{}

Analysis::~Analysis() {
    fInstance = nullptr;
}

void Analysis::Book() {
    if (fBooked) return;
    
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    
    // Set verbose level
    analysisManager->SetVerboseLevel(1);
    
    // Set output file name
    G4String fileName = fOutputDir + "/output";
    analysisManager->SetFileName(fileName);
    
    // Create histograms
    // H1 ID 0: Energy deposit
    analysisManager->CreateH1("Edep", "Energy deposit in detector", 
                              100, 0., 10.*MeV, "MeV");
    
    // H1 ID 1: Position Z distribution
    analysisManager->CreateH1("PosZ", "Hit position Z", 
                              100, -500.*mm, 500.*mm, "mm");
    
    // H2 ID 0: XY position
    analysisManager->CreateH2("PosXY", "Hit position XY",
                              100, -200.*mm, 200.*mm,
                              100, -200.*mm, 200.*mm,
                              "mm", "mm");
    
    // Create ntuple for detailed hit data
    analysisManager->CreateNtuple("hits", "Hit data");
    analysisManager->CreateNtupleIColumn("eventID");    // ID 0
    analysisManager->CreateNtupleDColumn("edep");       // ID 1
    analysisManager->CreateNtupleDColumn("posX");       // ID 2
    analysisManager->CreateNtupleDColumn("posY");       // ID 3
    analysisManager->CreateNtupleDColumn("posZ");       // ID 4
    analysisManager->CreateNtupleDColumn("time");       // ID 5
    analysisManager->FinishNtuple();
    
    // Open file
    analysisManager->OpenFile();
    
    fBooked = true;
    G4cout << "Analysis booked. Output: " << fileName << G4endl;
}

void Analysis::Save() {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    
    // Write and close file
    analysisManager->Write();
    analysisManager->CloseFile();
    
    G4cout << "Analysis saved." << G4endl;
    fBooked = false;
}

void Analysis::FillH1(G4int id, G4double value) {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    analysisManager->FillH1(id, value);
}

void Analysis::FillH2(G4int id, G4double xvalue, G4double yvalue) {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    analysisManager->FillH2(id, xvalue, yvalue);
}

void Analysis::FillNtupleIColumn(G4int id, G4int value) {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    analysisManager->FillNtupleIColumn(id, value);
}

void Analysis::FillNtupleDColumn(G4int id, G4double value) {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    analysisManager->FillNtupleDColumn(id, value);
}

void Analysis::FillNtupleSColumn(G4int id, const G4String& value) {
    // Note: String columns require special handling
}

void Analysis::AddNtupleRow() {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    analysisManager->AddNtupleRow();
}

