import unreal
import glob
import os
import shutil
import math
import struct

# Settings

propertyLookupPath = 'C:/Users/<path to a extracted property archive'
zoneLookupPath = 'C:/Users/<path to an extracted and converted zone folder with fbx files>'

# Offset the position of spawned objects.
positionOffsetX = 18
positionOffsetY = 337

objects = dict()
objectsLookup = dict()
dungeons = dict()
effects = dict()
foliage = dict()

tasks = dict()

def generate_fbx_import_task(
    filename,
    destination_path,
    destination_name=None,
    replace_existing=True,
    automated=True,
    save=True,
    materials=True,
    textures=True,
    as_skeletal=False
):
    task = unreal.AssetImportTask()
    task.filename = filename
    task.destination_path = destination_path

    # By default, destination_name is the filename without the extension
    if destination_name is not None:
        task.destination_name = destination_name

    task.save = save
    task.replace_existing = replace_existing
    task.automated = automated

    task.options = unreal.FbxImportUI()
    task.options.reset_to_default()
    task.options.automated_import_should_detect_type = False

    # General
    task.options.import_materials = materials
    task.options.import_textures = textures
    task.options.import_as_skeletal = as_skeletal

    # LOD
    task.options.auto_compute_lod_distances = False
    task.options.lod_number = 4
    task.options.lod_distance0 = 1.0
    task.options.lod_distance1 = 0.275
    task.options.lod_distance2 = 0.1
    task.options.lod_distance3 = 0.0175

    # Mesh
    task.options.static_mesh_import_data.combine_meshes = True
    task.options.static_mesh_import_data.build_nanite = True

    # Materials
    task.options.texture_import_data.material_search_location = unreal.MaterialSearchLocation.DO_NOT_SEARCH
    task.options.texture_import_data.base_material_name = unreal.SoftObjectPath('/Game/HeavenStones/Materials/Zone/M_ObjectBase')
    task.options.texture_import_data.base_diffuse_texture_name = 'Albedo'

    task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    if as_skeletal:
        task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH

    return task

def upperscoreFolders(str):
    folders = str.split('/')
    return '/'.join(folder.title() for folder in folders[1:])

def getMetin2Properties():
    files = []
    files += glob.glob(propertyLookupPath + '/**/*.prb', recursive=True)
    files += glob.glob(propertyLookupPath + '/**/*.prd', recursive=True)
    files += glob.glob(propertyLookupPath + '/**/*.pre', recursive=True)
    files += glob.glob(propertyLookupPath + '/**/*.prt', recursive=True)

    for file in files:
        lines = open(file, 'r').readlines()

        # Parse property number.
        propertyNumber = int(lines[1])

        if file.endswith('pre'):
            effects[propertyNumber] = True
            continue;

        if file.endswith('prt'):
            foliage[propertyNumber] = True
            continue;

        if file.endswith('prb') or file.endswith('prd'):
            # Ensure path begins with: 'd:/ymir work/'.
            if lines[2].find('d:/ymir work/') == -1:
                continue

            # Parse object file gr2
            objectFileGr2 = lines[2].rstrip()[lines[2].find('d:/ymir work/') + 13:-1]

            # Split in directory path and file path.
            fbxFileDirectory, fbxFileName = os.path.split(objectFileGr2)
            fbxFileDirectory = upperscoreFolders(fbxFileDirectory)

            # Normalize filename
            fbxFileName = fbxFileName.replace('-', '_');
            fbxFileName = fbxFileName.replace(' ', '_');
            fbxFileName = fbxFileName.replace('#', '_');
            fbxFileName = fbxFileName.title()

            # Change file extension and respect case after 'title' normalization.
            fbxFileName = fbxFileName.replace('gr2', 'fbx')
            fbxFileName = fbxFileName.replace('Gr2', 'fbx')

            # Join directory path and file path and remove zone prefix.
            fbxFilePath = fbxFileDirectory + '/SM_' + fbxFileName
            # fbxFilePath = fbxFilePath.replace('zone/', '')

            lookupPath = zoneLookupPath + '/' + fbxFilePath

            # Get reference by remove of file extension
            objectReference = fbxFilePath.replace('.fbx', '')

            # Ensure building file exists as fbx.
            isBuildingFileFbxExists = os.path.isfile(lookupPath)
            if isBuildingFileFbxExists == False:
                propertyType = 'building' if file.endswith('prb') else 'dungeon'
                print('not found ' + propertyType + ': ' + objectReference + ' (' + str(propertyNumber) + ') referend by ' + file[len(propertyLookupPath):])
                continue

            objects[propertyNumber] = '/Game/HeavenStones/Meshes/Zone/' + objectReference
            objectsLookup[propertyNumber] = lookupPath

getMetin2Properties()

def spawnActor(name, assetReference, positionX, positionY, positionZ, rotationX, rotationY, rotationZ):
    asset = unreal.load_asset(assetReference)
    actorLocation = unreal.Vector(positionX, positionY, positionZ)
    actorRotation = unreal.Rotator(rotationX, rotationY, rotationZ)
    spawnedActor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, actorLocation, actorRotation)

    if spawnedActor:
        spawnedActor.set_actor_label(name)
        spawnedActor.set_folder_path('Objects')

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
spawns = []

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
                isObject = propertyNumber in objects
                isDungeon = propertyNumber in dungeons
                isEffect = propertyNumber in effects
                isFoliage = propertyNumber in foliage

                # Set default property type.
                propertyType = 'object'

                if isObject == False:
                    if (isDungeon or isEffect or isFoliage):
                        propertyType = 'dungeon' if isDungeon else 'effect' if isEffect else 'foliage'
                    else:
                        print('not spawn: ' + str(propertyNumber))

                    line = reader.readline()
                    continue

                if isObject:
                    if not unreal.EditorAssetLibrary.does_asset_exist(objects[propertyNumber]) and objects[propertyNumber] not in tasks:
                        lookupPath = objectsLookup[propertyNumber]
                        relativePath = lookupPath[len(zoneLookupPath):]
                        relativePath = relativePath.strip('/\\')
                        relativePath = relativePath.replace('\\', '/')
                        relativePath = relativePath.rsplit('/', 1)
                        filenameWithoutExtension = relativePath[1].rsplit('.', 1)
                        tasks[objects[propertyNumber]] = generate_fbx_import_task(lookupPath, '/Game/HeavenStones/Meshes/Zone/' + relativePath[0], filenameWithoutExtension[0])

                    spawnsOnLandscape.append((name, objects[propertyNumber], positionX, positionY, positionZ, rotationX, rotationY, rotationZ))

                if isDungeon:
                    spawns.append((name, dungeons[propertyNumber], positionX, positionY, positionZ, rotationX, rotationY, rotationZ))

                print('spawn ' + str(propertyType) + ': ' + str(propertyNumber))

            line = reader.readline()

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks.values())

for spawn in spawnsOnLandscape:
    spawnActorOnLandscape(*spawn)

for spawn in spawns:
    spawnActor(*spawn)
