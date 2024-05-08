import functools


def get_addon_package():
    return __package__


def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))


def delayed_gather(func):
    """ It delays the gather until all resources are available """
    def wrapper_delayed_gather(*args, **kwargs):
        def gather():
            return func(*args, **kwargs)
        gather.delayed_gather = True
        return gather
    return wrapper_delayed_gather


def get_or_create_deps_path(name):
    import os
    deps_path = os.path.abspath(os.path.join(
        __file__, "..", ".__deps__", name))
    if not os.path.exists(deps_path):
        os.makedirs(deps_path, exist_ok=True)
    return deps_path


def is_module_available(name):
    import sys
    old_syspath = sys.path[:]
    old_sysmod = sys.modules.copy()

    try:
        path = get_or_create_deps_path(name)

        import importlib
        sys.path.insert(0, str(path))

        try:
            loader = importlib.util.find_spec(name)
        except ImportError as ex:
            print(f'{name} not found')

        import os
        path = os.path.join(path, name)
        return loader and os.path.exists(path)

    finally:
        # Restore without assigning a new list instance. That way references
        # held by other code will stay valid.
        sys.path[:] = old_syspath
        sys.modules.clear()
        sys.modules.update(old_sysmod)


def load_dependency(name):
    import sys
    old_syspath = sys.path[:]
    old_sysmod = sys.modules.copy()

    module = None
    try:
        modules = name.split(".")
        path = get_or_create_deps_path(modules[0])

        import importlib
        sys.path.insert(0, str(path))

        try:
            module = importlib.import_module(name)
        except ImportError as ex:
            print(f'Unable to load {name}')

    finally:
        # Restore without assigning a new list instance. That way references
        # held by other code will stay valid.
        sys.path[:] = old_syspath
        sys.modules.clear()
        sys.modules.update(old_sysmod)

    return module


HUBS_PREFS_DIR = ".__hubs_blender_addon_preferences"
HUBS_SELENIUM_PROFILE_FIREFOX = "hubs_selenium_profile.firefox"
HUBS_SELENIUM_PROFILE_CHROME = "hubs_selenium_profile.chrome"
HUBS_PREFS = "hubs_prefs.json"


def get_prefs_dir_path():
    import os
    home_directory = os.path.expanduser("~")
    prefs_dir_path = os.path.join(home_directory, HUBS_PREFS_DIR)
    return os.path.normpath(prefs_dir_path)


def create_prefs_dir():
    import os
    prefs_dir = get_prefs_dir_path()
    if not os.path.exists(prefs_dir):
        os.makedirs(prefs_dir)


def get_browser_profile_directory(browser):
    import os
    prefs_folder = get_prefs_dir_path()
    file_path = ""
    if browser == "Firefox":
        file_path = os.path.join(
            prefs_folder, HUBS_SELENIUM_PROFILE_FIREFOX)
    elif browser == "Chrome":
        file_path = os.path.join(
            prefs_folder, HUBS_SELENIUM_PROFILE_CHROME)

    return os.path.normpath(file_path)


def get_prefs_path():
    import os
    prefs_folder = get_prefs_dir_path()
    prefs_path = os.path.join(prefs_folder, HUBS_PREFS)
    return os.path.normpath(prefs_path)


def save_prefs(context):
    prefs = context.window_manager.hubs_scene_debugger_prefs

    data = {
        "scene_debugger": {},
        "scene_publisher": {}
    }

    instances_array = []
    for instance in prefs.hubs_instances:
        instances_array.append({
            "name": instance.name,
            "url": instance.url
        })
    data["scene_debugger"] = {
        "hubs_instance_idx": prefs.hubs_instance_idx,
        "hubs_instances": instances_array
    }

    rooms_array = []
    for room in prefs.hubs_rooms:
        rooms_array.append({
            "name": room.name,
            "url": room.url
        })
    data["scene_debugger"].update({
        "hubs_room_idx": prefs.hubs_room_idx,
        "hubs_rooms": rooms_array
    })

    scene_props = context.window_manager.hubs_scene_debugger_scenes_props
    scenes_array = []
    for scene in scene_props.scenes:
        scenes_array.append({
            "scene_id": scene["scene_id"],
            "name": scene["name"],
            "description": scene["description"],
            "url": scene["url"],
            "screenshot_url": scene["screenshot_url"],
        })
    data["scene_publisher"].update({
        "instance": scene_props.instance,
        "scenes": scenes_array,
        "scene_idx": scene_props.scene_idx
    })

    out_path = get_prefs_path()
    try:
        import json
        json_data = json.dumps(data)
        with open(out_path, "w") as outfile:
            outfile.write(json_data)

    except Exception as err:
        import bpy
        bpy.ops.wm.hubs_report_viewer(
            'INVOKE_DEFAULT', title="Hubs scene debugger report",
            report_string=f'An error happened while saving the preferences from {out_path}: {err}')


def load_prefs(context):
    data = {}

    out_path = get_prefs_path()
    import os
    if not os.path.isfile(out_path):
        return

    try:
        import json
        import os
        with open(out_path, "r") as outfile:
            if (os.path.getsize(out_path)) == 0:
                return
            data = json.load(outfile)

    except Exception as err:
        import bpy
        bpy.ops.wm.hubs_report_viewer(
            'INVOKE_DEFAULT', title="Hubs scene debugger report",
            report_string=f'An error happened while loading the preferences from {out_path}: {err}')

    if not data:
        return

    prefs = context.window_manager.hubs_scene_debugger_prefs
    if "scene_debugger" in data:
        scene_debugger = data["scene_debugger"]
        prefs["hubs_instance_idx"] = scene_debugger["hubs_instance_idx"]
        prefs.hubs_instances.clear()
        instances = scene_debugger["hubs_instances"]
        for instance in instances:
            new_instance = prefs.hubs_instances.add()
            new_instance.name = instance["name"]
            new_instance.url = instance["url"]

        prefs["hubs_room_idx"] = scene_debugger["hubs_room_idx"]
        prefs.hubs_rooms.clear()
        rooms = scene_debugger["hubs_rooms"]
        for room in rooms:
            new_room = prefs.hubs_rooms.add()
            new_room.name = room["name"]
            new_room.url = room["url"]

    scene_props = context.window_manager.hubs_scene_debugger_scenes_props
    if "scene_publisher" in data:
        scene_publisher = data["scene_publisher"]
        scene_props.instance = scene_publisher["instance"]
        scene_props.scene_idx = scene_publisher["scene_idx"]
        scene_props.scenes.clear()
        scenes = scene_publisher["scenes"]
        for scene in scenes:
            new_scene = scene_props.scenes.add()
            new_scene["scene_id"] = scene["scene_id"]
            new_scene["name"] = scene["name"]
            new_scene["description"] = scene["description"]
            new_scene["url"] = scene["url"]
            new_scene["screenshot_url"] = scene["screenshot_url"]

    prefs["hubs_room_idx"] = scene_debugger["hubs_room_idx"]
    prefs.hubs_rooms.clear()
    rooms = scene_debugger["hubs_rooms"]
    for room in rooms:
        new_room = prefs.hubs_rooms.add()
        new_room.name = room["name"]
        new_room.url = room["url"]


def find_area(area_type):
    try:
        import bpy
        for a in bpy.data.window_managers[0].windows[0].screen.areas:
            if a.type == area_type:
                return a
        return None
    except Exception as err:
        return None


def image_type_to_file_ext(image_type):
    file_extension = None
    if image_type == 'PNG':
        file_extension = '.png'
    elif image_type == 'JPEG':
        file_extension = '.jpg'
    elif image_type == 'BMP':
        file_extension = '.bmp'
    elif image_type == 'JPEG2000':
        file_extension = '.jpeg'
    elif image_type == 'TARGA':
        file_extension = '.tga'
    elif image_type == 'TARGA_RAW':
        file_extension = '.tga'
    return file_extension
