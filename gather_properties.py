import os
import datetime
import re
import bpy
from io_scene_gltf2.blender.exp import gltf2_blender_gather_materials, gltf2_blender_gather_image
from io_scene_gltf2.blender.exp.gltf2_blender_image import ExportImage
from io_scene_gltf2.blender.com import gltf2_blender_extras
from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
from io_scene_gltf2.blender.exp.gltf2_blender_gather_texture_info import (
    __filter_texture_info,
    __gather_index,
    __gather_tex_coord,
)
from .nodes import MozLightmapNode

def gather_properties(export_settings, blender_object, target, type_definition, hubs_config):
    value = {}

    for property_name, property_definition in type_definition['properties'].items():
        value[property_name] = gather_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)

    return value

def gather_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    property_type = property_definition['type']

    if property_type == 'material':
        return gather_material_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
    elif property_type == 'image':
        return gather_image_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
    elif property_type == 'collections':
        return gather_collections_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
    elif property_type == 'array':
        return gather_array_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
    elif property_type in ['vec2', 'vec3', 'vec4', 'ivec2', 'ivec3', 'ivec4']:
        return gather_vec_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
    elif property_type == 'color':
        return gather_color_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
    else:
        return gltf2_blender_extras.__to_json_compatible(getattr(target, property_name))

def gather_array_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    array_type = property_definition['arrayType']
    type_definition = hubs_config['types'][array_type]
    is_value_type = len(type_definition['properties']) == 1 and 'value' in type_definition['properties']
    value = []

    arr = getattr(target, property_name)

    for item in arr:
        if is_value_type:
            item_value = gather_property(export_settings, blender_object, item, "value", type_definition['properties']['value'], hubs_config)
        else:
            item_value = gather_properties(export_settings, blender_object, item, type_definition, hubs_config)
        value.append(item_value)
    
    return value

def gather_material_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    blender_material = getattr(target, property_name)

    if blender_material:
        double_sided = not blender_material.use_backface_culling
        material = gltf2_blender_gather_materials.gather_material(
            blender_material, double_sided, export_settings)
        return material
    else:
        return None

def gather_vec_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    vec = getattr(target, property_name)

    out = {
        "x": vec[0],
        "y": vec[1],
    }

    if len(vec) > 2:
        out["z"] = vec[2]
    if len(vec) > 3:
        out["w"] = vec[4]

    return out

def gather_image_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    blender_image = getattr(target, property_name)

    if blender_image:
        image_data = ExportImage.from_blender_image(blender_image)
        if image_data.empty():
            return None

        mime_type = gltf2_blender_gather_image.__gather_mime_type((), image_data, export_settings)
        name = gltf2_blender_gather_image.__gather_name(image_data, export_settings)

        uri = gltf2_blender_gather_image.__gather_uri(image_data, mime_type, name, export_settings)
        buffer_view = gltf2_blender_gather_image.__gather_buffer_view(image_data, mime_type, name, export_settings)

        return gltf2_blender_gather_image.__make_image(
            buffer_view,
            None,
            None,
            mime_type,
            name,
            uri,
            export_settings
        )
    else:
        return None

def gather_collections_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
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

    return filtered_collection_names

def gather_color_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    # Convert RGB color array to hex. Blender stores colors in linear space and GLTF color factors are typically in linear space
    c = getattr(target, property_name)
    return "#{0:02x}{1:02x}{2:02x}".format(max(0, min(int(c[0] * 256.0), 255)), max(0, min(int(c[1] * 256.0), 255)), max(0, min(int(c[2] * 256.0), 255)))

@cached
def gather_lightmap_texture_info(blender_material, export_settings):
    nodes = blender_material.node_tree.nodes
    lightmap_node = next((n for n in nodes if isinstance(n, MozLightmapNode)), None)

    if not lightmap_node: return

    texture = lightmap_node.inputs.get("Lightmap")
    intensity = lightmap_node.intensity

    if not __filter_texture_info((texture,), export_settings):
        return None

    texture_info = {
        "intensity": intensity,
        "index": __gather_index((texture,), export_settings),
        "texCoord": __gather_tex_coord((texture,), export_settings)
    }

    if texture_info["index"] is None:
        return None

    return texture_info
