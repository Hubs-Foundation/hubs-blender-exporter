from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType

# TODO Add this component in the scene by default?


class hubs_component_fog(HubsComponent):
    _definition = {
        'export_name': 'fog',
        'display_name': 'fog',
        'category': Category.SCENE,
        'node_type': NodeType.SCENE,
        'panel_type': PanelType.SCENE
    }

    type: EnumProperty(
        name="type",
        description="Fog Type",
        items=[("linear", "Linear fog", "Fog effect will increase linearly with distance"),
               ("exponential", "Exponential fog",
                "Fog effect will increase exponentially with distance")],
        default="linear")

    color: FloatVectorProperty(name="Color",
                               subtype='COLOR',
                               default=[1.0, 1.0, 1.0])

    near: FloatProperty(
        name="Near", description="Fog Near Distance (linear only)", default=1.0)

    far: FloatProperty(
        name="Far", description="Fog Far Distance (linear only)", default=100.0)

    density: FloatProperty(
        name="Far", description="Fog Density (exponential only)", default=0.1)
