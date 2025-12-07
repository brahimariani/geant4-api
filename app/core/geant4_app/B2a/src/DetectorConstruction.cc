// ********************************************************************
// * B2a Detector Construction Implementation
// * Based on: https://github.com/Geant4/geant4/tree/master/examples/basic/B2/B2a
// ********************************************************************

#include "DetectorConstruction.hh"
#include "DetectorMessenger.hh"
#include "TrackerSD.hh"

#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4SDManager.hh"

#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4PVReplica.hh"
#include "G4GlobalMagFieldMessenger.hh"
#include "G4AutoDelete.hh"

#include "G4GeometryTolerance.hh"
#include "G4GeometryManager.hh"

#include "G4UserLimits.hh"

#include "G4VisAttributes.hh"
#include "G4Colour.hh"

#include "G4SystemOfUnits.hh"

#include "G4GenericMessenger.hh"

namespace B2a
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

DetectorConstruction::DetectorConstruction()
{
    fMessenger = new G4GenericMessenger(this, "/B2a/", "Detector control");
    
    // Define commands
    fMessenger->DeclareMethod("setTargetMaterial", &DetectorConstruction::SetTargetMaterial)
        .SetGuidance("Select Material of the Target.")
        .SetParameterName("choice", false)
        .SetStates(G4State_PreInit, G4State_Idle);

    fMessenger->DeclareMethod("setChamberMaterial", &DetectorConstruction::SetChamberMaterial)
        .SetGuidance("Select Material of the Chamber.")
        .SetParameterName("choice", false)
        .SetStates(G4State_PreInit, G4State_Idle);

    DefineMaterials();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

DetectorConstruction::~DetectorConstruction()
{
    delete fMessenger;
    delete fStepLimit;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::DefineMaterials()
{
    G4NistManager* nistManager = G4NistManager::Instance();

    // Air
    nistManager->FindOrBuildMaterial("G4_AIR");

    // Lead
    fTargetMaterial = nistManager->FindOrBuildMaterial("G4_Pb");

    // Xenon gas
    fChamberMaterial = nistManager->FindOrBuildMaterial("G4_Xe");

    G4cout << G4endl << "Materials defined:" << G4endl;
    G4cout << "  Target: " << fTargetMaterial->GetName() << G4endl;
    G4cout << "  Chamber: " << fChamberMaterial->GetName() << G4endl;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4VPhysicalVolume* DetectorConstruction::Construct()
{
    return DefineVolumes();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4VPhysicalVolume* DetectorConstruction::DefineVolumes()
{
    G4Material* air = G4Material::GetMaterial("G4_AIR");

    // Sizes of the principal geometrical components
    G4double chamberSpacing = 80*cm;
    G4double chamberWidth = 20*cm;
    G4double targetLength = 5*cm;
    G4double trackerLength = (fNbOfChambers + 1) * chamberSpacing;

    G4double worldLength = 1.2 * (2*targetLength + trackerLength);

    G4double targetRadius = 0.5*targetLength;
    G4double trackerSize = 0.5*trackerLength;

    // Definitions of Solids, Logical Volumes, Physical Volumes

    // World
    G4GeometryManager::GetInstance()->SetWorldMaximumExtent(worldLength);

    G4cout << G4endl << "Geometry parameters:" << G4endl;
    G4cout << "  World extent: " << worldLength/m << " m" << G4endl;
    G4cout << "  Target length: " << targetLength/cm << " cm" << G4endl;
    G4cout << "  Tracker length: " << trackerLength/cm << " cm" << G4endl;
    G4cout << "  Number of chambers: " << fNbOfChambers << G4endl;

    G4Box* worldS = new G4Box("world", worldLength/2, worldLength/2, worldLength/2);
    G4LogicalVolume* worldLV = new G4LogicalVolume(worldS, air, "World");

    G4VPhysicalVolume* worldPV = new G4PVPlacement(
        nullptr,           // no rotation
        G4ThreeVector(),   // at (0,0,0)
        worldLV,           // its logical volume
        "World",           // its name
        nullptr,           // its mother volume
        false,             // no boolean operations
        0,                 // copy number
        fCheckOverlaps);   // checking overlaps

    // Target
    G4ThreeVector positionTarget = G4ThreeVector(0, 0, -(targetLength + trackerLength)/2);

    G4Tubs* targetS = new G4Tubs("target", 0., targetRadius, targetLength/2, 0.*deg, 360.*deg);
    fLogicTarget = new G4LogicalVolume(targetS, fTargetMaterial, "Target", nullptr, nullptr, nullptr);
    fTargetPV = new G4PVPlacement(
        nullptr,           // no rotation
        positionTarget,    // at (x,y,z)
        fLogicTarget,      // its logical volume
        "Target",          // its name
        worldLV,           // its mother volume
        false,             // no boolean operations
        0,                 // copy number
        fCheckOverlaps);   // checking overlaps

    G4cout << "  Target positioned at z = " << positionTarget.z()/cm << " cm" << G4endl;

    // Tracker (5 chambers)
    G4ThreeVector positionTracker = G4ThreeVector(0, 0, 0);

    G4Tubs* trackerS = new G4Tubs("tracker", 0., trackerSize, trackerSize, 0.*deg, 360.*deg);
    G4LogicalVolume* trackerLV = new G4LogicalVolume(trackerS, air, "Tracker", nullptr, nullptr, nullptr);
    new G4PVPlacement(
        nullptr,           // no rotation
        positionTracker,   // at (x,y,z)
        trackerLV,         // its logical volume
        "Tracker",         // its name
        worldLV,           // its mother volume
        false,             // no boolean operations
        0,                 // copy number
        fCheckOverlaps);   // checking overlaps

    // Tracker chambers
    G4double firstPosition = -trackerSize + chamberSpacing;
    G4double firstLength = trackerLength/10;
    G4double lastLength = trackerLength;

    G4double halfWidth = 0.5*chamberWidth;
    G4double rmaxFirst = 0.5 * firstLength;

    G4double rmaxIncr = 0.;
    if (fNbOfChambers > 0) {
        rmaxIncr = 0.5 * (lastLength - firstLength) / (fNbOfChambers - 1);
        if (chamberSpacing < chamberWidth) {
            G4Exception("DetectorConstruction::DefineVolumes()",
                        "InvalidSetup", FatalException,
                        "Width>Spacing");
        }
    }

    for (G4int copyNo = 0; copyNo < fNbOfChambers; copyNo++) {
        G4double Zposition = firstPosition + copyNo * chamberSpacing;
        G4double rmax = rmaxFirst + copyNo * rmaxIncr;

        G4Tubs* chamberS = new G4Tubs("Chamber_solid", 0, rmax, halfWidth, 0.*deg, 360.*deg);
        fLogicChamber = new G4LogicalVolume(chamberS, fChamberMaterial, "Chamber_LV", nullptr, nullptr, nullptr);

        fChamberPV = new G4PVPlacement(
            nullptr,                              // no rotation
            G4ThreeVector(0, 0, Zposition),       // at (x,y,z)
            fLogicChamber,                        // its logical volume
            "Chamber_PV",                         // its name
            trackerLV,                            // its mother volume
            false,                                // no boolean operations
            copyNo,                               // copy number
            fCheckOverlaps);                      // checking overlaps

        G4cout << "  Chamber " << copyNo << " at z = " << Zposition/cm << " cm, rmax = " << rmax/cm << " cm" << G4endl;
    }

    // Visualization attributes
    worldLV->SetVisAttributes(G4VisAttributes::GetInvisible());

    G4VisAttributes* boxVisAtt = new G4VisAttributes(G4Colour(1.0, 1.0, 1.0));
    G4VisAttributes* chamberVisAtt = new G4VisAttributes(G4Colour(1.0, 1.0, 0.0));
    fLogicTarget->SetVisAttributes(boxVisAtt);
    trackerLV->SetVisAttributes(boxVisAtt);
    fLogicChamber->SetVisAttributes(chamberVisAtt);

    // Set step limit
    G4double maxStep = 0.5*chamberWidth;
    fStepLimit = new G4UserLimits(maxStep);
    fLogicChamber->SetUserLimits(fStepLimit);

    return worldPV;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::ConstructSDandField()
{
    // Sensitive detectors
    G4String trackerChamberSDname = "/TrackerChamberSD";
    TrackerSD* aTrackerSD = new TrackerSD(trackerChamberSDname, "TrackerHitsCollection");
    G4SDManager::GetSDMpointer()->AddNewDetector(aTrackerSD);
    SetSensitiveDetector(fLogicChamber, aTrackerSD, true);

    G4cout << G4endl << "Sensitive detector attached to chambers" << G4endl;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::SetTargetMaterial(G4String materialName)
{
    G4NistManager* nistManager = G4NistManager::Instance();
    G4Material* pttoMaterial = nistManager->FindOrBuildMaterial(materialName);

    if (fTargetMaterial != pttoMaterial) {
        if (pttoMaterial) {
            fTargetMaterial = pttoMaterial;
            if (fLogicTarget) fLogicTarget->SetMaterial(fTargetMaterial);
            G4cout << "Target material changed to: " << materialName << G4endl;
        }
    }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::SetChamberMaterial(G4String materialName)
{
    G4NistManager* nistManager = G4NistManager::Instance();
    G4Material* pttoMaterial = nistManager->FindOrBuildMaterial(materialName);

    if (fChamberMaterial != pttoMaterial) {
        if (pttoMaterial) {
            fChamberMaterial = pttoMaterial;
            if (fLogicChamber) fLogicChamber->SetMaterial(fChamberMaterial);
            G4cout << "Chamber material changed to: " << materialName << G4endl;
        }
    }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::SetMaxStep(G4double maxStep)
{
    if ((fStepLimit) && (maxStep > 0.)) fStepLimit->SetMaxAllowedStep(maxStep);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::SetCheckOverlaps(G4bool checkOverlaps)
{
    fCheckOverlaps = checkOverlaps;
}

}

