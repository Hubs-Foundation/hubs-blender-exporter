from . import (components_registry, panels, operators)


def register():
    components_registry.register()
    operators.register()
    panels.register()


def unregister():
    panels.unregister()
    operators.unregister()
    components_registry.unregister()
