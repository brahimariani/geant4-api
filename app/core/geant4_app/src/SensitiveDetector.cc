/**
 * Sensitive Detector Implementation
 */

#include "SensitiveDetector.hh"

#include "G4Step.hh"
#include "G4Track.hh"
#include "G4HCofThisEvent.hh"
#include "G4TouchableHistory.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4RunManager.hh"

G4ThreadLocal G4Allocator<DetectorHit>* DetectorHitAllocator = nullptr;

// DetectorHit implementation
DetectorHit::DetectorHit()
    : G4VHit(),
      fEventID(0), fTrackID(0), fParentID(0),
      fParticleName(""), fParticlePDG(0),
      fPosition(0,0,0), fMomentum(0,0,0),
      fKineticEnergy(0), fEnergyDeposit(0),
      fGlobalTime(0), fLocalTime(0),
      fProcessName("")
{}

DetectorHit::DetectorHit(const DetectorHit& right) : G4VHit() {
    fEventID = right.fEventID;
    fTrackID = right.fTrackID;
    fParentID = right.fParentID;
    fParticleName = right.fParticleName;
    fParticlePDG = right.fParticlePDG;
    fPosition = right.fPosition;
    fMomentum = right.fMomentum;
    fKineticEnergy = right.fKineticEnergy;
    fEnergyDeposit = right.fEnergyDeposit;
    fGlobalTime = right.fGlobalTime;
    fLocalTime = right.fLocalTime;
    fProcessName = right.fProcessName;
}

DetectorHit::~DetectorHit() {}

const DetectorHit& DetectorHit::operator=(const DetectorHit& right) {
    fEventID = right.fEventID;
    fTrackID = right.fTrackID;
    fParentID = right.fParentID;
    fParticleName = right.fParticleName;
    fParticlePDG = right.fParticlePDG;
    fPosition = right.fPosition;
    fMomentum = right.fMomentum;
    fKineticEnergy = right.fKineticEnergy;
    fEnergyDeposit = right.fEnergyDeposit;
    fGlobalTime = right.fGlobalTime;
    fLocalTime = right.fLocalTime;
    fProcessName = right.fProcessName;
    return *this;
}

G4bool DetectorHit::operator==(const DetectorHit& right) const {
    return (this == &right);
}

void DetectorHit::Print() {
    G4cout << "Hit: event=" << fEventID 
           << " track=" << fTrackID
           << " particle=" << fParticleName
           << " edep=" << fEnergyDeposit/MeV << " MeV"
           << " pos=(" << fPosition.x()/mm << ", " 
                       << fPosition.y()/mm << ", "
                       << fPosition.z()/mm << ") mm"
           << G4endl;
}

// SensitiveDetector implementation
SensitiveDetector::SensitiveDetector(const G4String& name, const G4String& hcName)
    : G4VSensitiveDetector(name),
      fHitsCollection(nullptr),
      fHCID(-1)
{
    collectionName.insert(hcName);
}

SensitiveDetector::~SensitiveDetector() {}

void SensitiveDetector::Initialize(G4HCofThisEvent* hce) {
    fHitsCollection = new DetectorHitsCollection(SensitiveDetectorName, collectionName[0]);
    
    if (fHCID < 0) {
        fHCID = G4SDManager::GetSDMpointer()->GetCollectionID(collectionName[0]);
    }
    hce->AddHitsCollection(fHCID, fHitsCollection);
}

G4bool SensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory*) {
    G4double edep = step->GetTotalEnergyDeposit();
    
    // Skip if no energy deposit (optional: can record all steps)
    if (edep <= 0) return false;
    
    G4Track* track = step->GetTrack();
    G4StepPoint* preStep = step->GetPreStepPoint();
    
    DetectorHit* hit = new DetectorHit();
    
    hit->SetEventID(G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID());
    hit->SetTrackID(track->GetTrackID());
    hit->SetParentID(track->GetParentID());
    hit->SetParticleName(track->GetParticleDefinition()->GetParticleName());
    hit->SetParticlePDG(track->GetParticleDefinition()->GetPDGEncoding());
    hit->SetPosition(preStep->GetPosition());
    hit->SetMomentum(preStep->GetMomentum());
    hit->SetKineticEnergy(preStep->GetKineticEnergy());
    hit->SetEnergyDeposit(edep);
    hit->SetGlobalTime(preStep->GetGlobalTime());
    hit->SetLocalTime(preStep->GetLocalTime());
    
    if (step->GetPostStepPoint()->GetProcessDefinedStep()) {
        hit->SetProcessName(step->GetPostStepPoint()->GetProcessDefinedStep()->GetProcessName());
    }
    
    fHitsCollection->insert(hit);
    
    return true;
}

void SensitiveDetector::EndOfEvent(G4HCofThisEvent*) {
    // Can print summary here
    if (verboseLevel > 0) {
        G4int nHits = fHitsCollection->entries();
        G4cout << "SD " << SensitiveDetectorName << ": " << nHits << " hits" << G4endl;
    }
}

