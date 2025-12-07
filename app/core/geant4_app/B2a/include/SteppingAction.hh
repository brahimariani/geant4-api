// ********************************************************************
// * B2a Stepping Action Header
// ********************************************************************

#ifndef B2aSteppingAction_h
#define B2aSteppingAction_h 1

#include "G4UserSteppingAction.hh"
#include "globals.hh"

namespace B2a
{

class EventAction;

class SteppingAction : public G4UserSteppingAction
{
  public:
    SteppingAction(EventAction* eventAction);
    ~SteppingAction() override = default;

    void UserSteppingAction(const G4Step*) override;

  private:
    EventAction* fEventAction = nullptr;
};

}

#endif

