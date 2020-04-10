import os
import datetime
import re
import bpy
from io_scene_gltf2.blender.exp import gltf2_blender_gather_materials
from io_scene_gltf2.blender.com import gltf2_blender_extras

def gather_properties(export_settings, blender_object, target, type_definition, hubs_config):
    value = {}

    for property_name, property_definition in type_definition['properties'].items():
        value[property_name] = gather_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)

    return value

def gather_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    property_type = property_definition['type']

    if property_type == 'material':
        return gather_material_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
    elif property_type == 'collections':
        return gather_collections_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
    elif property_type == 'array':
        return gather_array_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
    else:
        return gltf2_blender_extras.__to_json_compatible(getattr(target, property_name))

def gather_array_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    array_type = property_definition['arrayType']
    print(array_type)
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
