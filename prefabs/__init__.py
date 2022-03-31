import importlib
from os.path import dirname, basename, isfile, join
import glob
import bpy
from bpy.types import VIEW3D_MT_add, Menu
from ..utils import get_module_path

modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [basename(f)[:-3] for f in modules if isfile(f)
           and not f.endswith('__init__.py')]


modules_path =  get_module_path(['prefabs'])

registered_modules = []

class HubsAddMenu(Menu):
    bl_label = "Hubs"
    bl_idname = "VIEW3D_MT_hubs_add_menu"

    def draw(self, context):
        for module in registered_modules:
            if not hasattr(module, "operators"):
                continue
            for operator in module.operators:
                self.layout.operator(
                    operator.bl_idname,
                    text=operator.bl_label,
                    icon='MESH_CUBE', # TODO: Use custom prefab icon
                )

def VIEW3D_MT_hubs_add(self, context):
    # TODO: Replace with custom icon
    self.layout.menu(menu=HubsAddMenu.bl_idname, icon='MESH_CUBE')

classes = (
    HubsAddMenu,
)
register_cls, unregister_cls = bpy.utils.register_classes_factory(classes)

def register():
    '''
    Dynamically register all prefabs in this folder.
    '''
    for module_name in __all__:
        if (module_name != modules_path):
            module = importlib.import_module(
                '.' + module_name, modules_path)
            registered_modules.append(module)
            print("Register prefab: " + module.__name__)
            module.register()

    register_cls()
    VIEW3D_MT_add.append(VIEW3D_MT_hubs_add)


def unregister():
    VIEW3D_MT_add.remove(VIEW3D_MT_hubs_add)
    unregister_cls()
    for module in registered_modules:
        print("Unregister prefab: " + module.__name__)
        module.unregister()
    del registered_modules[:]
