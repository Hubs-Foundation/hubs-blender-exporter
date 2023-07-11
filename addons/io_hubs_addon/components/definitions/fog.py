from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Fog(HubsComponent):
    _definition = {
        'name': 'fog',
        'display_name': 'Fog',
        'category': Category.SCENE,
        'node_type': NodeType.SCENE,
        'panel_type': [PanelType.SCENE],
        'icon': 'MOD_OCEAN',
        'version': (1, 0, 0)
    }

    type: EnumProperty(
        name="type",
        description="Fog Type",
        items=[("linear", "Linear fog", "Fog effect will increase linearly with distance"),
               ("exponential", "Exponential fog",
                "Fog effect will increase exponentially with distance")],
        default="linear")

    color: FloatVectorProperty(name="Color",
                               subtype='COLOR_GAMMA',
                               default=(1.0, 1.0, 1.0, 1.0),
                               size=4,
                               min=0,
                               max=1)

    # TODO Make these properties to be displayed dynamically based on the fog type
    near: FloatProperty(
        name="Near", description="Fog Near Distance (linear only)", default=1.0)

    far: FloatProperty(
        name="Far", description="Fog Far Distance (linear only)", default=100.0)

    density: FloatProperty(
        name="Density", description="Fog Density (exponential only)", default=0.00025)
