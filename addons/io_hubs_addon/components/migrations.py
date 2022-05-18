import bpy
from bpy.app.handlers import persistent
from .components_registry import get_components_registry


@persistent
def migrate_components(dummy):
    components_registry = get_components_registry()
    for _, component_class in components_registry.items():
        component_class.migrate()


def register():
    if not migrate_components in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(migrate_components)


def unregister():
    if migrate_components in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(migrate_components)
