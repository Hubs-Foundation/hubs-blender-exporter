import atexit
import bpy
from bpy.props import FloatProperty, StringProperty, EnumProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


def get_shape_keys(self, context):
    shape_keys = []
    if context.object.data.shape_keys:
        for item in context.object.data.shape_keys.key_blocks:
            shape_keys.append((item.name, item.name, ""))
    return shape_keys


class MorphAudioFeedback(HubsComponent):
    _definition = {
        'name': 'morph-audio-feedback',
        'display_name': 'Morph Audio Feedback',
        'category': Category.AVATAR,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'MOD_SMOOTH'
    }

    name: StringProperty(
        name="Name",
        description="Name"
    )

    shape_key: EnumProperty(
        name="Shape Key",
        description="Shape key to morph",
        items=get_shape_keys
    )

    minValue: FloatProperty(name="Min Value",
                            description="Min Value",
                            default=0.0,)

    maxValue: FloatProperty(name="Max Value",
                            description="Max Value",
                            default=1.0)

    @classmethod
    def poll(cls, context):
        return context.object.type == 'MESH'

    @classmethod
    def migrate(cls, version):
        if version < (0, 1, 0):
            for ob in bpy.data.objects:
                if cls.get_name() in ob.hubs_component_list.items:
                    ob.hubs_component_morph_audio_feedback.shape_key = (
                        ob.hubs_component_morph_audio_feedback.name)

    def draw(self, context, layout):
        shape_keys = context.object.data.shape_keys
        if shape_keys and len(shape_keys.key_blocks) > 0:
            layout.prop(data=self, property="shape_key")
            layout.prop(data=self, property="minValue")
            layout.prop(data=self, property="maxValue")
        else:
            col = layout.column()
            col.alert = True
            col.label(text='No shape keys available',
                      icon='ERROR')

    def gather(self, export_settings, object):
        return {
            'name': object.hubs_component_morph_audio_feedback.shape_key,
            'minValue': object.hubs_component_morph_audio_feedback.minValue,
            'maxValue': object.hubs_component_morph_audio_feedback.maxValue
        }
