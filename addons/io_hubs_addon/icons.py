import bpy
import os
from os import listdir
from os.path import join, isfile
import bpy.utils.previews


def load_icons():
    global __hubs_icons
    __hubs_icons = {}
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    icons = [f for f in listdir(icons_dir) if isfile(join(icons_dir, f))]
    for icon in icons:
        pcoll.load(icon, os.path.join(icons_dir, icon), 'IMAGE')
        print("Loading icon: " + icon)
    __hubs_icons["hubs"] = pcoll


def unload_icons():
    global __hubs_icons
    __hubs_icons["hubs"].close()
    del __hubs_icons


def get_hubs_icons():
    global __hubs_icons
    return __hubs_icons["hubs"]


__hubs_icons = {}


def register():
    load_icons()


def unregister():
    unload_icons()
