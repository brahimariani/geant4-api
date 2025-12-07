/**
 * Action Initialization
 */

#ifndef ActionInitialization_h
#define ActionInitialization_h 1

#include "G4VUserActionInitialization.hh"
#include "globals.hh"

class ActionInitialization : public G4VUserActionInitialization {
public:
    ActionInitialization(const G4String& outputDir = ".");
    virtual ~ActionInitialization();
    
    virtual void BuildForMaster() const override;
    virtual void Build() const override;
    
private:
    G4String fOutputDir;
};

#endif

