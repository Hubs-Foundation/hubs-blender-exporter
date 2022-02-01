from ..consts import ADDON_ROOT_FOLDER
import importlib
from os.path import dirname, basename, isfile, join
import glob

modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [basename(f)[:-3] for f in modules if isfile(f)
           and not f.endswith('__init__.py')]


folder = ADDON_ROOT_FOLDER + '.components'

registered_modules = []


def register():
    '''
    Dynamically register all components in this folder.
    '''
    for module_name in __all__:
        if (module_name != folder):
            module = importlib.import_module(
                '.' + module_name, folder)
            registered_modules.append(module)
            print("Register component: " + module.__name__)
            module.register()


def unregister():
    for module in registered_modules:
        print("Unregister component: " + module.__name__)
        module.unregister()
    del registered_modules[:]
