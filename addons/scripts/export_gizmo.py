# Blender utility script to export a mesh in the Gizmo format.
# Usage:
# Run Blender from the terminal.
# Create a new script file, copy this script in the new file and run.
# Copy the cosole output and paste it in a new file in the components/models folder.

import bpy


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
                    for i in range(3):
                        out += '(%f, %f, %f),' % (v.x, v.y, v.z)
    out += ')'
    return out


if __name__ == "__main__":
    gizmo = convert(bpy.context.selected_objects)
    print(gizmo)
