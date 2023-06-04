import unreal

old_material_reference = '/Game/NaturePackage/Materials/flora/TreeBrunch1'
new_material_reference = '/Game/HeavenStones/Materials/Foliage/MI_TreeBrunch_01'

old_material = unreal.EditorAssetLibrary.load_asset(old_material_reference)
if old_material is None:
	print("The old material cant be loaded")
	quit()

new_material = unreal.EditorAssetLibrary.load_asset(new_material_reference)
if new_material is None:
	print("The new material cant be loaded")
	quit()

actor_list = unreal.EditorLevelLibrary.get_all_level_actors()
actor_list = unreal.EditorFilterLibrary.by_class(actor_list, unreal.StaticMeshActor.static_class())
unreal.EditorLevelLibrary.replace_mesh_components_materials_on_actors(actor_list, old_material, new_material)
