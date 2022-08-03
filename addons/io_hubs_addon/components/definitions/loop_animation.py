import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty
from bpy.types import PropertyGroup, Menu, Operator
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType


class TracksList(bpy.types.UIList):
    bl_idname = "HUBS_UL_TRACKS_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        key_block = item
        ob = context.object
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.90, align=False)
            if ob.animation_data and item.name in ob.animation_data.nla_tracks:
                split.prop(key_block, "name", text="",
                           emboss=False, icon_value=icon)
                split.enabled = False
            elif hasattr(ob.data, 'shape_keys') and ob.data.shape_keys and ob.data.shape_keys.animation_data  and item.name in ob.data.shape_keys.animation_data.nla_tracks:
                split.prop(key_block, "name", text="",
                           emboss=False, icon_value=icon)
                split.enabled = False
            else:
                split.prop(key_block, "name", text="",
                           emboss=False, icon='ERROR')
            row = split.row(align=True)
            row.emboss = 'UI_EMBOSS_NONE_OR_STATUS' if bpy.app.version < (3, 0, 0) else 'NONE_OR_STATUS'
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class AddTrackOperator(Operator):
    bl_idname = "hubs_loop_animation.add_track"
    bl_label = "Add Track"
    bl_options = {'REGISTER', 'UNDO'}

    track_name: StringProperty(
        name="Track Name", description="Track Name", default="")

    panel_type: StringProperty(name="panel_type")

    def execute(self, context):
        panel_type = PanelType(self.panel_type)
        ob = context.object
        host = ob if panel_type == PanelType.OBJECT else context.active_bone

        track = host.hubs_component_loop_animation.tracks_list.add()
        track.name = self.track_name

        num_tracks = len(host.hubs_component_loop_animation.tracks_list)
        host.hubs_component_loop_animation.active_track_key = num_tracks - 1

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class RemoveTrackOperator(Operator):
    bl_idname = "hubs_loop_animation.remove_track"
    bl_label = "Remove Track"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        panel_type = PanelType(context.panel.bl_context)
        ob = context.object
        host = ob if panel_type == PanelType.OBJECT else context.active_bone

        return host.hubs_component_loop_animation.active_track_key != -1

    def execute(self, context):
        panel_type = PanelType(context.panel.bl_context)
        ob = context.object
        host = ob if panel_type == PanelType.OBJECT else context.active_bone

        active_track_key = host.hubs_component_loop_animation.active_track_key
        host.hubs_component_loop_animation.tracks_list.remove(
            active_track_key)

        if host.hubs_component_loop_animation.active_track_key != 0:
            host.hubs_component_loop_animation.active_track_key -= 1

        if len(host.hubs_component_loop_animation.tracks_list) == 0:
            host.hubs_component_loop_animation.active_track_key = -1

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
        panel_type = PanelType(context.panel.bl_context)
        no_tracks = True
        ob = context.object
        host = ob if panel_type == PanelType.OBJECT else context.active_bone
        if ob.animation_data:
            for _, a in enumerate(ob.animation_data.nla_tracks):
                if not has_track(host.hubs_component_loop_animation.tracks_list, a.name):
                    add_track = self.layout.operator(AddTrackOperator.bl_idname, icon='OBJECT_DATA',
                                         text=a.name)
                    add_track.track_name = a.name
                    add_track.panel_type = panel_type.value
                    no_tracks = False

        if hasattr(ob.data, 'shape_keys') and ob.data.shape_keys and ob.data.shape_keys.animation_data:
            for _, a in enumerate(ob.data.shape_keys.animation_data.nla_tracks):
                if not has_track(context.object.hubs_component_loop_animation.tracks_list, a.name):
                    add_track = self.layout.operator(AddTrackOperator.bl_idname, icon='OBJECT_DATA',
                                         text=a.name)
                    add_track.track_name = a.name
                    add_track.panel_type = panel_type.value
                    no_tracks = False

        if no_tracks:
            self.layout.label(text="No tracks found")


class TrackPropertyType(PropertyGroup):
    name: StringProperty(
        name="Track name",
        description="Track Name",
        default=""
    )


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

    def draw(self, context, layout, panel):
        layout.label(text='Animations to play:')

        row = layout.row()
        row.template_list(TracksList.bl_idname, "", self,
                          "tracks_list", self, "active_track_key", rows=3)

        col = row.column(align=True)

        col.context_pointer_set('panel', panel)
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


def register_module():
    bpy.utils.register_class(TrackPropertyType)


def unregister_module():
    bpy.utils.unregister_class(TrackPropertyType)
