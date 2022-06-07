from bpy.props import EnumProperty, StringProperty, BoolProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..consts import PROJECTION_MODE, TRANSPARENCY_MODE
from .networked import migrate_networked


class Image(HubsComponent):
    _definition = {
        'name': 'image',
        'display_name': 'Image',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'FILE_IMAGE',
        'deps': ['networked']
    }

    src: StringProperty(
        name="Image URL", description="Image URL", default="https://mozilla.org")

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

    @classmethod
    def migrate(cls):
        migrate_networked(cls.get_name())
