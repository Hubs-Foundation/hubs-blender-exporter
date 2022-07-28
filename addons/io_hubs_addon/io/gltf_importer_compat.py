import bpy
from io_scene_gltf2.blender.imp.gltf2_blender_node import BlenderNode
from io_scene_gltf2.blender.imp.gltf2_blender_material import BlenderMaterial
from io_scene_gltf2.blender.imp.gltf2_blender_scene import BlenderScene
from .utils import HUBS_CONFIG

# import hooks were only recently added to the glTF exporter, so make a custom hook for now
orig_BlenderNode_create_object = BlenderNode.create_object
orig_BlenderMaterial_create = BlenderMaterial.create
orig_BlenderScene_create = BlenderScene.create

EXTENSION_NAME = HUBS_CONFIG["gltfExtensionName"]


def add_hubs_components(gltf2_object, blender_object, import_settings):
    if not gltf2_object.extensions or EXTENSION_NAME not in gltf2_object.extensions:
        return

    components_data = gltf2_object.extensions[EXTENSION_NAME]
    from ..components.components_registry import get_component_by_name
    for component_name in components_data.keys():
        component_class = get_component_by_name(component_name)
        if component_class:
            component_value = components_data[component_name]
            component_class.gather_import(
                import_settings, blender_object, component_name, component_value)
        else:
            print('Could not import unsupported component "%s"' %
                  (component_name))


@staticmethod
def patched_BlenderNode_create_object(gltf, vnode_id):
    blender_object = orig_BlenderNode_create_object(gltf, vnode_id)

    vnode = gltf.vnodes[vnode_id]
    node = None

    if vnode.camera_node_idx is not None:
        parent_vnode = gltf.vnodes[vnode.parent]
        if parent_vnode.name:
            node = [n for n in gltf.data.nodes if n.name == parent_vnode.name][0]

    else:
        if vnode.name:
            node = [n for n in gltf.data.nodes if n.name == vnode.name][0]

    add_hubs_components(node, vnode.blender_object, gltf)

    return blender_object


@staticmethod
def patched_BlenderMaterial_create(gltf, material_idx, vertex_color):
    orig_BlenderMaterial_create(
        gltf, material_idx, vertex_color)
    gltf_material = gltf.data.materials[material_idx]
    blender_object = bpy.data.materials[gltf_material.blender_material[None]]
    add_hubs_components(gltf_material, blender_object, gltf)


@staticmethod
def patched_BlenderScene_create(gltf):
    orig_BlenderScene_create(gltf)
    gltf_scene = gltf.data.scenes[gltf.data.scene]
    blender_object = bpy.data.scenes[gltf.blender_scene]
    add_hubs_components(gltf_scene, blender_object, gltf)


def register():
    print("Register GLTF Importer")
    BlenderNode.create_object = patched_BlenderNode_create_object
    BlenderMaterial.create = patched_BlenderMaterial_create
    BlenderScene.create = patched_BlenderScene_create


def unregister():
    print("Unregister GLTF Importer")
    BlenderNode.create_object = orig_BlenderNode_create_object
    BlenderMaterial.create = orig_BlenderMaterial_create
    BlenderScene.create = orig_BlenderScene_create
