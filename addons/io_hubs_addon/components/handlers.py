import bpy
from bpy.app.handlers import persistent
from .components_registry import get_components_registry
from .utils import get_c_stdout
from .utils import host_components
from .gizmos import update_gizmos
import io
import sys

file_just_loaded = False
previous_undo_steps_dump = ""
previous_undo_step_index = 0


def migrate_components(migration_type):
    version = (0,0,0)
    if migration_type == 'GLOBAL':
        version = tuple(bpy.context.scene.HubsComponentsExtensionProperties.version)
        if version == (1,0,0):
            return

    for scene in bpy.data.scenes:
        for component in host_components(scene):
            if migration_type == 'LOCAL':
                version = (0,0,0) # TODO: add version to components.
            component.migrate(version, scene)

    for ob in bpy.data.objects:
        for component in host_components(ob):
            if migration_type == 'LOCAL':
                version = (0,0,0) # TODO: add version to components.
            component.migrate(version, ob, ob=ob)

        if ob.type == 'ARMATURE':
            for bone in ob.data.bones:
                for component in host_components(bone):
                    if migration_type == 'LOCAL':
                        version = (0,0,0) # TODO: add version to components.
                    component.migrate(version, bone, ob=ob)

    if migration_type == 'LOCAL':
        update_gizmos()


@persistent
def load_post(dummy):
    global file_just_loaded
    global previous_undo_steps_dump
    global previous_undo_step_index
    file_just_loaded = True
    previous_undo_steps_dump = ""
    previous_undo_step_index = 0
    migrate_components('GLOBAL')


@persistent
def version_update(dummy):
    from .. import (bl_info)
    bpy.context.scene.HubsComponentsExtensionProperties.version = bl_info['version']


def find_active_undo_step_index(undo_steps):
    index = 0
    for step in undo_steps:
        if "[*" in step:
            return index

        index += 1

    return None


@persistent
def append_link_handler(dummy):
    global file_just_loaded
    global previous_undo_steps_dump
    global previous_undo_step_index

    if file_just_loaded:
        file_just_loaded = False
        return

    binary_stream = io.BytesIO()

    with get_c_stdout(binary_stream):
        bpy.context.window_manager.print_undo_steps()

    undo_steps_dump = binary_stream.getvalue().decode(sys.stdout.encoding)

    if undo_steps_dump == previous_undo_steps_dump:
        # The undo stack hasn't changed, so return early.  Note: this prevents modal operators from triggering things repeatedly.
        return

    undo_steps = undo_steps_dump.split("\n")[1:-1]
    undo_step_index = find_active_undo_step_index(undo_steps)

    if undo_step_index < previous_undo_step_index:
        previous_undo_step_index = undo_step_index
        return

    active_undo_step = undo_steps[undo_step_index]
    undo_name = active_undo_step.split("name=")[-1][1:-1]

    if undo_name in {'Append', 'Link'}:
        migrate_components('LOCAL')

    previous_undo_steps_dump = undo_steps_dump
    previous_undo_step_index = undo_step_index


def register():
    if not load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post)

    if not version_update in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(version_update)

    if not append_link_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(append_link_handler)


def unregister():
    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    if version_update in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(version_update)

    if append_link_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(append_link_handler)
