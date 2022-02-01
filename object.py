import bpy
from bpy.types import PropertyGroup, StringProperty, PointerProperty


class StringArrayValueProperty(PropertyGroup):
    value: StringProperty(name="value", default="")


class HubsComponentProperties(PropertyGroup):
    """A target is a property of an object that is meant to be driven by a widget"""

    name: StringProperty(
        name="Name",
        description="Component name",
        default=""
    )

    value: StringProperty(
        name="Value",
        description="Component value",
        default=""
    )


def register():
    bpy.utils.register_class(StringArrayValueProperty)
    bpy.types.Object.hubs_components = PointerProperty(
        type=StringArrayValueProperty)


def unregister():
    del bpy.types.Object.hubs_components
    bpy.utils.unregister_class(StringArrayValueProperty)
