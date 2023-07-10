from . import (handlers, gizmos, components_registry, ui, operators, utils)


def register():
    utils.register()
    handlers.register()
    gizmos.register()
    components_registry.register()
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()
    components_registry.unregister()
    gizmos.unregister()
    handlers.unregister()
    utils.unregister()
