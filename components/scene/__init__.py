from os.path import dirname
import bpy
from bpy.props import PointerProperty
from ..utils import register_components_in_folder, unregister_components_in_folder, get_modules_in_folder
from ..component import HubsComponentList
from ...utils import get_module_path

modules_path =  get_module_path(['components', 'scene'])

registered_modules = []

def register():
    register_components_in_folder(get_modules_in_folder(dirname(__file__)), modules_path, registered_modules)
    bpy.types.Object.hubs_component_list = PointerProperty(type=HubsComponentList)


def unregister():
    del bpy.types.Object.hubs_component_list
    unregister_components_in_folder(registered_modules)
    del registered_modules[:]
