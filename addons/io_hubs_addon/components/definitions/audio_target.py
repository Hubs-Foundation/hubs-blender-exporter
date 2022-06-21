from bpy.props import FloatProperty, BoolProperty, PointerProperty, EnumProperty, StringProperty
from ..hubs_component import HubsComponent
from ..utils import has_component
from ..types import Category, PanelType, NodeType
from bpy.types import Object
from ...io.utils import gather_joint_property, gather_node_property


def filter_on_component(self, ob):
    from .audio_source import AudioSource
    dep_name = AudioSource.get_name()
    if hasattr(ob, 'type') and ob.type == 'ARMATURE':
        for bone in ob.data.bones:
            if has_component(bone, dep_name):
                return True
    return has_component(ob, dep_name)


bones = []


def get_bones(self, context):
    global bones
    bones = []
    count = 0
    from .audio_source import AudioSource
    dep_name = AudioSource.get_name()
    bones.append(("NONE", "None", "None", "BLANK", count))
    count += 1

    if self.srcNode and self.srcNode.type == 'ARMATURE':
        for bone in self.srcNode.data.bones:
            if has_component(bone, dep_name):
                bones.append((bone.name, bone.name, "", 'BONE_DATA', count))
                count += 1
    return bones


def get_bone(self):
    global bones
    list_ids = list(map(lambda x: x[0], bones))
    if self.bone_id in list_ids:
        return list_ids.index(self.bone_id)
    return 0


def set_bone(self, value):
    global bones
    list_indexes = list(map(lambda x: x[4], bones))
    if value in list_indexes:
        self.bone_id = bones[value][0]
    else:
        self.bone_id = "NONE"


class AudioTarget(HubsComponent):
    _definition = {
        'name': 'audio-target',
        'display_name': 'Audio Target',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'deps': ['audio-params'],
        'icon': 'SPEAKER'
    }

    srcNode: PointerProperty(
        name="Source",
        description="Node with a audio-source-zone to pull audio from",
        type=Object,
        poll=filter_on_component
    )

    bone: EnumProperty(
        name="Bone",
        description="Bone",
        items=get_bones,
        get=get_bone,
        set=set_bone
    )

    bone_id: StringProperty(
        name="bone_id",
        options={'HIDDEN'})

    minDelay: FloatProperty(
        name="Min Delay",
        description="Minimum random delay applied to the source audio",
        default=0.01,
        min=0.0,
        soft_min=0.0)

    maxDelay: FloatProperty(
        name="Max Delay",
        description="Maximum random delay applied to the source audio",
        default=0.03,
        min=0.0,
        soft_min=0.0)

    debug: BoolProperty(
        name="Debug",
        description="Show debug visuals",
        default=False)

    def draw(self, context, layout, panel_type):
        from .audio_source import AudioSource
        dep_name = AudioSource.get_name()

        layout.prop(data=self, property="srcNode")
        if hasattr(self.srcNode, 'type') and self.srcNode.type == 'ARMATURE':
            layout.prop(data=self, property="bone")

        has_bone_component = self.bone != "NONE" and has_component(
            self.srcNode.data.bones[self.bone], dep_name)
        has_obj_component = self.srcNode and has_component(
            self.srcNode, dep_name)
        if self.srcNode and self.bone == "NONE" and not has_obj_component:
            col = layout.column()
            col.alert = True
            col.label(
                text=f'The selected source doesn\'t have a {AudioSource.get_display_name()} component', icon='ERROR')
        elif self.srcNode and self.bone != "NONE" and not has_bone_component:
            col = layout.column()
            col.alert = True
            col.label(
                text=f'The selected bone doesn\'t have a {AudioSource.get_display_name()} component', icon='ERROR')

        layout.prop(data=self, property="minDelay")
        layout.prop(data=self, property="maxDelay")
        layout.prop(data=self, property="debug")

    def gather(self, export_settings, object):
        return {
            'srcNode': gather_joint_property(export_settings, self.srcNode, self, 'bone') if self.bone != "NONE" else gather_node_property(
                export_settings, object, self, 'srcNode'),
            'maxDelay': self.maxDelay,
            'minDelay': self.minDelay,
            'debug': self.debug
        }
