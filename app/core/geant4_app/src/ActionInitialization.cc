/**
 * Action Initialization Implementation
 */

#include "ActionInitialization.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "EventAction.hh"
#include "SteppingAction.hh"

ActionInitialization::ActionInitialization(const G4String& outputDir)
    : G4VUserActionInitialization(),
      fOutputDir(outputDir)
{}

ActionInitialization::~ActionInitialization() {}

void ActionInitialization::BuildForMaster() const {
    SetUserAction(new RunAction(fOutputDir));
}

void ActionInitialization::Build() const {
    SetUserAction(new PrimaryGeneratorAction);
    
    RunAction* runAction = new RunAction(fOutputDir);
    SetUserAction(runAction);
    
    EventAction* eventAction = new EventAction(runAction);
    SetUserAction(eventAction);
    
    SetUserAction(new SteppingAction(eventAction));
}

