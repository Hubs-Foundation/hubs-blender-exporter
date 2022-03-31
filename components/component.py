import bpy
from bpy.props import BoolProperty, StringProperty, CollectionProperty
from bpy.types import PropertyGroup

class HubsComponentName(PropertyGroup):
    name: StringProperty(name="name")
    expanded: BoolProperty(name="expanded", default=True)

class HubsComponentList(PropertyGroup):
    items: CollectionProperty(type=HubsComponentName)

def register():
    bpy.utils.register_class(HubsComponentName)
    bpy.utils.register_class(HubsComponentList)

def unregister():
    bpy.utils.unregister_class(HubsComponentName)
    bpy.utils.unregister_class(HubsComponentList)