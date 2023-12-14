from bpy.app.handlers import persistent
import bpy
from bpy.types import Context
from .preferences import EXPORT_TMP_FILE_NAME
from .utils import isModuleAvailable, save_prefs
from .icons import get_hubs_icons
from .session import Session, PARAMS_TO_STRING

ROOM_FLAGS_DOC_URL = "https://hubs.mozilla.com/docs/hubs-query-string-parameters.html"


def export_scene(context):
    export_prefs = context.scene.hubs_scene_debugger_room_export_prefs
    import os
    extension = '.glb'
    args = {
        # Settings from "Remember Export Settings"
        **dict(bpy.context.scene.get('glTF2ExportSettings', {})),

        'export_format': ('GLB' if extension == '.glb' else 'GLTF_SEPARATE'),
        'filepath': os.path.join(bpy.app.tempdir, EXPORT_TMP_FILE_NAME),
        'export_cameras': export_prefs.export_cameras,
        'export_lights': export_prefs.export_lights,
        'use_selection': export_prefs.use_selection,
        'use_visible': export_prefs.use_visible,
        'use_renderable': export_prefs.use_renderable,
        'use_active_collection': export_prefs.use_active_collection,
        'export_apply': export_prefs.export_apply,
        'export_force_sampling': False,
    }
    if bpy.app.version >= (3, 2, 0):
        args['use_active_scene'] = True

    bpy.ops.export_scene.gltf(**args)


hubs_session = None


def is_instance_set(context):
    prefs = context.window_manager.hubs_scene_debugger_prefs
    return prefs.hubs_instance_idx != -1


def is_room_set(context):
    prefs = context.window_manager.hubs_scene_debugger_prefs
    return prefs.hubs_room_idx != -1


class HubsUpdateSceneOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.update_scene"
    bl_label = "View Scene"
    bl_description = "Update scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return hubs_session and hubs_session.user_logged_in and hubs_session.user_in_room

    def execute(self, context):
        try:
            export_scene(context)
            hubs_session.update()
            hubs_session.bring_to_front(context)

            return {'FINISHED'}
        except Exception as err:
            print(err)
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report", report_string='\n\n'.join(
                ["The scene export has failed", "Check the export logs or quit the browser instance and try again", f'{err}']))
            return {'CANCELLED'}


class HubsCreateRoomOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.create_room"
    bl_label = "Create Room"
    bl_description = "Create room"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return is_instance_set(context)

    def execute(self, context):
        try:
            was_alive = hubs_session.init(context)

            prefs = context.window_manager.hubs_scene_debugger_prefs
            hubs_instance_url = prefs.hubs_instances[prefs.hubs_instance_idx].url
            hubs_session.load(
                f'{hubs_instance_url}?new&{hubs_session.get_url_params(context)}')

            if was_alive:
                hubs_session.bring_to_front(context)

            return {'FINISHED'}

        except Exception as err:
            hubs_session.close()
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'The room creation has failed: {err}')
            return {"CANCELLED"}


class HubsOpenRoomOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.open_room"
    bl_label = "Open Room"
    bl_description = "Open room"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return is_room_set(context)

    def execute(self, context):
        try:
            was_alive = hubs_session.init(context)

            prefs = context.window_manager.hubs_scene_debugger_prefs
            room_url = prefs.hubs_rooms[prefs.hubs_room_idx].url

            params = hubs_session.get_url_params(context)
            if params:
                if "?" in room_url:
                    hubs_session.load(f'{room_url}&{params}')
                else:
                    hubs_session.load(f'{room_url}?{params}')
            else:
                hubs_session.load(room_url)

            if was_alive:
                hubs_session.bring_to_front(context)

            return {'FINISHED'}

        except Exception as err:
            hubs_session.close()
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'An error happened while opening the room: {err}')
            return {"CANCELLED"}


class HubsCloseRoomOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.close_room"
    bl_label = "Close"
    bl_description = "Close browser window"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return hubs_session.is_alive()

    def execute(self, context):
        try:
            hubs_session.close()
            return {'FINISHED'}

        except Exception as err:
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'An error happened while closing the browser window: {err}')
            return {"CANCELLED"}


class HubsOpenAddonPrefsOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.open_addon_prefs"
    bl_label = "Open Preferences"
    bl_description = "Open Preferences"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return not hubs_session.is_alive()

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        context.preferences.active_section
        bpy.ops.preferences.addon_expand(module=__package__)
        bpy.ops.preferences.addon_show(module=__package__)
        return {'FINISHED'}


class HUBS_PT_ToolsSceneDebuggerCreatePanel(bpy.types.Panel):
    bl_idname = "HUBS_PT_ToolsSceneDebuggerCreatePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Create Room"
    bl_context = 'objectmode'
    bl_parent_id = "HUBS_PT_ToolsSceneDebuggerPanel"

    @classmethod
    def poll(cls, context: Context):
        return isModuleAvailable("selenium")

    def draw(self, context: Context):
        prefs = context.window_manager.hubs_scene_debugger_prefs
        box = self.layout.box()
        row = box.row()
        row.label(text="Instances:")
        row = box.row()
        list_row = row.row()
        list_row.template_list(HUBS_UL_ToolsSceneDebuggerServers.bl_idname, "", prefs,
                               "hubs_instances", prefs, "hubs_instance_idx", rows=3)
        col = row.column()
        col.operator(HubsSceneDebuggerInstanceAdd.bl_idname,
                     icon='ADD', text="")
        col.operator(HubsSceneDebuggerInstanceRemove.bl_idname,
                     icon='REMOVE', text="")

        row = box.row()
        col = row.column()
        col.operator(HubsCreateRoomOperator.bl_idname,
                     text='Create')
        col = row.column()
        col.operator(HubsCloseRoomOperator.bl_idname,
                     text='Close')


class HUBS_PT_ToolsSceneDebuggerOpenPanel(bpy.types.Panel):
    bl_idname = "HUBS_PT_ToolsSceneDebuggerOpenPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Open Room"
    bl_context = 'objectmode'
    bl_parent_id = "HUBS_PT_ToolsSceneDebuggerPanel"

    @classmethod
    def poll(cls, context: Context):
        return isModuleAvailable("selenium")

    def draw(self, context: Context):
        box = self.layout.box()
        prefs = context.window_manager.hubs_scene_debugger_prefs
        row = box.row()
        row.label(text="Rooms:")
        row = box.row()
        list_row = row.row()
        list_row.template_list(HUBS_UL_ToolsSceneDebuggerRooms.bl_idname, "", prefs,
                               "hubs_rooms", prefs, "hubs_room_idx", rows=3)
        col = row.column()
        op = col.operator(HubsSceneDebuggerRoomAdd.bl_idname,
                          icon='ADD', text="")
        op.url = "https://hubs.mozilla.com/demo"
        col.operator(HubsSceneDebuggerRoomRemove.bl_idname,
                     icon='REMOVE', text="")

        row = box.row()
        col = row.column()
        col.operator(HubsOpenRoomOperator.bl_idname,
                     text='Open')
        col = row.column()
        col.operator(HubsCloseRoomOperator.bl_idname,
                     text='Close')


class HUBS_PT_ToolsSceneDebuggerUpdatePanel(bpy.types.Panel):
    bl_idname = "HUBS_PT_ToolsSceneDebuggerUpdatePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Update Scene"
    bl_context = 'objectmode'
    bl_parent_id = "HUBS_PT_ToolsSceneDebuggerPanel"

    @classmethod
    def poll(cls, context: Context):
        return isModuleAvailable("selenium")

    def draw(self, context: Context):
        box = self.layout.box()
        row = box.row()
        row.label(
            text="Set the default export options in the glTF export panel")
        row = box.row()
        col = row.column(heading="Limit To:")
        col.use_property_split = True
        col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                 "use_selection")
        col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                 "use_visible")
        col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                 "use_renderable")
        col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                 "use_active_collection")
        if bpy.app.version >= (3, 2, 0):
            col_row = col.row()
            col_row.enabled = False
            col_row.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                         "use_active_scene")
        row = box.row()
        col = row.column(heading="Data:")
        col.use_property_split = True
        col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                 "export_cameras")
        col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                 "export_lights")
        row = box.row()
        col = row.column(heading="Mesh:")
        col.use_property_split = True
        col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                 "export_apply")
        row = box.row()
        col = row.column(heading="Animation:")
        col.use_property_split = True
        col_row = col.row()
        col_row.enabled = False
        col_row.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                     "export_force_sampling")
        row = box.row()

        update_mode = "Update Scene" if context.scene.hubs_scene_debugger_room_create_prefs.debugLocalScene else "Spawn as object"
        if hubs_session.is_alive():
            room_params = hubs_session.room_params
            update_mode = "Update Scene" if "debugLocalScene" in room_params else "Spawn as object"
        row.operator(HubsUpdateSceneOperator.bl_idname,
                     text=f'{update_mode}')


class HUBS_PT_ToolsSceneDebuggerPanel(bpy.types.Panel):
    bl_idname = "HUBS_PT_ToolsSceneDebuggerPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Scene Debugger"
    bl_context = 'objectmode'
    bl_parent_id = "HUBS_PT_ToolsPanel"

    def draw(self, context):
        main_box = self.layout.box()

        if isModuleAvailable("selenium"):
            row = main_box.row(align=True)
            row.alignment = "CENTER"
            col = row.column()
            col.alignment = "LEFT"
            col.label(text="Connection Status:")
            hubs_icons = get_hubs_icons()
            if hubs_session.is_alive():
                if hubs_session.user_logged_in:
                    if hubs_session.user_in_room:
                        col = row.column()
                        col.alignment = "LEFT"
                        col.active_default = True
                        col.label(
                            icon_value=hubs_icons["green-dot.png"].icon_id)
                        row = main_box.row(align=True)
                        row.alignment = "CENTER"
                        row.label(text=f'In room: {hubs_session.room_name}')

                    else:
                        col = row.column()
                        col.alignment = "LEFT"
                        col.label(
                            icon_value=hubs_icons["orange-dot.png"].icon_id)
                        row = main_box.row(align=True)
                        row.alignment = "CENTER"
                        row.label(text="Entering the room...")
                else:
                    col = row.column()
                    col.alignment = "LEFT"
                    col.alert = True
                    col.label(icon_value=hubs_icons["orange-dot.png"].icon_id)
                    row = main_box.row(align=True)
                    row.alignment = "CENTER"
                    row.label(text="Waiting for sign in...")

            else:
                col = row.column()
                col.alignment = "LEFT"
                col.alert = True
                col.label(icon_value=hubs_icons["red-dot.png"].icon_id)
                row = main_box.row(align=True)
                row.alignment = "CENTER"
                row.label(text="Waiting for room...")

            params_icons = {}
            if isWebdriverAlive():
                for key in PARAMS_TO_STRING.keys():
                    params_icons[key] = 'PANEL_CLOSE'
                params = get_current_room_params()

                for param in params:
                    if param in params_icons:
                        params_icons[param] = 'CHECKMARK'
            else:
                for key in PARAMS_TO_STRING.keys():
                    params_icons[key] = 'REMOVE'

            box = self.layout.box()
            row = box.row(align=True)
            row.alignment = "EXPAND"
            grid = row.grid_flow(columns=2, align=True,
                                 even_rows=False, even_columns=False)
            grid.alignment = "CENTER"
            flags_row = grid.row()
            flags_row.label(text="Room flags")
            op = flags_row.operator("wm.url_open", text="", icon="HELP")
            op.url = ROOM_FLAGS_DOC_URL
            for key in PARAMS_TO_STRING.keys():
                grid.prop(context.scene.hubs_scene_debugger_room_create_prefs,
                          key)
            grid.label(text="Is Active?")
            for key in PARAMS_TO_STRING.keys():
                grid.label(icon=params_icons[key])

        else:
            row = main_box.row()
            row.alert = True
            row.label(
                text="Selenium needs to be installed for the scene debugger functionality. Install from preferences.")
            row = main_box.row()
            row.operator(HubsOpenAddonPrefsOperator.bl_idname,
                         text='Setup')


class HubsSceneDebuggerInstanceAdd(bpy.types.Operator):
    bl_idname = "hubs_scene.scene_debugger_instance_add"
    bl_label = "Add Server Instance"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.window_manager.hubs_scene_debugger_prefs
        new_instance = prefs.hubs_instances.add()
        new_instance.name = "Demo Hub"
        new_instance.url = "https://hubs.mozilla.com/demo"
        prefs.hubs_instance_idx = len(
            prefs.hubs_instances) - 1

        save_prefs(context)

        return {'FINISHED'}


class HubsSceneDebuggerInstanceRemove(bpy.types.Operator):
    bl_idname = "hubs_scene.scene_debugger_instance_remove"
    bl_label = "Remove Server Instance"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.window_manager.hubs_scene_debugger_prefs
        prefs.hubs_instances.remove(prefs.hubs_instance_idx)

        if prefs.hubs_instance_idx >= len(prefs.hubs_instances):
            prefs.hubs_instance_idx -= 1

        save_prefs(context)

        return {'FINISHED'}


class HubsSceneDebuggerRoomAdd(bpy.types.Operator):
    bl_idname = "hubs_scene.scene_debugger_room_add"
    bl_label = "Add Room"
    bl_description = "Adds the current active room url to the list, if there is no active room it will add an empty string"
    bl_options = {'REGISTER', 'UNDO'}

    url: bpy.props.StringProperty(name="Room Url")

    def execute(self, context):
        prefs = context.window_manager.hubs_scene_debugger_prefs
        new_room = prefs.hubs_rooms.add()
        url = self.url
        if hubs_session.is_alive():
            current_url = hubs_session.get_url()
            if current_url:
                url = current_url
                if "hub_id=" in url:
                    url = url.split("&")[0]
                else:
                    url = url.split("?")[0]

        new_room.name = "Room Name"
        if hubs_session.is_alive():
            room_name = hubs_session.room_name
            if room_name:
                new_room.name = room_name
        new_room.url = url
        prefs.hubs_room_idx = len(
            prefs.hubs_rooms) - 1

        save_prefs(context)

        return {'FINISHED'}


class HubsSceneDebuggerRoomRemove(bpy.types.Operator):
    bl_idname = "hubs_scene.scene_debugger_room_remove"
    bl_label = "Remove Room"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        prefs = context.window_manager.hubs_scene_debugger_prefs
        return prefs.hubs_room_idx >= 0

    def execute(self, context):
        prefs = context.window_manager.hubs_scene_debugger_prefs
        prefs.hubs_rooms.remove(prefs.hubs_room_idx)

        if prefs.hubs_room_idx >= len(prefs.hubs_rooms):
            prefs.hubs_room_idx -= 1

        save_prefs(context)

        return {'FINISHED'}


class HUBS_UL_ToolsSceneDebuggerServers(bpy.types.UIList):
    bl_idname = "HUBS_UL_ToolsSceneDebuggerServers"
    bl_label = "Instances"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.25)
        split.prop(item, "name", text="", emboss=False)
        split.prop(item, "url", text="", emboss=False)


class HUBS_UL_ToolsSceneDebuggerRooms(bpy.types.UIList):
    bl_idname = "HUBS_UL_ToolsSceneDebuggerRooms"
    bl_label = "Rooms"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.25)
        split.prop(item, "name", text="", emboss=False)
        split.prop(item, "url", text="", emboss=False)


def set_url(self, value):
    try:
        import urllib
        parsed = urllib.parse.urlparse(value)
        parsed = parsed._replace(scheme="https")
        self.url_ = urllib.parse.urlunparse(parsed)
    except Exception:
        self.url_ = "https://hubs.mozilla.com/demo"


def get_url(self):
    return self.url_


def save_prefs_on_prop_update(self, context):
    save_prefs(context)


class HubsUrl(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(update=save_prefs_on_prop_update)
    url: bpy.props.StringProperty(
        set=set_url, get=get_url, update=save_prefs_on_prop_update)
    url_: bpy.props.StringProperty(options={"HIDDEN"})


class HubsSceneDebuggerPrefs(bpy.types.PropertyGroup):
    hubs_instances: bpy.props.CollectionProperty(
        type=HubsUrl)

    hubs_instance_idx: bpy.props.IntProperty(
        default=-1, update=save_prefs_on_prop_update)

    hubs_room_idx: bpy.props.IntProperty(
        default=-1, update=save_prefs_on_prop_update)

    hubs_rooms: bpy.props.CollectionProperty(
        type=HubsUrl)


class HubsSceneDebuggerRoomCreatePrefs(bpy.types.PropertyGroup):
    newLoader: bpy.props.BoolProperty(
        name=PARAMS_TO_STRING["newLoader"]["name"],
        default=True, description=PARAMS_TO_STRING["newLoader"]["description"])
    ecsDebug: bpy.props.BoolProperty(
        name=PARAMS_TO_STRING["ecsDebug"]["name"],
        default=True, description=PARAMS_TO_STRING["ecsDebug"]["description"])
    vr_entry_type: bpy.props.BoolProperty(
        name=PARAMS_TO_STRING["vr_entry_type"]["name"],
        default=True, description=PARAMS_TO_STRING["vr_entry_type"]["description"])
    debugLocalScene: bpy.props.BoolProperty(name=PARAMS_TO_STRING["debugLocalScene"]["name"], default=True,
                                            description=PARAMS_TO_STRING["debugLocalScene"]["description"])


class HubsSceneDebuggerRoomExportPrefs(bpy.types.PropertyGroup):
    export_cameras: bpy.props.BoolProperty(name="Export Cameras", default=True,
                                           description="Export cameras", options=set())
    export_lights: bpy.props.BoolProperty(
        name="Export Lights", default=True,
        description="Punctual Lights, Export directional, point, and spot lights. Uses \"KHR_lights_punctual\" glTF extension",
        options=set())
    use_selection: bpy.props.BoolProperty(name="Selection Only", default=False,
                                          description="Selection Only, Export selected objects only.",
                                          options=set())
    export_apply: bpy.props.BoolProperty(
        name="Apply Modifiers", default=True,
        description="Apply Modifiers, Apply modifiers (excluding Armatures) to mesh objects -WARNING: prevents exporting shape keys.",
        options=set())
    use_visible: bpy.props.BoolProperty(
        name='Visible Objects',
        description='Export visible objects only',
        default=False,
        options=set()
    )

    use_renderable: bpy.props.BoolProperty(
        name='Renderable Objects',
        description='Export renderable objects only',
        default=False,
        options=set()
    )

    use_active_collection: bpy.props.BoolProperty(
        name='Active Collection',
        description='Export objects in the active collection only',
        default=False,
        options=set()
    )
    use_active_scene: bpy.props.BoolProperty(
        name='Active Scene',
        description='Export objects in the active scene only.  This has been forced ON because Hubs can only use one scene anyway',
        default=True, options=set())
    export_force_sampling: bpy.props.BoolProperty(
        name='Sampling Animations',
        description='Apply sampling to all animations.  This has been forced OFF because it can break animations in Hubs',
        default=False, options=set())


@persistent
def load_post(dummy):
    from .utils import load_prefs
    load_prefs(bpy.context)

    prefs = bpy.context.window_manager.hubs_scene_debugger_prefs
    if len(prefs.hubs_instances) == 0:
        bpy.ops.hubs_scene.scene_debugger_instance_add('INVOKE_DEFAULT')


def register():
    global hubs_session
    hubs_session = Session()

    bpy.utils.register_class(HubsUrl)
    bpy.utils.register_class(HubsSceneDebuggerPrefs)
    bpy.utils.register_class(HubsCreateRoomOperator)
    bpy.utils.register_class(HubsOpenRoomOperator)
    bpy.utils.register_class(HubsCloseRoomOperator)
    bpy.utils.register_class(HubsUpdateSceneOperator)
    bpy.utils.register_class(HUBS_PT_ToolsSceneDebuggerPanel)
    bpy.utils.register_class(HUBS_PT_ToolsSceneDebuggerCreatePanel)
    bpy.utils.register_class(HUBS_PT_ToolsSceneDebuggerOpenPanel)
    bpy.utils.register_class(HUBS_PT_ToolsSceneDebuggerUpdatePanel)
    bpy.utils.register_class(HubsSceneDebuggerRoomCreatePrefs)
    bpy.utils.register_class(HubsOpenAddonPrefsOperator)
    bpy.utils.register_class(HubsSceneDebuggerRoomExportPrefs)
    bpy.utils.register_class(HubsSceneDebuggerInstanceAdd)
    bpy.utils.register_class(HubsSceneDebuggerInstanceRemove)
    bpy.utils.register_class(HubsSceneDebuggerRoomAdd)
    bpy.utils.register_class(HubsSceneDebuggerRoomRemove)
    bpy.utils.register_class(HUBS_UL_ToolsSceneDebuggerServers)
    bpy.utils.register_class(HUBS_UL_ToolsSceneDebuggerRooms)

    bpy.types.Scene.hubs_scene_debugger_room_create_prefs = bpy.props.PointerProperty(
        type=HubsSceneDebuggerRoomCreatePrefs)
    bpy.types.Scene.hubs_scene_debugger_room_export_prefs = bpy.props.PointerProperty(
        type=HubsSceneDebuggerRoomExportPrefs)
    bpy.types.WindowManager.hubs_scene_debugger_prefs = bpy.props.PointerProperty(
        type=HubsSceneDebuggerPrefs)

    if load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post)


def unregister():
    bpy.utils.unregister_class(HubsUpdateSceneOperator)
    bpy.utils.unregister_class(HubsOpenRoomOperator)
    bpy.utils.unregister_class(HubsCloseRoomOperator)
    bpy.utils.unregister_class(HubsCreateRoomOperator)
    bpy.utils.unregister_class(HUBS_PT_ToolsSceneDebuggerCreatePanel)
    bpy.utils.unregister_class(HUBS_PT_ToolsSceneDebuggerOpenPanel)
    bpy.utils.unregister_class(HUBS_PT_ToolsSceneDebuggerUpdatePanel)
    bpy.utils.unregister_class(HUBS_PT_ToolsSceneDebuggerPanel)
    bpy.utils.unregister_class(HubsSceneDebuggerRoomCreatePrefs)
    bpy.utils.unregister_class(HubsOpenAddonPrefsOperator)
    bpy.utils.unregister_class(HubsSceneDebuggerRoomExportPrefs)
    bpy.utils.unregister_class(HUBS_UL_ToolsSceneDebuggerServers)
    bpy.utils.unregister_class(HUBS_UL_ToolsSceneDebuggerRooms)
    bpy.utils.unregister_class(HubsSceneDebuggerInstanceAdd)
    bpy.utils.unregister_class(HubsSceneDebuggerInstanceRemove)
    bpy.utils.unregister_class(HubsSceneDebuggerRoomAdd)
    bpy.utils.unregister_class(HubsSceneDebuggerRoomRemove)
    bpy.utils.unregister_class(HubsSceneDebuggerPrefs)
    bpy.utils.unregister_class(HubsUrl)

    del bpy.types.Scene.hubs_scene_debugger_room_create_prefs
    del bpy.types.Scene.hubs_scene_debugger_room_export_prefs
    del bpy.types.WindowManager.hubs_scene_debugger_prefs

    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    hubs_session.close()
