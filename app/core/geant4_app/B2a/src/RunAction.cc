// ********************************************************************
// * B2a Run Action Implementation
// ********************************************************************

#include "RunAction.hh"

#include "G4Run.hh"
#include "G4RunManager.hh"

namespace B2a
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void RunAction::BeginOfRunAction(const G4Run* run)
{
    G4cout << G4endl;
    G4cout << "========================================" << G4endl;
    G4cout << "### Run " << run->GetRunID() << " starts." << G4endl;
    G4cout << "    Number of events: " << run->GetNumberOfEventToBeProcessed() << G4endl;
    G4cout << "========================================" << G4endl;

    // Inform the runManager to save random number seed
    G4RunManager::GetRunManager()->SetRandomNumberStore(false);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void RunAction::EndOfRunAction(const G4Run* run)
{
    G4int nofEvents = run->GetNumberOfEvent();
    if (nofEvents == 0) return;

    G4cout << G4endl;
    G4cout << "========================================" << G4endl;
    G4cout << "### Run " << run->GetRunID() << " ended." << G4endl;
    G4cout << "    Processed events: " << nofEvents << G4endl;
    G4cout << "========================================" << G4endl;
}

}

