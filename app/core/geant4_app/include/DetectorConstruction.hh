/**
 * Detector Construction
 * =====================
 * Supports both programmatic geometry and GDML loading.
 */

#ifndef DetectorConstruction_h
#define DetectorConstruction_h 1

#include "G4VUserDetectorConstruction.hh"
#include "G4LogicalVolume.hh"
#include "G4VPhysicalVolume.hh"
#include "globals.hh"

#include <vector>
#include <map>

class G4GDMLParser;

class DetectorConstruction : public G4VUserDetectorConstruction {
public:
    DetectorConstruction();
    DetectorConstruction(const G4String& gdmlFile);
    virtual ~DetectorConstruction();
    
    virtual G4VPhysicalVolume* Construct() override;
    virtual void ConstructSDandField() override;
    
    // Getters
    G4LogicalVolume* GetWorldLogical() const { return fWorldLogical; }
    const std::vector<G4String>& GetSensitiveVolumes() const { return fSensitiveVolumes; }
    
private:
    void ConstructDefaultGeometry();
    void LoadGDML();
    void FindSensitiveVolumes(G4LogicalVolume* lv);
    
    G4String fGdmlFile;
    G4GDMLParser* fParser;
    G4LogicalVolume* fWorldLogical;
    G4VPhysicalVolume* fWorldPhysical;
    
    std::vector<G4String> fSensitiveVolumes;
    std::map<G4String, G4LogicalVolume*> fLogicalVolumes;
};

#endif

