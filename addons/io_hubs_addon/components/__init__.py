from . import (migrations, gizmos, components_registry, panels, operators)


def register():
    migrations.register()
    gizmos.register()
    components_registry.register()
    operators.register()
    panels.register()


def unregister():
    panels.unregister()
    operators.unregister()
    components_registry.unregister()
    gizmos.unregister()
    migrations.unregister()
