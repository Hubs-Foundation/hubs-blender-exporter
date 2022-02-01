import bpy
from .types import HubsComponentTypes
from .gizmo_info import (
    GizmoInfo
)

# -------------------------------------------------------------------


def get_gizmo_modules():
    import os
    from os.path import join, dirname, realpath, isfile
    import importlib

    gizmo_module_names = []
    gizmo_module_dir = join(dirname(realpath(__file__)), "gizmos")
    for f in os.listdir(gizmo_module_dir):
        if f.endswith(".py") and isfile(join(gizmo_module_dir, f)):
            gizmo_module_names.append(f[:-3])

    return [
        importlib.import_module(".gizmos." + name, package=__package__)
        for name in gizmo_module_names
    ]

# -------------------------------------------------------------------


def load_gizmo_registry():
    """Recurse in the Gizmos directory to build the gizmo registry"""
    registry = {}
    for module in get_gizmo_modules():
        # Find variables of type GizmoInfo in the module and register them in registry
        for identifier in dir(module):
            member = getattr(module, identifier)
            t = type(member)
            if t == GizmoInfo:
                print("Registering gizmo: " + identifier)
                registry[identifier] = member

    return registry

# -------------------------------------------------------------------


class delete_override(bpy.types.Operator):
    """Override object delete operator to update gizmos after deletion"""
    bl_idname = "object.delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'UNDO'}

    use_global: bpy.props.BoolProperty(default=True)
    confirm: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for obj in context.selected_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

        from .gizmo_group import update_gizmos
        update_gizmos(None, context)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)


def consolidate_register_functions():
    """Recurse in the Gizmos directory to register and unregister functions"""
    register_functions = []
    unregister_functions = []
    for module in get_gizmo_modules():
        if hasattr(module, 'register'):
            register_functions.append(getattr(module, 'register'))
        if hasattr(module, 'unregister'):
            unregister_functions.append(getattr(module, 'unregister'))

    def register():
        bpy.types.Object.HBA_component_type = bpy.props.EnumProperty(
            items=HubsComponentTypes)
        bpy.utils.register_class(delete_override)
        for f in register_functions:
            f()

    def unregister():
        del bpy.types.Object.HBA_component_type
        bpy.utils.unregister_class(delete_override)
        for f in unregister_functions[::-1]:
            f()
    return register, unregister

# -------------------------------------------------------------------


registry = load_gizmo_registry()

register, unregister = consolidate_register_functions()
