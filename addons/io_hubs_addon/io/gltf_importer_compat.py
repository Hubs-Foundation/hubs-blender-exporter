import bpy
import traceback
from io_scene_gltf2.blender.imp.gltf2_blender_node import BlenderNode
from io_scene_gltf2.blender.imp.gltf2_blender_material import BlenderMaterial
from io_scene_gltf2.blender.imp.gltf2_blender_scene import BlenderScene
from io_scene_gltf2.blender.imp.gltf2_blender_image import BlenderImage

from ..components.definitions.loop_animation import has_track
from .utils import add_hubs_component, assign_property, set_color_from_hex

# import hooks were only recently added to the glTF exporter, so make a custom hook for now
orig_BlenderNode_create_object = BlenderNode.create_object
orig_BlenderMaterial_create = BlenderMaterial.create
orig_BlenderScene_create = BlenderScene.create

stored_components = {'object': {}, 'material': {}}


@staticmethod
def patched_BlenderNode_create_object(gltf, vnode_id):
    obj = orig_BlenderNode_create_object(gltf, vnode_id)

    vnode = gltf.vnodes[vnode_id]
    node = None

    if vnode.camera_node_idx is not None:
        parent_vnode = gltf.vnodes[vnode.parent]
        if parent_vnode.name:
            node = [n for n in gltf.data.nodes if n.name == parent_vnode.name][0]

    else:
        if vnode.name:
            node = [n for n in gltf.data.nodes if n.name == vnode.name][0]

    if node is not None:
        extensions = node.extensions
        if extensions:
            MOZ_hubs_components = extensions.get('MOZ_hubs_components')
            if MOZ_hubs_components:
                stored_components['object'][node.name] = (vnode, node)

    return obj


@staticmethod
def patched_BlenderMaterial_create(gltf, material_idx, vertex_color):
    orig_BlenderMaterial_create(gltf, material_idx, vertex_color)

    glb_material = gltf.data.materials[material_idx]

    if glb_material is not None:
        extensions = glb_material.extensions
        if extensions:
            MOZ_hubs_components = extensions.get('MOZ_hubs_components')
            if MOZ_hubs_components:
                stored_components['material'][glb_material.name] = glb_material


@staticmethod
def patched_BlenderScene_create(gltf):
    global stored_components
    orig_BlenderScene_create(gltf)

    create_object_hubs_components(gltf)
    create_material_hubs_components(gltf)
    create_scene_hubs_components(gltf)

    # clear stored components so as not to conflict with the next import
    for key in stored_components.keys():
        stored_components[key].clear()


def create_object_hubs_components(gltf):
    special_cases = {
        'networked': handle_networked,
        # 'audio-target': handle_audio_target,
        'spawn-point': handle_spawn_point,
        'heightfield': handle_heightfield,
        'box-collider': handle_box_collider,
        'scene-preview-camera': handle_scene_preview_camera,
        'trimesh': handle_trimesh,
        'spawner': handle_spawner,
        'loop-animation': handle_loop_animation,
    }

    for vnode, node in stored_components['object'].values():
        MOZ_hubs_components = node.extensions['MOZ_hubs_components']
        for glb_component_name, glb_component_value in MOZ_hubs_components.items():
            try:
                if glb_component_name in special_cases.keys():
                    special_cases[glb_component_name](
                        gltf, vnode, node, glb_component_name, glb_component_value)
                    continue

                else:
                    blender_component = add_hubs_component(
                        "object", glb_component_name, glb_component_value, vnode=vnode, node=node)

                    for property_name, property_value in glb_component_value.items():
                        assign_property(gltf.vnodes, blender_component,
                                        property_name, property_value)

            except Exception:
                print("Error encountered while adding Hubs components:")
                traceback.print_exc()
                print("Continuing on....\n")


def create_material_hubs_components(gltf):
    special_cases = {
        # 'video-texture-target': handle_video_texture_target,
    }

    for glb_material in stored_components['material'].values():
        MOZ_hubs_components = glb_material.extensions['MOZ_hubs_components']

        for glb_component_name, glb_component_value in MOZ_hubs_components.items():
            try:
                if glb_component_name in special_cases.keys():
                    special_cases[glb_component_name](
                        gltf, glb_material, glb_component_name, glb_component_value)
                    continue

                else:
                    blender_component = add_hubs_component(
                        "material", glb_component_name, glb_component_value, glb_material=glb_material)

                    for property_name, property_value in glb_component_value.items():
                        assign_property(gltf.vnodes, blender_component,
                                        property_name, property_value)

            except Exception:
                print("Error encountered while adding Hubs components:")
                traceback.print_exc()
                print("Continuing on....\n")


def create_scene_hubs_components(gltf):
    if gltf.data.scene is None:
        return

    special_cases = {
        'environment-settings': handle_environment_settings,
        'background': handle_background,
    }

    gltf_scene = gltf.data.scenes[gltf.data.scene]
    extensions = gltf_scene.extensions
    if extensions:
        MOZ_hubs_components = extensions.get('MOZ_hubs_components')
        if MOZ_hubs_components:
            for glb_component_name, glb_component_value in MOZ_hubs_components.items():
                try:
                    if glb_component_name in special_cases.keys():
                        special_cases[glb_component_name](
                            gltf, glb_component_name, glb_component_value)
                        continue

                    blender_component = add_hubs_component(
                        "scene", glb_component_name, glb_component_value, gltf=gltf)

                    for property_name, property_value in glb_component_value.items():
                        assign_property(gltf.vnodes, blender_component,
                                        property_name, property_value)

                except Exception:
                    print("Error encountered while adding Hubs components:")
                    traceback.print_exc()
                    print("Continuing on....\n")


# OBJECT SPECIAL CASES
def handle_networked(gltf, vnode, node, glb_component_name, glb_component_value):
    return


def handle_audio_target(gltf, vnode, node, glb_component_name, glb_component_value):
    blender_component = add_hubs_component(
        "object", glb_component_name, glb_component_value, vnode=vnode, node=node)

    for property_name, property_value in glb_component_value.items():
        if property_name == 'srcNode':
            setattr(blender_component, property_name,
                    gltf.vnodes[property_value['index']].blender_object)

        else:
            print(f"{property_name} = {property_value}")
            setattr(blender_component, property_name, property_value)


def handle_spawn_point(gltf, vnode, node, glb_component_name, glb_component_value):
    blender_component = add_hubs_component(
        "object", "waypoint", glb_component_value, vnode=vnode, node=node)

    blender_component.canBeSpawnPoint = True


def handle_heightfield(gltf, vnode, node, glb_component_name, glb_component_value):
    return


def handle_box_collider(gltf, vnode, node, glb_component_name, glb_component_value):
    blender_component = add_hubs_component(
        "object", "ammo-shape", glb_component_value, vnode=vnode, node=node)

    blender_component.type = "box"


def handle_scene_preview_camera(gltf, vnode, node, glb_component_name, glb_component_value):
    return


def handle_trimesh(gltf, vnode, node, glb_component_name, glb_component_value):
    return


def handle_spawner(gltf, vnode, node, glb_component_name, glb_component_value):
    blender_component = add_hubs_component(
        "object", glb_component_name, glb_component_value, vnode=vnode, node=node)

    for property_name, property_value in glb_component_value.items():
        if property_name == 'mediaOptions':
            setattr(blender_component, "applyGravity",
                    property_value["applyGravity"])

        else:
            assign_property(gltf.vnodes, blender_component,
                            property_name, property_value)


def handle_loop_animation(gltf, vnode, node, glb_component_name, glb_component_value):
    blender_component = add_hubs_component(
        "object", glb_component_name, glb_component_value, vnode=vnode, node=node)

    for property_name, property_value in glb_component_value.items():
        if property_name == 'clip':
            tracks = property_value.split(",")
            for track_name in tracks:
                if not has_track(blender_component.tracks_list, track_name):
                    track = blender_component.tracks_list.add()
                    track.name = track_name.strip()

        else:
            assign_property(gltf.vnodes, blender_component,
                            property_name, property_value)


# MATERIAL SPECIAL CASES
def handle_video_texture_target(gltf, glb_material, glb_component_name, glb_component_value):
    blender_component = add_hubs_component(
        "material", glb_component_name, glb_component_value, glb_material=glb_material)

    for property_name, property_value in glb_component_value.items():
        if property_name == 'srcNode':
            setattr(blender_component, property_name,
                    gltf.vnodes[property_value['index']].blender_object)

        else:
            print(f"{property_name} = {property_value}")
            setattr(blender_component, property_name, property_value)


# SCENE SPECIAL CASES
def handle_environment_settings(gltf, glb_component_name, glb_component_value):
    blender_component = add_hubs_component(
        "scene", glb_component_name, glb_component_value, gltf=gltf)

    # load environment maps
    enviro_imgs = {}
    for gltf_texture in gltf.data.textures:
        extensions = gltf_texture.extensions
        if extensions:
            MOZ_texture_rgbe = extensions.get('MOZ_texture_rgbe')
            if MOZ_texture_rgbe:
                BlenderImage.create(gltf, MOZ_texture_rgbe['source'])
                pyimg = gltf.data.images[MOZ_texture_rgbe['source']]
                blender_image_name = pyimg.blender_image_name
                enviro_imgs[MOZ_texture_rgbe['source']] = blender_image_name

    for property_name, property_value in glb_component_value.items():
        if isinstance(property_value, dict) and property_value['__mhc_link_type'] == "texture":
            blender_image_name = enviro_imgs[property_value['index']]
            blender_image = bpy.data.images[blender_image_name]

            setattr(blender_component, property_name, blender_image)

        else:
            assign_property(gltf.vnodes, blender_component,
                            property_name, property_value)


def handle_background(gltf, glb_component_name, glb_component_value):
    blender_component = add_hubs_component(
        "scene", "environment-settings", glb_component_value, gltf=gltf)

    blender_component.toneMapping = "LinearToneMapping"

    set_color_from_hex(blender_component, "backgroundColor",
                       glb_component_value['color'])


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
