from bpy.app.handlers import persistent
import bpy
from bpy.types import Context
from .preferences import EXPORT_TMP_FILE_NAME
from .utils import isModuleAvailable, save_prefs
from .icons import get_hubs_icons
from .hubs_session import HubsSession, PARAMS_TO_STRING
from . import api
from bpy.types import AnyType

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


class HubsUpdateRoomOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.update_room"
    bl_label = "View Scene"
    bl_description = "Update room"
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
                f'{hubs_instance_url}?new&{hubs_session.url_params_string_from_prefs(context)}')

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

            params = hubs_session.url_params_string_from_prefs(context)
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
    bl_description = "Close session"
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
        row.operator(HubsCreateRoomOperator.bl_idname,
                     text='Create')


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
        row.operator(HubsOpenRoomOperator.bl_idname,
                     text='Open')


class HUBS_PT_ToolsSceneDebuggerUpdatePanel(bpy.types.Panel):
    bl_idname = "HUBS_PT_ToolsSceneDebuggerUpdatePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Update Room Scene"
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
        if not hubs_session.is_alive() or not hubs_session.user_logged_in:
            row = box.row()
            row.alert = True
            row.label(
                text="You need to be signed in Hubs to update the room scene or spawn objects")

        update_mode = "Update Scene" if context.scene.hubs_scene_debugger_room_create_prefs.debugLocalScene else "Spawn as object"
        if hubs_session.is_alive():
            room_params = hubs_session.room_params
            update_mode = "Update Scene" if "debugLocalScene" in room_params else "Spawn as object"
        row = box.row()
        row.operator(HubsUpdateRoomOperator.bl_idname,
                     text=f'{update_mode}')


class HUBS_PT_ToolsSceneSessionPanel(bpy.types.Panel):
    bl_idname = "HUBS_PT_ToolsSceneSessionPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Status"
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
                    row.label(text="Waiting for session sign in...")

                ret_instance = hubs_session.reticulum_url
                if ret_instance:
                    row = main_box.row(align=True)
                    row.alignment = "CENTER"
                    row.label(
                        text=f'Connected to Instance: {ret_instance}')

            else:
                col = row.column()
                col.alignment = "LEFT"
                col.alert = True
                col.label(icon_value=hubs_icons["red-dot.png"].icon_id)
                row = main_box.row(align=True)
                row.alignment = "CENTER"
                row.label(text="Waiting for session...")

            row = self.layout.row()
            row.operator(HubsCloseRoomOperator.bl_idname, text='Close')

        else:
            row = main_box.row()
            row.alert = True
            row.label(
                text="Selenium needs to be installed for the scene debugger functionality. Install from preferences.")
            row = main_box.row()
            row.operator(HubsOpenAddonPrefsOperator.bl_idname,
                         text='Setup')


class HUBS_PT_ToolsSceneDebuggerPanel(bpy.types.Panel):
    bl_idname = "HUBS_PT_ToolsSceneDebuggerPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Debug"
    bl_context = 'objectmode'
    bl_parent_id = "HUBS_PT_ToolsPanel"

    @classmethod
    def poll(cls, context: Context):
        return isModuleAvailable("selenium")

    def draw(self, context):
        params_icons = {}
        if hubs_session.is_alive():
            for key in PARAMS_TO_STRING.keys():
                params_icons[key] = 'PANEL_CLOSE'

            for param in hubs_session.room_params:
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


def add_instance(context):
    prefs = context.window_manager.hubs_scene_debugger_prefs
    new_instance = prefs.hubs_instances.add()
    new_instance.name = "Demo Hub"
    new_instance.url = "https://hubs.mozilla.com/demo"
    prefs.hubs_instance_idx = len(
        prefs.hubs_instances) - 1

    save_prefs(context)


class HubsSceneDebuggerInstanceAdd(bpy.types.Operator):
    bl_idname = "hubs_scene.scene_debugger_instance_add"
    bl_label = "Add Server Instance"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        add_instance(context)

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


class HubsPublishSceneOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.publish_scene"
    bl_label = "Scene Manager"
    bl_description = "Publish scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        props = context.scene.hubs_scene_debugger_scene_publish_props
        return hubs_session.is_alive() and hubs_session.user_logged_in and props.screenshot and props.scene_name

    def execute(self, context):
        try:
            export_scene(context)
            import os
            url = hubs_session.reticulum_url

            scene_data = {}

            name = context.scene.hubs_scene_debugger_scene_publish_props.scene_name
            scene_data.update({"name": name})

            glb_path = os.path.join(bpy.app.tempdir, EXPORT_TMP_FILE_NAME)
            glb = open(glb_path, "rb")
            glb_data = api.upload_media(url, glb)
            scene_data.update({
                "model_file_id": glb_data["file_id"],
                "model_file_token": glb_data["access_token"]
            })

            screenshot = context.scene.hubs_scene_debugger_scene_publish_props.screenshot
            screenshot_full = bpy.path.abspath(
                screenshot.filepath, library=screenshot.library)
            screenshot_norm = os.path.normpath(screenshot_full)
            screenshot_data = api.upload_media(
                url, open(screenshot_norm, "rb"))
            scene_data.update({
                "screenshot_file_id": screenshot_data["file_id"],
                "screenshot_file_token": screenshot_data["access_token"]
            })
            print(screenshot_data)

            scene_data.update({
                "allow_remixing": False,
                "allow_promotion": False,
                "attributions": {
                    "creator": "",
                    "content": []
                }
            })
            api.publish_scene(url, hubs_session.get_token(), scene_data)

            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'Scene {name} successfully published')

            bpy.ops.hubs_scene.get_scenes()

            return {'FINISHED'}

        except Exception as err:
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'An error happened while publishing the scene: {err}')
            return {"CANCELLED"}


class HubsUpdateSceneOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.update_scene"
    bl_label = "Update"
    bl_description = "Update selected scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return hubs_session.is_alive() and hubs_session.user_logged_in and context.window_manager.hubs_scene_debugger_scenes_props.scene_idx > -1

    def execute(self, context):
        try:
            export_scene(context)
            import os
            url = hubs_session.reticulum_url

            scenes = context.window_manager.hubs_scene_debugger_scenes_props
            scene = scenes.scenes[scenes.scene_idx]

            scene_data = {}

            glb_path = os.path.join(bpy.app.tempdir, EXPORT_TMP_FILE_NAME)
            glb = open(glb_path, "rb")
            glb_data = api.upload_media(url, glb)
            scene_data.update({
                "model_file_id": glb_data["file_id"],
                "model_file_token": glb_data["access_token"]
            })
            api.publish_scene(url, hubs_session.get_token(),
                              scene_data, scene.scene_id)

            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'Scene {scene.name} successfully updated')

            return {'FINISHED'}

        except Exception as err:
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'An error happened while updated the scene: {err}')
            return {"CANCELLED"}

    def invoke(self, context, event):
        def draw(self, context):
            row = self.layout.row()
            row.label(
                text="Are you sure that you want to overwrite the selected scene?")
            row = self.layout.row()
            col = row.column()
            col.operator(HubsUpdateSceneOperator.bl_idname, text="Yes")

        bpy.context.window_manager.popup_menu(draw)
        return {'FINISHED'}


class HubsCreateSceneOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.create_scene"
    bl_label = "Create Room"
    bl_description = "Create a room with the selected scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return hubs_session.is_alive() and hubs_session.user_logged_in and context.window_manager.hubs_scene_debugger_scenes_props.scene_idx > -1

    def execute(self, context):
        try:
            scenes_props = context.window_manager.hubs_scene_debugger_scenes_props
            scene = scenes_props.scenes[scenes_props.scene_idx]

            # Try to create a Hubs with credentials
            response = api.create_room(
                hubs_session.reticulum_url, token=hubs_session.get_token(),
                scene_name=scene.name, scene_id=scene.scene_id)
            if "error" in response:
                hubs_session.set_credentials(None, None)

                # Try to create a Hubs anonymously
                response = api.create_room(
                    hubs_session.reticulum_url, scene_name=scene.name, scene_id=scene.scene_id)
                if "error" in response:
                    raise Exception(response["error"])

            if "creator_assignment_token" in response:
                embed_token = None
                creator_token = response["creator_assignment_token"]
                if creator_token:
                    if "embed_token" in response:
                        embed_token = response["embed_token"]
                    hubs_session.set_creator_assignment_token(
                        creator_token, embed_token)

            was_alive = hubs_session.init(context)

            hubs_session.load(f'{response["url"]}?new&{hubs_session.url_params_string_from_prefs(context)}')

            if was_alive:
                hubs_session.bring_to_front(context)

            return {'FINISHED'}

        except Exception as err:
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'An error happened while opening the scene: {err}')
            return {"CANCELLED"}


class HubsGetScenesOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.get_scenes"
    bl_label = "Get Scenes"
    bl_description = "Get Scenes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return hubs_session.is_alive() and hubs_session.user_logged_in

    def execute(self, context):
        scenes_props = context.window_manager.hubs_scene_debugger_scenes_props
        scenes_props.instance = hubs_session.reticulum_url
        scenes_props.scenes.clear()
        try:
            export_scene(context)
            url = hubs_session.reticulum_url
            scenes = api.get_projects(url,  hubs_session.get_token())

            for scene in scenes:
                new_scene = scenes_props.scenes.add()
                new_scene["scene_id"] = scene["scene_id"]
                new_scene["name"] = scene["name"]
                new_scene["url"] = scene["url"]
                new_scene["description"] = scene["description"]
                new_scene["screenshot_url"] = scene["screenshot_url"]
                scenes_props.scene_idx = len(scenes_props.scenes) - 1

            if len(scenes_props.scenes) > 0:
                scenes_props.scene_idx = 0

            save_prefs(context)

            return {'FINISHED'}

        except Exception as err:
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'An error happened while getting the scenes: {err}')
            return {"CANCELLED"}


class HUBS_UL_ToolsSceneDebuggerProjects(bpy.types.UIList):
    bl_idname = "HUBS_UL_ToolsSceneDebuggerProjects"
    bl_label = "Projects"

    def filter_items(self, context: Context, data: AnyType, property: str):
        scene_props = context.window_manager.hubs_scene_debugger_scenes_props
        items = getattr(data, property)
        filtered = [self.bitflag_filter_item] * len(items)
        ordered = [i for i, item in enumerate(items)]
        ret_instance = hubs_session.reticulum_url if hubs_session.is_alive() else None
        filter = not scene_props.instance or ret_instance != scene_props.instance
        if filter:
            for i, item in enumerate(items):
                filtered[i] &= ~self.bitflag_filter_item

        return filtered, ordered

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.75)
        split.prop(item, "name", text="", emboss=False)
        split.prop(item, "scene_id", text="", emboss=False)


class HUBS_PT_ToolsSceneDebuggerPublishScenePanel(bpy.types.Panel):
    bl_idname = "HUBS_PT_ToolsSceneDebuggerPublishScenePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Publish"
    bl_context = 'objectmode'
    bl_parent_id = "HUBS_PT_ToolsPanel"

    @classmethod
    def poll(cls, context: Context):
        return isModuleAvailable("selenium")

    def draw(self, context: Context):
        if not hubs_session.is_alive() or not hubs_session.user_logged_in:
            box = self.layout.box()
            row = box.row()
            row.alert = True
            row.label(
                text="You need to be signed in Hubs to get, update or publish scenes")
            row = box.row()
            row.alert = True
            row.label(
                text="Create or open a room to open a session")

        box = self.layout.box()
        row = box.row()
        row.label(text="Manage:")
        row = box.row()
        list_row = row.row()
        list_row.template_list(
            HUBS_UL_ToolsSceneDebuggerProjects.bl_idname, "", context.window_manager.hubs_scene_debugger_scenes_props,
            "scenes", context.window_manager.hubs_scene_debugger_scenes_props, "scene_idx", rows=3)

        row = box.row()
        col = row.column()
        col.operator(HubsGetScenesOperator.bl_idname,
                     text='Get Scenes')
        col = row.column()
        col.operator(HubsUpdateSceneOperator.bl_idname,
                     text='Update')

        row = box.row()
        row = row.column()
        row.operator(HubsCreateSceneOperator.bl_idname,
                     text='Create Room')

        box = self.layout.box()
        row = box.row()
        row.label(text="Publish:")
        row = box.row()
        publish_props_box = row.box()
        row = publish_props_box.row()
        row.prop(context.scene.hubs_scene_debugger_scene_publish_props, "scene_name")
        row = publish_props_box.row()
        col = row.column()
        col.prop(context.scene.hubs_scene_debugger_scene_publish_props, "screenshot")
        col = row.column()
        col.context_pointer_set(
            "target", context.scene.hubs_scene_debugger_scene_publish_props)
        col.context_pointer_set("host", context.scene)
        op = col.operator("image.hubs_open_image", text='', icon='FILE_FOLDER')
        op.target_property = "screenshot"
        row = box.row()
        op = row.operator(HubsPublishSceneOperator.bl_idname,
                          text='Publish')


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
    export_cameras: bpy.props.BoolProperty(name="Export Cameras", default=False,
                                           description="Export cameras", options=set())
    export_lights: bpy.props.BoolProperty(
        name="Punctual Lights", default=False,
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


class HubsSceneProject(bpy.types.PropertyGroup):
    scene_id: bpy.props.StringProperty(
        name="Id",
        description="Scene id",
        default="Scene id",
        get=lambda self: self["scene_id"]
    )
    name: bpy.props.StringProperty(
        name="Name",
        description="Scene name",
        default="Scene name",
        get=lambda self: self["name"]
    )
    description: bpy.props.StringProperty(
        name="Description",
        description="Scene description",
        default="Scene description",
        get=lambda self: self["description"]
    )
    url: bpy.props.StringProperty(
        name="Scene URL",
        description="Scene URL",
        default="Scene URL",
        get=lambda self: self["url"]
    )
    screenshot_url: bpy.props.StringProperty(
        name="Screenshot URL",
        description="Scene URL",
        default="Scene URL",
        get=lambda self: self["screenshot_url"]
    )


class HubsSceneDebuggerScenePublishProps(bpy.types.PropertyGroup):
    scene_name: bpy.props.StringProperty(
        name="Name",
        description="Scene name",
        default="Scene name"
    )
    screenshot: bpy.props.PointerProperty(
        name="Screenshot",
        description="Scene screenshot",
        type=bpy.types.Image
    )


def save_prefs_on_prop_update(self, context):
    save_prefs(context)


class HubsSceneDebuggerScenes(bpy.types.PropertyGroup):
    instance: bpy.props.StringProperty(
        name="Instance",
        description="Instance URL"
    )
    scenes: bpy.props.CollectionProperty(
        type=HubsSceneProject)

    scene_idx: bpy.props.IntProperty(
        default=-1, update=save_prefs_on_prop_update)


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


def init():
    if not bpy.app.timers.is_registered(update_session):
        bpy.app.timers.register(update_session)

    from .utils import load_prefs
    load_prefs(bpy.context)

    prefs = bpy.context.window_manager.hubs_scene_debugger_prefs
    if len(prefs.hubs_instances) == 0:
        add_instance(bpy.context)


@persistent
def load_post(dummy):
    init()


@persistent
def update_session():
    hubs_session.update_session_state()
    return 2.0


classes = (
    HubsUrl,
    HubsSceneDebuggerPrefs,
    HubsCreateRoomOperator,
    HubsOpenRoomOperator,
    HubsCloseRoomOperator,
    HubsUpdateRoomOperator,
    HUBS_PT_ToolsSceneSessionPanel,
    HUBS_PT_ToolsSceneDebuggerPanel,
    HUBS_PT_ToolsSceneDebuggerCreatePanel,
    HUBS_PT_ToolsSceneDebuggerOpenPanel,
    HUBS_PT_ToolsSceneDebuggerUpdatePanel,
    HubsSceneDebuggerRoomCreatePrefs,
    HubsOpenAddonPrefsOperator,
    HubsSceneDebuggerRoomExportPrefs,
    HubsSceneDebuggerInstanceAdd,
    HubsSceneDebuggerInstanceRemove,
    HubsSceneDebuggerRoomAdd,
    HubsSceneDebuggerRoomRemove,
    HUBS_UL_ToolsSceneDebuggerServers,
    HUBS_UL_ToolsSceneDebuggerRooms,
    HUBS_PT_ToolsSceneDebuggerPublishScenePanel,
    HubsPublishSceneOperator,
    HubsUpdateSceneOperator,
    HubsCreateSceneOperator,
    HubsGetScenesOperator,
    HUBS_UL_ToolsSceneDebuggerProjects,
    HubsSceneProject,
    HubsSceneDebuggerScenePublishProps,
    HubsSceneDebuggerScenes
)


def register():
    global hubs_session
    hubs_session = HubsSession()

    for cls in (classes):
        bpy.utils.register_class(cls)

    bpy.types.Scene.hubs_scene_debugger_room_create_prefs = bpy.props.PointerProperty(
        type=HubsSceneDebuggerRoomCreatePrefs)
    bpy.types.Scene.hubs_scene_debugger_room_export_prefs = bpy.props.PointerProperty(
        type=HubsSceneDebuggerRoomExportPrefs)
    bpy.types.Scene.hubs_scene_debugger_scene_publish_props = bpy.props.PointerProperty(
        type=HubsSceneDebuggerScenePublishProps)
    bpy.types.WindowManager.hubs_scene_debugger_scenes_props = bpy.props.PointerProperty(
        type=HubsSceneDebuggerScenes)
    bpy.types.WindowManager.hubs_scene_debugger_prefs = bpy.props.PointerProperty(
        type=HubsSceneDebuggerPrefs)

    if load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post)

    init()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.hubs_scene_debugger_room_create_prefs
    del bpy.types.Scene.hubs_scene_debugger_room_export_prefs
    del bpy.types.Scene.hubs_scene_debugger_scene_publish_props
    del bpy.types.WindowManager.hubs_scene_debugger_scenes_props
    del bpy.types.WindowManager.hubs_scene_debugger_prefs

    if bpy.app.timers.is_registered(update_session):
        bpy.app.timers.unregister(update_session)

    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    hubs_session.close()
