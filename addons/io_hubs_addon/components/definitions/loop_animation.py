import atexit
import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty
from bpy.types import PropertyGroup
from .hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class ClipPropertyType(PropertyGroup):
    name: StringProperty(
        name="Animation name",
        description="Animation name",
        default=""
    )


bpy.utils.register_class(ClipPropertyType)


@atexit.register
def unregister():
    bpy.utils.unregister_class(ClipPropertyType)


def get_clips(self, context):
    clips = []
    for a in bpy.data.actions:
        clips.append((a.name, a.name, ""))
    return clips


class LoopAnimation(HubsComponent):
    _definition = {
        'id': 'loop-animation',
        'name': 'hubs_component_loop_animation',
        'display_name': 'Loop Animation',
        'category': Category.ANIMATION,
        'node_type': NodeType.NODE,
        'panel_type': PanelType.OBJECT,
        'icon': 'LOOP_BACK'
    }

    clip: EnumProperty(
        name="Animation Clip",
        description="Animation clip to use",
        items=get_clips,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    paused: BoolProperty(
        name="Paused",
        description="Paused",
        default=False
    )

    def draw(self, context, layout):
        if len(bpy.data.actions) > 0:
            super().draw(context, layout)
        else:
            layout.label(text='No clips available',
                         icon='ERROR')
