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


def get_user_python_path():
    import sys
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'site',
                            '--user-site'], capture_output=True, text=True, input="y")
    return result.stdout.strip("\n")


def isModuleAvailable(name):
    import importlib
    loader = importlib.util.find_spec(name)
    return loader is not None


HUBS_SELENIUM_PROFILE_NAME_FIREFOX = ".__hubs_blender_exporter_selenium_profile.firefox"
HUBS_SELENIUM_PROFILE_NAME_CHROME = ".__hubs_blender_exporter_selenium_profile.chrome"
HUBS_PREFS = ".__hubs_debugger_prefs.json"


def get_browser_profile_directory(browser):
    import os
    home_directory = os.path.expanduser("~")
    file_path = ""
    if browser == "Firefox":
        file_path = os.path.join(
            home_directory, HUBS_SELENIUM_PROFILE_NAME_FIREFOX)
    elif browser == "Chrome":
        file_path = os.path.join(
            home_directory, HUBS_SELENIUM_PROFILE_NAME_CHROME)

    return file_path


def get_prefs_path():
    import os
    home_directory = os.path.expanduser("~")
    return os.path.join(home_directory, HUBS_PREFS)


def save_prefs(context):
    prefs = context.window_manager.hubs_scene_debugger_prefs

    data = {
        "scene_debugger": {}
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

    out_path = get_prefs_path()
    try:
        import json
        json_data = json.dumps(data)
        with open(out_path, "w") as outfile:
            outfile.write(json_data)

    except Exception as err:
        import bpy
        bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
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
        bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Hubs scene debugger report",
                                      report_string=f'An error happened while loading the preferences from {out_path}: {err}')

    if not data:
        return

    prefs = context.window_manager.hubs_scene_debugger_prefs
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
