/**
 * Primary Generator Action
 * Uses G4GeneralParticleSource (GPS) for flexibility
 */

#ifndef PrimaryGeneratorAction_h
#define PrimaryGeneratorAction_h 1

#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"

class G4GeneralParticleSource;
class G4Event;

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction {
public:
    PrimaryGeneratorAction();
    virtual ~PrimaryGeneratorAction();
    
    virtual void GeneratePrimaries(G4Event* event) override;
    
    G4GeneralParticleSource* GetGPS() const { return fGPS; }
    
private:
    G4GeneralParticleSource* fGPS;
};

#endif

