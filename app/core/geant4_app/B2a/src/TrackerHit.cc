// ********************************************************************
// * B2a Tracker Hit Implementation
// * Based on: https://github.com/Geant4/geant4/tree/master/examples/basic/B2/B2a
// ********************************************************************

#include "TrackerHit.hh"

#include "G4UnitsTable.hh"
#include "G4VVisManager.hh"
#include "G4Circle.hh"
#include "G4Colour.hh"
#include "G4VisAttributes.hh"
#include "G4SystemOfUnits.hh"

#include <iomanip>

namespace B2a
{

G4ThreadLocal G4Allocator<TrackerHit>* TrackerHitAllocator = nullptr;

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4bool TrackerHit::operator==(const TrackerHit& right) const
{
    return (this == &right) ? true : false;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void TrackerHit::Print()
{
    // API-friendly output format
    G4cout << "Hit: chamber=" << fChamberNb
           << " track=" << fTrackID
           << " particle=" << fParticleName
           << " edep=" << std::setprecision(4) << fEdep/keV << " keV"
           << " pos=(" << std::setprecision(2) 
                       << fPos.x()/mm << ", " 
                       << fPos.y()/mm << ", "
                       << fPos.z()/mm << ") mm"
           << " time=" << std::setprecision(3) << fTime/ns << " ns"
           << G4endl;
}

}

