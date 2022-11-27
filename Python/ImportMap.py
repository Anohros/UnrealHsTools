import unreal
import glob
import os
import shutil
import math
import struct

objects = dict()
dungeons = dict()
effects = dict()
foliage = dict()

def getMetin2Properties():
    propertyLookupPath = "C:/Users/<path to a extracted property archive>"
    zoneLookupPath = "C:/Users/<path to an extracted and converted zone folder with fbx files>"

    files = []
    files += glob.glob(propertyLookupPath + "/**/*.prb", recursive=True)
    files += glob.glob(propertyLookupPath + "/**/*.prd", recursive=True)
    files += glob.glob(propertyLookupPath + "/**/*.pre", recursive=True)
    files += glob.glob(propertyLookupPath + "/**/*.prt", recursive=True)

    for file in files:
        lines = open(file, "r", encoding="utf8", errors='ignore').readlines()

        # Parse property number.
        propertyNumber = int(lines[1])

        if file.endswith("pre"):
            effects[propertyNumber] = True
            continue;

        if file.endswith("prt"):
            foliage[propertyNumber] = True
            continue;

        if file.endswith("prb") or file.endswith("prd"):
            # Ensure path begins with: "d:/ymir work/".
            if lines[2].find("d:/ymir work/") == -1:
                continue

            # Parse object file gr2
            objectFileGr2 = lines[2].rstrip()[lines[2].find("d:/ymir work/") + 13:-1]

            # Split in directory path and file path.
            fbxFileDirectory, fbxFileName = os.path.split(objectFileGr2)

            # Normalize filename
            fbxFileName = fbxFileName.replace('-', '_');
            fbxFileName = fbxFileName.replace(' ', '_');
            fbxFileName = fbxFileName.replace('#', '_');
            fbxFileName = fbxFileName.title()

            # Change file extension and respect case after "title" normalization.
            fbxFileName = fbxFileName.replace("Gr2", "fbx")

            # Join directory path and file path and remove zone prefix.
            fbxFilePath = fbxFileDirectory + "/SK_" + fbxFileName
            fbxFilePath = fbxFilePath.replace("zone/", "")

            lookupPath = zoneLookupPath + "/" + fbxFilePath

            # Get reference by remove of file extension
            objectReference = fbxFilePath.replace(".fbx", "")

            # Ensure building file exists as fbx.
            isBuildingFileFbxExists = os.path.isfile(lookupPath)
            if isBuildingFileFbxExists == False:
                propertyType = "building" if file.endswith("prb") else "dungeon"
                print("not found " + propertyType + ": " + objectReference + " (" + str(propertyNumber) + ") referend by " + file[len(propertyLookupPath):])
                continue

            objects[propertyNumber] = "Zone/" + objectReference

getMetin2Properties()

def spawnActor(name, assetReference, positionX, positionY, positionZ, rotationX, rotationY, rotationZ):
    asset = unreal.load_asset('/Game/' + assetReference)
    actorLocation = unreal.Vector(positionX, positionY, positionZ)
    actorRotation = unreal.Rotator(rotationX, rotationY, rotationZ)
    spawnedActor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, actorLocation, actorRotation)

    if spawnedActor:
        spawnedActor.set_actor_label(name)
        spawnedActor.set_folder_path("Objects")

def spawnActorOnLandscape(name, assetReference, positionX, positionY, positionZ, rotationX, rotationY, rotationZ):
    hits = unreal.SystemLibrary.line_trace_multi_for_objects(
        unreal.EditorLevelLibrary.get_editor_world(),
        unreal.Vector(positionX, positionY, 30000),
        unreal.Vector(positionX, positionY, -30000),
        [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1],
        True,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
        unreal.LinearColor.RED,
        unreal.LinearColor.GREEN,
        5.0
    )

    for hit in hits:
        className = hit.to_tuple()[9].get_class().get_name()

        # Ensure hit is landscape.
        if className != "Landscape":
            continue

        positionZ = hit.to_tuple()[4].z + heightOffset

    spawnActor(name, assetReference, positionX, positionY, positionZ, rotationX, rotationY, rotationZ)

for file in glob.glob("C:/Users/<path to an extracted and converted map folder>/*/areadata.txt"):
    with open(file, "r") as reader:
        line = reader.readline()
        while line != '':
            if line.startswith("Start"):
                # Parse position.
                name = line.split()[1]
                position = reader.readline().strip()
                positionParts = position.split()
                positionX = float(positionParts[0])
                positionY = -float(positionParts[1])
                positionZ = float(positionParts[2])

                # Parse property number.
                propertyNumber = int(reader.readline().strip())

                # Parse rotation.
                rotation = reader.readline().strip()
                rotationParts = rotation.split('#')
                rotationX = float(rotationParts[0])
                rotationY = float(rotationParts[1])
                rotationZ = float(rotationParts[2])

                # Convert metin2 rotation values to unreal rotation values.
                rotation = unreal.MathLibrary.rotate_angle_axis(unreal.Vector(rotationX, rotationY, rotationZ), 180.0, unreal.Vector(1.0, 0.0, 0.0))
                rotationX = rotation.x
                rotationY = rotation.y
                rotationZ = rotation.z

                # Parsing height offset and add to positionZ.
                heightOffset = float(reader.readline())
                positionZ += heightOffset

                # Ensure property is known.
                isObject = propertyNumber in objects
                isDungeon = propertyNumber in dungeons
                isEffect = propertyNumber in effects
                isFoliage = propertyNumber in foliage

                if isObject == False:
                    if (isDungeon or isEffect or isFoliage):
                        propertyType = "dungeon" if isDungeon else "effect" if isEffect else "foliage"
                    else:
                        print("not spawn: " + str(propertyNumber))

                    line = reader.readline()
                    continue

                print("spawn " + str(propertyType) + ": " + str(propertyNumber))

                if isObject:
                    spawnActor(name, objects[propertyNumber], positionX, positionY, positionZ, rotationX, rotationY, rotationZ)

                if isDungeon:
                    spawnActor(name, dungeons[propertyNumber], positionX, positionY, positionZ, rotationX, rotationY, rotationZ)

            line = reader.readline()
