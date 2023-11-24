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
