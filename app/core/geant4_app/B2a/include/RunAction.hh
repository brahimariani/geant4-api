// ********************************************************************
// * B2a Run Action Header
// ********************************************************************

#ifndef B2aRunAction_h
#define B2aRunAction_h 1

#include "G4UserRunAction.hh"
#include "globals.hh"

class G4Run;

namespace B2a
{

class RunAction : public G4UserRunAction
{
  public:
    RunAction() = default;
    ~RunAction() override = default;

    void BeginOfRunAction(const G4Run*) override;
    void EndOfRunAction(const G4Run*) override;
};

}

#endif

