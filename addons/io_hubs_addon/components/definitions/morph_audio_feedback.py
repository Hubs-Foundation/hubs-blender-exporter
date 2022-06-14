import atexit
import bpy
from bpy.props import FloatProperty, StringProperty, EnumProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType

shape_keys = []


def get_shape_keys(self, context):
    global shape_keys
    shape_keys = []
    count = 0
    if self.name:
        shape_keys.append((self.name, self.name,
                          "No matching shape key found", 'ERROR', count))
        count += 1
    if context.object.data.shape_keys:
        for item in context.object.data.shape_keys.key_blocks:
            if ' ' in item.name or ',' in item.name:
                shape_keys.append((item.name, item.name,
                                  "Shape key names can't have spaces or commas", 'ERROR', count))
                count += 1
            elif item == item.relative_key:
                pass
            else:
                shape_keys.append(
                    (item.name, item.name, "", 'SHAPEKEY_DATA', count))
                count += 1
    return shape_keys


def get_shape_key(self):
    return self["shape_key"]


def set_shape_key(self, value):
    global shape_keys
    if self.name and self.name != shape_keys[value][0]:
        self.name = ''
        self["shape_key"] = value - 1
    else:
        self["shape_key"] = value


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
        items=get_shape_keys,
        get=get_shape_key,
        set=set_shape_key
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
                    component = ob.hubs_component_morph_audio_feedback
                    if component.name in get_shape_keys(component, bpy.context):
                        component.shape_key = (component.name)
                        component.name = ''
                    else:
                        component.shape_key = (component.name)

    def draw(self, context, layout):
        if get_shape_keys(self, context):
            layout.prop(data=self, property="shape_key")
            if self.shape_key not in context.object.data.shape_keys.key_blocks:
                col = layout.column()
                col.alert = True
                col.label(text="No matching shape key found",
                          icon='ERROR')
            elif ' ' in self.shape_key or ',' in self.shape_key:
                col = layout.column()
                col.alert = True
                col.label(text="Shape key names can't have spaces or commas",
                          icon='ERROR')
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
