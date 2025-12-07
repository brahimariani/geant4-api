// ********************************************************************
// * B2a Detector Construction Header
// * Based on: https://github.com/Geant4/geant4/tree/master/examples/basic/B2/B2a
// ********************************************************************

#ifndef B2aDetectorConstruction_h
#define B2aDetectorConstruction_h 1

#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

class G4VPhysicalVolume;
class G4LogicalVolume;
class G4Material;
class G4UserLimits;
class G4GenericMessenger;

namespace B2a
{

class DetectorMessenger;

class DetectorConstruction : public G4VUserDetectorConstruction
{
  public:
    DetectorConstruction();
    ~DetectorConstruction() override;

    G4VPhysicalVolume* Construct() override;
    void ConstructSDandField() override;

    // Set methods
    void SetTargetMaterial(G4String);
    void SetChamberMaterial(G4String);
    void SetMaxStep(G4double);
    void SetCheckOverlaps(G4bool);

    // Get methods
    const G4VPhysicalVolume* GetTargetPV() const { return fTargetPV; }
    const G4VPhysicalVolume* GetChamberPV() const { return fChamberPV; }

  private:
    void DefineMaterials();
    G4VPhysicalVolume* DefineVolumes();

    G4GenericMessenger* fMessenger = nullptr;
    
    G4int fNbOfChambers = 5;

    G4LogicalVolume* fLogicTarget = nullptr;
    G4LogicalVolume* fLogicChamber = nullptr;

    G4VPhysicalVolume* fTargetPV = nullptr;
    G4VPhysicalVolume* fChamberPV = nullptr;

    G4Material* fTargetMaterial = nullptr;
    G4Material* fChamberMaterial = nullptr;

    G4UserLimits* fStepLimit = nullptr;

    G4bool fCheckOverlaps = true;
};

}

#endif

