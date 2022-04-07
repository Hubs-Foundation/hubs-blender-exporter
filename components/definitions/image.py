from bpy.props import EnumProperty, StringProperty, BoolProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType

# TODO Add this component in the scene by default?

TRANSPARENCY_MODE = [("opaque", "No transparency (opaque)", "Alpha channel will be ignored"),
                     ("blend", "Gradual transparency (blend)",
                      "Alpha channel will be applied"),
                     ("mask", "Binary transparency (mask)",
                      "Alpha channel will be used as a threshold between opaque and transparent pixels")]

PROJECTION_MODE = [("flat", "2D image (flat)", "Image will be shown on a 2D surface"),
                   ("360-equirectangular",
                    "Spherical (360-equirectangular)", "Image will be shown on a sphere")]


class hubs_component_image(HubsComponent):
    _definition = {
        'id': 'image',
        'display_name': 'Image',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'networked': True,
        'icon': 'image.png'
    }

    src: StringProperty(
        name="Image URL", description="Image URL", default="https://")

    controls: BoolProperty(name="Controls", default=True)

    alphaMode: EnumProperty(
        name="Transparency Mode",
        description="Transparency Mode",
        items=TRANSPARENCY_MODE,
        default="opaque")

    projection: EnumProperty(
        name="Projection",
        description="Projection",
        items=PROJECTION_MODE,
        default="flat")
