// ********************************************************************
// * B2a Primary Generator Action Header
// ********************************************************************

#ifndef B2aPrimaryGeneratorAction_h
#define B2aPrimaryGeneratorAction_h 1

#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"

class G4GeneralParticleSource;
class G4Event;

namespace B2a
{

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
  public:
    PrimaryGeneratorAction();
    ~PrimaryGeneratorAction() override;

    void GeneratePrimaries(G4Event* ) override;

    G4GeneralParticleSource* GetGPS() const { return fGPS; }

  private:
    G4GeneralParticleSource* fGPS = nullptr;
};

}

#endif

