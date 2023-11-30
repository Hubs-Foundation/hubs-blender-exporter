import bpy
from bpy.types import AddonPreferences, Context
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, CollectionProperty
from .utils import get_addon_package, isModuleAvailable, get_browser_profile_directory
import platform
from os.path import join, dirname, realpath

EXPORT_TMP_FILE_NAME = "__hubs_tmp_scene_.glb"


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

    dep_names: CollectionProperty(type=DepsProperty)

    def execute(self, context):
        import subprocess
        import sys

        deps = []
        for _, dep in self.dep_names.items():
            if dep.version:
                deps.append(f'{dep.name}=={dep.version}')
            else:
                deps.append(dep.name)

        from .utils import get_user_python_path
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', *deps,
             '-t', get_user_python_path()],
            capture_output=False, text=True, input="y")

        return {'FINISHED'}


class UninstallDepsOperator(bpy.types.Operator):
    bl_idname = "pref.hubs_prefs_uninstall_dep"
    bl_label = "Uninstall a python dependency through pip"
    bl_property = "dep_names"
    bl_options = {'REGISTER', 'UNDO'}

    dep_names: CollectionProperty(type=DepsProperty)
    force: BoolProperty(default=False)

    def execute(self, context):
        import subprocess
        import sys

        subprocess.run([sys.executable, '-m', 'ensurepip'],
                       capture_output=False, text=True, input="y")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'uninstall', *
                [name for name, _ in self.dep_names.items()]],
            capture_output=False, text=True, input="y")

        if self.force:
            import os
            from .utils import get_user_python_path
            deps_paths = [os.path.join(get_user_python_path(), name)
                          for name, _ in self.dep_names.items()]
            import shutil
            for dep_path in deps_paths:
                shutil.rmtree(deps_paths)

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

    hubs_instance_url: StringProperty(name="Hubs instance URL", description="URL of the hubs instance to use",
                                      default="https://hubs.local:8080/")

    browser: EnumProperty(
        name="Choose a browser", description="Type",
        items=[("Firefox", "Firefox", "Use Firefox as the viewer browser"),
               ("Chrome", "Chrome", "Use Chrome as the viewer browser")],
        default="Firefox")

    force_uninstall: BoolProperty(
        default=False, name="Force",
        description="Force uninstall of the selenium dependencies by deleting the module directory")

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

        selenium_available = isModuleAvailable("selenium")
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

        row = box.row()
        row.alert = not modules_available
        row.label(
            text="Modules found."
            if modules_available else
            "Selenium module not found. These modules are required to run the viewer")
        row = box.row()
        row.prop(self, "hubs_instance_url")
        row = box.row()

        if modules_available:
            row.prop(self, "force_uninstall")
            op = row.operator(UninstallDepsOperator.bl_idname,
                              text="Uninstall dependencies (selenium)")
            op.dep_names.add().name = "selenium"
        else:
            op = row.operator(InstallDepsOperator.bl_idname,
                              text="Install dependencies (selenium)")
            dep = op.dep_names.add()
            dep.name = "selenium"
            dep.version = "4.15.2"


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
