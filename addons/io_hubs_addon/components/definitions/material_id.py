from bpy.props import StringProperty, FloatVectorProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class MaterialID(HubsComponent):
    _definition = {
        'name': 'material-id',
        'display_name': 'Material ID',
        'category': Category.OBJECT,
        'node_type': NodeType.MATERIAL,
        'panel_type': [PanelType.MATERIAL],
        'icon': 'NONE',
        'version': (1, 0, 0)
    }

    id: StringProperty(name="ID",
                       description="ID",
                       default="")

    name: StringProperty(name="Name",
                         description="Name",
                         default="")
