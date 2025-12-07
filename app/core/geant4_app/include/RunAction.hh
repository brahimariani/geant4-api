/**
 * Run Action
 * Handles output file management and run-level histograms
 */

#ifndef RunAction_h
#define RunAction_h 1

#include "G4UserRunAction.hh"
#include "globals.hh"

class G4Run;

class RunAction : public G4UserRunAction {
public:
    RunAction(const G4String& outputDir = ".");
    virtual ~RunAction();
    
    virtual void BeginOfRunAction(const G4Run* run) override;
    virtual void EndOfRunAction(const G4Run* run) override;
    
    // Accumulate energy deposit
    void AddEdep(G4double edep);
    
private:
    G4String fOutputDir;
    G4double fEdep;
    G4double fEdep2;
};

#endif

