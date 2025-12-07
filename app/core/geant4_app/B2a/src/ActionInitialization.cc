// ********************************************************************
// * B2a Action Initialization Implementation
// ********************************************************************

#include "ActionInitialization.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "EventAction.hh"
#include "SteppingAction.hh"

namespace B2a
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void ActionInitialization::BuildForMaster() const
{
    SetUserAction(new RunAction);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void ActionInitialization::Build() const
{
    SetUserAction(new PrimaryGeneratorAction);
    SetUserAction(new RunAction);
    
    auto eventAction = new EventAction;
    SetUserAction(eventAction);
    
    SetUserAction(new SteppingAction(eventAction));
}

}

