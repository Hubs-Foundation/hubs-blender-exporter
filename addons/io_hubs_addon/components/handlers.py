import bpy
from bpy.app.handlers import persistent
from .components_registry import get_components_registry
from .utils import redirect_c_stdout, get_host_components, is_linked
from .gizmos import update_gizmos
from .types import MigrationType, PanelType
import io
import sys
import traceback

previous_undo_steps_dump = ""
previous_undo_step_index = 0
previous_window_setups = []
file_loading = False


def migrate(component, migration_type, panel_type, host, migration_report, ob=None):
    instance_version = tuple(component.instance_version)
    definition_version = component.__class__.get_definition_version()
    was_migrated = False

    if instance_version < definition_version:
        was_migrated = component.migrate(
            migration_type, panel_type, instance_version, host, migration_report, ob=ob)

        if type(was_migrated) != bool:
            print(f"Warning: the {component.get_display_name()} component didn't return whether a migration occurred.")
            # Fall back to assuming there was a migration since the version increased.
            was_migrated = True

        component.instance_version = definition_version

    if panel_type not in component.__class__.get_panel_type() or not component.__class__.poll(panel_type, host, ob=ob):
        message = component.__class__.get_unsupported_host_message(panel_type, host)
        migration_report.append(message)

    return was_migrated


def migrate_components(
        migration_type, *, do_beta_versioning=False, do_update_gizmos=True, display_report=True,
        override_report_title=""):
    migration_report = []
    migrated_linked_components = []
    link_migration_occurred = False
    display_registration_message = False

    if do_beta_versioning:
        display_registration_message |= handle_beta_versioning()

    for scene in bpy.data.scenes:
        for component in get_host_components(scene):
            try:
                was_migrated = migrate(
                    component, migration_type, PanelType.SCENE, scene, migration_report)
            except Exception as e:
                was_migrated = True
                error = f"Error: Migration failed for component {component.get_display_name()} on scene \"{scene.name_full}\""
                migration_report.append(f"{error}\n{e} (See Blender's console for details)")
                print(error)
                traceback.print_exc()

            display_registration_message |= was_migrated
            if was_migrated and is_linked(scene):
                link_migration_occurred = True
                component_info = f"{component.get_display_name()} component on scene \"{scene.name_full}\""
                migrated_linked_components.append(component_info)

    for ob in bpy.data.objects:
        for component in get_host_components(ob):
            try:
                was_migrated = migrate(
                    component, migration_type, PanelType.OBJECT, ob, migration_report, ob=ob)
            except Exception as e:
                was_migrated = True
                error = f"Error: Migration failed for component {component.get_display_name()} on object \"{ob.name_full}\""
                migration_report.append(f"{error}\n{e} (See Blender's console for details)")
                print(error)
                traceback.print_exc()

            display_registration_message |= was_migrated
            if was_migrated and is_linked(ob):
                link_migration_occurred = True
                component_info = f"{component.get_display_name()} component on object \"{ob.name_full}\""
                migrated_linked_components.append(component_info)

        if ob.type == 'ARMATURE':
            for bone in ob.data.bones:
                for component in get_host_components(bone):
                    try:
                        was_migrated = migrate(
                            component, migration_type, PanelType.BONE, bone, migration_report, ob=ob)
                    except Exception as e:
                        was_migrated = True
                        error = f"Error: Migration failed for component {component.get_display_name()} on bone \"{bone.name}\" in \"{ob.name_full}\""
                        migration_report.append(f"{error}\n{e} (See Blender's console for details)")
                        print(error)
                        traceback.print_exc()

                    display_registration_message |= was_migrated
                    if was_migrated and is_linked(ob):
                        link_migration_occurred = True
                        component_info = f"{component.get_display_name()} component on bone \"{bone.name}\" in \"{ob.name_full}\""
                        migrated_linked_components.append(component_info)

    for material in bpy.data.materials:
        for component in get_host_components(material):
            try:
                was_migrated = migrate(
                    component, migration_type, PanelType.MATERIAL, material, migration_report)
            except Exception as e:
                was_migrated = True
                error = f"Error: Migration failed for component {component.get_display_name()} on material \"{material.name_full}\""
                migration_report.append(f"{error}\n{e} (See Blender's console for details)")
                print(error)
                traceback.print_exc()

            display_registration_message |= was_migrated
            if was_migrated and is_linked(material):
                link_migration_occurred = True
                component_info = f"{component.get_display_name()} component on material \"{material.name_full}\""
                migrated_linked_components.append(component_info)

    if do_update_gizmos:
        update_gizmos()

    if link_migration_occurred:
        migration_report.insert(
            0,
            "WARNING: A MIGRATION WAS PERFORMED ON LINKED COMPONENTS, THIS IS UNSTABLE AND MAY NOT BE PERMANENT.  RESAVE THE LINKED BLEND FILES WITH THE NEW VERSION TO AVOID THIS.")
        migration_report.append("MIGRATED LINKED COMPONENTS:")
        migration_report.extend(migrated_linked_components)

    if migration_type == MigrationType.REGISTRATION and display_registration_message:
        migration_report.insert(0, "WARNING: A MIGRATION WAS PERFORMED AFTER ADD-ON REGISTRATION.  AN UNDO STEP HAS BEEN ADDED TO STORE THE RESULTS OF THE MIGRATION.  IF YOU UNDO PAST THIS UNDO STEP YOU WILL HAVE TO INITIATE ANOTHER MIGRATION.\nRELOADING THE FILE WITH THE ADD-ON ALREADY ENABLED IS ADVISED.")

    if migration_report and display_report:
        title = "Component Migration Report"
        if override_report_title:
            title = override_report_title

        def report_migration():
            bpy.ops.wm.hubs_report_viewer('INVOKE_DEFAULT', title=title, report_string='\n\n'.join(migration_report))
        bpy.app.timers.register(report_migration)


def version_beta_components():
    for scene in bpy.data.scenes:
        if not is_linked(scene):
            for component in get_host_components(scene):
                component.instance_version = (1, 0, 0)

    for ob in bpy.data.objects:
        if not is_linked(ob):
            for component in get_host_components(ob):
                component.instance_version = (1, 0, 0)
            if ob.type == 'ARMATURE':
                for bone in ob.data.bones:
                    for component in get_host_components(bone):
                        component.instance_version = (1, 0, 0)

    for material in bpy.data.materials:
        if not is_linked(material):
            for component in get_host_components(material):
                component.instance_version = (1, 0, 0)


def handle_beta_versioning():
    did_versioning = False
    extension_properties = bpy.context.scene.HubsComponentsExtensionProperties
    if extension_properties:
        file_version = extension_properties.get('version')
        if file_version:
            if tuple(file_version) == (1, 0, 0):
                did_versioning = True
                version_beta_components()

            del bpy.context.scene.HubsComponentsExtensionProperties['version']

    return did_versioning


@persistent
def load_post(dummy):
    global previous_undo_steps_dump
    global previous_undo_step_index
    global previous_window_setups
    global file_loading
    previous_undo_steps_dump = ""
    previous_undo_step_index = 0
    previous_window_setups = []
    file_loading = True

    migrate_components(MigrationType.GLOBAL, do_beta_versioning=True)


def find_active_undo_step_index(undo_steps):
    index = 0
    for step in undo_steps:
        if "[*" in step:
            return index

        index += 1

    return None


@persistent
def undo_stack_handler(dummy):
    global previous_undo_steps_dump
    global previous_undo_step_index
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

    # Get the interim undo steps that need to be processed (can be more than one) and whether the change has been forward ('DO') or backward ('UNDO').  'UNDO' includes the previous index, while 'DO' does not.
    try:
        if undo_step_index < previous_undo_step_index:  # UNDO
            start = previous_undo_step_index
            stop = undo_step_index
            interim_undo_steps = [undo_steps[i] for i in range(start, stop, -1)]
            step_type = 'UNDO'
        else:  # DO
            start = previous_undo_step_index + 1
            stop = undo_step_index
            interim_undo_steps = [undo_steps[i] for i in range(start, stop)]
            step_type = 'DO'

    except Exception:  # Fall back to just processing the current undo step.
        print("Warning: Couldn't get the full range of undo steps to process.  Falling back to the current one.")
        interim_undo_steps = []
        step_type = 'DO'

    # Multiple undo steps/operations are being processed at once in this handler, so allow tasks to be combined into one that is executed at the end.  This also allows performance heavy tasks to be run as little as possible.  In general, any actual work performed should be scheduled as a task.
    task_scheduler = set()
    # task options
    display_report = False

    # Handle the undo steps that have passed since the previous time this executed. This accounts for steps undone, users jumping around in the history ,and any updates that might have been missed.
    for undo_step in interim_undo_steps:
        step_name = undo_step.split("name=")[-1][1:-1]

        if step_type == 'DO' and step_name in {'Link'}:
            # Components need to be migrated after they are linked, but don't need to be remigrated when returning to the link step, and don't store the migrated values in subsequent undo steps until after they have been made local.
            task_scheduler.add('migrate_components')
            display_report = False

        if step_type == 'UNDO' and step_name in {'Make Local', 'Localized Data'}:
            # Components need to be migrated again if they are returned to a linked state.
            task_scheduler.add('migrate_components')
            display_report = False
            task_scheduler.add('update_gizmos')

        if step_type == 'UNDO' and step_name in {'Delete', 'Unlink Object'}:
            # Linked components need to be migrated again if their removal was undone.
            task_scheduler.add('migrate_components')
            display_report = False

        if step_name in {'Add Hubs Component', 'Remove Hubs Component'}:
            task_scheduler.add('update_gizmos')

    # If the user has jumped ahead/back multiple undo steps, update the gizmos in case the number of objects/bones in the scene has remained the same, but gizmo objects have been added/removed.
    if abs(previous_undo_step_index - undo_step_index) > 1:
        task_scheduler.add('update_gizmos')

    # Handle the active undo step.  Migrations (or anything that modifies blend data) need to be handled here because the undo step in which they occurred holds the unmodified data, so the modifications need to be applied each time it becomes active.
    active_step_name = undo_steps[undo_step_index].split("name=")[-1][1:-1]

    if step_type == 'DO' and active_step_name in {'Link'}:
        # Components need to be migrated after they are linked, but don't need to be remigrated when returning to the link step, and don't store the migrated values in subsequent undo steps until after they have been made local.
        task_scheduler.add('migrate_components')
        display_report = True

    if step_type == 'DO' and active_step_name in {'Add Hubs Component', 'Remove Hubs Component'}:
        task_scheduler.add('update_gizmos')

    if active_step_name in {'Append'}:
        task_scheduler.add('migrate_components')
        display_report = (step_type == 'DO')

    # Execute the scheduled tasks.
    # Note: Blender seems to somehow be caching calls to update_gizmos, so having it as a scheduled task may not affect performance.  Calls to migrate_components are not cached by Blender.
    for task in task_scheduler:
        if task == 'update_gizmos':
            update_gizmos()
        elif task == 'migrate_components':
            migrate_components(MigrationType.LOCAL, do_update_gizmos=False, display_report=display_report,
                               override_report_title="Append/Link: Component Migration Report")
        else:
            print('Error: unrecognized task scheduled')

    # Store things for comparison next time.
    previous_undo_steps_dump = undo_steps_dump
    previous_undo_step_index = undo_step_index


def scene_and_view_layer_update_notifier(self, context):
    """Some scene/view layer actions/changes don't trigger a depsgraph update so watch the top bar for changes to the scene or view layer by hooking into it's draw method.  Known actions that don't trigger a depsgraph update:
    - Creating a new scene.
    - Switching the scene.
    - Creating a new view layer.
    - Switching the view layer - if the last action was also a view layer switch"""
    global previous_window_setups
    wm = context.window_manager
    current_window_setups = [w.scene.name+w.view_layer.name for w in wm.windows]
    if sorted(current_window_setups) != sorted(previous_window_setups):
        bpy.app.timers.register(update_gizmos)
        previous_window_setups = current_window_setups


def register():
    global previous_undo_steps_dump
    global previous_undo_step_index
    global previous_window_setups
    previous_undo_steps_dump = ""
    previous_undo_step_index = 0
    previous_window_setups = []

    if not load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post)

    if not undo_stack_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(undo_stack_handler)

    bpy.types.TOPBAR_HT_upper_bar.append(scene_and_view_layer_update_notifier)


def unregister():
    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    if undo_stack_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(undo_stack_handler)

    bpy.types.TOPBAR_HT_upper_bar.remove(scene_and_view_layer_update_notifier)
