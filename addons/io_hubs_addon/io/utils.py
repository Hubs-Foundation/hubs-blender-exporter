import os
import bpy
from io_scene_gltf2.blender.com import gltf2_blender_extras
if bpy.app.version >= (3, 6, 0):
    from io_scene_gltf2.blender.exp import gltf2_blender_gather_nodes, gltf2_blender_gather_joints
    from io_scene_gltf2.blender.exp.material import gltf2_blender_gather_materials, gltf2_blender_gather_texture_info
    from io_scene_gltf2.blender.exp.material.extensions import gltf2_blender_image
else:
    from io_scene_gltf2.blender.exp import gltf2_blender_gather_materials, gltf2_blender_gather_nodes, gltf2_blender_gather_joints
    from io_scene_gltf2.blender.exp import gltf2_blender_gather_texture_info, gltf2_blender_export_keys
    from io_scene_gltf2.blender.exp import gltf2_blender_image
from io_scene_gltf2.blender.exp.gltf2_blender_gather_cache import cached
if bpy.app.version >= (4, 1, 0):
    from io_scene_gltf2.blender.exp.material import gltf2_blender_search_node_tree
from io_scene_gltf2.io.com import gltf2_io_extensions
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.io.exp import gltf2_io_binary_data
from io_scene_gltf2.io.exp import gltf2_io_image_data
from io_scene_gltf2.blender.imp.gltf2_blender_image import BlenderImage
from typing import Optional, Tuple, Union
from ..nodes.lightmap import MozLightmapNode
import re

HUBS_CONFIG = {
    "gltfExtensionName": "MOZ_hubs_components",
    "gltfExtensionVersion": 4,
}

imported_images = {}

# gather_texture/image with HDR support via MOZ_texture_rgbe


class HubsImageData(gltf2_io_image_data.ImageData):
    @property
    def file_extension(self):
        if self._mime_type == "image/vnd.radiance":
            return ".hdr"
        return super().file_extension


class HubsExportImage(gltf2_blender_image.ExportImage):
    @staticmethod
    def from_blender_image(image: bpy.types.Image):
        export_image = HubsExportImage()
        for chan in range(image.channels):
            export_image.fill_image(image, dst_chan=chan, src_chan=chan)
        return export_image

    def encode(self, mime_type: Optional[str], export_settings) -> Union[Tuple[bytes, bool], bytes]:
        if mime_type == "image/vnd.radiance":
            if bpy.app.version < (4, 1, 0):
                return self.encode_from_image_hdr(self.blender_image())
            else:
                return self.encode_from_image_hdr(self.blender_image(export_settings))
        if bpy.app.version < (3, 5, 0):
            return super().encode(mime_type)
        else:
            return super().encode(mime_type, export_settings)

    # TODO this should allow conversion from other HDR formats (namely EXR),
    # in memory images, and combining separate channels like SDR images
    def encode_from_image_hdr(self, image: bpy.types.Image) -> Union[Tuple[bytes, bool], bytes]:
        if image.file_format == "HDR" and image.source == 'FILE' and not image.is_dirty:
            if image.packed_file is not None:
                return image.packed_file.data
            else:
                src_path = bpy.path.abspath(image.filepath_raw)
                if os.path.isfile(src_path):
                    with open(src_path, 'rb') as f:
                        return f.read()

        raise Exception(
            "HDR images must be saved as a .hdr file before exporting")


@cached
def gather_image(blender_image, export_settings):
    if not blender_image:
        return None

    name, _extension = os.path.splitext(
        os.path.basename(blender_image.filepath))

    if export_settings["gltf_image_format"] == "AUTO":
        if blender_image.file_format == "HDR":
            mime_type = "image/vnd.radiance"
        else:
            mime_type = "image/png"
    else:
        mime_type = "image/jpeg"

    data = HubsExportImage.from_blender_image(blender_image).encode(mime_type, export_settings)

    if type(data) is tuple:
        data = data[0]

    if export_settings['gltf_format'] == 'GLTF_SEPARATE':
        uri = HubsImageData(data=data, mime_type=mime_type, name=name)
        buffer_view = None
    else:
        uri = None
        buffer_view = gltf2_io_binary_data.BinaryData(data=data)

    return gltf2_io.Image(
        buffer_view=buffer_view,
        extensions=None,
        extras=None,
        mime_type=mime_type,
        name=name,
        uri=uri
    )

    # export_user_extensions('gather_image_hook', export_settings, image, blender_shader_sockets)

    return None


@cached
def gather_texture(blender_image, export_settings):
    image = gather_image(blender_image, export_settings)

    if not image:
        return None

    texture_extensions = {}
    is_hdr = blender_image and blender_image.file_format == "HDR"

    if is_hdr:
        ext_name = "MOZ_texture_rgbe"
        texture_extensions[ext_name] = gltf2_io_extensions.Extension(
            name=ext_name,
            extension={
                "source": image
            },
            required=False
        )

    # export_user_extensions('gather_texture_hook', export_settings, texture, blender_shader_sockets)

    return gltf2_io.Texture(
        extensions=texture_extensions,
        extras=None,
        name=None,
        sampler=None,
        source=None if is_hdr else image
    )


def gather_properties(export_settings, object, component):
    value = {}

    for key in component.get_properties():
        value[key] = gather_property(
            export_settings, object, component, key)

    if value:
        return value
    else:
        return {"__empty_component_dummy": None}


def gather_property(export_settings, blender_object, target, property_name):
    property_definition = target.bl_rna.properties[property_name]
    property_value = getattr(target, property_name)
    isArray = getattr(property_definition, 'is_array', None)

    if isArray and property_definition.is_array:
        if property_definition.subtype.startswith('COLOR'):
            return gather_color_property(
                export_settings, blender_object, target, property_name, property_definition.subtype)
        else:
            return gather_vec_property(export_settings, blender_object, target, property_name)

    elif (property_definition.bl_rna.identifier == 'PointerProperty'):
        if type(property_value) is bpy.types.Object:
            return gather_node_property(export_settings, blender_object, target, property_name)
        elif type(property_value) is bpy.types.Material:
            return gather_material_property(export_settings, blender_object, target, property_name)
        elif type(property_value) is bpy.types.Image:
            return gather_image_property(export_settings, blender_object, target, property_name)
        elif type(property_value) is bpy.types.Texture:
            return gather_texture_property(export_settings, blender_object, target, property_name)

    return gltf2_blender_extras.__to_json_compatible(property_value)


def gather_array_property(export_settings, blender_object, target, property_name):
    value = []

    property_value = getattr(target, property_name)
    for item in property_value:
        item_value = gather_property(
            export_settings, blender_object, item, None)
        value.append(item_value)

    return value


def gather_node_property(export_settings, blender_object, target, property_name):
    blender_object = getattr(target, property_name)

    if blender_object:
        if bpy.app.version < (3, 2, 0):
            node = gltf2_blender_gather_nodes.gather_node(
                blender_object,
                blender_object.library.name if blender_object.library else None,
                blender_object.users_scene[0],
                None,
                export_settings
            )
        else:
            vtree = export_settings['vtree']
            vnode = vtree.nodes[next((uuid for uuid in vtree.nodes if (
                vtree.nodes[uuid].blender_object == blender_object)), None)]
            node = vnode.node or gltf2_blender_gather_nodes.gather_node(
                vnode,
                export_settings
            )

        return {
            "__mhc_link_type": "node",
            "index": node
        }
    else:
        return None

# PointerProperty doesn't support bones so for now we have to call this manually where using an object pointer


def gather_joint_property(export_settings, blender_object, target, property_name):
    joint_name = getattr(target, property_name)
    joint = blender_object.pose.bones[joint_name]

    if joint:
        if bpy.app.version < (3, 2, 0):
            node = gltf2_blender_gather_joints.gather_joint(
                blender_object,
                joint,
                export_settings
            )
        else:
            vtree = export_settings['vtree']
            vnode = vtree.nodes[next((uuid for uuid in vtree.nodes if (
                vtree.nodes[uuid].blender_bone == joint)), None)]
            node = vnode.node or gltf2_blender_gather_joints.gather_joint_vnode(
                vnode,
                export_settings
            )

        return {
            "__mhc_link_type": "node",
            "index": node
        }
    else:
        return None


def gather_material_property(export_settings, blender_object, target, property_name):
    blender_material = getattr(target, property_name)

    if blender_material:
        material = gltf2_blender_gather_materials.gather_material(
            blender_material, export_settings)
        return material
    else:
        return None


def gather_vec_property(export_settings, blender_object, target, property_name):
    vec = getattr(target, property_name)

    property_definition = target.bl_rna.properties[property_name]
    unit = getattr(property_definition, 'unit', None)
    subtype = getattr(property_definition, 'subtype', None)

    # We export vectors with no unit and no subtype as arrays. This is not ideal, we should find a way
    # to tag properties as Array/Object to decouple the Blender type from the export type.
    if unit == 'NONE' and subtype == 'NONE':
        out = []
        for value in vec:
            out.append(value)
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


def gather_image_property(export_settings, blender_object, target, property_name):
    blender_image = getattr(target, property_name)
    image = gather_image(blender_image, export_settings)
    if image:
        return {
            "__mhc_link_type": "image",
            "index": image
        }
    else:
        return None


def gather_texture_property(export_settings, blender_object, target, property_name):
    blender_image = getattr(target, property_name)
    texture = gather_texture(blender_image, export_settings)
    if texture:
        return {
            "__mhc_link_type": "texture",
            "index": texture
        }
    else:
        return None


def srgb2lin(s):
    if s <= 0.0404482362771082:
        lin = s / 12.92
    else:
        lin = pow(((s + 0.055) / 1.055), 2.4)
    return lin


def lin2srgb(lin):
    if lin > 0.0031308:
        s = 1.055 * (pow(lin, (1.0 / 2.4))) - 0.055
    else:
        s = 12.92 * lin
    return s


def gather_color_property(export_settings, object, component, property_name, color_type):
    c = list(getattr(component, property_name))

    # Blender stores colors in linear space for subtype COLOR and sRGB for COLOR_GAMMA
    # Hubs expects colors in the glTF components to be in sRGB so we convert them here if needed.
    if color_type == "COLOR":
        c[0] = lin2srgb(c[0])
        c[1] = lin2srgb(c[1])
        c[2] = lin2srgb(c[2])

    c[0] = max(0, min(int(c[0] * 256.0), 255))
    c[1] = max(0, min(int(c[1] * 256.0), 255))
    c[2] = max(0, min(int(c[2] * 256.0), 255))

    return "#{0:02x}{1:02x}{2:02x}".format(c[0], c[1], c[2], 255)


# MOZ_lightmap extension data


def gather_lightmap_texture_info(blender_material, export_settings):
    nodes = blender_material.node_tree.nodes
    lightmap_node = next(
        (n for n in nodes if isinstance(n, MozLightmapNode)), None)

    if not lightmap_node:
        return

    texture_socket = lightmap_node.inputs.get("Lightmap")
    intensity = lightmap_node.intensity

    # TODO this assumes a single image directly connected to the socket
    blender_image = texture_socket.links[0].from_node.image
    texture = gather_texture(blender_image, export_settings)
    socket = lightmap_node.inputs.get("Lightmap") if bpy.app.version < (4, 1, 0) \
        else gltf2_blender_search_node_tree.NodeSocket(texture_socket, blender_material)
    tex_attributes = gltf2_blender_gather_texture_info.__gather_texture_transform_and_tex_coord(
        socket, export_settings)
    tex_transform, tex_coord = tex_attributes[:2]
    texture_info = gltf2_io.TextureInfo(
        extensions=gltf2_blender_gather_texture_info.__gather_extensions(
            tex_transform, export_settings),
        extras=None,
        index=texture,
        tex_coord=tex_coord
    )

    if not texture_info:
        return

    return {
        "intensity": intensity,
        'extensions': texture_info.extensions,
        'extras': texture_info.extras,
        "index": texture_info.index,
        "texCoord": texture_info.tex_coord
    }


def import_image(gltf, gltf_texture):
    texture_extensions = gltf_texture.extensions
    if texture_extensions and texture_extensions.get('MOZ_texture_rgbe'):
        source = gltf_texture.extensions['MOZ_texture_rgbe']['source']
    else:
        source = gltf_texture.source

    BlenderImage.create(
        gltf, source)
    pyimg = gltf.data.images[source]
    blender_image_name = pyimg.blender_image_name
    blender_image = bpy.data.images[blender_image_name]
    if pyimg.mime_type == "image/vnd.radiance":
        if bpy.app.version < (4, 0, 0):
            blender_image.colorspace_settings.name = "Linear"
        else:
            blender_image.colorspace_settings.name = "Linear Rec.709"

    return blender_image_name, source


def import_all_images(gltf):
    global imported_images
    imported_images.clear()

    if not gltf.data.textures:
        return

    for gltf_texture in gltf.data.textures:
        blender_image_name, source = import_image(gltf, gltf_texture)
        imported_images[source] = blender_image_name


def import_component(component_name, blender_object):
    from ..components.utils import add_component, has_component
    from ..components.components_registry import get_component_by_name
    component_class = get_component_by_name(component_name)
    if component_class:
        if not has_component(blender_object, component_name):
            add_component(blender_object, component_name)

    return getattr(blender_object, component_class.get_id())


def set_color_from_hex(blender_component, property_name, hexcolor):
    hexcolor = hexcolor.lstrip('#')
    rgb_int = [int(hexcolor[i:i + 2], 16) for i in (0, 2, 4)]

    for x, value in enumerate(rgb_int):
        rgb_float = value / 255 if value > 0 else 0
        if blender_component.bl_rna.properties[property_name].subtype == 'COLOR':
            # Blender stores colors in linear space for subtype COLOR and sRGB for COLOR_GAMMA
            # Colors in the glTF components are in sRGB so we convert them here if needed.
            rgb_float = srgb2lin(rgb_float)
        getattr(blender_component, property_name)[x] = rgb_float


def assign_property(vnodes, blender_component, property_name, property_value):
    if isinstance(property_value, dict):
        if property_value.get('__mhc_link_type'):
            if len(property_value) == 2:
                if property_value['__mhc_link_type'] == "node":
                    try:
                        setattr(blender_component, property_name,
                                vnodes[property_value['index']].blender_object)
                    except AttributeError:
                        # Assume that the target is a bone
                        bone_vnode = vnodes[property_value['index']]
                        armature_vnode = vnodes[bone_vnode.bone_arma]
                        setattr(blender_component, property_name,
                                armature_vnode.blender_object)
                        setattr(blender_component, "bone",
                                bone_vnode.blender_bone_name)
                elif property_value['__mhc_link_type'] == "texture":
                    global imported_images
                    blender_image_name = imported_images[property_value['index']]
                    blender_image = bpy.data.images[blender_image_name]
                    setattr(blender_component, property_name, blender_image)

        else:
            blender_subcomponent = getattr(blender_component, property_name)
            for x, subproperty_value in enumerate(property_value.values()):
                blender_subcomponent[x] = subproperty_value

    elif re.fullmatch("#[0-9a-fA-F]*", str(property_value)):
        set_color_from_hex(blender_component, property_name, property_value)

    else:
        setattr(blender_component, property_name, property_value)
