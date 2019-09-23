import os
import datetime
import re
import bpy
from io_scene_gltf2.blender.exp import gltf2_blender_gather, gltf2_blender_gather_nodes
from io_scene_gltf2.blender.exp import gltf2_blender_gather, gltf2_blender_gather_nodes
from io_scene_gltf2.blender.exp.gltf2_blender_gltf2_exporter import GlTF2Exporter
from io_scene_gltf2.io.exp import gltf2_io_export
from io_scene_gltf2.io.com import gltf2_io_extensions
from io_scene_gltf2.blender.com import gltf2_blender_json
from . import components

def is_empty_collection(value):
    return isinstance(value, (dict, list)) and len(value) == 0

def should_include_json_value(key, value):
    allowed_empty_collections = ["KHR_materials_unlit"]

    if value is None:
        return False
    if is_empty_collection(value) and key not in allowed_empty_collections:
        return False
    return True

def fix_json(obj):
    fixed = obj
    if isinstance(obj, dict):
        fixed = {}
        for key, value in obj.items():
            if not should_include_json_value(key, value):
                continue
            fixed[key] = fix_json(value)
    elif isinstance(obj, list):
        fixed = []
        for value in obj:
            fixed.append(fix_json(value))
    elif isinstance(obj, float):
        # force floats to int, if they are integers
        # (prevent INTEGER_WRITTEN_AS_FLOAT validator warnings)
        if int(obj) == obj:
            return int(obj)
    return fixed

original_gather_extensions = gltf2_blender_gather_nodes.__gather_extensions

def __to_json_compatible(value):
    """Make a value (usually a custom property) compatible with json"""

    if isinstance(value, bpy.types.ID):
        return value

    elif isinstance(value, str):
        return value

    elif isinstance(value, (int, float)):
        return value

    elif isinstance(value, bpy.types.bpy_prop_collection):
        value = list(value)
        # make sure contents are json-compatible too
        for index in range(len(value)):
            value[index] = __to_json_compatible(value[index])
        return value

    elif isinstance(value, components.StringArrayValueProperty):
        return value.value

    # for list classes
    elif isinstance(value, list):
        value = list(value)
        # make sure contents are json-compatible too
        for index in range(len(value)):
            value[index] = __to_json_compatible(value[index])
        return value

    # for IDPropertyArray classes
    elif hasattr(value, "to_list"):
        value = value.to_list()
        return value

    elif hasattr(value, "to_dict"):
        value = value.to_dict()
        if gltf2_blender_json.is_json_convertible(value):
            return value

    return None

def patched_gather_extensions(blender_object, export_settings):
    extensions = original_gather_extensions(blender_object, export_settings)

    component_list = blender_object.hubs_component_list
    hubs_config = export_settings['hubs_config']
    registered_hubs_components = export_settings['registered_hubs_components']

    if component_list.items:
        extension_name = hubs_config["gltfExtensionName"]
        component_data = {}

        for component_item in component_list.items:
            component_name = component_item.name
            component_data[component_name] = {}
            component_definition = hubs_config['components'][component_name]
            component_class = registered_hubs_components[component_name]
            component_class_name = component_class.__name__
            component = getattr(blender_object, component_class_name)

            for property_name, property_definition in component_definition['properties'].items():
                property_type = property_definition['type']

                if property_type == 'collections':
                    filtered_collection_names = []

                    collection_prefix_regex = None

                    if 'collectionPrefix' in property_definition:
                        collection_prefix = property_definition['collectionPrefix']
                        collection_prefix_regex = re.compile(r'^' + collection_prefix)

                    for collection in blender_object.users_collection:
                        if collection_prefix_regex and collection_prefix_regex.match(collection.name):
                            new_name = collection_prefix_regex.sub("", collection.name)
                            filtered_collection_names.append(new_name)
                        elif not collection_prefix_regex:
                            filtered_collection_names.append(collection.name)

                    component_data[component_name][property_name] = filtered_collection_names
                else:
                    component_data[component_name][property_name] = __to_json_compatible(
                        getattr(component, property_name)
                    )

        if extensions is None:
            extensions = {}

        extensions[extension_name] = gltf2_io_extensions.Extension(
            name=extension_name,
            extension=component_data,
            required=False
        )

    return extensions if extensions else None

def export(blender_scene, selected, hubs_config, registered_hubs_components):
    if bpy.data.filepath == '':
        raise RuntimeError("Save project before exporting")

    filepath = bpy.data.filepath.replace('.blend', '')
    filename_ext = '.glb'

    export_settings = {}
    export_settings['timestamp'] = datetime.datetime.now()
    export_settings['gltf_filepath'] = bpy.path.ensure_ext(filepath, filename_ext)

    if os.path.exists(export_settings['gltf_filepath']):
        os.remove(export_settings['gltf_filepath'])

    export_settings['gltf_filedirectory'] = os.path.dirname(
        export_settings['gltf_filepath']) + '/'
    export_settings['gltf_format'] = 'GLB'
    export_settings['gltf_image_format'] = 'NAME'
    export_settings['gltf_copyright'] = ''
    export_settings['gltf_texcoords'] = True
    export_settings['gltf_normals'] = True
    export_settings['gltf_tangents'] = False
    export_settings['gltf_draco_mesh_compression'] = False
    export_settings['gltf_materials'] = True
    export_settings['gltf_colors'] = True
    export_settings['gltf_cameras'] = False
    export_settings['gltf_selected'] = selected
    export_settings['gltf_layers'] = True
    export_settings['gltf_extras'] = False
    export_settings['gltf_yup'] = True
    export_settings['gltf_apply'] = False
    export_settings['gltf_current_frame'] = False
    export_settings['gltf_animations'] = False
    export_settings['gltf_frame_range'] = False
    export_settings['gltf_move_keyframes'] = False
    export_settings['gltf_force_sampling'] = False
    export_settings['gltf_skins'] = False
    export_settings['gltf_all_vertex_influences'] = False
    export_settings['gltf_frame_step'] = 1
    export_settings['gltf_morph'] = False
    export_settings['gltf_morph_normal'] = False
    export_settings['gltf_morph_tangent'] = False
    export_settings['gltf_lights'] = False
    export_settings['gltf_displacement'] = False
    export_settings['gltf_binary'] = bytearray()
    export_settings['gltf_binaryfilename'] = os.path.splitext(
        os.path.basename(bpy.path.ensure_ext(filepath, filename_ext)))[0] + '.bin'

    export_settings['hubs_config'] = hubs_config
    export_settings['registered_hubs_components'] = registered_hubs_components

    gltf2_blender_gather_nodes.__gather_extensions = patched_gather_extensions

    # In most recent version this function will return active_scene
    # as the first value for a total of 3 return values
    scenes, _animations = gltf2_blender_gather.gather_gltf2(export_settings)

    for gltf_scene in scenes:
        gltf_scene.extensions = patched_gather_extensions(blender_scene, export_settings)

    exporter = GlTF2Exporter(export_settings['gltf_copyright'])
    exporter.add_scene(scenes[0], True)
    buffer = exporter.finalize_buffer(export_settings['gltf_filedirectory'], is_glb=True)
    exporter.finalize_images(export_settings['gltf_filedirectory'])

    gltf_json = fix_json(exporter.glTF.to_dict())

    extension_name = hubs_config["gltfExtensionName"]

    if 'extensionsRequired' in gltf_json:
        gltf_json['extensionsRequired'].remove(extension_name)
        if not gltf_json['extensionsRequired']:
            del gltf_json['extensionsRequired']

    if 'extensionsUsed' not in gltf_json:
        gltf_json['extensionsUsed'] = [extension_name]
    elif extension_name not in gltf_json['extensionsUsed']:
        gltf_json['extensionsUsed'].append(extension_name)


    if 'extensions' not in gltf_json:
        gltf_json['extensions'] = {}

    gltf_json['extensions'][extension_name] = {
        "version": hubs_config["gltfExtensionVersion"]
    }

    gltf2_io_export.save_gltf(
        gltf_json,
        export_settings,
        gltf2_blender_json.BlenderJSONEncoder,
        buffer
    )

    gltf2_blender_gather_nodes.__gather_extensions = original_gather_extensions

    return export_settings['gltf_filepath']
