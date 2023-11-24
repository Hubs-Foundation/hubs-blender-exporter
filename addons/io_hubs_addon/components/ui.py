import bpy
from bpy.props import StringProperty
from bpy.types import Context
from .types import PanelType
from .components_registry import get_component_by_name, get_components_registry
from .utils import get_object_source, is_linked
from ..preferences import get_addon_pref, EXPORT_TMP_FILE_NAME
from ..utils import isModuleAvailable, get_browser_profile_directory


def draw_component_global(panel, context):
    layout = panel.layout
    components_registry = get_components_registry()
    for _, component_class in components_registry.items():
        component_class.draw_global(context, layout, panel)


def draw_component(panel, context, obj, row, component_item):
    component_name = component_item.name
    component_class = get_component_by_name(component_name)
    if component_class:
        panel_type = PanelType(panel.bl_context)
        if panel_type not in component_class.get_panel_type() or not component_class.poll(panel_type, obj, ob=context.object):
            col = row.box().column()
            top_row = col.row()
            top_row.label(
                text=f"Unsupported host for component '{component_class.get_display_name()}'", icon="ERROR")
            remove_component_operator = top_row.operator(
                "wm.remove_hubs_component",
                text="",
                icon="X"
            )
            remove_component_operator.component_name = component_name
            remove_component_operator.panel_type = panel.bl_context
            return

        component_id = component_class.get_id()
        component = getattr(obj, component_id)

        has_properties = len(component_class.get_properties()) > 0

        col = row.box().column()
        top_row = col.row()

        if has_properties:
            top_row.prop(component_item, "expanded",
                         icon="TRIA_DOWN" if component_item.expanded else "TRIA_RIGHT",
                         icon_only=True, emboss=False
                         )

        display_name = component_class.get_display_name()

        top_row.label(text=display_name)

        if has_properties or not component_class.is_dep_only():
            top_row.context_pointer_set("panel", panel)
            copy_component_operator = top_row.operator(
                "wm.copy_hubs_component",
                text="",
                icon="PASTEDOWN"
            )
            copy_component_operator.component_name = component_name
            copy_component_operator.panel_type = panel.bl_context

        if not (component_class.is_dep_only() or component_item.isDependency):
            top_row.context_pointer_set("panel", panel)
            remove_component_operator = top_row.operator(
                "wm.remove_hubs_component",
                text="",
                icon="X"
            )
            remove_component_operator.component_name = component_name
            remove_component_operator.panel_type = panel.bl_context

        body_col = col.column()
        body_col.enabled = not is_linked(obj)
        if component_item.expanded:
            component.draw(context, body_col, panel)

    else:
        col = row.box().column()
        top_row = col.row()
        top_row.label(
            text=f"Unknown component '{component_name}'", icon="ERROR")
        top_row.context_pointer_set("panel", panel)
        remove_component_operator = top_row.operator(
            "wm.remove_hubs_component",
            text="",
            icon="X"
        )
        remove_component_operator.component_name = component_name
        remove_component_operator.panel_type = panel.bl_context


def draw_components_list(panel, context):
    layout = panel.layout

    obj = get_object_source(context, panel.bl_context)

    if not obj:
        return

    layout.context_pointer_set("panel", panel)
    add_component_operator = layout.operator(
        "wm.add_hubs_component",
        text="Add Component",
        icon="ADD"
    )
    add_component_operator.panel_type = panel.bl_context

    for component_item in obj.hubs_component_list.items:
        row = layout.row()
        draw_component(panel, context, obj, row, component_item)

    layout.separator()


def add_link_indicator(layout, datablock):
    if datablock.library:
        library = datablock.library
        icon = 'LINKED'
    else:
        library = datablock.override_library.reference.library
        icon = 'LIBRARY_DATA_OVERRIDE'

    tooltip = (
        f"{datablock.name}\n"
        f"\n"
        f"Source Library:\n"
        f"[{library.name}]\n"
        f"{library.filepath}"
    )
    layout.operator("ui.hubs_tooltip_label", text='',
                    icon=icon).tooltip = tooltip


class HubsObjectPanel(bpy.types.Panel):
    bl_label = "Hubs"
    bl_idname = "OBJECT_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        draw_components_list(self, context)


def export_scene():
    try:
        import os
        import sys
        extension = '.glb'
        output_dir = bpy.app.tempdir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        args = {
            # Settings from "Remember Export Settings"
            **dict(bpy.context.scene.get('glTF2ExportSettings', {})),

            'export_format': ('GLB' if extension == '.glb' else 'GLTF_SEPARATE'),
            'filepath': os.path.join(bpy.app.tempdir, EXPORT_TMP_FILE_NAME),
            'export_cameras': True,
            'export_lights': True,
            'export_extras': True,
            'use_visible': True,
            'export_apply': True
        }
        bpy.ops.export_scene.gltf(**args)
    except Exception as err:
        print(err, file=sys.stderr)


web_driver = None


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


def refresh_scene_viewer():
    import os
    document = web_driver.find_element("tag name", "html")
    file_input = web_driver.execute_script(JS_DROP_FILE, document, 0, 0)
    file_input.send_keys(os.path.join(bpy.app.tempdir, EXPORT_TMP_FILE_NAME))


def isWebdriverAlive(driver):
    try:
        if not isModuleAvailable("selenium"):
            return False
        else:
            return driver.current_url
    except Exception:
        return False


def get_local_storage():
    storage = None
    if isWebdriverAlive(web_driver):
        storage = web_driver.execute_script("return window.localStorage;")

    return storage


def is_user_logged_in():
    has_credentials = False
    if isWebdriverAlive(web_driver):
        storage = get_local_storage()
        hubs_store = storage.get("___hubs_store")
        if hubs_store:
            import json
            hubs_store = json.loads(storage.get("___hubs_store"))
            has_credentials = "credentials" in hubs_store

    return has_credentials


def is_user_in_entered():
    return web_driver.execute_script('try { return APP.scene.is("entered"); } catch(e) { return false; }')


class HubsUpdateSceneOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.view_scene"
    bl_label = "View Scene"
    bl_description = "Update scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        global web_driver
        return isWebdriverAlive(web_driver) and is_user_logged_in() and is_user_in_entered()

    def execute(self, context):
        export_scene()
        refresh_scene_viewer()

        web_driver.switch_to.window(web_driver.current_window_handle)

        return {'FINISHED'}


class HubsCreateRoomOperator(bpy.types.Operator):
    bl_idname = "hubs_scene.open_window"
    bl_label = "Create Room"
    bl_description = "Create room"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context):
        global web_driver
        return not isWebdriverAlive(web_driver)

    def execute(self, context):
        try:
            global web_driver
            if not web_driver or not isWebdriverAlive(web_driver):
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

                params = "new&debugLocalScene"
                if context.scene.hubs_scene_debugger_room_create_prefs.new_loader:
                    params = f'{params}&newLoader'
                if context.scene.hubs_scene_debugger_room_create_prefs.ecs_debug:
                    params = f'{params}&ecsDebug'
                if context.scene.hubs_scene_debugger_room_create_prefs.vr_entry_type:
                    params = f'{params}&vr_entry_type=2d_now'

                web_driver.get(
                    f'{get_addon_pref(context).hubs_instance_url}?{params}')

                return {'FINISHED'}

        except Exception as e:
            print(e)
            return {"CANCELLED"}


class HUBS_PT_ToolsPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Hubs"
    bl_category = "Hubs"
    bl_context = 'objectmode'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        main_box = row.box()

        top_row = main_box.row()
        top_row.prop(context.scene, "hubs_scene_debugger_expanded",
                     icon="TRIA_DOWN" if context.scene.hubs_scene_debugger_expanded else "TRIA_RIGHT",
                     icon_only=True, emboss=False
                     )
        top_row.label(text="Scene Debugger")

        if context.scene.hubs_scene_debugger_expanded:
            if isModuleAvailable("selenium"):
                box = main_box.box()
                row = box.row()
                col = row.column(heading="Room flags:")
                col.use_property_split = True
                col.prop(context.scene.hubs_scene_debugger_room_create_prefs,
                         "new_loader")
                col.prop(context.scene.hubs_scene_debugger_room_create_prefs,
                         "ecs_debug")
                col.prop(context.scene.hubs_scene_debugger_room_create_prefs,
                         "vr_entry_type")
                row = box.row()
                row.operator(HubsCreateRoomOperator.bl_idname,
                             text='Create')

                main_box.separator()
                box = main_box.box()
                row = box.row()
                row.label(text="Set the export options in the glTF export panel")
                if isWebdriverAlive(web_driver) and not is_user_logged_in():
                    row = box.row()
                    row.alert = True
                    row.label(text="Sign in the room to start debugging")
                row = box.row()
                row.operator(HubsUpdateSceneOperator.bl_idname,
                             text='Update')
            else:
                row = main_box.row()
                row.alert = True
                row.label(
                    text="Selenium needs to be installed for the scene debugger functionality. Install from preferences.")


class HubsScenePanel(bpy.types.Panel):
    bl_label = 'Hubs'
    bl_idname = "SCENE_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        draw_component_global(self, context)
        layout = self.layout
        layout.separator()
        draw_components_list(self, context)


class HubsMaterialPanel(bpy.types.Panel):
    bl_label = 'Hubs'
    bl_idname = "MATERIAL_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        draw_components_list(self, context)


class HubsBonePanel(bpy.types.Panel):
    bl_label = "Hubs"
    bl_idname = "BONE_PT_hubs"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    def draw(self, context):
        draw_components_list(self, context)


class TooltipLabel(bpy.types.Operator):
    bl_idname = "ui.hubs_tooltip_label"
    bl_label = "---"

    tooltip: StringProperty(default=" ")

    @ classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        return {'CANCELLED'}


def window_menu_addition(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("wm.hubs_view_last_report")


def object_menu_addition(self, context):
    layout = self.layout
    layout.separator()
    op = layout.operator("wm.migrate_hubs_components")
    op.is_registration = False


def gizmo_display_popover_addition(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("wm.update_hubs_gizmos")


class HubsSceneDebuggerRoomCreatePrefs(bpy.types.PropertyGroup):
    new_loader: bpy.props.BoolProperty(name="New Loader", default=True,
                                       description="Creates the room using the new bitECS loader", options=set())
    ecs_debug: bpy.props.BoolProperty(name="ECS Debug",
                                      default=True, description="Enables the ECS debugging side panel", options=set())
    vr_entry_type: bpy.props.BoolProperty(name="Skip Entry", default=True,
                                          description="Omits the entry setup panel and goes straight into the room",
                                          options=set())


def register():
    bpy.utils.register_class(HubsCreateRoomOperator)
    bpy.utils.register_class(HubsUpdateSceneOperator)
    bpy.utils.register_class(HubsObjectPanel)
    bpy.utils.register_class(HubsScenePanel)
    bpy.utils.register_class(HubsMaterialPanel)
    bpy.utils.register_class(HubsBonePanel)
    bpy.utils.register_class(TooltipLabel)
    bpy.utils.register_class(HUBS_PT_ToolsPanel)
    bpy.utils.register_class(HubsSceneDebuggerRoomCreatePrefs)

    bpy.types.Scene.hubs_scene_debugger_room_create_prefs = bpy.props.PointerProperty(
        type=HubsSceneDebuggerRoomCreatePrefs)
    bpy.types.Scene.hubs_scene_debugger_expanded = bpy.props.BoolProperty(
        default=True)

    bpy.types.TOPBAR_MT_window.append(window_menu_addition)
    bpy.types.VIEW3D_MT_object.append(object_menu_addition)
    bpy.types.VIEW3D_PT_gizmo_display.append(gizmo_display_popover_addition)


def unregister():
    bpy.utils.unregister_class(HubsObjectPanel)
    bpy.utils.unregister_class(HubsScenePanel)
    bpy.utils.unregister_class(HubsMaterialPanel)
    bpy.utils.unregister_class(HubsBonePanel)
    bpy.utils.unregister_class(TooltipLabel)
    bpy.utils.unregister_class(HubsUpdateSceneOperator)
    bpy.utils.unregister_class(HubsCreateRoomOperator)
    bpy.utils.unregister_class(HUBS_PT_ToolsPanel)
    bpy.utils.unregister_class(HubsSceneDebuggerRoomCreatePrefs)

    del bpy.types.Scene.hubs_scene_debugger_room_create_prefs
    del bpy.types.Scene.hubs_scene_debugger_expanded

    bpy.types.TOPBAR_MT_window.remove(window_menu_addition)
    bpy.types.VIEW3D_MT_object.remove(object_menu_addition)
    bpy.types.VIEW3D_PT_gizmo_display.remove(gizmo_display_popover_addition)

    global web_driver
    if web_driver and isWebdriverAlive(web_driver):
        web_driver.close()
