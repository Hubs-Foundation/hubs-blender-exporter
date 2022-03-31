from os.path import dirname
from ..utils import register_components_in_folder, unregister_components_in_folder, get_modules_in_folder
from ...utils import get_module_path

modules_path =  get_module_path(['components', 'object'])

registered_modules = []

def register():
    register_components_in_folder(get_modules_in_folder(dirname(__file__)), modules_path, registered_modules)


def unregister():
    unregister_components_in_folder(registered_modules)
    del registered_modules[:]
