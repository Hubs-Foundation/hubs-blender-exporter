import bpy
import atexit
from bpy.types import Context
from .preferences import get_addon_pref, EXPORT_TMP_FILE_NAME
from .utils import isModuleAvailable, get_browser_profile_directory
from .icons import get_hubs_icons

JS_DROP_FILE = """
    var target = arguments[0],
        offsetX = arguments[1],
        offsetY = arguments[2],
        document = target.ownerDocument || document,
        window = document.defaultView || window;

    var input = document.createElement('INPUT');
    input.type = 'file';
    input.onchange = function () {
      var rect = target.getBoundingClientRect(),
          x = rect.left + (offsetX || (rect.width >> 1)),
          y = rect.top + (offsetY || (rect.height >> 1)),
          dataTransfer = { files: this.files };

      ['dragenter', 'dragover', 'drop'].forEach(function (name) {
        var evt = document.createEvent('MouseEvent');
        evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
        evt.dataTransfer = dataTransfer;
        target.dispatchEvent(evt);
      });

      setTimeout(function () { document.body.removeChild(input); }, 25);
    };
    document.body.appendChild(input);
    return input;
"""

web_driver = None


def export_scene(context):
    import os
    extension = '.glb'
    output_dir = bpy.app.tempdir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    args = {
        # Settings from "Remember Export Settings"
        **dict(bpy.context.scene.get('glTF2ExportSettings', {})),

        'export_format': ('GLB' if extension == '.glb' else 'GLTF_SEPARATE'),
        'filepath': os.path.join(bpy.app.tempdir, EXPORT_TMP_FILE_NAME),
        'export_cameras': context.scene.hubs_scene_debugger_room_export_prefs.export_cameras,
        'export_lights': context.scene.hubs_scene_debugger_room_export_prefs.export_lights,
        'use_selection': context.scene.hubs_scene_debugger_room_export_prefs.use_selection,
        'export_apply': context.scene.hubs_scene_debugger_room_export_prefs.export_apply
    }
    bpy.ops.export_scene.gltf(**args)


def refresh_scene_viewer():
    import os
    document = web_driver.find_element("tag name", "html")
    file_input = web_driver.execute_script(JS_DROP_FILE, document, 0, 0)
    file_input.send_keys(os.path.join(bpy.app.tempdir, EXPORT_TMP_FILE_NAME))


def isWebdriverAlive():
    try:
        if not web_driver or not isModuleAvailable("selenium"):
            return False
        else:
            return web_driver.current_url
    except Exception:
        return False


def get_local_storage():
    storage = None
    if isWebdriverAlive():
        storage = web_driver.execute_script("return window.localStorage;")

    return storage


def is_user_logged_in():
    has_credentials = False
    if isWebdriverAlive():
        storage = get_local_storage()
        if storage:
            hubs_store = storage.get("___hubs_store")
            if hubs_store:
                import json
                hubs_store = json.loads(storage.get("___hubs_store"))
                has_credentials = "credentials" in hubs_store

    return has_credentials


def is_user_in_room():
    return web_driver.execute_script('try { return APP.scene.is("entered"); } catch(e) { return false; }')


class HubsUpdateSceneOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.view_scene"
    bl_label = "View Scene"
    bl_description = "Update scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return isWebdriverAlive() and is_user_logged_in() and is_user_in_room()

    def execute(self, context):
        try:
            export_scene(context)
            refresh_scene_viewer()

            web_driver.switch_to.window(web_driver.current_window_handle)

            return {'FINISHED'}
        except Exception as err:
            print(err)
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string='\n\n'.join(["The scene export has failed",
                                                                     "Check the export logs or quit the browser instance and try again",
                                                                     f'{err}']))
            return {'CANCELLED'}


class HubsCreateRoomOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.open_window"
    bl_label = "Create Room"
    bl_description = "Create room"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return not isWebdriverAlive()

    def execute(self, context):
        try:
            global web_driver
            if not web_driver or not isWebdriverAlive():
                if web_driver:
                    web_driver.quit()
                browser = get_addon_pref(context).browser
                import os
                file_path = get_browser_profile_directory(browser)
                if not os.path.exists(file_path):
                    os.mkdir(file_path)
                if browser == "Firefox":
                    from selenium import webdriver
                    options = webdriver.FirefoxOptions()
                    override_ff_path = get_addon_pref(
                        context).override_firefox_path
                    ff_path = get_addon_pref(context).firefox_path
                    if override_ff_path and ff_path:
                        options.binary_location = ff_path
                    # This should work but it doesn't https://github.com/SeleniumHQ/selenium/issues/11028 so using arguments instead
                    # firefox_profile = webdriver.FirefoxProfile(file_path)
                    # firefox_profile.accept_untrusted_certs = True
                    # firefox_profile.assume_untrusted_cert_issuer = True
                    # options.profile = firefox_profile
                    options.add_argument("-profile")
                    options.add_argument(file_path)
                    web_driver = webdriver.Firefox(options=options)
                else:
                    from selenium import webdriver
                    options = webdriver.ChromeOptions()
                    options.add_argument('--ignore-certificate-errors')
                    options.add_argument(
                        f'user-data-dir={file_path}')
                    override_chrome_path = get_addon_pref(
                        context).override_chrome_path
                    chrome_path = get_addon_pref(context).chrome_path
                    if override_chrome_path and chrome_path:
                        options.binary_location = chrome_path
                    web_driver = webdriver.Chrome(options=options)

                params = "new"
                if context.scene.hubs_scene_debugger_room_create_prefs.new_loader:
                    params = f'{params}&newLoader'
                if context.scene.hubs_scene_debugger_room_create_prefs.ecs_debug:
                    params = f'{params}&ecsDebug'
                if context.scene.hubs_scene_debugger_room_create_prefs.vr_entry_type:
                    params = f'{params}&vr_entry_type=2d_now'
                if context.scene.hubs_scene_debugger_room_create_prefs.debug_local_scene:
                    params = f'{params}&debugLocalScene'

                web_driver.get(
                    f'{get_addon_pref(context).hubs_instance_url}?{params}')

                return {'FINISHED'}

        except Exception as err:
            if web_driver:
                web_driver.quit()
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string=f'The room creation has failed: {err}')
            return {"CANCELLED"}


class HubsOpenAddonPrefsOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.open_addon_prefs"
    bl_label = "Open Preferences"
    bl_description = "Update scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        return not isWebdriverAlive()

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        context.preferences.active_section
        bpy.ops.preferences.addon_expand(module=__package__)
        bpy.ops.preferences.addon_show(module=__package__)
        return {'FINISHED'}


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
            row = main_box.row()
            row.label(
                text="Create room")
            box = main_box.box()
            row = box.row()
            row.enabled = not isWebdriverAlive()
            col = row.column(heading="Room flags:")
            col.use_property_split = True
            col.prop(context.scene.hubs_scene_debugger_room_create_prefs,
                     "new_loader")
            col.prop(context.scene.hubs_scene_debugger_room_create_prefs,
                     "ecs_debug")
            col.prop(context.scene.hubs_scene_debugger_room_create_prefs,
                     "vr_entry_type")
            col.prop(context.scene.hubs_scene_debugger_room_create_prefs,
                     "debug_local_scene")
            row = box.row()
            row.operator(HubsCreateRoomOperator.bl_idname,
                         text='Create')

            main_box.separator()
            row = main_box.row()
            row.label(
                text="Update scene")
            box = main_box.box()
            row = box.row()
            row.label(
                text="Set the default export options in the glTF export panel")
            row = box.row()
            col = row.column(heading="Overridden export options:")
            col.enabled = isWebdriverAlive() and is_user_in_room()
            col.use_property_split = True
            col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                     "export_cameras")
            col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                     "export_lights")
            col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                     "use_selection")
            col.prop(context.scene.hubs_scene_debugger_room_export_prefs,
                     "export_apply")
            row = box.row()
            row.operator(HubsUpdateSceneOperator.bl_idname,
                         text='Update')

            box = main_box.box()
            row = box.row(align=True)
            row.alignment = "CENTER"
            col = row.column()
            col.alignment = "LEFT"
            col.label(text="Status:")
            hubs_icons = get_hubs_icons()
            if isWebdriverAlive():
                if is_user_logged_in():
                    if is_user_in_room():
                        col = row.column()
                        col.alignment = "LEFT"
                        col.active_default = True
                        col.label(
                            icon_value=hubs_icons["green-dot.png"].icon_id)
                        row = box.row(align=True)
                        row.alignment = "CENTER"
                        row.label(text="In room")

                    else:
                        col = row.column()
                        col.alignment = "LEFT"
                        col.label(
                            icon_value=hubs_icons["orange-dot.png"].icon_id)
                        row = box.row(align=True)
                        row.alignment = "CENTER"
                        row.label(text="Entering the room...")
                else:
                    col = row.column()
                    col.alignment = "LEFT"
                    col.alert = True
                    col.label(icon_value=hubs_icons["orange-dot.png"].icon_id)
                    row = box.row(align=True)
                    row.alignment = "CENTER"
                    row.label(text="Waiting for sign in...")
            else:
                col = row.column()
                col.alignment = "LEFT"
                col.alert = True
                col.label(icon_value=hubs_icons["red-dot.png"].icon_id)
                row = box.row(align=True)
                row.alignment = "CENTER"
                row.label(text="Waiting for room...")

        else:
            row = main_box.row()
            row.alert = True
            row.label(
                text="Selenium needs to be installed for the scene debugger functionality. Install from preferences.")
            row = main_box.row()
            row.operator(HubsOpenAddonPrefsOperator.bl_idname,
                         text='Setup')


class HubsSceneDebuggerRoomCreatePrefs(bpy.types.PropertyGroup):
    new_loader: bpy.props.BoolProperty(name="New Loader", default=True,
                                       description="Creates the room using the new bitECS loader", options=set())
    ecs_debug: bpy.props.BoolProperty(name="ECS Debug",
                                      default=True, description="Enables the ECS debugging side panel", options=set())
    vr_entry_type: bpy.props.BoolProperty(name="Skip Entry", default=True,
                                          description="Omits the entry setup panel and goes straight into the room",
                                          options=set())
    debug_local_scene: bpy.props.BoolProperty(name="Debug Local Scene", default=True,
                                              description="Allows scene override. Use this if you want to update the scene. If you just want to spawn an object disable it.",
                                              options=set())


class HubsSceneDebuggerRoomExportPrefs(bpy.types.PropertyGroup):
    export_cameras: bpy.props.BoolProperty(name="Export Cameras", default=True,
                                           description="Export cameras", options=set())
    export_lights: bpy.props.BoolProperty(name="Export Lights",
                                          default=True, description="Punctual Lights, Export directional, point, and spot lights. Uses \"KHR_lights_punctual\" glTF extension", options=set())
    use_selection: bpy.props.BoolProperty(name="Selection Only", default=False,
                                          description="Selection Only, Export selected objects only.",
                                          options=set())
    export_apply: bpy.props.BoolProperty(name="Export Apply", default=True,
                                              description="Apply Modifiers, Apply modifiers (excluding Armatures) to mesh objects -WARNING: prevents exporting shape keys.",
                                              options=set())


def register():
    bpy.utils.register_class(HubsCreateRoomOperator)
    bpy.utils.register_class(HubsUpdateSceneOperator)
    bpy.utils.register_class(HUBS_PT_ToolsSceneDebuggerPanel)
    bpy.utils.register_class(HubsSceneDebuggerRoomCreatePrefs)
    bpy.utils.register_class(HubsOpenAddonPrefsOperator)
    bpy.utils.register_class(HubsSceneDebuggerRoomExportPrefs)

    bpy.types.Scene.hubs_scene_debugger_room_create_prefs = bpy.props.PointerProperty(
        type=HubsSceneDebuggerRoomCreatePrefs)
    bpy.types.Scene.hubs_scene_debugger_room_export_prefs = bpy.props.PointerProperty(
        type=HubsSceneDebuggerRoomExportPrefs)


def unregister():
    bpy.utils.unregister_class(HubsUpdateSceneOperator)
    bpy.utils.unregister_class(HubsCreateRoomOperator)
    bpy.utils.unregister_class(HUBS_PT_ToolsSceneDebuggerPanel)
    bpy.utils.unregister_class(HubsSceneDebuggerRoomCreatePrefs)
    bpy.utils.unregister_class(HubsOpenAddonPrefsOperator)
    bpy.utils.unregister_class(HubsSceneDebuggerRoomExportPrefs)

    del bpy.types.Scene.hubs_scene_debugger_room_create_prefs
    del bpy.types.Scene.hubs_scene_debugger_room_export_prefs

    if isWebdriverAlive():
        web_driver.close()


def cleanup():
    if isWebdriverAlive():
        web_driver.close()


atexit.register(cleanup)
