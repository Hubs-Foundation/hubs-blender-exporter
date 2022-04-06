import bpy
from .gizmo_info import (
    GizmoInfo
)


def get_gizmo_modules():
    import os
    from os.path import join, dirname, realpath, isfile
    import importlib

    gizmo_module_names = []
    gizmo_module_dir = join(dirname(realpath(__file__)), "types")
    for f in os.listdir(gizmo_module_dir):
        if f.endswith(".py") and isfile(join(gizmo_module_dir, f)):
            gizmo_module_names.append(f[:-3])

    return [
        importlib.import_module(".types." + name, package=__package__)
        for name in gizmo_module_names
    ]


def load_gizmo_registry():
    """Recurse in the Gizmos directory to build the gizmo registry"""
    global __registry
    for module in get_gizmo_modules():
        # Find variables of type GizmoInfo in the module and register them in registry
        for identifier in dir(module):
            member = getattr(module, identifier)
            t = type(member)
            if t == GizmoInfo:
                print("Registering gizmo with id: " + member.id)
                __registry[member.id] = member


def unload_gizmo_registry():
    """Recurse in the Gizmos directory to unload the registered the gizmos"""
    print("Unregistering all gizmos")
    global __registry
    del __registry


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
        bpy.utils.register_class(delete_override)
        for f in register_functions:
            f()

        load_gizmo_registry()

    def unregister():
        bpy.utils.unregister_class(delete_override)
        for f in unregister_functions[::-1]:
            f()

        unload_gizmo_registry()

    return register, unregister


__registry = {}


def get_components_registry():
    global __registry
    return __registry


register, unregister = consolidate_register_functions()
