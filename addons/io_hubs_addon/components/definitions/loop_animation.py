import bpy
from bpy.app.handlers import persistent
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import PropertyGroup, Menu, Operator
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..utils import redraw_component_ui

msgbus_owners = []


class TrackPropertyType(PropertyGroup):
    name: StringProperty(
        name="Display Name",
        description="Display Name",
    )
    track_name: StringProperty(
        name="Track Name",
        description="Track Name",
    )
    strip_name: StringProperty(  # Will only contain data if the track name is generic
        name="Strip Name",
        description="Strip Name",
    )
    action_name: StringProperty(  # Will only contain data if the track name is generic
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


class Errors():
    _errors = {}

    @classmethod
    def log(cls, track, error_type, error_message, severity='Error'):
        has_error = cls._errors.get(track.track_type + track.name, '')
        if not has_error:
            cls._errors[track.track_type + track.name] = {
                'type': error_type, 'message': error_message, 'severity': severity}

    @classmethod
    def get(cls, track):
        return cls._errors.get(track.track_type + track.name, '')

    @classmethod
    def clear(cls):
        cls._errors.clear()

    @classmethod
    def are_present(cls):
        return bool(cls._errors)

    @classmethod
    def display_error(cls, layout, error):
        message_lines = error['message'].split('\n')
        padding = layout.row(align=False)
        padding.scale_y = 0.18
        padding.label()
        for i, line in enumerate(message_lines):
            error_row = layout.row(align=False)
            error_row.scale_y = 0.7

            if i == 0:
                error_row.label(
                    text=f"{error['severity']}: {line}", icon='ERROR')
            else:
                error_row.label(text=line, icon='BLANK1')

        padding = layout.row(align=False)
        padding.scale_y = 0.2
        padding.label()


def register_msgbus():
    global msgbus_owners

    if msgbus_owners:
        return

    for animtype in [bpy.types.NlaTrack, bpy.types.NlaStrip, bpy.types.Action]:
        owner = object()
        msgbus_owners.append(owner)
        bpy.msgbus.subscribe_rna(
            key=(animtype, "name"),
            owner=owner,
            args=(bpy.context,),
            notify=redraw_component_ui,
        )


def unregister_msgbus():
    global msgbus_owners

    for owner in msgbus_owners:
        bpy.msgbus.clear_by_owner(owner)
    msgbus_owners.clear()


@persistent
def load_post(dummy):
    unregister_msgbus()
    register_msgbus()


@persistent
def undo_redo_post(dummy):
    unregister_msgbus()
    register_msgbus()


def is_default_name(track_name):
    return bool(track_name.startswith("NlaTrack") or track_name.startswith("[Action Stash]"))


def get_display_name(track_name, strip_name):
    return track_name if not is_default_name(track_name) else f"{track_name} ({strip_name})"


def get_strip_name(nla_track):
    try:
        return nla_track.strips[0].name
    except IndexError:
        return ''


def get_action_name(nla_track):
    try:
        return nla_track.strips[0].action.name
    except (IndexError, AttributeError):
        return ''


def get_menu_id(nla_track, track_type, display_name):
    return display_name if not is_default_name(nla_track.name) else track_type + display_name


def is_unique_action(animation_data, target_nla_track):
    try:
        target_action = target_nla_track.strips[0].action
    except (IndexError):
        return True

    for nla_track in animation_data.nla_tracks:
        if nla_track == target_nla_track:
            continue

        try:
            action = nla_track.strips[0].action
        except (IndexError):
            continue

        if action == target_action:
            return False

    return True


def has_track(tracks_list, nla_track, invalid_track=None):
    strip_name = get_strip_name(nla_track)
    action_name = get_action_name(nla_track)
    exists = False
    for track in tracks_list:
        if is_default_name(nla_track.name):
            if track.track_name == nla_track.name and track.strip_name == strip_name and track.action_name == action_name:
                exists = True
                break

        else:
            if track.track_name == nla_track.name and track != invalid_track:
                exists = True
                break

    return exists


def is_matching_track(nla_track_type, nla_track, track):
    if nla_track_type != track.track_type:
        return False

    if is_default_name(nla_track.name):
        if nla_track.name == track.track_name:
            if get_strip_name(nla_track) == track.strip_name:
                if get_action_name(nla_track) == track.action_name:
                    return True

                Errors.log(track, 'INVALID_ACTION',
                           "The action has changed for this strip/track.\nChoose the track again to update.")

    else:
        if nla_track.name == track.track_name:
            return True

    return False


def is_useable_nla_track(animation_data, nla_track, track):
    track_name = nla_track.name
    action_name = get_action_name(nla_track)

    if track_name == '':
        Errors.log(track, 'FORBIDDEN_NAME', "Track names can't be nothing.")
        return False

    forbidden_chars = [",", " "]
    if not is_default_name(track_name):
        if any([c for c in forbidden_chars if c in track_name]):
            Errors.log(track, 'FORBIDDEN_NAME',
                       "Custom track names can't contain commas or spaces.")
            return False

    else:
        if any([c for c in forbidden_chars if c in action_name]):
            Errors.log(track, 'FORBIDDEN_NAME',
                       "Action names can't contain commas or spaces.")
            return False

    if len(nla_track.strips) > 1:
        Errors.log(track, 'MULTIPLE_STRIPS',
                   "Only one strip is allowed in the track.")
        return False

    if not nla_track.strips:
        Errors.log(track, 'NO_STRIPS', "No strips are present in the track.")
        return False

    if nla_track.strips[0].mute:
        Errors.log(track, 'MUTED_STRIP',
                   "The strip is muted and won't export.")
        return False

    if not action_name:
        Errors.log(track, 'NO_ACTION',
                   "The strip/track doesn't have an action.")
        return False

    if not nla_track.strips[0].action.fcurves:
        Errors.log(track, 'NO_FCURVES',
                   "The strip/track's action doesn't have any animation and\nwon't be exported.")
        return False

    if not is_unique_action(animation_data, nla_track):
        Errors.log(
            track, 'NON_UNIQUE_ACTION',
            "This strip/track contains an action that is present in multiple\nstrips/tracks on this object and may not export correctly.",
            severity="Warning")
        return False

    return True


def is_valid_regular_track(ob, track):
    if ob.animation_data:
        for nla_track in ob.animation_data.nla_tracks:
            if is_matching_track("object", nla_track, track):
                if is_useable_nla_track(ob.animation_data, nla_track, track):
                    return True

                return False

    Errors.log(track, 'NOT_FOUND', "Track not found.  Did you mean:")

    return False


def is_valid_shape_key_track(ob, track):
    if hasattr(ob.data, 'shape_keys') and ob.data.shape_keys and ob.data.shape_keys.animation_data:
        for nla_track in ob.data.shape_keys.animation_data.nla_tracks:
            if is_matching_track("shape_key", nla_track, track):
                if is_useable_nla_track(ob.data.shape_keys.animation_data, nla_track, track):
                    return True

                return False

    Errors.log(track, 'NOT_FOUND', "Track not found.  Did you mean:")

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
                spacer = '  '  # needed so the menu arrow doesn't intersect with the name
                row = split.row(align=False)
                row.emboss = 'NONE'
                row.alignment = 'LEFT'
                row.context_pointer_set('hubs_component', data)
                row.context_pointer_set('track', item)
                row.menu(UpdateTrackContextMenu.bl_idname,
                         text=item.name + spacer, icon='ERROR')
            row = split.row(align=True)
            row.emboss = 'UI_EMBOSS_NONE_OR_STATUS' if bpy.app.version < (
                3, 0, 0) else 'NONE_OR_STATUS'
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

    strip_name: StringProperty(
        name="Strip Name", description="Strip Name", default="")

    action_name: StringProperty(
        name="Action Name", description="Action Name", default="")

    track_type: StringProperty(
        name="Track Type", description="Track Type", default="")

    def execute(self, context):
        track = context.track
        track.name = self.name
        track.track_name = self.track_name
        track.strip_name = self.strip_name
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

    strip_name: StringProperty(
        name="Strip Name", description="Strip Name", default="")

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
        track.strip_name = self.strip_name
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

        error = Errors.get(track)
        if error:
            Errors.display_error(layout, error)
            if error['type'] not in ['NOT_FOUND', 'INVALID_ACTION']:
                return

            layout.separator()

        if ob.animation_data:
            for _, nla_track in enumerate(ob.animation_data.nla_tracks):
                strip_name = get_strip_name(nla_track)
                action_name = get_action_name(nla_track)
                display_name = get_display_name(nla_track.name, strip_name)
                track_type = "object"
                menu_id = get_menu_id(nla_track, track_type, display_name)

                if menu_id not in menu_tracks and not has_track(
                        hubs_component.tracks_list, nla_track, invalid_track=track):
                    row = layout.row(align=False)
                    row.context_pointer_set('track', track)

                    update_track = row.operator(UpdateTrack.bl_idname,
                                                icon='OBJECT_DATA', text=display_name)
                    update_track.name = display_name
                    update_track.track_name = nla_track.name
                    update_track.strip_name = strip_name if is_default_name(
                        nla_track.name) else ''
                    update_track.action_name = action_name if is_default_name(
                        nla_track.name) else ''
                    update_track.track_type = track_type

                    no_tracks = False
                    menu_tracks.append(menu_id)

        if hasattr(ob.data, 'shape_keys') and ob.data.shape_keys and ob.data.shape_keys.animation_data:
            for _, nla_track in enumerate(ob.data.shape_keys.animation_data.nla_tracks):
                strip_name = get_strip_name(nla_track)
                action_name = get_action_name(nla_track)
                display_name = get_display_name(nla_track.name, strip_name)
                track_type = "shape_key"
                menu_id = get_menu_id(nla_track, track_type, display_name)

                if menu_id not in menu_tracks and not has_track(
                        hubs_component.tracks_list, nla_track, invalid_track=track):
                    row = layout.row(align=False)
                    row.context_pointer_set('track', track)

                    update_track = row.operator(UpdateTrack.bl_idname,
                                                icon='SHAPEKEY_DATA', text=display_name)
                    update_track.name = display_name
                    update_track.track_name = nla_track.name
                    update_track.strip_name = strip_name if is_default_name(
                        nla_track.name) else ''
                    update_track.action_name = action_name if is_default_name(
                        nla_track.name) else ''
                    update_track.track_type = track_type

                    no_tracks = False
                    menu_tracks.append(menu_id)

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
                strip_name = get_strip_name(nla_track)
                action_name = get_action_name(nla_track)
                display_name = get_display_name(nla_track.name, strip_name)
                track_type = "object"
                menu_id = get_menu_id(nla_track, track_type, display_name)

                if menu_id not in menu_tracks and not has_track(component_tracks_list, nla_track):
                    add_track = layout.operator(AddTrackOperator.bl_idname,
                                                icon='OBJECT_DATA', text=display_name)
                    add_track.name = display_name
                    add_track.track_name = nla_track.name
                    add_track.strip_name = strip_name if is_default_name(
                        nla_track.name) else ''
                    add_track.action_name = action_name if is_default_name(
                        nla_track.name) else ''
                    add_track.track_type = track_type
                    add_track.panel_type = panel_type.value

                    no_tracks = False
                    menu_tracks.append(menu_id)

        if hasattr(ob.data, 'shape_keys') and ob.data.shape_keys and ob.data.shape_keys.animation_data:
            for _, nla_track in enumerate(ob.data.shape_keys.animation_data.nla_tracks):
                strip_name = get_strip_name(nla_track)
                action_name = get_action_name(nla_track)
                display_name = get_display_name(nla_track.name, strip_name)
                track_type = "shape_key"
                menu_id = get_menu_id(nla_track, track_type, display_name)

                if menu_id not in menu_tracks and not has_track(component_tracks_list, nla_track):
                    add_track = layout.operator(AddTrackOperator.bl_idname,
                                                icon='SHAPEKEY_DATA', text=display_name)
                    add_track.name = display_name
                    add_track.track_name = nla_track.name
                    add_track.strip_name = strip_name if is_default_name(
                        nla_track.name) else ''
                    add_track.action_name = action_name if is_default_name(
                        nla_track.name) else ''
                    add_track.track_type = track_type
                    add_track.panel_type = panel_type.value

                    no_tracks = False
                    menu_tracks.append(menu_id)

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

    startOffset: IntProperty(
        name="Start Offset",
        description="Time in frames to skip on the first loop of the animation",
        default=0
    )

    timeScale: FloatProperty(
        name="Time Scale",
        description="Scale animation playback speed by this factor. Normal playback rate being 1. Negative values will play the animation backwards",
        default=1.0
    )

    def draw(self, context, layout, panel):
        Errors.clear()

        layout.prop(data=self, property="startOffset")
        layout.prop(data=self, property="timeScale")

        layout.label(text='Animations to play:')

        row = layout.row()
        row.template_list(TracksList.bl_idname, "", self,
                          "tracks_list", self, "active_track_key", rows=3)

        col = row.column(align=True)

        col.context_pointer_set('panel', panel)
        col.menu(TracksContextMenu.bl_idname, icon='ADD', text="")
        col.operator(RemoveTrackOperator.bl_idname,
                     icon='REMOVE', text="")

        if Errors.are_present():
            error_row = layout.row()
            error_row.alert = True
            error_row.label(text="Errors detected, click on the flagged tracks for more information.",
                            icon='ERROR')

        layout.separator()

    def gather(self, export_settings, object):
        final_track_names = []
        for track in object.hubs_component_loop_animation.tracks_list.values():
            final_track_names.append(track.track_name if not is_default_name(
                track.track_name) else track.action_name)

        fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base

        return {
            'clip': ",".join(
                final_track_names),
            'startOffset': self.startOffset / fps,
            'timeScale': self.timeScale
        }

    @staticmethod
    def register():
        bpy.utils.register_class(TracksList)
        bpy.utils.register_class(UpdateTrackContextMenu)
        bpy.utils.register_class(TracksContextMenu)
        bpy.utils.register_class(UpdateTrack)
        bpy.utils.register_class(AddTrackOperator)
        bpy.utils.register_class(RemoveTrackOperator)

        if load_post not in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(load_post)
        if undo_redo_post not in bpy.app.handlers.undo_post:
            bpy.app.handlers.undo_post.append(undo_redo_post)
        if undo_redo_post not in bpy.app.handlers.redo_post:
            bpy.app.handlers.redo_post.append(undo_redo_post)

        register_msgbus()

    @staticmethod
    def unregister():
        bpy.utils.unregister_class(TracksList)
        bpy.utils.unregister_class(UpdateTrackContextMenu)
        bpy.utils.unregister_class(TracksContextMenu)
        bpy.utils.unregister_class(UpdateTrack)
        bpy.utils.unregister_class(AddTrackOperator)
        bpy.utils.unregister_class(RemoveTrackOperator)

        if load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_post)
        if undo_redo_post in bpy.app.handlers.undo_post:
            bpy.app.handlers.undo_post.remove(undo_redo_post)
        if undo_redo_post in bpy.app.handlers.redo_post:
            bpy.app.handlers.redo_post.remove(undo_redo_post)

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
                            strip_name = get_strip_name(nla_track)
                            action_name = get_action_name(nla_track)
                            track.name = get_display_name(
                                nla_track.name, strip_name)
                            track.track_name = nla_track.name
                            track.strip_name = strip_name if is_default_name(
                                nla_track.name) else ''
                            track.action_name = action_name if is_default_name(
                                nla_track.name) else ''
                            track.track_type = track_type

            for ob in bpy.data.objects:
                migrate_data(ob, ob)

                if ob.type == 'ARMATURE':
                    for bone in ob.data.bones:
                        migrate_data(ob, bone)


def register_module():
    bpy.utils.register_class(TrackPropertyType)


def unregister_module():
    bpy.utils.unregister_class(TrackPropertyType)
