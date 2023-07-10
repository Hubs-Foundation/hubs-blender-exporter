from email.policy import default
from bpy.props import FloatProperty, BoolProperty, PointerProperty, EnumProperty, StringProperty
from ..hubs_component import HubsComponent
from ..utils import has_component, is_linked
from ..types import Category, PanelType, NodeType
from ..ui import add_link_indicator
from bpy.types import Object
from ...utils import delayed_gather
from .audio_source import AudioSource


BLANK_ID = "374e54CMHFCipSk"


def filter_on_component(self, ob):
    dep_name = AudioSource.get_name()
    if hasattr(ob, 'type') and ob.type == 'ARMATURE':
        if ob.mode == 'EDIT':
            ob.update_from_editmode()

        for bone in ob.data.bones:
            if has_component(bone, dep_name):
                return True
    return has_component(ob, dep_name)


bones = []


def get_bones(self, context):
    global bones
    bones = []
    count = 0
    dep_name = AudioSource.get_name()
    bones.append((BLANK_ID, "Select a bone", "None", "BLANK", count))
    count += 1

    if self.srcNode and self.srcNode.mode == 'EDIT':
        self.srcNode.update_from_editmode()

    found = False
    if self.srcNode and self.srcNode.type == 'ARMATURE':
        for bone in self.srcNode.data.bones:
            if has_component(bone, dep_name):
                bones.append((bone.name, bone.name, "", 'BONE_DATA', count))
                count += 1
                if bone.name == self.bone_id:
                    found = True

    if self.bone_id != BLANK_ID and not found:
        bones.append(
            (self.bone_id, self.bone_id, "", "ERROR", count))
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
        self.bone_id = BLANK_ID


class AudioTarget(HubsComponent):
    _definition = {
        'name': 'audio-target',
        'display_name': 'Audio Target',
        'category': Category.MEDIA,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'deps': ['audio-params'],
        'icon': 'SPEAKER',
        'version': (1, 0, 0)
    }

    srcNode: PointerProperty(
        name="Source",
        description="The object with an audio-source component to pull audio from",
        type=Object,
        poll=filter_on_component,
        update=lambda self, context: setattr(self, 'bone', BLANK_ID)
    )

    bone: EnumProperty(
        name="Bone",
        description="The bone with an audio-source component to pull audio from.  If a bone is selected, this will override the object source, otherwise if no bone is selected, the source will be pulled from the object",
        items=get_bones,
        get=get_bone,
        set=set_bone
    )

    bone_id: StringProperty(
        name="bone_id",
        default=BLANK_ID,
        options={'HIDDEN'})

    minDelay: FloatProperty(
        name="Min Delay",
        description="Minimum random delay applied to the source audio",
        default=0.01,
        min=0.0)

    maxDelay: FloatProperty(
        name="Max Delay",
        description="Maximum random delay applied to the source audio",
        default=0.03,
        min=0.0)

    debug: BoolProperty(
        name="Debug",
        description="Show debug visuals",
        default=False)

    def draw(self, context, layout, panel):
        dep_name = AudioSource.get_name()

        has_obj_component = False
        has_bone_component = False
        row = layout.row(align=True)
        sub_row = row.row(align=True)
        sub_row.prop(data=self, property="srcNode")
        if is_linked(context.active_object):
            # Manually disable the PointerProperty, needed for Blender 3.2+.
            sub_row.enabled = False
        if is_linked(self.srcNode):
            sub_row = row.row(align=True)
            sub_row.enabled = False
            add_link_indicator(sub_row, self.srcNode)

        if hasattr(self.srcNode, 'type'):
            has_obj_component = has_component(self.srcNode, dep_name)
            if self.srcNode.type == 'ARMATURE':
                layout.prop(data=self, property="bone")
                if self.bone_id != BLANK_ID and self.bone in self.srcNode.data.bones:
                    has_bone_component = has_component(
                        self.srcNode.data.bones[self.bone], dep_name)

        if self.srcNode and self.bone_id == BLANK_ID and not has_obj_component:
            col = layout.column()
            col.alert = True
            col.label(
                text=f'The selected source doesn\'t have an {AudioSource.get_display_name()} component', icon='ERROR')
        elif self.srcNode and self.bone_id != BLANK_ID and not has_bone_component:
            col = layout.column()
            col.alert = True
            col.label(
                text=f'The selected bone doesn\'t have an {AudioSource.get_display_name()} component', icon='ERROR')

        layout.prop(data=self, property="minDelay")
        layout.prop(data=self, property="maxDelay")
        layout.prop(data=self, property="debug")

    @delayed_gather
    def gather(self, export_settings, object):
        from ...io.utils import gather_joint_property, gather_node_property
        return {
            'srcNode': gather_joint_property(export_settings, self.srcNode, self, 'bone') if self.bone_id != BLANK_ID else gather_node_property(
                export_settings, object, self, 'srcNode'),
            'maxDelay': self.maxDelay,
            'minDelay': self.minDelay,
            'debug': self.debug
        }
