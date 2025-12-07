// ********************************************************************
// * B2a Event Action Implementation
// ********************************************************************

#include "EventAction.hh"

#include "G4Event.hh"

namespace B2a
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::BeginOfEventAction(const G4Event*)
{
    // Nothing to do here - hits are collected by TrackerSD
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::EndOfEventAction(const G4Event*)
{
    // Hit summary is printed by TrackerSD::EndOfEvent
}

}

