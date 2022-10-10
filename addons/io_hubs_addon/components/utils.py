import bpy
from .components_registry import get_component_by_name
from .gizmos import update_gizmos
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
        component_class.init_addon_version(obj)
        component_class.init(obj)
        for dep_name in component_class.get_deps():
            dep_class = get_component_by_name(dep_name)
            if dep_class:
                dep_exists = obj.hubs_component_list.items.find(dep_name) > -1
                if not dep_exists:
                    add_component(obj, dep_name)
            else:
                print("Dependecy '%s' from module '%s' not registered" %
                      (dep_name, component_name))


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


def dash_to_title(s):
    return s.replace("-", " ").title()


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


# Note: Set up stuff specifically for C FILE pointers so that they aren't truncated to 32 bits on 64 bit systems.
class _FILE(ctypes.Structure):
    """opaque C FILE type"""


if platform.system() == "Windows":
    try:
        # Get stdio from the CRT Blender's using (currently ships with Blender)
        libc = ctypes.windll.LoadLibrary('api-ms-win-crt-stdio-l1-1-0')

        try: # Attempt to set up flushing for the C stdout.
            libc.__acrt_iob_func.restype = ctypes.POINTER(_FILE)
            stdout = libc.__acrt_iob_func(1)

            def c_fflush():
                try:
                    libc.fflush(stdout)
                except:
                    print("Error: Unable to flush the C stdout")

        except: # Fall back to flushing all open output streams.
            print("Warning: Couldn't get the C stdout")
            def c_fflush():
                try:
                    libc.fflush(None)
                except:
                    print("Error: Unable to flush the C stdout")

    except: # Warn and fail gracefully.  Flushing the C stdout is required because Windows switches to full buffering when redirected.
        print("Error: Unable to find the C runtime.")
        def c_fflush():
            print("Error: Unable to flush the C stdout")

else: # Linux/Mac
    try: # get the C runtime
        libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))

        try: # Attempt to set up flushing for the C stdout.
            if platform.system() == "Linux":
                c_stdout = ctypes.POINTER(_FILE).in_dll(libc, 'stdout')
            else: # Mac
                c_stdout = ctypes.POINTER(_FILE).in_dll(libc, '__stdoutp')

            def c_fflush():
                try:
                    libc.fflush(c_stdout)
                except:
                    print("Warning: Unable to flush the C stdout.")

        except: # The C stdout wasn't found.  This is unlikely to happen, but if it does then just skip flushing since Linux/Mac doesn't seem to strictly require a C-level flush to work.
            print("Warning: Couldn't get the C stdout.")
            def c_fflush():
                pass

    except: # The C runtime wasn't found.  This is unlikely to happen, but if it does then just skip flushing since Linux/Mac doesn't seem to strictly require a C-level flush to work.
        print("Warning: Unable to find the C runtime.")
        def c_fflush():
            pass


@contextmanager
def redirect_c_stdout(binary_stream):
    stdout_file_descriptor = sys.stdout.fileno()
    original_stdout_file_descriptor_copy = os.dup(stdout_file_descriptor)
    pipe_read_end, pipe_write_end = os.pipe() # os.pipe returns two file descriptors.

    try:
        # Flush the C-level buffer of stdout before redirecting.  This should make sure that only the desired data is captured.
        c_fflush()
        # Redirect stdout to your pipe.
        os.dup2(pipe_write_end, stdout_file_descriptor)
        yield # wait for input
    finally:
        # Flush the C-level buffer of stdout before returning things to normal.  This seems to be mainly needed on Windows because it looks like Windows changes the buffering policy to be fully buffered when redirecting stdout.
        c_fflush()
        # Redirect stdout back to the original file descriptor.
        os.dup2(original_stdout_file_descriptor_copy, stdout_file_descriptor)
        # Close the write end of the pipe to allow reading.
        os.close(pipe_write_end)
        # Read what was written to the pipe and pass it to the binary stream for use outside this function.
        pipe_reader = os.fdopen(pipe_read_end, 'rb')
        binary_stream.write(pipe_reader.read())
        # Close the reader, also closes the pipe_read_end file descriptor.
        pipe_reader.close()
        # Close the remaining open file descriptor.
        os.close(original_stdout_file_descriptor_copy)

def get_host_components(host):
    for component_item in host.hubs_component_list.items:
        component_name = component_item.name
        component_class = get_component_by_name(component_name)
        if not component_class:
            continue

        component = getattr(host, component_class.get_id())
        yield component
