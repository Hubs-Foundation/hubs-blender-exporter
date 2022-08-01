import atexit
import bpy
from bpy.app.handlers import persistent
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty, EnumProperty
from bpy.types import PropertyGroup, Menu, Operator
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..utils import redraw_component_ui

nla_track_name_msgbus_owner = None
action_name_msgbus_owner = None

class TrackPropertyType(PropertyGroup):
    name: StringProperty(
        name="Display Name",
        description="Display Name",
    )
    track_name: StringProperty(
        name="Track Name",
        description="Track Name",
    )
    action_name: StringProperty( # Will only contain data if the track name is generic
        name="Action Name",
        description="Action Name",
    )
    track_type: EnumProperty(
        name="Track Type",
        description="Track Type",
        items=[
            ("object", "Object", "Object"),
            ("shape_key", "Shape Key", "Shape Key")
            ],
        default="object"
    )

bpy.utils.register_class(TrackPropertyType)

@atexit.register
def unregister():
    bpy.utils.unregister_class(TrackPropertyType)

def register_msgbus():
    global nla_track_name_msgbus_owner
    global action_name_msgbus_owner

    if nla_track_name_msgbus_owner:
        return

    nla_track_name_msgbus_owner = object()
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.NlaTrack, "name"),
        owner=nla_track_name_msgbus_owner,
        args=(bpy.context,),
        notify=redraw_component_ui,
    )

    if action_name_msgbus_owner:
        return

    action_name_msgbus_owner = object()
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Action, "name"),
        owner=action_name_msgbus_owner,
        args=(bpy.context,),
        notify=redraw_component_ui,
    )

def unregister_msgbus():
    global nla_track_name_msgbus_owner
    global action_name_msgbus_owner

    bpy.msgbus.clear_by_owner(nla_track_name_msgbus_owner)
    bpy.msgbus.clear_by_owner(action_name_msgbus_owner)

    nla_track_name_msgbus_owner = None
    action_name_msgbus_owner = None

@persistent
def load_post(dummy):
    unregister_msgbus()
    register_msgbus()

def is_default_name(track_name):
    return bool(track_name.startswith("NlaTrack") or track_name.startswith("[Action Stash]"))

def get_display_name(track_name, action_name):
    return track_name if not is_default_name(track_name) else f"{track_name} ({action_name})"

def get_action_name(nla_track):
    try:
        return nla_track.strips[0].name
    except IndexError:
        return ''

def has_track(tracks_list, nla_track):
    action_name = get_action_name(nla_track)
    exists = False
    for track in tracks_list:
        if is_default_name(nla_track.name):
            if track.track_name == nla_track.name and track.action_name == action_name:
                exists = True
                break

        else:
            if track.track_name == nla_track.name:
                exists = True
                break

    return exists

def is_matching_track(nla_track, track):
    if is_default_name(nla_track.name):
        if nla_track.name == track.track_name and get_action_name(nla_track) == track.action_name:
            return True

    else:
        if nla_track.name == track.track_name:
            return True

    return False

def is_useable_nla_track(nla_track):
    track_name = nla_track.name
    action_name = get_action_name(nla_track)

    forbidden_chars = [",", " "]
    has_forbidden_chars = False
    if not is_default_name(track_name):
        if any([c for c in forbidden_chars if c in track_name]):
            has_forbidden_chars = True
    else:
        if any([c for c in forbidden_chars if c in action_name]):
            has_forbidden_chars = True

    return len(nla_track.strips) == 1 and action_name in bpy.data.actions and not has_forbidden_chars

def is_valid_regular_track(ob, track):
    if ob.animation_data:
        for nla_track in ob.animation_data.nla_tracks:
            if is_matching_track(nla_track, track):
                if is_useable_nla_track(nla_track):
                    return True

                return False

    return False

def is_valid_shape_key_track(ob, track):
    if hasattr(ob.data, 'shape_keys') and ob.data.shape_keys and ob.data.shape_keys.animation_data:
        for nla_track in ob.data.shape_keys.animation_data.nla_tracks:
            if is_matching_track(nla_track, track):
                if is_useable_nla_track(nla_track):
                    return True

                return False

    return False


class TracksList(bpy.types.UIList):
    bl_idname = "HUBS_UL_TRACKS_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        key_block = item
        ob = context.object
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.90, align=False)
            if item.track_type == "object" and is_valid_regular_track(ob, item):
                split.prop(key_block, "name", text="",
                           emboss=False, icon='OBJECT_DATA')
                split.enabled = False
            elif item.track_type == "shape_key" and is_valid_shape_key_track(ob, item):
                split.prop(key_block, "name", text="",
                           emboss=False, icon='SHAPEKEY_DATA')
                split.enabled = False
            else:
                spacer = '  ' # needed so the menu arrow doesn't intersect with the name
                row = split.row(align=False)
                row.emboss = 'NONE'
                row.alignment = 'LEFT'
                row.context_pointer_set('hubs_component', data)
                row.context_pointer_set('track', item)
                row.menu(UpdateTrackContextMenu.bl_idname, text=item.name+spacer, icon='ERROR')
            row = split.row(align=True)
            row.emboss = 'UI_EMBOSS_NONE_OR_STATUS' if bpy.app.version < (3, 0, 0) else 'NONE_OR_STATUS'
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class UpdateTrack(Operator):
    bl_idname = "hubs_loop_animation.update_track"
    bl_label = "Update the track with a new NLA Track"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(
        name="Display Name", description="Display Name", default="")

    track_name: StringProperty(
        name="Track Name", description="Track Name", default="")

    action_name: StringProperty(
        name="Action Name", description="Action Name", default="")

    track_type: StringProperty(
        name="Track Type", description="Track Type", default="")


    def execute(self, context):
        track = context.track
        track.name = self.name
        track.track_name = self.track_name
        track.action_name = self.action_name
        track.track_type = self.track_type

        redraw_component_ui(context)
        return {'FINISHED'}


class AddTrackOperator(Operator):
    bl_idname = "hubs_loop_animation.add_track"
    bl_label = "Add Track"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(
        name="Display Name", description="Display Name", default="")

    track_name: StringProperty(
        name="Track Name", description="Track Name", default="")

    action_name: StringProperty(
        name="Action Name", description="Action Name", default="")

    track_type: StringProperty(
        name="Track Type", description="Track Type", default="")

    panel_type: StringProperty(name="panel_type")

    def execute(self, context):
        panel_type = PanelType(self.panel_type)
        ob = context.object
        host = ob if panel_type == PanelType.OBJECT else context.active_bone

        track = host.hubs_component_loop_animation.tracks_list.add()
        track.name = self.name
        track.track_name = self.track_name
        track.action_name = self.action_name
        track.track_type = self.track_type

        num_tracks = len(host.hubs_component_loop_animation.tracks_list)
        host.hubs_component_loop_animation.active_track_key = num_tracks - 1

        redraw_component_ui(context)

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

        redraw_component_ui(context)

        return {'FINISHED'}


class UpdateTrackContextMenu(Menu):
    bl_idname = "HUBS_MT_TRACKS_update_track_context_menu"
    bl_label = "Update Track"

    def draw(self, context):
        track = context.track
        hubs_component = context.hubs_component
        layout = self.layout
        no_tracks = True
        menu_tracks = []
        ob = context.object

        if ob.animation_data:
            for _, nla_track in enumerate(ob.animation_data.nla_tracks):
                action_name = get_action_name(nla_track)
                display_name = get_display_name(nla_track.name, action_name)

                if display_name not in menu_tracks and not has_track(hubs_component.tracks_list, nla_track):
                    row = layout.row(align=False)
                    row.context_pointer_set('track', track)

                    update_track = row.operator(UpdateTrack.bl_idname,
                                         icon='OBJECT_DATA', text=display_name)
                    update_track.name = display_name
                    update_track.track_name = nla_track.name
                    update_track.action_name = action_name if is_default_name(nla_track.name) else ''
                    update_track.track_type = "object"

                    no_tracks = False
                    menu_tracks.append(display_name)

        if hasattr(ob.data, 'shape_keys') and ob.data.shape_keys and ob.data.shape_keys.animation_data:
            for _, nla_track in enumerate(ob.data.shape_keys.animation_data.nla_tracks):
                action_name = get_action_name(nla_track)
                display_name = get_display_name(nla_track.name, action_name)

                if display_name not in menu_tracks and not has_track(hubs_component.tracks_list, nla_track):
                    row = layout.row(align=False)
                    row.context_pointer_set('track', track)

                    update_track = row.operator(UpdateTrack.bl_idname,
                                         icon='SHAPEKEY_DATA', text=display_name)
                    update_track.name = display_name
                    update_track.track_name = nla_track.name
                    update_track.action_name = action_name if is_default_name(nla_track.name) else ''
                    update_track.track_type = "shape_key"

                    no_tracks = False
                    menu_tracks.append(display_name)

        if no_tracks:
            layout.label(text="No tracks found")


class TracksContextMenu(Menu):
    bl_idname = "HUBS_MT_TRACKS_context_menu"
    bl_label = "Add Track"

    def draw(self, context):
        panel_type = PanelType(context.panel.bl_context)
        layout = self.layout
        no_tracks = True
        menu_tracks = []
        ob = context.object
        host = ob if panel_type == PanelType.OBJECT else context.active_bone
        component_tracks_list = host.hubs_component_loop_animation.tracks_list

        if ob.animation_data:
            for _, nla_track in enumerate(ob.animation_data.nla_tracks):
                action_name = get_action_name(nla_track)
                display_name = get_display_name(nla_track.name, action_name)

                if display_name not in menu_tracks and not has_track(component_tracks_list, nla_track):
                    add_track = layout.operator(AddTrackOperator.bl_idname,
                                         icon='OBJECT_DATA', text=display_name)
                    add_track.name = display_name
                    add_track.track_name = nla_track.name
                    add_track.action_name = action_name if is_default_name(nla_track.name) else ''
                    add_track.track_type = "object"
                    add_track.panel_type = panel_type.value

                    no_tracks = False
                    menu_tracks.append(display_name)

        if hasattr(ob.data, 'shape_keys') and ob.data.shape_keys and ob.data.shape_keys.animation_data:
            for _, nla_track in enumerate(ob.data.shape_keys.animation_data.nla_tracks):
                action_name = get_action_name(nla_track)
                display_name = get_display_name(nla_track.name, action_name)

                if display_name not in menu_tracks and not has_track(component_tracks_list, nla_track):
                    add_track = layout.operator(AddTrackOperator.bl_idname,
                                         icon='SHAPEKEY_DATA', text=display_name)
                    add_track.name = display_name
                    add_track.track_name = nla_track.name
                    add_track.action_name = action_name if is_default_name(nla_track.name) else ''
                    add_track.track_type = "shape_key"
                    add_track.panel_type = panel_type.value

                    no_tracks = False
                    menu_tracks.append(display_name)

        if no_tracks:
            layout.label(text="No tracks found")


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
        final_track_names = []
        for track in object.hubs_component_loop_animation.tracks_list.values():
            final_track_names.append(track.track_name if not is_default_name(track.track_name) else track.action_name)

        return {
            'clip': ",".join(
                final_track_names),
            'paused': self.paused
        }


    @staticmethod
    def register():
        bpy.utils.register_class(TracksList)
        bpy.utils.register_class(UpdateTrackContextMenu)
        bpy.utils.register_class(TracksContextMenu)
        bpy.utils.register_class(UpdateTrack)
        bpy.utils.register_class(AddTrackOperator)
        bpy.utils.register_class(RemoveTrackOperator)

        if not load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(load_post)

        register_msgbus()


    @staticmethod
    def unregister():
        global msgbus_owners

        bpy.utils.unregister_class(TracksList)
        bpy.utils.unregister_class(UpdateTrackContextMenu)
        bpy.utils.unregister_class(TracksContextMenu)
        bpy.utils.unregister_class(UpdateTrack)
        bpy.utils.unregister_class(AddTrackOperator)
        bpy.utils.unregister_class(RemoveTrackOperator)

        if load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_post)

        unregister_msgbus()

    @classmethod
    def migrate(cls, version):
        if version < (1, 0, 0):
            def migrate_data(ob, host):
                if cls.get_name() in host.hubs_component_list.items:
                    tracks = host.hubs_component_loop_animation.clip.split(",")
                    for track_name in tracks:
                        try:
                            nla_track = ob.animation_data.nla_tracks[track_name]
                            track_type = "object"
                        except (AttributeError, KeyError):
                            try:
                                nla_track = ob.data.shape_keys.animation_data.nla_tracks[track_name]
                                track_type = "shape_key"
                            except (AttributeError, KeyError):
                                track = host.hubs_component_loop_animation.tracks_list.add()
                                track.name = track_name
                                continue

                        if not has_track(host.hubs_component_loop_animation.tracks_list, nla_track):
                            track = host.hubs_component_loop_animation.tracks_list.add()
                            action_name = get_action_name(nla_track)
                            track.name = get_display_name(nla_track.name, action_name)
                            track.track_name = nla_track.name
                            track.action_name = action_name if is_default_name(nla_track.name) else ''
                            track.track_type = track_type

            for ob in bpy.data.objects:
                migrate_data(ob, ob)

                if ob.type == 'ARMATURE':
                    for bone in ob.data.bones:
                        migrate_data(ob, bone)
