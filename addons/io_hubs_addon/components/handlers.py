import bpy
from bpy.app.handlers import persistent
from .components_registry import get_components_registry


@persistent
def migrate_components(dummy):
    components_registry = get_components_registry()
    for _, component_class in components_registry.items():
        component_class.migrate(tuple(
            bpy.context.scene.HubsComponentsExtensionProperties.version))


@persistent
def version_update(dummy):
    from .. import (bl_info)
    bpy.context.scene.HubsComponentsExtensionProperties.version = bl_info['version'][0:3]


def register():
    if not migrate_components in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(migrate_components)

    if not version_update in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(version_update)


def unregister():
    if migrate_components in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(migrate_components)

    if version_update in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(version_update)
