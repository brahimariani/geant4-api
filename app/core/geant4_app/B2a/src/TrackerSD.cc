// ********************************************************************
// * B2a Tracker Sensitive Detector Implementation
// * Based on: https://github.com/Geant4/geant4/tree/master/examples/basic/B2/B2a
// ********************************************************************

#include "TrackerSD.hh"

#include "G4HCofThisEvent.hh"
#include "G4Step.hh"
#include "G4ThreeVector.hh"
#include "G4SDManager.hh"
#include "G4ios.hh"
#include "G4SystemOfUnits.hh"
#include "G4RunManager.hh"

namespace B2a
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

TrackerSD::TrackerSD(const G4String& name, const G4String& hitsCollectionName)
 : G4VSensitiveDetector(name)
{
    collectionName.insert(hitsCollectionName);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void TrackerSD::Initialize(G4HCofThisEvent* hce)
{
    // Create hits collection
    fHitsCollection = new TrackerHitsCollection(SensitiveDetectorName, collectionName[0]);

    // Add this collection in hce
    G4int hcID = G4SDManager::GetSDMpointer()->GetCollectionID(collectionName[0]);
    hce->AddHitsCollection(hcID, fHitsCollection);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4bool TrackerSD::ProcessHits(G4Step* aStep, G4TouchableHistory*)
{
    // Energy deposit
    G4double edep = aStep->GetTotalEnergyDeposit();

    if (edep == 0.) return false;

    auto newHit = new TrackerHit();

    newHit->SetTrackID(aStep->GetTrack()->GetTrackID());
    newHit->SetChamberNb(aStep->GetPreStepPoint()->GetTouchableHandle()->GetCopyNumber());
    newHit->SetEdep(edep);
    newHit->SetPos(aStep->GetPostStepPoint()->GetPosition());
    newHit->SetTime(aStep->GetPostStepPoint()->GetGlobalTime());
    newHit->SetParticleName(aStep->GetTrack()->GetParticleDefinition()->GetParticleName());

    fHitsCollection->insert(newHit);

    return true;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void TrackerSD::EndOfEvent(G4HCofThisEvent*)
{
    G4int nofHits = fHitsCollection->entries();
    
    // Get event ID
    G4int eventID = G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID();
    
    // Print summary for API parsing
    G4cout << ">>> Event " << eventID << " | Hits: " << nofHits;
    
    G4double totalEdep = 0.;
    for (G4int i = 0; i < nofHits; i++) {
        totalEdep += (*fHitsCollection)[i]->GetEdep();
    }
    
    G4cout << " | Total Edep: " << totalEdep/keV << " keV" << G4endl;
    
    // Output detailed hit info (for API)
    if (verboseLevel > 1) {
        G4cout << "---------- Hit Details ----------" << G4endl;
        for (G4int i = 0; i < nofHits; i++) {
            (*fHitsCollection)[i]->Print();
        }
    }
}

}

