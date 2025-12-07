// ********************************************************************
// * B2a Tracker Hit Header
// * Based on: https://github.com/Geant4/geant4/tree/master/examples/basic/B2/B2a
// ********************************************************************

#ifndef B2aTrackerHit_h
#define B2aTrackerHit_h 1

#include "G4VHit.hh"
#include "G4THitsCollection.hh"
#include "G4Allocator.hh"
#include "G4ThreeVector.hh"
#include "tls.hh"

namespace B2a
{

class TrackerHit : public G4VHit
{
  public:
    TrackerHit() = default;
    TrackerHit(const TrackerHit&) = default;
    ~TrackerHit() override = default;

    // Operators
    TrackerHit& operator=(const TrackerHit&) = default;
    G4bool operator==(const TrackerHit&) const;

    inline void* operator new(size_t);
    inline void  operator delete(void*);

    // Methods from base class
    void Print() override;

    // Set methods
    void SetTrackID(G4int track)      { fTrackID = track; }
    void SetChamberNb(G4int chamb)    { fChamberNb = chamb; }
    void SetEdep(G4double de)         { fEdep = de; }
    void SetPos(G4ThreeVector xyz)    { fPos = xyz; }
    void SetTime(G4double t)          { fTime = t; }
    void SetParticleName(G4String n)  { fParticleName = n; }

    // Get methods
    G4int GetTrackID() const          { return fTrackID; }
    G4int GetChamberNb() const        { return fChamberNb; }
    G4double GetEdep() const          { return fEdep; }
    G4ThreeVector GetPos() const      { return fPos; }
    G4double GetTime() const          { return fTime; }
    G4String GetParticleName() const  { return fParticleName; }

  private:
    G4int         fTrackID = -1;
    G4int         fChamberNb = -1;
    G4double      fEdep = 0.;
    G4ThreeVector fPos;
    G4double      fTime = 0.;
    G4String      fParticleName = "";
};

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

using TrackerHitsCollection = G4THitsCollection<TrackerHit>;

extern G4ThreadLocal G4Allocator<TrackerHit>* TrackerHitAllocator;

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

inline void* TrackerHit::operator new(size_t)
{
    if (!TrackerHitAllocator) {
        TrackerHitAllocator = new G4Allocator<TrackerHit>;
    }
    return (void *) TrackerHitAllocator->MallocSingle();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

inline void TrackerHit::operator delete(void *hit)
{
    TrackerHitAllocator->FreeSingle((TrackerHit*) hit);
}

}

#endif

