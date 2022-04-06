from . import (gizmo_registry, gizmo_group)


def register():
    gizmo_registry.register()
    gizmo_group.register()


def unregister():
    gizmo_group.unregister()
    gizmo_registry.unregister()
