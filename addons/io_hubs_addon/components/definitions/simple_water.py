from bpy.props import FloatVectorProperty, FloatProperty
from ..hubs_component import HubsComponent
from ..types import Category, NodeType, PanelType


class SimpleWater(HubsComponent):
    _definition = {
        'name': 'simple-water',
        'display_name': 'Simple Water',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'MOD_FLUIDSIM'
    }

    color: FloatVectorProperty(name="Color",
                               description="Color",
                               subtype='COLOR',
                               default=(1.0, 1.0, 1.0, 1.0),
                               size=4,
                               min=0,
                               max=1)

    opacity: FloatProperty(name="Opacity",
                           description="Opacity",
                           default=1.0)

    tideHeight: FloatProperty(name="Tide Height",
                              description="Tide Height",
                              default=0.01)

    tideScale: FloatVectorProperty(name="Tide Scale",
                                   description="Tide Scale",
                                   size=2,
                                   unit="LENGTH",
                                   subtype="XYZ",
                                   default=[1.0, 1.0])

    tideSpeed: FloatVectorProperty(name="Tide Speed",
                                   description="Tide Speed",
                                   size=2,
                                   unit="VELOCITY",
                                   subtype="XYZ",
                                   default=[0.5, 0.5])

    waveHeight: FloatProperty(name="Wave Height",
                                   default=1.0)

    waveScale: FloatVectorProperty(name="Wave Scale",
                                   description="Wave Scale",
                                   size=2,
                                   unit="LENGTH",
                                   subtype="XYZ",
                                   default=[1.0, 20.0])

    waveSpeed: FloatVectorProperty(name="Wave Speed",
                                   description="Wave Speed",
                                   size=2,
                                   unit="VELOCITY",
                                   subtype="XYZ",
                                   default=[0.05, 6.0])

    ripplesSpeed: FloatProperty(name="Ripples Speed",
                                default=0.25)

    ripplesScale: FloatProperty(name="Ripples Scale",
                                default=1.0)
