/**
 * Event Action Implementation
 */

#include "EventAction.hh"
#include "RunAction.hh"
#include "Analysis.hh"

#include "G4Event.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4HCofThisEvent.hh"
#include "G4SDManager.hh"

EventAction::EventAction(RunAction* runAction)
    : G4UserEventAction(),
      fRunAction(runAction),
      fEdep(0.)
{}

EventAction::~EventAction() {}

void EventAction::BeginOfEventAction(const G4Event* event) {
    fEdep = 0.;
    
    // Print progress every 100 events
    G4int eventID = event->GetEventID();
    if (eventID % 100 == 0) {
        G4cout << "---> Event " << eventID << G4endl;
    }
}

void EventAction::EndOfEventAction(const G4Event* event) {
    // Accumulate energy deposit
    fRunAction->AddEdep(fEdep);
    
    // Fill histogram
    Analysis* analysis = Analysis::Instance();
    analysis->FillH1(0, fEdep/MeV);
    
    // Fill ntuple
    G4int eventID = event->GetEventID();
    analysis->FillNtupleIColumn(0, eventID);
    analysis->FillNtupleDColumn(1, fEdep/MeV);
    analysis->AddNtupleRow();
    
    // Print event summary for significant events
    if (fEdep > 0.1*MeV) {
        G4cout << "    Event " << eventID << ": edep = " << fEdep/MeV << " MeV" << G4endl;
    }
}

