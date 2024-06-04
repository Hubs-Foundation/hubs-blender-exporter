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
    bl_options = {'REGISTER', 'UNDO'}

    dep_config: PointerProperty(type=DepsProperty)

    def execute(self, context):
        import subprocess
        import sys

        result = subprocess.run([sys.executable, '-m', 'ensurepip'],
                                capture_output=False, text=True, input="y")
        if result.returncode < 0:
            print(result.stderr)
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string='\n\n'.join(["Dependencies install has failed installing pip",
                                                                     f'{result.stderr}']))
            return {'CANCELLED'}

        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
            capture_output=False, text=True, input="y")
        if result.returncode < 0:
            print(result.stderr)
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                          report_string='\n\n'.join(["Dependencies install has failed upgrading pip",
                                                                     f'{result.stderr}']))
            return {'CANCELLED'}

        from .utils import get_or_create_deps_path
        dep = self.dep_config.name
        if self.dep_config.version:
            dep = f'{self.dep_config.name}=={self.dep_config.version}'

        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', dep,
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


class HubsUserComponentsPath(bpy.types.PropertyGroup):
    name: StringProperty(
        name='User components path entry name',
        description='An optional, user defined label to allow quick discernment between different user component definition directories.',
    )
    path: StringProperty(
        name='User components path path',
        description='The path to a user defined component definitions directory. You can copy external components here and they will be loaded automatically.',
        subtype='FILE_PATH'
    )


class HubsUserComponentsPathAdd(bpy.types.Operator):
    bl_idname = "hubs_preferences.add_user_components_path"
    bl_label = "Add user components path"
    bl_description = "Adds a new component path entry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        addon_prefs = addon_prefs = get_addon_pref(bpy.context)
        paths = addon_prefs.user_components_paths
        paths.add()

        return {'FINISHED'}


class HubsUserComponentsPathRemove(bpy.types.Operator):
    bl_idname = "hubs_preferences.remove_user_components_path"
    bl_label = "Remove user components path entry"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(name="User Components Path Index", default=0)

    def execute(self, context):
        addon_prefs = addon_prefs = get_addon_pref(bpy.context)
        paths = addon_prefs.user_components_paths
        paths.remove(self.index)

        return {'FINISHED'}


def draw_user_modules_path_panel(context, layout, prefs):
    box = layout.box()
    box.row().label(text="Additional components directories:")

    dirs_layout = box.row()

    entries = prefs.user_components_paths

    if len(entries) == 0:
        dirs_layout.operator(HubsUserComponentsPathAdd.bl_idname,
                             text="Add", icon='ADD')
        return

    dirs_layout.use_property_split = False
    dirs_layout.use_property_decorate = False

    box = dirs_layout.box()
    split = box.split(factor=0.35)
    name_col = split.column()
    path_col = split.column()

    row = name_col.row(align=True)  # Padding
    row.separator()
    row.label(text="Name")

    row = path_col.row(align=True)  # Padding
    row.separator()
    row.label(text="Path")

    row.operator(HubsUserComponentsPathAdd.bl_idname,
                 text="", icon='ADD', emboss=False)

    for i, entry in enumerate(entries):
        row = name_col.row()
        row.alert = not entry.name
        row.prop(entry, "name", text="")

        row = path_col.row()
        subrow = row.row()
        subrow.alert = not entry.path
        subrow.prop(entry, "path", text="")
        row.operator(HubsUserComponentsPathRemove.bl_idname,
                     text="", icon='X', emboss=False).index = i


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

    user_components_paths: CollectionProperty(type=HubsUserComponentsPath)

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        box.row().prop(self, "row_length")
        box.row().prop(self, "recast_lib_path")

        draw_user_modules_path_panel(context, layout, self)
        box = layout.box()
        box.label(text="Scene debugger configuration")

        modules_available = is_module_available("selenium")
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
    bpy.utils.register_class(HubsUserComponentsPath)
    bpy.utils.register_class(HubsUserComponentsPathAdd)
    bpy.utils.register_class(HubsUserComponentsPathRemove)
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
    bpy.utils.unregister_class(HubsUserComponentsPathRemove)
    bpy.utils.unregister_class(HubsUserComponentsPathAdd)
    bpy.utils.unregister_class(HubsUserComponentsPath)
