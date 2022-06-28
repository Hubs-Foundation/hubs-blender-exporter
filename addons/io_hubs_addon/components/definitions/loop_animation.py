import atexit
import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty
from bpy.types import PropertyGroup, Menu, Operator
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class TracksList(bpy.types.UIList):
    bl_idname = "HUBS_UL_TRACKS_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        key_block = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.90, align=False)
            if context.object.animation_data and item.name in context.object.animation_data.nla_tracks:
                split.prop(key_block, "name", text="",
                           emboss=False, icon_value=icon)
                split.enabled = False
            else:
                split.prop(key_block, "name", text="",
                           emboss=False, icon='ERROR')
            row = split.row(align=True)
            row.emboss = 'NONE_OR_STATUS'
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class AddTrackOperator(Operator):
    bl_idname = "hubs_loop_animation.add_track"
    bl_label = "Add Track"

    track_name: StringProperty(
        name="Track Name", description="Track Name", default="")

    def execute(self, context):
        ob = context.object
        if context.mode == 'POSE' or context.mode == 'EDIT_ARMATURE':
            ob = context.active_bone

        track = ob.hubs_component_loop_animation.tracks_list.add()
        track.name = self.track_name

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class RemoveTrackOperator(Operator):
    bl_idname = "hubs_loop_animation.remove_track"
    bl_label = "Remove Track"

    @classmethod
    def poll(self, context):
        return context.object.hubs_component_loop_animation.active_track_key != -1

    def execute(self, context):
        ob = context.object
        if context.mode == 'POSE' or context.mode == 'EDIT_ARMATURE':
            ob = context.active_bone

        active_track_key = ob.hubs_component_loop_animation.active_track_key
        ob.hubs_component_loop_animation.tracks_list.remove(
            active_track_key)

        return {'FINISHED'}


def has_track(tracks_list, track):
    exists = False
    for item in tracks_list:
        if item.name == track:
            exists = True
            break

    return exists


class TracksContextMenu(Menu):
    bl_idname = "HUBS_MT_TRACKS_context_menu"
    bl_label = "Tracks Specials"

    def draw(self, context):
        no_tracks = True
        ob = context.object
        if ob.animation_data:
            for _, a in enumerate(ob.animation_data.nla_tracks):
                if not has_track(context.object.hubs_component_loop_animation.tracks_list, a.name):
                    self.layout.operator(AddTrackOperator.bl_idname, icon='OBJECT_DATA',
                                         text=a.name).track_name = a.name
                    no_tracks = False

        if no_tracks:
            self.layout.label(text="No tracks found")


class TrackPropertyType(PropertyGroup):
    name: StringProperty(
        name="Track name",
        description="Track Name",
        default=""
    )


bpy.utils.register_class(TrackPropertyType)


@atexit.register
def unregister():
    bpy.utils.unregister_class(TrackPropertyType)


class LoopAnimation(HubsComponent):
    _definition = {
        'name': 'loop-animation',
        'display_name': 'Loop Animation',
        'category': Category.ANIMATION,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'LOOP_BACK'
    }

    tracks_list: CollectionProperty(
        type=TrackPropertyType)

    clip: StringProperty(
        name="Animation Clip",
        description="Animation clip to use",
        default=""
    )

    active_track_key: IntProperty(
        name="Active track index",
        description="Active track index",
        default=-1
    )

    paused: BoolProperty(
        name="Paused",
        description="Paused",
        default=False
    )

    def draw(self, context, layout, panel_type):
        layout.label(text='Animations to play:')

        row = layout.row()
        row.template_list(TracksList.bl_idname, "", self,
                          "tracks_list", self, "active_track_key", rows=3)

        col = row.column(align=True)

        col.menu(TracksContextMenu.bl_idname, icon='ADD', text="")
        col.operator(RemoveTrackOperator.bl_idname,
                     icon='REMOVE', text="")

        layout.separator()

        layout.prop(data=self, property='paused')

    def gather(self, export_settings, object):
        return {
            'clip': ",".join(
                object.hubs_component_loop_animation.tracks_list.keys()),
            'paused': self.paused
        }

    @staticmethod
    def register():
        bpy.utils.register_class(TracksList)
        bpy.utils.register_class(TracksContextMenu)
        bpy.utils.register_class(AddTrackOperator)
        bpy.utils.register_class(RemoveTrackOperator)

    @staticmethod
    def unregister():
        bpy.utils.unregister_class(TracksList)
        bpy.utils.unregister_class(TracksContextMenu)
        bpy.utils.unregister_class(AddTrackOperator)
        bpy.utils.unregister_class(RemoveTrackOperator)

    @classmethod
    def migrate(cls, version):
        if version < (1, 0, 0):
            def migrate_data(ob):
                if cls.get_name() in ob.hubs_component_list.items:
                    tracks = ob.hubs_component_loop_animation.clip.split(",")
                    for track_name in tracks:
                        if not has_track(ob.hubs_component_loop_animation.tracks_list, track_name):
                            track = ob.hubs_component_loop_animation.tracks_list.add()
                            track.name = track_name.strip()

            for ob in bpy.data.objects:
                migrate_data(ob)

                if ob.type == 'ARMATURE':
                    for bone in ob.data.bones:
                        migrate_data(bone)
