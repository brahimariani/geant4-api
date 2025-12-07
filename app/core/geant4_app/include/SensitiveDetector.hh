/**
 * Sensitive Detector
 * ==================
 * Records hits and energy deposits in sensitive volumes.
 */

#ifndef SensitiveDetector_h
#define SensitiveDetector_h 1

#include "G4VSensitiveDetector.hh"
#include "G4THitsCollection.hh"
#include "G4ThreeVector.hh"

// Hit class
class DetectorHit : public G4VHit {
public:
    DetectorHit();
    DetectorHit(const DetectorHit&);
    virtual ~DetectorHit();
    
    const DetectorHit& operator=(const DetectorHit&);
    G4bool operator==(const DetectorHit&) const;
    
    inline void* operator new(size_t);
    inline void operator delete(void*);
    
    virtual void Print() override;
    
    // Setters
    void SetEventID(G4int id) { fEventID = id; }
    void SetTrackID(G4int id) { fTrackID = id; }
    void SetParentID(G4int id) { fParentID = id; }
    void SetParticleName(G4String name) { fParticleName = name; }
    void SetParticlePDG(G4int pdg) { fParticlePDG = pdg; }
    void SetPosition(G4ThreeVector pos) { fPosition = pos; }
    void SetMomentum(G4ThreeVector mom) { fMomentum = mom; }
    void SetKineticEnergy(G4double e) { fKineticEnergy = e; }
    void SetEnergyDeposit(G4double e) { fEnergyDeposit = e; }
    void SetGlobalTime(G4double t) { fGlobalTime = t; }
    void SetLocalTime(G4double t) { fLocalTime = t; }
    void SetProcessName(G4String name) { fProcessName = name; }
    
    // Getters
    G4int GetEventID() const { return fEventID; }
    G4int GetTrackID() const { return fTrackID; }
    G4int GetParentID() const { return fParentID; }
    G4String GetParticleName() const { return fParticleName; }
    G4int GetParticlePDG() const { return fParticlePDG; }
    G4ThreeVector GetPosition() const { return fPosition; }
    G4ThreeVector GetMomentum() const { return fMomentum; }
    G4double GetKineticEnergy() const { return fKineticEnergy; }
    G4double GetEnergyDeposit() const { return fEnergyDeposit; }
    G4double GetGlobalTime() const { return fGlobalTime; }
    G4double GetLocalTime() const { return fLocalTime; }
    G4String GetProcessName() const { return fProcessName; }
    
private:
    G4int fEventID;
    G4int fTrackID;
    G4int fParentID;
    G4String fParticleName;
    G4int fParticlePDG;
    G4ThreeVector fPosition;
    G4ThreeVector fMomentum;
    G4double fKineticEnergy;
    G4double fEnergyDeposit;
    G4double fGlobalTime;
    G4double fLocalTime;
    G4String fProcessName;
};

typedef G4THitsCollection<DetectorHit> DetectorHitsCollection;

extern G4ThreadLocal G4Allocator<DetectorHit>* DetectorHitAllocator;

inline void* DetectorHit::operator new(size_t) {
    if (!DetectorHitAllocator)
        DetectorHitAllocator = new G4Allocator<DetectorHit>;
    return (void*)DetectorHitAllocator->MallocSingle();
}

inline void DetectorHit::operator delete(void* hit) {
    DetectorHitAllocator->FreeSingle((DetectorHit*)hit);
}

// Sensitive detector class
class SensitiveDetector : public G4VSensitiveDetector {
public:
    SensitiveDetector(const G4String& name, const G4String& hcName);
    virtual ~SensitiveDetector();
    
    virtual void Initialize(G4HCofThisEvent* hce) override;
    virtual G4bool ProcessHits(G4Step* step, G4TouchableHistory* history) override;
    virtual void EndOfEvent(G4HCofThisEvent* hce) override;
    
private:
    DetectorHitsCollection* fHitsCollection;
    G4int fHCID;
};

#endif

