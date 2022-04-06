import bpy
import traceback
import re
from io_scene_gltf2.blender.imp.gltf2_blender_node import BlenderNode
from io_scene_gltf2.blender.imp.gltf2_blender_material import BlenderMaterial
from io_scene_gltf2.blender.imp.gltf2_blender_scene import BlenderScene
from io_scene_gltf2.blender.imp.gltf2_blender_image import BlenderImage

# import hooks are not present, make a custom hook for now
# ideally we can resolve this upstream somehow https://github.com/KhronosGroup/glTF-Blender-IO
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
    orig_BlenderScene_create(gltf)

    create_object_hubs_components(gltf)
    create_material_hubs_components(gltf)
    create_scene_hubs_components(gltf)


def create_object_hubs_components(gltf):
    special_cases = {
        'networked': handle_networked,
        'audio-target': handle_audio_target,
        'kit-alt-materials': handle_kit_alt_materials,
    }

    for vnode, node in stored_components['object'].values():
        MOZ_hubs_components = node.extensions['MOZ_hubs_components']
        for glb_component_name, glb_component_value in MOZ_hubs_components.items():
            try:
                if glb_component_name in special_cases.keys():
                    special_cases[glb_component_name](gltf, vnode, node, glb_component_name, glb_component_value)
                    continue

                else:
                    blender_component = add_hubs_component("object", glb_component_name, glb_component_value, vnode=vnode, node=node)

                    for property_name, property_value in glb_component_value.items():
                        if isinstance(property_value, dict):
                            blender_subcomponent = getattr(blender_component, property_name)
                            for x, subproperty_value in enumerate(property_value.values()):
                                print(f"{property_name}[{x}] = {subproperty_value}")
                                blender_subcomponent[x] = subproperty_value

                        else:
                            if re.fullmatch("#[0-9a-fA-F]*", str(property_value)):
                                hexcolor = property_value.lstrip('#')
                                rgb_int = tuple(int(hexcolor[i:i+2], 16) for i in (0, 2, 4))
                                rgb_float = tuple((i/255 for i in rgb_int))

                                for x, value in enumerate(rgb_float):
                                    print(f"{property_name}[{x}] = {value}")
                                    getattr(blender_component, property_name)[x] = value

                            else:
                                print(f"{property_name} = {property_value}")
                                setattr(blender_component, property_name, property_value)

            except Exception:
                print("Error encountered while adding Hubs components:")
                traceback.print_exc()
                print("Continuing on....\n")

def create_material_hubs_components(gltf):
    special_cases = {
        'video-texture-target': handle_video_texture_target,
    }

    for glb_material in stored_components['material'].values():
        MOZ_hubs_components = glb_material.extensions['MOZ_hubs_components']

        for glb_component_name, glb_component_value in MOZ_hubs_components.items():
            try:
                if glb_component_name in special_cases.keys():
                    special_cases[glb_component_name](gltf, glb_material, glb_component_name, glb_component_value)
                    continue

                else:
                    blender_component = add_hubs_component("material", glb_component_name, glb_component_value, glb_material=glb_material)

                    for property_name, property_value in glb_component_value.items():
                        print(f"{property_name} = {property_value}")
                        setattr(blender_component, property_name, property_value)


            except Exception:
                print("Error encountered while adding Hubs components:")
                traceback.print_exc()
                print("Continuing on....\n")

def create_scene_hubs_components(gltf):
    if gltf.data.scene is None:
        return

    special_cases = {
        'environment-settings': handle_environment_settings,
    }

    gltf_scene = gltf.data.scenes[gltf.data.scene]
    extensions = gltf_scene.extensions
    if extensions:
        MOZ_hubs_components = extensions.get('MOZ_hubs_components')
        if MOZ_hubs_components:
            for glb_component_name, glb_component_value in MOZ_hubs_components.items():
                try:
                    if glb_component_name in special_cases.keys():
                        special_cases[glb_component_name](gltf, glb_component_name, glb_component_value)
                        continue

                    blender_component = add_hubs_component("scene", glb_component_name, glb_component_value, gltf=gltf)

                    for property_name, property_value in glb_component_value.items():
                        if re.fullmatch("#[0-9a-fA-F]*", str(property_value)):
                            hexcolor = property_value.lstrip('#')
                            rgb_int = tuple(int(hexcolor[i:i+2], 16) for i in (0, 2, 4))
                            rgb_float = tuple((i/255 for i in rgb_int))

                            for x, value in enumerate(rgb_float):
                                print(f"{property_name}[{x}] = {value}")
                                getattr(blender_component, property_name)[x] = value

                        else:
                            print(f"{property_name} = {property_value}")
                            setattr(blender_component, property_name, property_value)

                except Exception:
                    print("Error encountered while adding Hubs components:")
                    traceback.print_exc()
                    print("Continuing on....\n")

# OBJECT SPECIAL CASES
def handle_networked(gltf, vnode, node, glb_component_name, glb_component_value):
    return

def handle_audio_target(gltf, vnode, node, glb_component_name, glb_component_value):
    blender_component = add_hubs_component("object", glb_component_name, glb_component_value, vnode=vnode, node=node)

    for property_name, property_value in glb_component_value.items():
        if property_name == 'srcNode':
            setattr(blender_component, property_name, gltf.vnodes[property_value['index']].blender_object)

        else:
            print(f"{property_name} = {property_value}")
            setattr(blender_component, property_name, property_value)

def handle_kit_alt_materials(gltf, vnode, node, glb_component_name, glb_component_value):
    blender_component = add_hubs_component("object", glb_component_name, glb_component_value, vnode=vnode, node=node)

    for property_name, property_value in glb_component_value.items():
        if property_name == 'defaultMaterials':
            for x, glb_defaultMaterial in enumerate(property_value):
                bpy.ops.wm.add_hubs_component_item(context_override, path="object.hubs_component_kit_alt_materials.defaultMaterials")

                for subproperty_name, subproperty_value in glb_defaultMaterial.items():
                    if subproperty_name == 'material':
                        setattr(blender_component.defaultMaterials[x], 'material', bpy.data.materials[gltf.data.materials[subproperty_value].name])

                    else:
                        setattr(blender_component.defaultMaterials[x], subproperty_name, subproperty_value)

        elif property_name == 'altMaterials':
            for x, glb_altMaterial in enumerate(property_value):
                bpy.ops.wm.add_hubs_component_item(context_override, path="object.hubs_component_kit_alt_materials.altMaterials")
                altMaterial_component = blender_component.altMaterials[x]

                for y, glb_sub_altMaterial_index in enumerate(glb_altMaterial):
                    bpy.ops.wm.add_hubs_component_item(context_override, path=f"object.hubs_component_kit_alt_materials.altMaterials.0.value")
                    altMaterial_component.value[y].value = bpy.data.materials[gltf.data.materials[glb_sub_altMaterial_index].name]

        else:
            setattr(blender_component, property_name, property_value)

# MATERIAL SPECIAL CASES
def handle_video_texture_target(gltf, glb_material, glb_component_name, glb_component_value):
    blender_component = add_hubs_component("material", glb_component_name, glb_component_value, glb_material=glb_material)

    for property_name, property_value in glb_component_value.items():
        if property_name == 'srcNode':
            setattr(blender_component, property_name, gltf.vnodes[property_value['index']].blender_object)

        else:
            print(f"{property_name} = {property_value}")
            setattr(blender_component, property_name, property_value)

# SCENE SPECIAL CASES
def handle_environment_settings(gltf, glb_component_name, glb_component_value):
    blender_component = add_hubs_component("scene", glb_component_name, glb_component_value, gltf=gltf)

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
            if re.fullmatch("#[0-9a-fA-F]*", str(property_value)):
                hexcolor = property_value.lstrip('#')
                rgb_int = tuple(int(hexcolor[i:i+2], 16) for i in (0, 2, 4))
                rgb_float = tuple((i/255 for i in rgb_int))

                for x, value in enumerate(rgb_float):
                    print(f"{property_name}[{x}] = {value}")
                    getattr(blender_component, property_name)[x] = value

            else:
                print(f"{property_name} = {property_value}")
                setattr(blender_component, property_name, property_value)

def add_hubs_component(element_type, glb_component_name, glb_component_value, vnode=None, node=None, glb_material=None, gltf=None):
    # get element
    if element_type == "object":
        element = vnode.blender_object

    elif element_type == "material":
        element = bpy.data.materials[glb_material.blender_material[None]]

    elif element_type == "scene":
        element = bpy.data.scenes[gltf.blender_scene]

    else:
        element = None

    # print debug info
    if element_type == "object":
        print(f"Node Name: {node.name}")
        print(f"Object: {element}")

    print(f"Hubs Component Name: {glb_component_name}")
    print(f"Hubs Component Value: {glb_component_value}")


    # override context
    context_override = bpy.context.copy()
    context_override[element_type] = element

    # create component
    bpy.ops.wm.add_hubs_component(context_override, object_source=element_type, component_name=glb_component_name)

    return getattr(element, f"hubs_component_{glb_component_name.replace('-', '_')}")

def register():
    BlenderNode.create_object = patched_BlenderNode_create_object
    BlenderMaterial.create = patched_BlenderMaterial_create
    BlenderScene.create = patched_BlenderScene_create

def unregister():
    BlenderNode.create_object = orig_BlenderNode_create_object
    BlenderMaterial.create = orig_BlenderMaterial_create
    BlenderScene.create = orig_BlenderScene_create
