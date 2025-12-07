/**
 * Primary Generator Action Implementation
 */

#include "PrimaryGeneratorAction.hh"

#include "G4GeneralParticleSource.hh"
#include "G4Event.hh"

PrimaryGeneratorAction::PrimaryGeneratorAction()
    : G4VUserPrimaryGeneratorAction(),
      fGPS(nullptr)
{
    fGPS = new G4GeneralParticleSource();
    
    // Default configuration (will be overridden by macro)
    // GPS is fully controlled via macro commands like /gps/particle, /gps/energy, etc.
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() {
    delete fGPS;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
    fGPS->GeneratePrimaryVertex(event);
}

