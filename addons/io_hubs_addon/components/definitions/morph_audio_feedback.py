import bpy
from bpy.props import FloatProperty, StringProperty, EnumProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType

shape_keys = []

BLANK_ID = "cKsdi5pSEUGvSg8"


def get_object_shape_keys(cmp, ob):
    global shape_keys
    shape_keys = []
    count = 0

    shape_keys.append(
        (BLANK_ID, "Select a shape key", "None", "BLANK", count))
    count += 1

    found = False
    if ob.data.shape_keys:
        for item in ob.data.shape_keys.key_blocks:
            if item == item.relative_key:
                pass
            else:
                shape_keys.append(
                    (item.name, item.name, "", 'SHAPEKEY_DATA', count))
                count += 1
                if item.name == cmp.name:
                    found = True

    if cmp.name != BLANK_ID and not found:
        shape_keys.append(
            (cmp.name, cmp.name, "", "ERROR", count))
        count += 1

    return shape_keys


def get_shape_keys(self, context):
    return get_object_shape_keys(self, context.object)


def get_shape_key(self):
    global shape_keys
    list_ids = list(map(lambda x: x[0], shape_keys))
    if self.name in list_ids:
        return list_ids.index(self.name)
    return 0


def set_shape_key(self, value):
    global shape_keys
    list_indexes = list(map(lambda x: x[4], shape_keys))
    if value in list_indexes:
        self.name = shape_keys[value][0]
    else:
        self.name = BLANK_ID


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
        description="Name",
        default=BLANK_ID
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
    def poll(cls, context, panel_type):
        return context.object.type == 'MESH'

    @classmethod
    def migrate(cls, version):
        if version < (1, 0, 0):
            for ob in bpy.data.objects:
                if cls.get_name() in ob.hubs_component_list.items:
                    component = ob.hubs_component_morph_audio_feedback
                    shape_keys = get_object_shape_keys(component, ob)
                    list_ids = list(map(lambda x: x[0], shape_keys))
                    if not component.name in list_ids:
                        component.name = component.name

    def draw(self, context, layout, panel):
        layout.prop(data=self, property="shape_key")
        shape_keys = context.object.data.shape_keys
        if self.shape_key != BLANK_ID and shape_keys and self.shape_key not in shape_keys.key_blocks:
            col = layout.column()
            col.alert = True
            col.label(text="No matching shape key found",
                      icon='ERROR')
        layout.prop(data=self, property="minValue")
        layout.prop(data=self, property="maxValue")

    def gather(self, export_settings, object):
        return {
            'name': self.name if self.name != BLANK_ID else "",
            'minValue': self.minValue,
            'maxValue': self.maxValue
        }
