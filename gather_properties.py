import os
import datetime
import re
import bpy
from io_scene_gltf2.blender.exp import gltf2_blender_gather_materials, gltf2_blender_gather_image, gltf2_blender_gather_nodes
from io_scene_gltf2.blender.exp.gltf2_blender_image import ExportImage
from io_scene_gltf2.blender.com import gltf2_blender_extras
from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
from io_scene_gltf2.blender.exp.gltf2_blender_gather_texture_info import gather_texture_info
from .nodes import MozLightmapNode

def gather_properties(export_settings, blender_object, target, type_definition, hubs_config):
    value = {}

    for property_name, property_definition in type_definition['properties'].items():
        value[property_name] = gather_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)

    if value:
        return value
    else:
        return { "__empty_component_dummy": None }

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
    elif property_type == 'nodeRef':
        return gather_node_property(export_settings, blender_object, target, property_name, property_definition, hubs_config)
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

def gather_node_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    blender_object = getattr(target, property_name)

    if blender_object:
        return gltf2_blender_gather_nodes.gather_node(
            blender_object,
            blender_object.library.name if blender_object.library else None,
            blender_object.users_scene[0],
            None,
            export_settings
        )
    else:
        return None

def gather_material_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    blender_material = getattr(target, property_name)

    if blender_material:
        material = gltf2_blender_gather_materials.gather_material(
            blender_material, export_settings)
        return material
    else:
        return None

def gather_vec_property(export_settings, blender_object, target, property_name, property_definition, hubs_config):
    vec = getattr(target, property_name)

    if property_definition.get("unit") == "PIXEL":
        out = [vec[0], vec[1]]
    else:
        out = {
            "x": vec[0],
            "y": vec[1],
        }

        if len(vec) > 2:
            out["z"] = vec[2]
        if len(vec) > 3:
            out["w"] = vec[3]

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

# @cached
def gather_lightmap_texture_info(blender_material, export_settings):
    nodes = blender_material.node_tree.nodes
    lightmap_node = next((n for n in nodes if isinstance(n, MozLightmapNode)), None)

    if not lightmap_node: return

    texture_socket = lightmap_node.inputs.get("Lightmap")
    intensity = lightmap_node.intensity

    print("gather_lightmap")

    texture_info = gather_hdr_texture_info(texture_socket, (texture_socket,), export_settings)
    if not texture_info: return

    return {
        "intensity": intensity,
        'extensions': texture_info.extensions,
        'extras': texture_info.extras,
        "index": texture_info.index,
        "texCoord": texture_info.tex_coord
    }


from io_scene_gltf2.blender.exp import gltf2_blender_gather_texture_info, gltf2_blender_gather_texture, gltf2_blender_export_keys
from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
from io_scene_gltf2.io.exp import gltf2_io_binary_data, gltf2_io_image_data
from io_scene_gltf2.io.com import gltf2_io

# TODO this should allow conversion from other HDR formats (namely EXR), and in memory images
def __encode_from_image(image: bpy.types.Image) -> bytes:
    if image.source == 'FILE' and image.file_format == "HDR" and not image.is_dirty:
        if image.packed_file is not None:
            return image.packed_file.data
        else:
            src_path = bpy.path.abspath(image.filepath_raw)
            if os.path.isfile(src_path):
                with open(src_path, 'rb') as f:
                    return f.read()

    raise Exception("You must save your lightmap as a .hdr image.")

def gather_hdr_texture_info(primary_socket, blender_shader_sockets, export_settings):
    # TODO this assumes a single image directly connected to the socket
    blender_image = primary_socket.links[0].from_node.image
    is_hdr = blender_image.file_format == "HDR"
    texture_extensions = {}

    if is_hdr:
        mime_type = "image/vnd.radiance"
        data = __encode_from_image(blender_image)
        name, _extension = os.path.splitext(os.path.basename(blender_image.filepath))

        buffer_view = None
        uri = None
        if export_settings[gltf2_blender_export_keys.FORMAT] == 'GLTF_SEPARATE':
            uri = gltf2_io_image_data.ImageData(data=data, mime_type=mime_type, name=name)
        else:
            buffer_view = gltf2_io_binary_data.BinaryData(data=data)

        image = gltf2_io.Image(
            buffer_view=buffer_view,
            extensions=None,
            extras=None,
            mime_type=mime_type,
            name=name,
            uri=uri
        )

        ext_name = "MOZ_texture_rgbe"
        texture_extensions[ext_name] = Extension(
            name=ext_name,
            extension={
                "source": image
            },
            required=False
        )

    texture = gltf2_io.Texture(
        extensions=texture_extensions,
        extras=None,
        name=None,
        sampler=gltf2_blender_gather_texture.__gather_sampler(blender_shader_sockets, export_settings),
        source=None if is_hdr else gltf2_blender_gather_texture.__gather_source(blender_shader_sockets, export_settings)
    )

    # export_user_extensions('gather_texture_hook', export_settings, texture, blender_shader_sockets)

    tex_transform, tex_coord = gltf2_blender_gather_texture_info.__gather_texture_transform_and_tex_coord(primary_socket, export_settings)
    return gltf2_io.TextureInfo(
        extensions=gltf2_blender_gather_texture_info.__gather_extensions(tex_transform, export_settings),
        extras=None,
        index=texture,
        tex_coord=tex_coord
    )
