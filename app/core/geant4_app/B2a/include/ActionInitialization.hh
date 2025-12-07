// ********************************************************************
// * B2a Action Initialization Header
// ********************************************************************

#ifndef B2aActionInitialization_h
#define B2aActionInitialization_h 1

#include "G4VUserActionInitialization.hh"

namespace B2a
{

class ActionInitialization : public G4VUserActionInitialization
{
  public:
    ActionInitialization() = default;
    ~ActionInitialization() override = default;

    void BuildForMaster() const override;
    void Build() const override;
};

}

#endif

