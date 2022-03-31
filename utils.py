def get_addon_folder():
    import info
    import addon_utils
    import os

    for mod in addon_utils.modules():
        if mod.bl_info['name'] == info.bl_info["name"]:
            filepath = mod.__file__
            return os.path.basename(os.path.dirname(filepath))
        else:
            pass
