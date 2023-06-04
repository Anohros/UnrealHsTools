import unreal
import glob
import os
import shutil
import math
import struct
import random

# Settings

propertyLookupPath = 'C:/Users/<path to a extracted property archive'

# Offset the position of spawned objects.
positionOffsetX = 18
positionOffsetY = 337

foliage = dict()

def getMetin2Properties():
    files = []
    files += glob.glob(propertyLookupPath + '/**/*.prt', recursive=True)

    for file in files:
        lines = open(file, 'r').readlines()

        # Parse property number.
        propertyNumber = int(lines[1])

        # Add foliage to list of known foliage.
        foliage[propertyNumber] = True

getMetin2Properties()

def spawnActor(name, assetReference, positionX, positionY, positionZ, rotationX, rotationY, rotationZ):
    asset = unreal.load_asset(assetReference)
    actorLocation = unreal.Vector(positionX, positionY, positionZ)
    actorRotation = unreal.Rotator(rotationX, rotationY, rotationZ)
    spawnedActor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, actorLocation, actorRotation)

    if spawnedActor:
        spawnedActor.set_actor_label(name)
        spawnedActor.set_folder_path('Foliage')

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
        if className != 'Landscape':
            continue

        positionZ = hit.to_tuple()[4].z + heightOffset

    spawnActor(name, assetReference, positionX, positionY, positionZ, rotationX, rotationY, rotationZ)

spawnsOnLandscape = []

for file in glob.glob('C:/Users/<path to an extracted map folder>/*/areadata.txt'):
    with open(file, 'r') as reader:
        line = reader.readline()
        while line != '':
            if line.startswith('Start'):
                # Parse position.
                name = line.split()[1]
                position = reader.readline().strip()
                positionParts = position.split()
                positionX = float(positionParts[0]) - positionOffsetX
                positionY = -float(positionParts[1]) - positionOffsetY
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
                isFoliage = propertyNumber in foliage

                # Set default property type.
                propertyType = 'object'

                if isFoliage:
                    spawnsOnLandscape.append((name, "/Game/NaturePackage/Meshes/flora/flowers0" + str(random.randint(1, 4)), positionX, positionY, positionZ, rotationX, rotationY, rotationZ))

                print('spawn ' + str(propertyType) + ': ' + str(propertyNumber))

            line = reader.readline()

for spawn in spawnsOnLandscape:
    spawnActorOnLandscape(*spawn)
