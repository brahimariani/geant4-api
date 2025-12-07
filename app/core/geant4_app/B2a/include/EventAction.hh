// ********************************************************************
// * B2a Event Action Header
// ********************************************************************

#ifndef B2aEventAction_h
#define B2aEventAction_h 1

#include "G4UserEventAction.hh"
#include "globals.hh"

namespace B2a
{

class EventAction : public G4UserEventAction
{
  public:
    EventAction() = default;
    ~EventAction() override = default;

    void BeginOfEventAction(const G4Event*) override;
    void EndOfEventAction(const G4Event*) override;
};

}

#endif

