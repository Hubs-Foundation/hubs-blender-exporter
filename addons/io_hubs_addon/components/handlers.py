import bpy
from bpy.app.handlers import persistent
from .components_registry import get_components_registry
from .utils import redirect_c_stdout
from .utils import get_host_components
from .gizmos import update_gizmos
from ..utils import get_version
import io
import sys

previous_undo_steps_dump = ""
previous_undo_step_index = 0
previous_scene_name = ""
previous_view_layer_name = ""
file_loading = False


def migrate_components(migration_type, *, do_update_gizmos=True):
    version = (0,0,0)
    global_version = get_version()
    migration_report = []
    if migration_type == 'GLOBAL':
        version = tuple(bpy.context.scene.HubsComponentsExtensionProperties.version)
        if version == global_version:
            return

    for scene in bpy.data.scenes:
        for component in get_host_components(scene):
            if migration_type == 'LOCAL':
                version = tuple(component.addon_version)
            try:
                component.migrate(migration_type, version, scene, migration_report)
                component.addon_version = global_version
            except:
                error = f"Error: Migration failed for component {component.get_display_name()} on scene \"{scene.name_full}\""
                migration_report.append(error)

    for ob in bpy.data.objects:
        for component in get_host_components(ob):
            if migration_type == 'LOCAL':
                version = tuple(component.addon_version)
            try:
                component.migrate(migration_type, version, ob, migration_report, ob=ob)
                component.addon_version = global_version
            except:
                error = f"Error: Migration failed for component {component.get_display_name()} on object \"{ob.name_full}\""
                migration_report.append(error)

        if ob.type == 'ARMATURE':
            for bone in ob.data.bones:
                for component in get_host_components(bone):
                    if migration_type == 'LOCAL':
                        version = tuple(component.addon_version)
                    try:
                        component.migrate(migration_type, version, bone, migration_report, ob=ob)
                        component.addon_version = global_version
                    except:
                        error = f"Error: Migration failed for component {component.get_display_name()} on bone \"{bone.name}\" in \"{ob.name_full}\""
                        migration_report.append(error)


    if migration_type == 'LOCAL' and do_update_gizmos:
        update_gizmos()

    if migration_report:
        def report_migration():
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title="Component Migration Report", report_string='\n'.join(migration_report))
        bpy.app.timers.register(report_migration)


@persistent
def load_post(dummy):
    global previous_undo_steps_dump
    global previous_undo_step_index
    global previous_scene_name
    global previous_view_layer_name
    global file_loading
    previous_undo_steps_dump = ""
    previous_undo_step_index = 0
    previous_scene_name = bpy.context.scene.name
    previous_view_layer_name = bpy.context.view_layer.name
    file_loading = True
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
def undo_stack_handler(dummy=None):
    global previous_undo_steps_dump
    global previous_undo_step_index
    global previous_scene_name
    global previous_view_layer_name
    global file_loading

    # Return if Blender isn't in a fully loaded state. (Prevents Blender crashing)
    if file_loading and not bpy.context.space_data:
        file_loading = False
        return

    file_loading = False

    # Get a representation of the undo stack.
    binary_stream = io.BytesIO()

    with redirect_c_stdout(binary_stream):
        bpy.context.window_manager.print_undo_steps()

    undo_steps_dump = binary_stream.getvalue().decode(sys.stdout.encoding)
    binary_stream.close()

    if undo_steps_dump == previous_undo_steps_dump:
        # The undo stack hasn't changed, so return early.  Note: this prevents modal operators (and anything else) from triggering things repeatedly when nothing has changed.
        return

    # Convert the undo stack representation into a list of undo steps (removing the unneeded header and footer in the process) and find the active undo step index.
    undo_steps = undo_steps_dump.split("\n")[1:-1]
    undo_step_index = find_active_undo_step_index(undo_steps)

    try: # Get the interim undo steps that need to be processed (can be more than one) and whether the change has been forward ('DO') or backward ('UNDO').  'UNDO' includes the previous index, while 'DO' does not.
        if undo_step_index < previous_undo_step_index: # UNDO
            start = previous_undo_step_index
            stop = undo_step_index
            interim_undo_steps = [undo_steps[i] for i in range(start, stop, -1)]
        else: # DO
            start = previous_undo_step_index + 1
            stop = undo_step_index
            interim_undo_steps = [undo_steps[i] for i in range(start, stop)]

    except: # Fall back to just processing the current undo step.
        print("Warning: Couldn't get the full range of undo steps to process.  Falling back to the current one.")
        interim_undo_steps = []


    # Allow performance heavy tasks to be combined into one task that is executed at the end of the handler so they're run as little as possible.
    task_scheduler = set()

    # Handle the undo steps that have passed since the previous time this executed. This accounts for steps undone, users jumping around in the history ,and any updates that might have been missed.
    for undo_step in interim_undo_steps:
        step_name = undo_step.split("name=")[-1][1:-1]

        if step_name in {'Append', 'Link'}:
            task_scheduler.add('update_gizmos')

        if step_name in {'Add Hubs Component', 'Remove Hubs Component', 'Delete'}:
            task_scheduler.add('update_gizmos')

    # Handle the active undo step.  Migrations (or anything that modifies blend data) need to be handled here because the undo step in which they occurred holds the unmodified data, so the modifications need to be applied each time it becomes active.
    active_step_name = undo_steps[undo_step_index].split("name=")[-1][1:-1]

    if active_step_name in {'Append', 'Link'}:
        migrate_components('LOCAL', do_update_gizmos=False)
        task_scheduler.add('update_gizmos')

    if active_step_name in {'Add Hubs Component', 'Remove Hubs Component', 'Delete'}:
        task_scheduler.add('update_gizmos')

    # Handle scene and view layer changes.  The step names aren't specific enough and the interim steps don't matter, so just check if the scene or view layer has changed.
    if previous_scene_name != bpy.context.scene.name or previous_view_layer_name != bpy.context.view_layer.name:
        task_scheduler.add('update_gizmos')

    # Execute the scheduled performance heavy tasks.
    for task in task_scheduler:
        if task == 'update_gizmos':
            update_gizmos()
        else:
            print('Error: unrecognized task scheduled')

    # Store things for comparison next time.
    previous_undo_steps_dump = undo_steps_dump
    previous_undo_step_index = undo_step_index
    previous_scene_name = bpy.context.scene.name
    previous_view_layer_name = bpy.context.view_layer.name


def scene_and_view_layer_update_notifier(self, context):
    """Some scene/view layer actions/changes don't trigger a depsgraph update so watch the top bar for changes to the scene or view layer by hooking into it's draw method."""
    global previous_scene_name
    global previous_view_layer_name

    if context.scene.name != previous_scene_name or context.view_layer.name != previous_view_layer_name:
        bpy.app.timers.register(undo_stack_handler)


def register():
    if not load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post)

    if not version_update in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(version_update)

    if not undo_stack_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(undo_stack_handler)

    bpy.types.TOPBAR_HT_upper_bar.append(scene_and_view_layer_update_notifier)


def unregister():
    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    if version_update in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(version_update)

    if undo_stack_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(undo_stack_handler)

    bpy.types.TOPBAR_HT_upper_bar.remove(scene_and_view_layer_update_notifier)
