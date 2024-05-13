import bpy
from bpy.types import AddonPreferences, Context
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, PointerProperty
from .utils import get_addon_package, is_module_available, get_browser_profile_directory
import platform
from os.path import join, dirname, realpath

EXPORT_TMP_FILE_NAME = "__hubs_tmp_scene_.glb"
EXPORT_TMP_SCREENSHOT_FILE_NAME = "__hubs_tmp_screenshot_"


def get_addon_pref(context):
    addon_package = get_addon_package()
    return context.preferences.addons[addon_package].preferences


def get_recast_lib_path():
    recast_lib = join(dirname(realpath(__file__)), "bin", "recast")

    file_name = None
    if platform.system() == 'Windows':
        file_name = "RecastBlenderAddon.dll"
    elif platform.system() == 'Darwin':
        file_name = "libRecastBlenderAddon.dylib"
    else:
        file_name = "libRecastBlenderAddon.so"

    return join(recast_lib, file_name)


class DepsProperty(bpy.types.PropertyGroup):
    name: StringProperty(default=" ")
    version: StringProperty(default="")


class InstallDepsOperator(bpy.types.Operator):
    bl_idname = "pref.hubs_prefs_install_dep"
    bl_label = "Install a python dependency through pip"
    bl_property = "dep_names"
    bl_options = {'REGISTER', 'UNDO'}

    dep_config: PointerProperty(type=DepsProperty)

    def execute(self, context):
        import subprocess
        import sys

        from .utils import get_or_create_deps_path
        dep = self.dep_config.name
        if self.dep_config.version:
            dep = f'{self.dep_config.name}=={self.dep_config.version}'

        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', dep,
             '-t', get_or_create_deps_path(self.dep_config.name)],
            capture_output=True, text=True, input="y")
        failed = False
        if not is_module_available(self.dep_config.name):
            failed = True
        if result.returncode != 0 or failed:
            print(result.stderr)
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string='\n\n'.join(["Dependencies install has failed",
                                                                     f'{result.stderr}']))
            return {'CANCELLED'}
        else:
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string="Dependencies installed successfully")
            return {'FINISHED'}


class UninstallDepsOperator(bpy.types.Operator):
    bl_idname = "pref.hubs_prefs_uninstall_dep"
    bl_label = "Uninstall a python dependency through pip"
    bl_options = {'REGISTER', 'UNDO'}

    dep_config: PointerProperty(type=DepsProperty)

    def execute(self, context):
        from .utils import get_or_create_deps_path
        import shutil
        shutil.rmtree(get_or_create_deps_path(self.dep_config.name))

        return {'FINISHED'}


class DeleteProfileOperator(bpy.types.Operator):
    bl_idname = "pref.hubs_prefs_remove_profile"
    bl_label = "Delete"
    bl_description = "Delete Browser profile"
    bl_options = {'REGISTER', 'UNDO'}

    browser: StringProperty()

    @classmethod
    def poll(cls, context: Context):
        if hasattr(context, "prefs"):
            prefs = getattr(context, 'prefs')
            path = get_browser_profile_directory(prefs.browser)
            import os
            return os.path.exists(path)

        return False

    def execute(self, context):
        path = get_browser_profile_directory(self.browser)
        import os
        if os.path.exists(path):
            import shutil
            shutil.rmtree(path)

        return {'FINISHED'}


class HubsPreferences(AddonPreferences):
    bl_idname = __package__

    row_length: IntProperty(
        name="Add Component Menu Row Length",
        description="Allows you to control how many categories are added to a row before it starts on the next row. Set to 0 to have it all on one row",
        default=4,
        min=0,
    )

    recast_lib_path: StringProperty(
        name='Recast library path',
        subtype='FILE_PATH',
        default=get_recast_lib_path()
    )

    viewer_available: BoolProperty()

    browser: EnumProperty(
        name="Choose a browser", description="Type",
        items=[("Firefox", "Firefox", "Use Firefox as the viewer browser"),
               ("Chrome", "Chrome", "Use Chrome as the viewer browser")],
        default="Firefox")

    override_firefox_path: BoolProperty(
        name="Override Firefox executable path", description="Override Firefox executable path", default=False)
    firefox_path: StringProperty(
        name="Firefox executable path", description="Binary path", subtype='FILE_PATH')
    override_chrome_path: BoolProperty(
        name="Override Chrome executable path", description="Override Chrome executable path", default=False)
    chrome_path: StringProperty(
        name="Chrome executable path", description="Binary path", subtype='FILE_PATH')

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        box.row().prop(self, "row_length")
        box.row().prop(self, "recast_lib_path")

        selenium_available = is_module_available("selenium")
        modules_available = selenium_available
        box = layout.box()
        box.label(text="Scene debugger configuration")

        if modules_available:
            browser_box = box.box()
            row = browser_box.row()
            row.prop(self, "browser")
            row = browser_box.row()
            col = row.column()
            col.label(text=f'Delete {self.browser} profile')
            col = row.column()
            col.context_pointer_set("prefs", self)
            op = col.operator(DeleteProfileOperator.bl_idname)
            row = browser_box.row()
            row.label(
                text="This will only delete the Hubs related profile, not your local browser profile")
            op.browser = self.browser
            if self.browser == "Firefox":
                row = browser_box.row()
                row.prop(self, "override_firefox_path")
                if self.override_firefox_path:
                    row = browser_box.row()
                    row.label(
                        text="In some cases the browser binary might not be located automatically, in those cases you'll need to specify the binary location manually below")
                    row = browser_box.row()
                    row.alert = True
                    row.label(
                        text="You don't need to set a path below unless the binary cannot be located automatically.")
                    row = browser_box.row()
                    row.prop(self, "firefox_path",)
            elif self.browser == "Chrome":
                row = browser_box.row()
                row.prop(self, "override_chrome_path")
                if self.override_chrome_path:
                    row = browser_box.row()
                    row.label(
                        text="In some cases the browser binary might not be located automatically, in those cases you'll need to specify the binary location manually below")
                    row = browser_box.row()
                    row.alert = True
                    row.label(
                        text="You don't need to set a path below unless the binary cannot be located automatically.")
                    row = browser_box.row()
                    row.prop(self, "chrome_path")

        modules_box = box.box()
        row = modules_box.row()
        row.alert = not modules_available
        row.label(
            text="Modules found."
            if modules_available else
            "Selenium module not found. These modules are required to run the viewer")
        row = modules_box.row()
        if modules_available:
            op = row.operator(UninstallDepsOperator.bl_idname,
                              text="Uninstall dependencies (selenium)")
            op.dep_config.name = "selenium"
        else:
            op = row.operator(InstallDepsOperator.bl_idname,
                              text="Install dependencies (selenium)")
            op.dep_config.name = "selenium"
            op.dep_config.version = "4.15.2"


def register():
    bpy.utils.register_class(DepsProperty)
    bpy.utils.register_class(HubsPreferences)
    bpy.utils.register_class(InstallDepsOperator)
    bpy.utils.register_class(UninstallDepsOperator)
    bpy.utils.register_class(DeleteProfileOperator)


def unregister():
    bpy.utils.unregister_class(DeleteProfileOperator)
    bpy.utils.unregister_class(UninstallDepsOperator)
    bpy.utils.unregister_class(InstallDepsOperator)
    bpy.utils.unregister_class(HubsPreferences)
    bpy.utils.unregister_class(DepsProperty)
