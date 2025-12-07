// ********************************************************************
// * B2a Tracker Sensitive Detector Header
// * Based on: https://github.com/Geant4/geant4/tree/master/examples/basic/B2/B2a
// ********************************************************************

#ifndef B2aTrackerSD_h
#define B2aTrackerSD_h 1

#include "G4VSensitiveDetector.hh"
#include "TrackerHit.hh"

class G4Step;
class G4HCofThisEvent;

namespace B2a
{

class TrackerSD : public G4VSensitiveDetector
{
  public:
    TrackerSD(const G4String& name, const G4String& hitsCollectionName);
    ~TrackerSD() override = default;

    // Methods from base class
    void   Initialize(G4HCofThisEvent* hitCollection) override;
    G4bool ProcessHits(G4Step* step, G4TouchableHistory* history) override;
    void   EndOfEvent(G4HCofThisEvent* hitCollection) override;

  private:
    TrackerHitsCollection* fHitsCollection = nullptr;
};

}

#endif

