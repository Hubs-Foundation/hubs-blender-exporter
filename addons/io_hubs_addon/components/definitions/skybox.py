import bpy
from bpy.props import FloatVectorProperty, FloatProperty, BoolProperty, IntVectorProperty
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class Skybox(HubsComponent):
    _definition = {
        'id': 'skybox',
        'name': 'hubs_component_skybox',
        'display_name': 'Skybox',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'MAT_SPHERE_SKY'
    }

    azimuth: FloatProperty(name="Time of Day",
                           description="Time of Day",
                           default=0.15)

    inclination: FloatProperty(name="Latitude",
                               description="Latitude",
                               default=0.0)

    luminance: FloatProperty(name="Luminance",
                             description="Luminance",
                             default=1.0)

    mieCoefficient: FloatProperty(name="Scattering Amount",
                                  description="Scattering Amount",
                                  default=0.005)

    mieDirectionalG: FloatProperty(name="Scattering Distance",
                                   description="Scattering Distance",
                                   default=0.8)

    turbidity: FloatProperty(name="Horizon Start",
                                  description="Horizon Start",
                                  default=10.0)

    rayleigh: FloatProperty(name="Horizon End",
                            description="Horizon End",
                            default=2.0)

    distance: FloatProperty(name="Distance",
                            description="Distance",
                            default=8000.0)
