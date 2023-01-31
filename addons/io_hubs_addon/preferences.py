import bpy
from bpy.types import AddonPreferences
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, CollectionProperty
from .utils import get_addon_package, isModuleAvailable
import platform
from os.path import join, dirname, realpath


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


class InstallDepsOperator(bpy.types.Operator):
    bl_idname = "pref.hubs_prefs_install_dep"
    bl_label = "Install a python dependency through pip"
    bl_property = "dep_name"
    bl_options = {'REGISTER', 'UNDO'}

    dep_names: CollectionProperty(type=DepsProperty)

    def execute(self, context):
        import subprocess
        import sys

        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                       capture_output=False, text=True, input="y")
        from .utils import get_user_python_path
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', *[name for name, _ in self.dep_names.items()],
             '-t', get_user_python_path()],
            capture_output=False, text=True, input="y")

        return {'FINISHED'}


class UninstallDepsOperator(bpy.types.Operator):
    bl_idname = "pref.hubs_prefs_uninstall_dep"
    bl_label = "Uninstall a python dependency through pip"
    bl_property = "dep_name"
    bl_options = {'REGISTER', 'UNDO'}

    dep_names: CollectionProperty(type=DepsProperty)

    def execute(self, context):
        import subprocess
        import sys

        subprocess.run([sys.executable, '-m', 'ensurepip'],
                       capture_output=False, text=True, input="y")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                       capture_output=False, text=True, input="y")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'uninstall', *
                [name for name, _ in self.dep_names.items()]],
            capture_output=False, text=True, input="y")

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
    viewer_enabled: BoolProperty(default=True)
    viewer_url: StringProperty(default="https://hubs.local:8080/viewer.html")

    browser: EnumProperty(
        name="Choose a viewer browser", description="Type",
        items=[("Firefox", "Firefox", "Use Firefox as the viewer browser"),
               ("Chrome", "Chrome", "Use Chrome as the viewer browser")],
        default="Firefox")

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        box.row().prop(self, "row_length")
        box.row().prop(self, "recast_lib_path")

        selenium_available = isModuleAvailable("selenium")
        websockets_available = isModuleAvailable("websockets")
        modules_available = selenium_available and websockets_available
        box = layout.box()
        box.label(text="Viewer configuration")
        box.prop(self, "viewer_enabled")
        if modules_available:
            row = box.row()
            row.prop(self, "browser")
        row = box.row()
        row.alert = not modules_available
        row.label(
            text="Modules found."
            if modules_available else
            "Selenium and websockets modules not found. These modules are required to run the viewer")
        row = box.row()
        row.prop(self, "viewer_url")
        row = box.row()

        if self.viewer_available:
            op = row.operator(UninstallDepsOperator.bl_idname,
                              text="Uninstall selenium dependencies")
            op.dep_name = "selenium"
        else:
            op = row.operator(InstallDepsOperator.bl_idname,
                              text="Install selenium dependencies")
            op.dep_name = "selenium"

        if modules_available:
            op = row.operator(UninstallDepsOperator.bl_idname,
                              text="Uninstall dependencies (selenium, websockets)")
            op.dep_names.add().name = "selenium"
            op.dep_names.add().name = "websockets"
        else:
            op = row.operator(InstallDepsOperator.bl_idname,
                              text="Install dependencies (selenium, websockets")
            op.dep_names.add().name = "selenium"
            op.dep_names.add().name = "websockets"


def register():
    bpy.utils.register_class(DepsProperty)
    bpy.utils.register_class(HubsPreferences)
    bpy.utils.register_class(InstallDepsOperator)
    bpy.utils.register_class(UninstallDepsOperator)


def unregister():
    bpy.utils.unregister_class(UninstallDepsOperator)
    bpy.utils.unregister_class(InstallDepsOperator)
    bpy.utils.unregister_class(HubsPreferences)
    bpy.utils.unregister_class(DepsProperty)
