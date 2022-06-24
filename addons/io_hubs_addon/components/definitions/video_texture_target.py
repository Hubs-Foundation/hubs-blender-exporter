from bpy.props import BoolProperty, PointerProperty, EnumProperty, StringProperty
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..utils import has_component
from bpy.types import Object
from ...io.utils import gather_joint_property, gather_node_property

NONE = "pXph8WBzMu9fung"


def filter_on_component(self, ob):
    from .video_texture_source import VideoTextureSource
    dep_name = VideoTextureSource.get_name()
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
    from .video_texture_source import VideoTextureSource
    dep_name = VideoTextureSource.get_name()
    bones.append((NONE, "No bone selected", "None", "BLANK", count))
    count += 1

    found = False
    if self.srcNode and self.srcNode.type == 'ARMATURE':
        for bone in self.srcNode.data.bones:
            if has_component(bone, dep_name):
                bones.append((bone.name, bone.name, "", 'BONE_DATA', count))
                count += 1
                if bone.name == self.bone_id:
                    found = True

    if self.bone_id != NONE and not found:
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
        self.bone_id = NONE


class VideoTextureTarget(HubsComponent):
    _definition = {
        'name': 'video-texture-target',
        'display_name': 'Video Texture Target',
        'category': Category.AVATAR,
        'node_type': NodeType.MATERIAL,
        'panel_type': [PanelType.MATERIAL],
        'icon': 'IMAGE_DATA'
    }

    targetBaseColorMap: BoolProperty(
        name="Override Base Color Map", description="Should the video texture override the base color map?", default=True)

    targetEmissiveMap: BoolProperty(
        name="Override Emissive Color Map", description="Should the video texture override the emissive map?", default=False)

    srcNode: PointerProperty(
        name="Source",
        description="Node with a vide-texture-source to pull video from",
        type=Object,
        poll=filter_on_component)

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

    def draw(self, context, layout, panel_type):
        from .video_texture_source import VideoTextureSource
        dep_name = VideoTextureSource.get_name()

        layout.prop(data=self, property="srcNode")
        if hasattr(self.srcNode, 'type') and self.srcNode.type == 'ARMATURE':
            layout.prop(data=self, property="bone")

        has_bone_component = self.bone != NONE and has_component(
            self.srcNode.data.bones[self.bone], dep_name)
        has_obj_component = self.srcNode and has_component(
            self.srcNode, dep_name)
        if self.srcNode and self.bone == NONE and not has_obj_component:
            col = layout.column()
            col.alert = True
            col.label(
                text=f'The selected source doesn\'t have a {VideoTextureSource.get_display_name()} component', icon='ERROR')
        elif self.srcNode and self.bone != NONE and not has_bone_component:
            col = layout.column()
            col.alert = True
            col.label(
                text=f'The selected bone doesn\'t have a {VideoTextureSource.get_display_name()} component', icon='ERROR')

        layout.prop(data=self, property="targetBaseColorMap")
        layout.prop(data=self, property="targetEmissiveMap")

        has_material = len(context.object.material_slots) > 0
        if not has_material:
            col = layout.column()
            col.alert = True
            col.label(text='This component requires a material',
                      icon='ERROR')

    def gather(self, export_settings, object):

        return {
            'targetBaseColorMap': self.targetBaseColorMap,
            'targetEmissiveMap': self.targetEmissiveMap,
            'srcNode': gather_joint_property(export_settings, self.srcNode, self, 'bone') if self.bone != NONE else gather_node_property(
                export_settings, object, self, 'srcNode'),
        }
