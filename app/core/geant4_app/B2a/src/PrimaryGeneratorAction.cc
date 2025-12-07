// ********************************************************************
// * B2a Primary Generator Action Implementation
// * Uses GPS for full API control via macros
// ********************************************************************

#include "PrimaryGeneratorAction.hh"

#include "G4GeneralParticleSource.hh"
#include "G4SystemOfUnits.hh"

namespace B2a
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PrimaryGeneratorAction::PrimaryGeneratorAction()
{
    fGPS = new G4GeneralParticleSource();
    
    // Default: proton at 3 GeV (can be overridden by macro)
    // GPS settings are controlled via /gps/* commands
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
    delete fGPS;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* anEvent)
{
    fGPS->GeneratePrimaryVertex(anEvent);
}

}

