from bpy.props import StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from .networked import migrate_networked


class Model(HubsComponent):
    _definition = {
        'name': 'model',
        'display_name': 'Model',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'SCENE_DATA',
        'deps': ['networked']
    }

    src: StringProperty(name="Model URL", description="Model URL",
                        default="https://mozilla.org")

    @classmethod
    def migrate(cls):
        migrate_networked(cls.get_name())
