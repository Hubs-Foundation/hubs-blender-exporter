from bpy.props import BoolProperty
from ..hubs_component import HubsComponent
from ..types import NodeType, PanelType, Category


class Grabbable(HubsComponent):
    _definition = {
        'name': 'grabbable',
        'display_name': 'Grabbable',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'VIEW_PAN',
        'deps': ['rigidbody', 'networked-transform'],
        'version': (1, 0, 0)
    }

    cursor: BoolProperty(
        name="By Cursor", description="Can be grabbed by a cursor", default=True)

    hand: BoolProperty(
        name="By Hand", description="Can be grabbed by VR hands", default=True)

    @classmethod
    def init(cls, obj):
        obj.hubs_component_list.items.get('rigidbody').isDependency = True
