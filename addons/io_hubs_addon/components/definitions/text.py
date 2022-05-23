from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty, StringProperty
from bpy.types import Node
from ..hubs_component import HubsComponent
from ..types import Category, PanelType


class Text(HubsComponent):
    _definition = {
        'name': 'text',
        'display_name': 'Text',
        'category': Category.ELEMENTS,
        'node_type': Node,
        'panel_type': PanelType.OBJECT,
        'icon': 'FONT_DATA'
    }

    value: StringProperty(
        name="Text", description="Text", default="Hello world!")

    align: EnumProperty(
        name="Alignment",
        description="Alignment",
        items=[("left", "Left align", "Text will be aligned to the left"),
               ("right", "Right align", "Text will be aligned to the right"),
               ("center", "Center align", "Text will be centered")],
        default="left")

    baseline: EnumProperty(
        name="Baseline",
        description="Baseline",
        items=[("top", "Top align", "Alignment will be with the top of the text"),
               ("center", "Center align",
                "Alignment will be with the center of the text"),
               ("bottom", "Bottom align", "Alignment will be with the bottom of the text")],
        default="top")

    side: EnumProperty(
        name="Display Side",
        description="Display Side",
        items=[("front", "Show on front", "Text will be shown on the front (-Y)"),
               ("back", "Show on back", "Text will be shown on the back (+Y)"),
               ("double", "Show on both", "Text will be shown on both sides")],
        default="front")

    whiteSpace: EnumProperty(
        name="White Space",
        description="White Space",
        items=[("normal", "Normal", "Text will flow normally"),
               ("pre", "Preserve", "White space will be preserved"),
               ("nowrap", "No Wrapping", "Text will not be word-wrapped")],
        default="normal")

    font: StringProperty(
        name="Font", description="Font", default="roboto")

    color: FloatVectorProperty(name="Color",
                               description="Color",
                               subtype='COLOR',
                               default=[1.0, 1.0, 1.0])

    width: FloatProperty(
        name="Width", description="Width", default=1.0)

    wrapCount: FloatProperty(
        name="Wrap Count", description="Wrap Count", default=40.0)

    wrapPixels: FloatProperty(
        name="Wrap Pixels", description="Wrap Pixels", default=0.0)

    letterSpacing: FloatProperty(
        name="Letter Space", description="Letter Space", default=0.0)

    lineHeight: FloatProperty(
        name="Line Height", description="Line Height", default=0.0)

    opacity: FloatProperty(
        name="Opacity", description="Opacity", default=1.0)

    xOffset: FloatProperty(
        name="X-Offset", description="X-Offset", default=0.0)

    zOffset: FloatProperty(
        name="Z-Offset", description="Z-Offset", default=0.001)
