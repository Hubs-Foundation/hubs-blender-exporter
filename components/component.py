import bpy
from bpy.props import BoolProperty, StringProperty, CollectionProperty, PointerProperty
from bpy.types import PropertyGroup


class HubsComponentName(PropertyGroup):
    name: StringProperty(name="name")
    expanded: BoolProperty(name="expanded", default=True)


class HubsComponentList(PropertyGroup):
    items: CollectionProperty(type=HubsComponentName)


class HubsActiveGizmo(PropertyGroup):
    type: StringProperty(name="type")


def register():
    bpy.utils.register_class(HubsComponentName)
    bpy.utils.register_class(HubsComponentList)
    bpy.utils.register_class(HubsActiveGizmo)

    bpy.types.Object.hubs_component_list = PointerProperty(
        type=HubsComponentList)
    bpy.types.Object.hubs_active_gizmo = PointerProperty(type=HubsActiveGizmo)


def unregister():
    del bpy.types.Object.hubs_component_list
    del bpy.types.Object.hubs_active_gizmo

    bpy.utils.unregister_class(HubsComponentName)
    bpy.utils.unregister_class(HubsComponentList)
    bpy.utils.unregister_class(HubsActiveGizmo)
