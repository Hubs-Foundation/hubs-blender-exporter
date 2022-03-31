def get_addon_folder():
    from .info import bl_info
    import addon_utils
    import os

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == bl_info["name"]:
            filepath = mod.__file__
            return os.path.basename(os.path.dirname(filepath))
        else:
            pass

def get_module_path(module_names):
    return '.'.join([get_addon_folder()] + module_names)
