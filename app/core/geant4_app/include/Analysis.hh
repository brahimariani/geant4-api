/**
 * Analysis Manager
 * Handles ROOT/CSV output for histograms and ntuples
 */

#ifndef Analysis_h
#define Analysis_h 1

#include "globals.hh"

// Choose analysis output format
// Options: g4root, g4csv, g4xml
#include "g4csv.hh"  // CSV is most portable

class Analysis {
public:
    static Analysis* Instance();
    ~Analysis();
    
    void SetOutputDirectory(const G4String& dir) { fOutputDir = dir; }
    void Book();
    void Save();
    
    void FillH1(G4int id, G4double value);
    void FillH2(G4int id, G4double xvalue, G4double yvalue);
    
    void FillNtupleIColumn(G4int id, G4int value);
    void FillNtupleDColumn(G4int id, G4double value);
    void FillNtupleSColumn(G4int id, const G4String& value);
    void AddNtupleRow();
    
private:
    Analysis();
    static Analysis* fInstance;
    
    G4String fOutputDir;
    G4bool fBooked;
};

#endif

