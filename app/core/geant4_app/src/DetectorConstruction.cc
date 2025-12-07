/**
 * Detector Construction Implementation
 */

#include "DetectorConstruction.hh"
#include "SensitiveDetector.hh"

#include "G4GDMLParser.hh"
#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4Sphere.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4SDManager.hh"
#include "G4VisAttributes.hh"
#include "G4SystemOfUnits.hh"

DetectorConstruction::DetectorConstruction()
    : G4VUserDetectorConstruction(),
      fGdmlFile(""),
      fParser(nullptr),
      fWorldLogical(nullptr),
      fWorldPhysical(nullptr)
{}

DetectorConstruction::DetectorConstruction(const G4String& gdmlFile)
    : G4VUserDetectorConstruction(),
      fGdmlFile(gdmlFile),
      fParser(nullptr),
      fWorldLogical(nullptr),
      fWorldPhysical(nullptr)
{}

DetectorConstruction::~DetectorConstruction() {
    if (fParser) delete fParser;
}

G4VPhysicalVolume* DetectorConstruction::Construct() {
    if (!fGdmlFile.empty()) {
        LoadGDML();
    } else {
        ConstructDefaultGeometry();
    }
    
    return fWorldPhysical;
}

void DetectorConstruction::LoadGDML() {
    fParser = new G4GDMLParser();
    fParser->Read(fGdmlFile, false);  // false = don't validate schema
    
    fWorldPhysical = fParser->GetWorldVolume();
    fWorldLogical = fWorldPhysical->GetLogicalVolume();
    
    // Find sensitive volumes from GDML auxiliary info
    FindSensitiveVolumes(fWorldLogical);
    
    G4cout << "Loaded GDML geometry from: " << fGdmlFile << G4endl;
    G4cout << "Found " << fSensitiveVolumes.size() << " sensitive volumes" << G4endl;
}

void DetectorConstruction::FindSensitiveVolumes(G4LogicalVolume* lv) {
    // Check for SensDet auxiliary tag
    if (fParser) {
        const G4GDMLAuxListType* auxList = fParser->GetVolumeAuxiliaryInformation(lv);
        if (auxList) {
            for (auto& aux : *auxList) {
                if (aux.type == "SensDet") {
                    fSensitiveVolumes.push_back(lv->GetName());
                    fLogicalVolumes[lv->GetName()] = lv;
                    G4cout << "  Sensitive detector: " << lv->GetName() << G4endl;
                }
            }
        }
    }
    
    // Recurse into daughters
    for (size_t i = 0; i < lv->GetNoDaughters(); i++) {
        G4VPhysicalVolume* pv = lv->GetDaughter(i);
        FindSensitiveVolumes(pv->GetLogicalVolume());
    }
}

void DetectorConstruction::ConstructDefaultGeometry() {
    // Default: Water phantom with detector
    G4NistManager* nist = G4NistManager::Instance();
    
    // Materials
    G4Material* air = nist->FindOrBuildMaterial("G4_AIR");
    G4Material* water = nist->FindOrBuildMaterial("G4_WATER");
    
    // World
    G4double worldSize = 1.0*m;
    G4Box* worldSolid = new G4Box("World", worldSize, worldSize, worldSize);
    fWorldLogical = new G4LogicalVolume(worldSolid, air, "World");
    fWorldPhysical = new G4PVPlacement(nullptr, G4ThreeVector(), 
                                        fWorldLogical, "World", nullptr, false, 0);
    
    // Water phantom
    G4double phantomSize = 150.0*mm;
    G4Box* phantomSolid = new G4Box("Phantom", phantomSize, phantomSize, phantomSize);
    G4LogicalVolume* phantomLogical = new G4LogicalVolume(phantomSolid, water, "Phantom");
    
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                      phantomLogical, "Phantom", fWorldLogical, false, 0);
    
    // Mark as sensitive
    fSensitiveVolumes.push_back("Phantom");
    fLogicalVolumes["Phantom"] = phantomLogical;
    
    // Visualization
    fWorldLogical->SetVisAttributes(G4VisAttributes::GetInvisible());
    phantomLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.0, 0.0, 1.0, 0.3)));
    
    G4cout << "Constructed default water phantom geometry" << G4endl;
}

void DetectorConstruction::ConstructSDandField() {
    G4SDManager* sdManager = G4SDManager::GetSDMpointer();
    
    for (const auto& name : fSensitiveVolumes) {
        G4String sdName = name + "_SD";
        SensitiveDetector* sd = new SensitiveDetector(sdName, name + "_HC");
        sdManager->AddNewDetector(sd);
        
        if (fLogicalVolumes.count(name)) {
            SetSensitiveDetector(fLogicalVolumes[name], sd);
            G4cout << "Attached SD to: " << name << G4endl;
        }
    }
}

