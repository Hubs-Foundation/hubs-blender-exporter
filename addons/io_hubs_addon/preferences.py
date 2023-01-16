import bpy
from bpy.types import AddonPreferences
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty
from .utils import get_addon_package
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


class InstallDepsOperator(bpy.types.Operator):
    bl_idname = "pref.hubs_prefs_install_dep"
    bl_label = "Install a python dependency through pip"
    bl_property = "dep_name"
    bl_options = {'REGISTER', 'UNDO'}

    dep_name: StringProperty(default=" ")

    def execute(self, context):
        import subprocess
        import sys

        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                       capture_output=False, text=True, input="y")
        from .utils import get_user_python_path
        subprocess.run([sys.executable, '-m', 'pip', 'install', self.dep_name, '-t', get_user_python_path()],
                       capture_output=False, text=True, input="y")

        return {'FINISHED'}


class UninstallDepsOperator(bpy.types.Operator):
    bl_idname = "pref.hubs_prefs_uninstall_dep"
    bl_label = "Uninstall a python dependency through pip"
    bl_property = "dep_name"
    bl_options = {'REGISTER', 'UNDO'}

    dep_name: StringProperty(default=" ")

    def execute(self, context):
        import subprocess
        import sys

        subprocess.run([sys.executable, '-m', 'ensurepip'],
                       capture_output=False, text=True, input="y")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                       capture_output=False, text=True, input="y")
        subprocess.run([sys.executable, '-m', 'pip', 'uninstall', self.dep_name],
                       capture_output=False, text=True, input="y")

        return {'FINISHED'}


def isViewerAvailable():
    import importlib
    selenium_loader = importlib.util.find_spec('selenium')
    return selenium_loader is not None


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

        viewer_available = isViewerAvailable()
        box = layout.box()
        box.label(text="Viewer configuration")
        if viewer_available:
            row = box.row()
            row.prop(self, "browser")
        row = box.row()
        row.alert = not viewer_available
        row.label(
            text="Selenium module found."
            if viewer_available else "Selenium module not found. Selenium is required to run the viewer")
        row = box.row()
        row.prop(self, "viewer_url")
        row = box.row()
        if viewer_available:
            op = row.operator(UninstallDepsOperator.bl_idname,
                              text="Uninstall selenium dependencies")
            op.dep_name = "selenium"
        else:
            op = row.operator(InstallDepsOperator.bl_idname,
                              text="Install selenium dependencies")
            op.dep_name = "selenium"


def register():
    bpy.utils.register_class(HubsPreferences)
    bpy.utils.register_class(InstallDepsOperator)
    bpy.utils.register_class(UninstallDepsOperator)


def unregister():
    bpy.utils.unregister_class(UninstallDepsOperator)
    bpy.utils.unregister_class(InstallDepsOperator)
    bpy.utils.unregister_class(HubsPreferences)
