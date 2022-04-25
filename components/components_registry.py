import bpy.utils.previews
import bpy
from bpy.props import BoolProperty, StringProperty, CollectionProperty, PointerProperty
from bpy.types import PropertyGroup

import importlib
import inspect
import os
from os import listdir
from os.path import join, isfile, dirname, realpath

from .definitions.hubs_component import HubsComponent, NodeType


class HubsComponentName(PropertyGroup):
    # For backwards compatibility reasons this attribute is called "name" but it actually points to the component id
    name: StringProperty(name="name")
    expanded: BoolProperty(name="expanded", default=True)


class HubsComponentList(PropertyGroup):
    items: CollectionProperty(type=HubsComponentName)


def get_component_definitions():
    component_module_names = []
    components_dir = join(dirname(realpath(__file__)), "definitions")
    for f in os.listdir(components_dir):
        if isfile(join(components_dir, f)) and f.endswith(".py"):
            component_module_names.append(f[:-3])

    return [
        importlib.import_module(".definitions." + name, package=__package__)
        for name in component_module_names
    ]


def register_component(component_class):
    print("Registering component: " + component_class.get_id())
    bpy.utils.register_class(component_class)

    component_name = component_class.get_name()
    if component_class.get_node_type() == NodeType.SCENE:
        setattr(
            bpy.types.Scene,
            component_name,
            PointerProperty(type=component_class)
        )
    elif component_class.get_node_type() == NodeType.NODE:
        setattr(
            bpy.types.Object,
            component_name,
            PointerProperty(type=component_class)
        )
        setattr(
            bpy.types.Bone,
            component_name,
            PointerProperty(type=component_class)
        )
        setattr(
            bpy.types.EditBone,
            component_name,
            PointerProperty(type=component_class)
        )
    elif component_class.get_node_type() == NodeType.MATERIAL:
        setattr(
            bpy.types.Material,
            component_name,
            PointerProperty(type=component_class)
        )


def unregister_component(component_class):
    component_name = component_class.get_name()
    if component_class.get_node_type() == NodeType.SCENE:
        delattr(bpy.types.Scene, component_name)
    elif component_class.get_node_type() == NodeType.NODE:
        delattr(bpy.types.Object, component_name)
        delattr(bpy.types.Bone, component_name)
        delattr(bpy.types.EditBone, component_name)
    elif component_class.get_node_type() == NodeType.MATERIAL:
        delattr(bpy.types.Material, component_name)

    bpy.utils.unregister_class(component_class)

    print("Component unregistered: " + component_class.get_id())


def load_components_registry():
    """Recurse in the components directory to build the components registry"""
    global __components_registry
    __components_registry = {}
    for module in get_component_definitions():
        for _, member in inspect.getmembers(module):
            if inspect.isclass(member) and issubclass(member, HubsComponent) and member != HubsComponent:
                register_component(member)
                __components_registry[member.get_id()] = member


def unload_components_registry():
    """Recurse in the components directory to unload the registered components"""
    global __components_registry
    for _, component_class in __components_registry.items():
        unregister_component(component_class)


def load_icons():
    global __component_icons
    __component_icons = {}
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    icons = [f for f in listdir(icons_dir) if isfile(join(icons_dir, f))]
    for icon in icons:
        pcoll.load(icon, os.path.join(icons_dir, icon), 'IMAGE')
        print("Loading icon: " + icon)
    __component_icons["hubs"] = pcoll


def unload_icons():
    print("Unloading all icons")
    global __component_icons
    __component_icons["hubs"].close()
    del __component_icons


__component_icons = {}
__components_registry = {}


def get_components_registry():
    global __components_registry
    return __components_registry


def get_components_icons():
    global __component_icons
    return __component_icons["hubs"]


def get_component_by_name(component_id):
    global __components_registry
    return __components_registry.get(component_id, None)


def get_component_by_id(component_id):
    global __components_registry
    return next((component_class for _, component_class in __components_registry.items() if component_class.get_id() == component_id), None)


def register():
    load_icons()
    load_components_registry()

    bpy.utils.register_class(HubsComponentName)
    bpy.utils.register_class(HubsComponentList)

    bpy.types.Object.hubs_component_list = PointerProperty(
        type=HubsComponentList)
    bpy.types.Scene.hubs_component_list = PointerProperty(
        type=HubsComponentList)
    bpy.types.Material.hubs_component_list = PointerProperty(
        type=HubsComponentList)
    bpy.types.Bone.hubs_component_list = PointerProperty(
        type=HubsComponentList)
    bpy.types.EditBone.hubs_component_list = PointerProperty(
        type=HubsComponentList)


def unregister():
    del bpy.types.Object.hubs_component_list
    del bpy.types.Scene.hubs_component_list
    del bpy.types.Material.hubs_component_list
    del bpy.types.Bone.hubs_component_list
    del bpy.types.EditBone.hubs_component_list

    bpy.utils.unregister_class(HubsComponentName)
    bpy.utils.unregister_class(HubsComponentList)

    unload_components_registry()
    unload_icons()

    global __components_registry
    del __components_registry
