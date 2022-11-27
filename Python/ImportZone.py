import unreal
import glob

def _unreal_import_fbx_asset(input_path, destination_path, destination_name):
    """
    Import an FBX into Unreal Content Browser
    :param input_path: The fbx file to import
    :param destination_path: The Content Browser path where the asset will be placed
    :param destination_name: The asset name to use; if None, will use the filename without extension
    """
    tasks = []
    tasks.append(_generate_fbx_import_task(input_path, destination_path, destination_name))

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    first_imported_object = None

    for task in tasks:
        unreal.log("Import Task for: {}".format(task.filename))
        for object_path in task.imported_object_paths:
            unreal.log("Imported object: {}".format(object_path))
            if not first_imported_object:
                first_imported_object = object_path

    return first_imported_object
   
def _generate_fbx_import_task(filename, destination_path, destination_name=None, replace_existing=True,
                             automated=True, save=True, materials=True,
                             textures=True, as_skeletal=False):
    """
    Create and configure an Unreal AssetImportTask
    :param filename: The fbx file to import
    :param destination_path: The Content Browser path where the asset will be placed
    :return the configured AssetImportTask
    """
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

    # Materials
    task.options.texture_import_data.material_search_location = unreal.MaterialSearchLocation.DO_NOT_SEARCH
    task.options.texture_import_data.base_material_name = unreal.SoftObjectPath("/Game/Zone/M_ObjectMaster")
    task.options.texture_import_data.base_diffuse_texture_name = "Color"

    task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    if as_skeletal:
        task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH

    return task

path = "C:/Users/<path to an extracted and converted zone folder with fbx files>"

for file in glob.glob(path + "/**/*.fbx", recursive=True):
    relativePath = file[len(path):]
    relativePath = relativePath.strip("/\\")
    relativePath = relativePath.replace("\\", "/")
    relativePath = relativePath.rsplit("/", 1)
    filenameWithoutExtension = relativePath[1].rsplit(".", 1)
    _unreal_import_fbx_asset(file, "/Game/Zone/" + relativePath[0], filenameWithoutExtension[0])
