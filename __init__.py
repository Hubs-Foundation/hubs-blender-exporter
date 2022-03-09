import bpy
import uuid
import traceback
import re

from . import settings
from . import components
from . import operators
from . import panels
from . import nodes
from .gather_properties import gather_properties, gather_lightmap_texture_info

bl_info = {
    "name" : "Hubs Blender Exporter",
    "author" : "MozillaReality",
    "description" : "Tools for developing GLTF assets for Mozilla Hubs",
    "blender" : (2, 93, 4),
    "version" : (0, 0, 15),
    "location" : "",
    "wiki_url": "https://github.com/MozillaReality/hubs-blender-exporter",
    "tracker_url": "https://github.com/MozillaReality/hubs-blender-exporter/issues",
    "support": "COMMUNITY",
    "warning" : "",
    "category" : "Generic"
}

def get_version_string():
    return str(bl_info['version'][0]) + '.' + str(bl_info['version'][1]) + '.' + str(bl_info['version'][2])

# gather_gltf_hook does not expose the info we need, make a custom hook for now
# ideally we can resolve this upstream somehow https://github.com/KhronosGroup/glTF-Blender-IO/issues/1009
from io_scene_gltf2.blender.exp import gltf2_blender_export
from io_scene_gltf2.io.exp.gltf2_io_user_extensions import export_user_extensions
from io_scene_gltf2.blender.imp.gltf2_blender_node import BlenderNode
from io_scene_gltf2.blender.imp.gltf2_blender_material import BlenderMaterial
from io_scene_gltf2.blender.imp.gltf2_blender_scene import BlenderScene
from io_scene_gltf2.blender.imp.gltf2_blender_image import BlenderImage
orig_gather_gltf = gltf2_blender_export.__gather_gltf
orig_BlenderNode_create_object = BlenderNode.create_object
orig_BlenderMaterial_create = BlenderMaterial.create
orig_BlenderScene_create = BlenderScene.create

stored_components = {'object': {}, 'material': {}}

def patched_gather_gltf(exporter, export_settings):
    orig_gather_gltf(exporter, export_settings)
    export_user_extensions('hubs_gather_gltf_hook', export_settings, exporter._GlTF2Exporter__gltf)
    exporter._GlTF2Exporter__traverse(exporter._GlTF2Exporter__gltf.extensions)

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
    create_object_components(gltf)
    create_material_components(gltf)
    create_scene_components(gltf)

def create_object_components(gltf):
    for vnode, node in stored_components['object'].values():
        MOZ_hubs_components = node.extensions['MOZ_hubs_components']
        for glb_component_name, glb_component_value in MOZ_hubs_components.items():
            if glb_component_name == 'networked':
                continue

            try:
                # ADD MAIN HUBS COMPONENT
                obj = vnode.blender_object

                print(f"Node Name: {node.name}")
                print(f"Object: {obj}")
                print(f"Hubs Component Name: {glb_component_name}")
                print(f"Hubs Component Value: {glb_component_value}")

                context_override = bpy.context.copy()
                context_override['object'] = obj

                bpy.ops.wm.add_hubs_component(context_override, object_source="object", component_name=glb_component_name)

                blender_component = getattr(obj, f"hubs_component_{glb_component_name.replace('-', '_')}")

                # AUDIO TARGET HUBS COMPONENT BEGIN
                if glb_component_name == 'audio-target':
                    for property_name, property_value in glb_component_value.items():

                        if property_name == 'srcNode':
                            setattr(blender_component, property_name, gltf.vnodes[property_value['index']].blender_object)

                        else:
                            print(f"{property_name} = {property_value}")
                            setattr(blender_component, property_name, property_value)
                # AUDIO TARGET HUBS COMPONENT END

                # KIT ALT MATERIALS BEGIN
                elif glb_component_name == 'kit-alt-materials':
                    #print(gltf.data.materials[0].name)
                    for property_name, property_value in glb_component_value.items():

                        # DEFAULT MATERIALS BEGIN
                        if property_name == 'defaultMaterials':
                            for x, glb_defaultMaterial in enumerate(property_value):
                                bpy.ops.wm.add_hubs_component_item(context_override, path="object.hubs_component_kit_alt_materials.defaultMaterials")

                                for subproperty_name, subproperty_value in glb_defaultMaterial.items():
                                    if subproperty_name == 'material':
                                        setattr(blender_component.defaultMaterials[x], 'material', bpy.data.materials[gltf.data.materials[subproperty_value].name])

                                    else:
                                        setattr(blender_component.defaultMaterials[x], subproperty_name, subproperty_value)
                        # DEFAULT MATERIALS END

                        # ALT MATERIALS BEGIN
                        elif property_name == 'altMaterials':
                            for x, glb_altMaterial in enumerate(property_value):
                                bpy.ops.wm.add_hubs_component_item(context_override, path="object.hubs_component_kit_alt_materials.altMaterials")
                                altMaterial_component = blender_component.altMaterials[x]

                                for y, glb_sub_altMaterial_index in enumerate(glb_altMaterial):
                                    bpy.ops.wm.add_hubs_component_item(context_override, path=f"object.hubs_component_kit_alt_materials.altMaterials.0.value")
                                    altMaterial_component.value[y].value = bpy.data.materials[gltf.data.materials[glb_sub_altMaterial_index].name]

                        else:
                            setattr(blender_component, property_name, property_value)
                        # ALT MATERIALS END

                # KIT ALT MATERIALS END

                else:
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


def create_material_components(gltf):
    for glb_material in stored_components['material'].values():
        MOZ_hubs_components = glb_material.extensions['MOZ_hubs_components']

        for glb_component_name, glb_component_value in MOZ_hubs_components.items():
            print(f"Hubs Component Name: {glb_component_name}")
            print(f"Hubs Component Value: {glb_component_value}")

            try:
                # ADD MAIN HUBS COMPONENT
                material = bpy.data.materials[glb_material.blender_material[None]]

                context_override = bpy.context.copy()
                context_override['material'] = material

                bpy.ops.wm.add_hubs_component(context_override, object_source="material", component_name=glb_component_name)

                blender_component = getattr(material, f"hubs_component_{glb_component_name.replace('-', '_')}")


                if glb_component_name == 'video-texture-target':
                    for property_name, property_value in glb_component_value.items():

                        if property_name == 'srcNode':
                            setattr(blender_component, property_name, gltf.vnodes[property_value['index']].blender_object)

                        else:
                            print(f"{property_name} = {property_value}")
                            setattr(blender_component, property_name, property_value)

            except Exception:
                print("Error encountered while adding Hubs components:")
                traceback.print_exc()
                print("Continuing on....\n")

def create_scene_components(gltf):
    if gltf.data.scene is None:
        return

    gltf_scene = gltf.data.scenes[gltf.data.scene]
    extensions = gltf_scene.extensions
    if extensions:
        MOZ_hubs_components = extensions.get('MOZ_hubs_components')
        if MOZ_hubs_components:
            enviro_imgs = {}

            for glb_component_name, glb_component_value in MOZ_hubs_components.items():
                print(f"Hubs Component Name: {glb_component_name}")
                print(f"Hubs Component Value: {glb_component_value}")

                if glb_component_name == "environment-settings":

                    for gltf_texture in gltf.data.textures:
                        extensions = gltf_texture.extensions
                        if extensions:
                            MOZ_texture_rgbe = extensions.get('MOZ_texture_rgbe')
                            if MOZ_texture_rgbe:
                                BlenderImage.create(gltf, MOZ_texture_rgbe['source'])
                                pyimg = gltf.data.images[MOZ_texture_rgbe['source']]
                                blender_image_name = pyimg.blender_image_name
                                enviro_imgs[MOZ_texture_rgbe['source']] = blender_image_name


                try:
                    # ADD MAIN HUBS COMPONENT
                    scene = bpy.data.scenes[gltf.blender_scene]
                    bpy.ops.wm.add_hubs_component(object_source="scene", component_name=glb_component_name)
                    blender_component = getattr(scene, f"hubs_component_{glb_component_name.replace('-', '_')}")

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

                except Exception:
                    print("Error encountered while adding Hubs components:")
                    traceback.print_exc()
                    print("Continuing on....\n")

def register():
    gltf2_blender_export.__gather_gltf = patched_gather_gltf
    BlenderNode.create_object = patched_BlenderNode_create_object
    BlenderMaterial.create = patched_BlenderMaterial_create
    BlenderScene.create = patched_BlenderScene_create


    components.register()
    settings.register()
    operators.register()
    panels.register()
    nodes.register()

def unregister():
    gltf2_blender_export.__gather_gltf = orig_gather_gltf
    BlenderNode.create_object = orig_BlenderNode_create_object
    BlenderMaterial.create = orig_BlenderMaterial_create
    BlenderScene.create = orig_BlenderScene_create

    components.unregister()
    settings.unregister()
    operators.unregister()
    panels.unregister()
    nodes.unregister()

    unregister_export_panel()

# called by gltf-blender-io after it has loaded
def register_panel():
    try:
        bpy.utils.register_class(panels.HubsGLTFExportPanel)
    except Exception:
        pass
    return unregister_export_panel

def unregister_export_panel():
    # Since panel is registered on demand, it is possible it is not registered
    try:
        bpy.utils.unregister_class(panels.HubsGLTFExportPanel)
    except Exception:
        pass

# This class name is specifically looked for by gltf-blender-io and it's hooks are automatically invoked on export
class glTF2ExportUserExtension:
    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension

        self.Extension = Extension
        self.properties = bpy.context.scene.HubsComponentsExtensionProperties
        self.hubs_settings = bpy.context.scene.hubs_settings
        self.was_used = False

    def hubs_gather_gltf_hook(self, gltf2_object, export_settings):
        if not self.properties.enabled or not self.was_used: return

        hubs_config = self.hubs_settings.hubs_config
        extension_name = hubs_config["gltfExtensionName"]
        gltf2_object.extensions[extension_name] = self.Extension(
            name=extension_name,
            extension={
                "version": hubs_config["gltfExtensionVersion"],
                "exporterVersion": get_version_string()
            },
            required=False
        )

        if gltf2_object.asset.extras is None:
            gltf2_object.asset.extras = {}
        gltf2_object.asset.extras["HUBS_blenderExporterVersion"] = get_version_string()

    def gather_scene_hook(self, gltf2_object, blender_scene, export_settings):
        if not self.properties.enabled: return

        # Don't include hubs component data again in extras, even if "include custom properties" is enabled
        if gltf2_object.extras:
            for key in list(gltf2_object.extras):
                if key.startswith("hubs_"): del gltf2_object.extras[key]

        self.add_hubs_components(gltf2_object, blender_scene, export_settings)

    def gather_node_hook(self, gltf2_object, blender_object, export_settings):
        if not self.properties.enabled: return

        # Don't include hubs component data again in extras, even if "include custom properties" is enabled
        if gltf2_object.extras:
            for key in list(gltf2_object.extras):
                if key.startswith("hubs_"): del gltf2_object.extras[key]

        self.add_hubs_components(gltf2_object, blender_object, export_settings)

    def gather_material_hook(self, gltf2_object, blender_material, export_settings):
        if not self.properties.enabled: return

        self.add_hubs_components(gltf2_object, blender_material, export_settings)

        if blender_material.node_tree and blender_material.use_nodes:
            lightmap_texture_info = gather_lightmap_texture_info(blender_material, export_settings)
            if lightmap_texture_info:
                gltf2_object.extensions["MOZ_lightmap"] = self.Extension(
                    name="MOZ_lightmap",
                    extension=lightmap_texture_info,
                    required=False,
                )
    def gather_material_unlit_hook(self, gltf2_object, blender_material, export_settings):
        self.gather_material_hook(gltf2_object, blender_material, export_settings)

    def gather_joint_hook(self, gltf2_object, blender_pose_bone, export_settings):
        if not self.properties.enabled: return
        self.add_hubs_components(gltf2_object, blender_pose_bone.bone, export_settings)

    def add_hubs_components(self, gltf2_object, blender_object, export_settings):
        component_list = blender_object.hubs_component_list

        hubs_config = self.hubs_settings.hubs_config
        registered_hubs_components = self.hubs_settings.registered_hubs_components

        if component_list.items:
            extension_name = hubs_config["gltfExtensionName"]
            is_networked = False
            component_data = {}

            for component_item in component_list.items:
                component_name = component_item.name
                component_definition = hubs_config['components'][component_name]
                component_class = registered_hubs_components[component_name]
                component_class_name = component_class.__name__
                component = getattr(blender_object, component_class_name)
                component_data[component_name] = gather_properties(export_settings, blender_object, component, component_definition, hubs_config)
                is_networked |= component_definition.get("networked", False)

            # NAF-supported media require a network ID
            if is_networked:
                component_data["networked"] = {
                    "id" : str(uuid.uuid4()).upper()
                }

            if gltf2_object.extensions is None:
                gltf2_object.extensions = {}
            gltf2_object.extensions[extension_name] = self.Extension(
                name=extension_name,
                extension=component_data,
                required=False
            )

            self.was_used = True
