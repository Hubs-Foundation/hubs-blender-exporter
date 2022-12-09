# Blender utility script to export a mesh in the Gizmo format.
# Usage:
# Run Blender from the terminal.
# Create a new script file, copy this script in the new file and run.

import bpy

from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator


def convert(objects):
    '''Prints the model vertices in gizmo format and world space'''
    out = 'SHAPE = ('
    for ob in objects:
        if ob.type == 'MESH':
            mesh = ob.data
            mat = ob.matrix_world
            mesh.calc_loop_triangles()
            for tri in mesh.loop_triangles:
                for i in range(3):
                    v_index = tri.vertices[i]
                    v = mat @ mesh.vertices[v_index].co
                    out += '(%f, %f, %f),' % (v.x, v.y, v.z)
    out += ')'
    return out


class SaveGizmoOperator(Operator, ImportHelper):

    bl_idname = "hubs.save_gizmo"
    bl_label = "Save Gizmo"

    filter_glob: StringProperty(
        default='*.py;',
        options={'HIDDEN'}
    )

    def execute(self, context):
        """Save gizmo outout to a file."""
        gizmo = convert(context.selected_objects)

        f = open(self.filepath, "w")
        f.write(gizmo)
        f.close()

        return {'FINISHED'}


def register():
    bpy.utils.register_class(SaveGizmoOperator)


def unregister():
    bpy.utils.unregister_class(SaveGizmoOperator)


if __name__ == "__main__":
    register()
    bpy.ops.hubs.save_gizmo('INVOKE_DEFAULT')
