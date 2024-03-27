import tempfile
import bpy
from .components_registry import get_component_by_name, get_components_registry
from .gizmos import update_gizmos
from .types import PanelType
from mathutils import Vector
from contextlib import contextmanager
import os
import sys
import platform
import ctypes
import ctypes.util

V_S1 = Vector((1.0, 1.0, 1.0))


def add_component(obj, component_name):
    component_item = obj.hubs_component_list.items.add()
    component_item.name = component_name

    component_class = get_component_by_name(component_name)
    if component_class:
        if 'create_gizmo' in component_class.__dict__:
            update_gizmos()
        component_class.init_instance_version(obj)
        for dep_name in component_class.get_deps():
            dep_class = get_component_by_name(dep_name)
            if dep_class:
                dep_exists = obj.hubs_component_list.items.find(dep_name) > -1
                if not dep_exists:
                    add_component(obj, dep_name)
            else:
                print("Dependency '%s' from module '%s' not registered" %
                      (dep_name, component_name))
        component_class.init(obj)


def remove_component(obj, component_name):
    component_items = obj.hubs_component_list.items
    component_items.remove(component_items.find(component_name))
    component_class = get_component_by_name(component_name)

    component_class = get_component_by_name(component_name)
    if component_class:
        del obj[component_class.get_id()]
        if 'create_gizmo' in component_class.__dict__:
            update_gizmos()
        for dep_name in component_class.get_deps():
            dep_class = get_component_by_name(dep_name)
            dep_name = dep_class.get_name()
            if dep_class:
                if not is_dep_required(obj, component_name, dep_name):
                    remove_component(obj, dep_name)
            else:
                print("Dependecy '%s' from module '%s' not registered" %
                      (dep_name, component_name))


def get_objects_with_component(component_name):
    return [ob for ob in bpy.context.view_layer.objects if has_component(ob, component_name)]


def has_component(obj, component_name):
    component_items = obj.hubs_component_list.items
    return component_name in component_items


def has_components(obj, component_names):
    component_items = obj.hubs_component_list.items
    for name in component_names:
        if name not in component_items:
            return False
    return True


def is_dep_required(obj, component_name, dep_name):
    '''Checks if there is any other component that requires this dependency'''
    is_required = False
    items = obj.hubs_component_list.items
    for cmp in items:
        if cmp.name != component_name:
            dep_component_class = get_component_by_name(
                cmp.name)
            if dep_name in dep_component_class.get_deps():
                is_required = True
                break
    return is_required


def get_object_source(context, panel_type):
    if panel_type == "material":
        return context.material
    elif panel_type == "bone":
        return context.bone or context.edit_bone
    elif panel_type == "scene":
        return context.scene
    else:
        return context.object


def children_recurse(ob, result):
    for child in ob.children:
        result.append(child)
        children_recurse(child, result)


def children_recursive(ob):
    if bpy.app.version < (3, 1, 0):
        ret = []
        children_recurse(ob, ret)
        return ret
    else:
        return ob.children_recursive


def is_gpu_available(context):
    cycles_addon = context.preferences.addons["cycles"]
    return cycles_addon and cycles_addon.preferences.has_active_device()


def redraw_component_ui(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()


def is_linked(datablock):
    if not datablock:
        return False
    return bool(datablock.id_data.library or datablock.id_data.override_library)


def update_image_editors(old_img, img):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                if area.spaces.active.image == old_img:
                    area.spaces.active.image = img

# Note: Set up stuff specifically for C FILE pointers so that they aren't truncated to 32 bits on 64 bit systems.


class _FILE(ctypes.Structure):
    """opaque C FILE type"""


if platform.system() == "Windows":
    try:
        # Get stdio from the CRT Blender's using (currently ships with Blender)
        libc = ctypes.windll.LoadLibrary('api-ms-win-crt-stdio-l1-1-0')

        try:  # Attempt to set up flushing for the C stdout.
            libc.__acrt_iob_func.restype = ctypes.POINTER(_FILE)
            stdout = libc.__acrt_iob_func(1)

            def c_fflush():
                try:
                    libc.fflush(stdout)
                except BaseException as e:
                    print("Error: Unable to flush the C stdout")

        except BaseException as e:  # Fall back to flushing all open output streams.
            print("Warning: Couldn't get the C stdout")

            def c_fflush():
                try:
                    libc.fflush(None)
                except BaseException as e:
                    print("Error: Unable to flush the C stdout")

    # Warn and fail gracefully.  Flushing the C stdout is required because Windows switches to full buffering when redirected.
    except BaseException as e:
        print("Error: Unable to find the C runtime.")

        def c_fflush():
            print("Error: Unable to flush the C stdout")


else:  # Linux/Mac
    try:  # get the C runtime
        libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))

        try:  # Attempt to set up flushing for the C stdout.
            if platform.system() == "Linux":
                c_stdout = ctypes.POINTER(_FILE).in_dll(libc, 'stdout')
            else:  # Mac
                c_stdout = ctypes.POINTER(_FILE).in_dll(libc, '__stdoutp')

            def c_fflush():
                try:
                    libc.fflush(c_stdout)
                except BaseException as e:
                    print("Warning: Unable to flush the C stdout.")

        # The C stdout wasn't found.  This is unlikely to happen, but if it does then just skip flushing since Linux/Mac doesn't seem to strictly require a C-level flush to work.
        except BaseException as e:
            print("Warning: Couldn't get the C stdout.")

            def c_fflush():
                pass

    # The C runtime wasn't found.  This is unlikely to happen, but if it does then just skip flushing since Linux/Mac doesn't seem to strictly require a C-level flush to work.
    except BaseException as e:
        print("Warning: Unable to find the C runtime.")

        def c_fflush():
            pass


@contextmanager
def redirect_c_stdout(binary_stream):
    #this causes an error on windows when the addon is enabled using:  bpy.ops.preferences.addon_enable(module="io_hubs_addon")
    stdout_file_descriptor = sys.stdout.fileno()
    original_stdout_file_descriptor_copy = os.dup(stdout_file_descriptor)
    try:
        # Flush the C-level buffer of stdout before redirecting.  This should make sure that only the desired data is captured.
        c_fflush()
        #  Move the file pointer to the start of the file
        __stack_tmp_file.seek(0)
        # Redirect stdout to your pipe.
        os.dup2(__stack_tmp_file.fileno(), stdout_file_descriptor)
        yield  # wait for input
    finally:
        # Flush the C-level buffer of stdout before returning things to normal.  This seems to be mainly needed on Windows because it looks like Windows changes the buffering policy to be fully buffered when redirecting stdout.
        c_fflush()
        # Redirect stdout back to the original file descriptor.
        os.dup2(original_stdout_file_descriptor_copy, stdout_file_descriptor)
        # Truncate file to the written amount of bytes
        __stack_tmp_file.truncate()
        #  Move the file pointer to the start of the file
        __stack_tmp_file.seek(0)
        # Write back to the input stream
        binary_stream.write(__stack_tmp_file.read())
        # Close the remaining open file descriptor.
        os.close(original_stdout_file_descriptor_copy)


def get_host_components(host):
    # Note: this used to be a generator but we detected some issues in Mac so we reverted to returning an array.
    components = []
    for component_item in host.hubs_component_list.items:
        component_name = component_item.name
        component_class = get_component_by_name(component_name)
        if not component_class:
            continue

        component = getattr(host, component_class.get_id())
        components.append(component)
    return components


def wrap_text(text, max_length=70):
    '''Wraps text in a string so that the total characters in a single line doesn't exceed the specified maximum length.  Lines are broken by word, and the increased width of capital letters is accounted for so that the displayed line length is roughly the same regardless of case.  The maximum length is based on lowercase characters.'''
    wrapped_lines = []

    for section in text.split('\n'):
        text_line = ''
        line_length = 0
        words = section.split(' ')

        for word in words:
            word_length = 0
            for char in word:
                word_length += 1
                if char.isupper():
                    word_length += 0.25

            if line_length + word_length < max_length:
                text_line += word + ' '
                line_length += word_length + 1

            else:
                wrapped_lines.append(text_line.rstrip())
                text_line = word + ' '
                line_length = word_length + 1

        if text_line.rstrip():
            wrapped_lines.append(text_line.rstrip())

    return wrapped_lines


def display_wrapped_text(layout, wrapped_text, *, heading_icon='NONE'):
    if not wrapped_text:
        return

    padding_icon = 'NONE' if heading_icon == 'NONE' else 'BLANK1'
    text_column = layout.column()
    text_column.scale_y = 0.7
    for i, line in enumerate(wrapped_text):
        if i == 0:
            text_column.label(text=line, icon=heading_icon)
        else:
            text_column.label(text=line, icon=padding_icon)


def get_host_reference_message(panel_type, host, ob=None):
    '''The ob argument is used for bone hosts and is the armature object, but will fall back to the armature if the armature object isn't available.'''
    if panel_type == PanelType.BONE:
        ob_type = "armature" if type(ob) == bpy.types.Armature else "object"
        host_reference = f"\"{host.name}\" in {ob_type} \"{ob.name_full}\""
    else:
        host_reference = f"\"{host.name_full}\""

    return host_reference


__stack_tmp_file = None


def register():
    global __stack_tmp_file
    __stack_tmp_file = tempfile.NamedTemporaryFile(
        mode='w+b', buffering=0, delete=False, dir=bpy.app.tempdir)


def unregister():
    __stack_tmp_file.close()
    os.unlink(__stack_tmp_file.name)
