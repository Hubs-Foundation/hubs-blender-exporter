#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

import os
import traceback
import bpy

import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty, PointerProperty, FloatVectorProperty
from bpy.types import Panel, PropertyGroup
from mathutils import Matrix, Vector
from ..preferences import get_addon_pref
from ..components.utils import add_component, get_objects_with_component, has_component

import ctypes
import ctypes.util
from ctypes import c_int, c_float

import bmesh


# x -> x'
# y -> -z'
# z -> y'

def swap(vec):
    return Vector([vec.x, vec.z, -vec.y])


def reswap(vec):
    return Vector([vec.x, -vec.z, vec.y])


class RecastData(ctypes.Structure):
    _fields_ = [("cellsize", c_float),
                ("cellheight", c_float),
                ("agentmaxslope", c_float),
                ("agentmaxclimb", c_float),
                ("agentheight", c_float),
                ("agentradius", c_float),
                ("edgemaxlen", c_float),
                ("edgemaxerror", c_float),
                ("regionminsize", c_float),
                ("regionmergesize", c_float),
                ("vertsperpoly", c_int),
                ("detailsampledist", c_float),
                ("detailsamplemaxerror", c_float),
                ("partitioning", ctypes.c_short),
                ("pad1", ctypes.c_short)]


class recast_polyMesh(ctypes.Structure):
    _fields_ = [("verts", ctypes.POINTER(ctypes.c_ushort)),  # The mesh vertices. [Form: (x, y, z) * #nverts]
                ("polys", ctypes.POINTER(ctypes.c_ushort)),  # Polygon and neighbor data. [Length: #maxpolys * 2 * #nvp]
                # The region id assigned to each polygon. [Length: #maxpolys]
                ("regs", ctypes.POINTER(ctypes.c_ushort)),
                # The user defined flags for each polygon. [Length: #maxpolys]
                ("flags", ctypes.POINTER(ctypes.c_ushort)),
                ("areas", ctypes.POINTER(ctypes.c_ubyte)),  # The area id assigned to each polygon. [Length: #maxpolys]
                ("nverts", c_int),                          # The number of vertices.
                ("npolys", c_int),                          # The number of polygons.
                ("maxpolys", c_int),                        # The number of allocated polygons.
                ("nvp", c_int),                             # The maximum number of vertices per polygon.
                ("bmin", c_float * 3),                        # The minimum bounds in world space. [(x, y, z)]
                ("bmax", c_float * 3),                        # The maximum bounds in world space. [(x, y, z)]
                ("cs", c_float),                            # The size of each cell. (On the xz-plane.)
                ("ch", c_float),                            # The height of each cell. (The minimum increment along the y-axis.)
                # The AABB border size used to generate the source data from which the mesh was derived.
                ("borderSize", c_int),
                ("maxEdgeError", c_float)]                 # The max error of the polygon edges in the mesh.


class recast_polyMeshDetail(ctypes.Structure):
    _fields_ = [("meshes", ctypes.POINTER(ctypes.c_uint)),  # The sub-mesh data. [Size: 4*#nmeshes]
                ("verts", ctypes.POINTER(ctypes.c_float)),  # The mesh vertices. [Size: 3*#nverts]
                ("tris", ctypes.POINTER(ctypes.c_ubyte)),  # The mesh triangles. [Size: 4*#ntris]
                ("nmeshes", c_int),                        # The number of sub-meshes defined by #meshes.
                ("nverts", c_int),                         # The number of vertices in #verts.
                ("ntris", c_int)]                         # The number of triangles in #tris.


class recast_polyMesh_holder(ctypes.Structure):
    _fields_ = [("pmesh", ctypes.POINTER(recast_polyMesh))]


class recast_polyMeshDetail_holder(ctypes.Structure):
    _fields_ = [("dmesh", ctypes.POINTER(recast_polyMeshDetail))]


def recastDataFromBlender(scene):
    recastData = RecastData()
    recastData.cellsize = scene.recast_navmesh.cell_size
    recastData.cellheight = scene.recast_navmesh.cell_height
    recastData.agentmaxslope = scene.recast_navmesh.slope_max
    recastData.agentmaxclimb = scene.recast_navmesh.climb_max
    recastData.agentheight = scene.recast_navmesh.agent_height
    recastData.agentradius = scene.recast_navmesh.agent_radius
    recastData.edgemaxlen = scene.recast_navmesh.edge_max_len
    recastData.edgemaxerror = scene.recast_navmesh.edge_max_error
    recastData.regionminsize = scene.recast_navmesh.region_min_size
    recastData.regionmergesize = scene.recast_navmesh.region_merge_size
    recastData.vertsperpoly = scene.recast_navmesh.verts_per_poly
    recastData.detailsampledist = scene.recast_navmesh.sample_dist
    recastData.detailsamplemaxerror = scene.recast_navmesh.sample_max_error
    recastData.partitioning = 0
    if scene.recast_navmesh.partitioning == "WATERSHED":
        recastData.partitioning = 0
    if scene.recast_navmesh.partitioning == "MONOTONE":
        recastData.partitioning = 1
    if scene.recast_navmesh.partitioning == "LAYERS":
        recastData.partitioning = 2
    recastData.pad1 = 0
    return recastData


def object_has_collection(ob, groupName):
    for group in ob.users_collection:
        if group.name == groupName:
            return True
    return False


def objects_from_collection(allObjects, collectionName):
    objects = []
    for ob in allObjects:
        if object_has_collection(ob, collectionName):
            objects.append(ob)
    return objects

# take care of applying modiffiers and triangulation


def extractTriangulatedInputMeshList(objects, matrix, verts_offset, verts, tris, depsgraph):
    for ob in objects:
        if ob.instance_type == 'COLLECTION':
            subobjects = objects_from_collection(bpy.data.objects, ob.name)
            parent_matrix = matrix @ ob.matrix_world
            verts_offset = extractTriangulatedInputMeshList(
                subobjects, parent_matrix, verts_offset, verts, tris, depsgraph)

        if ob.type != 'MESH':
            continue

        bm = bmesh.new()
        bm.from_object(ob, depsgraph)
        real_matrix_world = matrix @ ob.matrix_world
        bmesh.ops.transform(bm, matrix=real_matrix_world, verts=bm.verts)

        tm = bmesh.ops.triangulate(bm, faces=bm.faces[:])
        # tm['faces']   # but it seems that it modify bmesh anyway

        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        for v in bm.verts:
            vp = swap(v.co)  # swap from blender coordinates to recast coordinates
            verts.append(vp.x)
            verts.append(vp.y)
            verts.append(vp.z)

        for f in bm.faces:
            for i in f.verts:  # After triangulation it will always be 3 vertexes
                tris.append(i.index + verts_offset)

        verts_offset += len(bm.verts)
        bm.free()
    return verts_offset

# take care of applying modiffiers and triangulation


def extractTriangulatedInputMesh(context):
    depsgraph = context.evaluated_depsgraph_get()
    verts = []
    tris = []
    list = context.selected_objects
    extractTriangulatedInputMeshList(list, Matrix(), 0, verts, tris, depsgraph)
    return (verts, tris)


def createMesh(context, dmesh_holder, obj=None):
    scene = context.scene
    if not obj:
        mesh = bpy.data.meshes.new("navmesh")  # add a new mesh
        obj = bpy.data.objects.new("navmesh", mesh)  # add a new object using the mesh
        scene.collection.objects.link(obj)
        from ..components.definitions.nav_mesh import NavMesh
        add_component(obj, NavMesh.get_name())
    else:
        mesh = obj.data

    orig_selection = context.selected_objects

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = obj  # set as the active object in the scene
    obj.select_set(True)  # select object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in orig_selection:
        obj.select_set(True) 

    bm = bmesh.new()
    nverts = (int)(dmesh_holder.dmesh.contents.nverts)
    for i in range(nverts):
        x = dmesh_holder.dmesh.contents.verts[i * 3 + 0]
        y = dmesh_holder.dmesh.contents.verts[i * 3 + 1]
        z = dmesh_holder.dmesh.contents.verts[i * 3 + 2]
        v = reswap(Vector([x, y, z]))
        bm.verts.new(v)  # add a new vert
    bm.verts.ensure_lookup_table()

    nmeshes = (int)(dmesh_holder.dmesh.contents.nmeshes)
    for j in range(nmeshes):
        baseVerts = dmesh_holder.dmesh.contents.meshes[j * 4 + 0]
        meshNVerts = dmesh_holder.dmesh.contents.meshes[j * 4 + 1]
        baseTri = dmesh_holder.dmesh.contents.meshes[j * 4 + 2]
        meshNTris = dmesh_holder.dmesh.contents.meshes[j * 4 + 3]
        meshVertsList = []
        # if len(meshVertsList) >= 3:
        #    bm.faces.new(meshVertsList)

        for i in range(meshNTris):
            i1 = dmesh_holder.dmesh.contents.tris[(baseTri + i) * 4 + 0] + baseVerts
            i2 = dmesh_holder.dmesh.contents.tris[(baseTri + i) * 4 + 1] + baseVerts
            i3 = dmesh_holder.dmesh.contents.tris[(baseTri + i) * 4 + 2] + baseVerts
            flags = dmesh_holder.dmesh.contents.tris[(baseTri + i) * 4 + 3]
            # print("face = (%i, %i, %i)" % (i1, i2, i3))
            bm.faces.new((bm.verts[i1], bm.verts[i2], bm.verts[i3]))  # add a new vert

    # Recast: The vertex indices in the triangle array are local to the sub-mesh, not global. To translate into an global index in the vertices array, the values must be offset by the sub-mesh's base vertex index.
    # ntris = (int)(dmesh_holder.dmesh.contents.ntris)
    # for i in range(ntris):
    #    i1 = dmesh_holder.dmesh.contents.tris[i*3+0]
    #    i2 = dmesh_holder.dmesh.contents.tris[i*3+1]
    #    i3 = dmesh_holder.dmesh.contents.tris[i*3+2]
    #    print("face[%i] = (%i, %i, %i)" % (i, i1, i2, i3))
    #    bm.faces.new((bm.verts[i1], bm.verts[i2], bm.verts[i3]))  # add a new vert

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00001)

    # make the bmesh the object's mesh
    bm.to_mesh(mesh)
    bm.free()  # always do this when finished

    # Assign nav mesh color
    mat = bpy.data.materials.get("Navmesh Material")
    if mat is None:
        mat = bpy.data.materials.new(name="Navmesh Material")
        mat.diffuse_color = context.scene.recast_navmesh.color

    if mesh.materials:
        mesh.materials[0] = mat
    else:
        mesh.materials.append(mat)


class ReacastNavmeshGenerateOperator(bpy.types.Operator):
    bl_idname = "recast.build_navigation_mesh"
    bl_label = "Build Navigation Mesh"
    bl_description = "Build navigation mesh using recast."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # bpy.ops.wm.call_menu(name="ADDITIVE_ANIMATION_insert_keyframe_menu")

        from ..components.definitions.nav_mesh import NavMesh
        nav_mesh_id = NavMesh.get_name()
        for ob in context.selected_objects:
            if has_component(ob, nav_mesh_id):
                self.report({'ERROR'}, 'A Navmesh cannot be part of the selection')
                return {'FINISHED'}

        navMesh = None
        navMeshes = get_objects_with_component(nav_mesh_id)
        if navMeshes:
            navMesh = navMeshes[0]

        addon_prefs = get_addon_pref(context)
        libpath = os.path.abspath(addon_prefs.recast_lib_path)
        libpathr = libpath.replace("\\", "/")
        if not os.path.exists(libpathr):
            self.report({'ERROR'}, 'File not exists: %s\n' % libpathr)
            return {'FINISHED'}

        verts, tris = extractTriangulatedInputMesh(context)
        vertsCount = len(verts)
        trisCount = len(tris)
        nverts = (int)(len(verts) / 3)
        ntris = (int)(len(tris) / 3)
        recastData = recastDataFromBlender(context.scene)

        prevWorkingDir = os.getcwd()
        nextWorkingDir = os.path.dirname(libpathr)
        os.chdir(nextWorkingDir)
        try:
            recast = ctypes.CDLL(libpathr)
        except OSError as e:
            tracebackStr = traceback.format_exc()
            self.report(
                {'ERROR'},
                'Failed to load shared library: %s\nPath to shared library: %s\n\nTraceback: %s' %
                (str(e),
                 libpathr, tracebackStr))
            os.chdir(prevWorkingDir)
            return {'FINISHED'}

        os.chdir(prevWorkingDir)
        print("nverts %i" % nverts)
        print("ntris %i" % ntris)
        print("cell size %f" % recastData.cellsize)

        # print("verts: %s" % str(verts))
        # print("tris: %s" % str(tris))

        pmesh = recast_polyMesh_holder()
        dmesh = recast_polyMeshDetail_holder()
        nreportMsg = 128
        reportMsg = ctypes.create_string_buffer(b'\000' * nreportMsg)     # 128 chars mutable text
        recast.buildNavMesh.argtypes = [
            ctypes.POINTER(RecastData),
            c_int, c_float * vertsCount, c_int, c_int * trisCount, ctypes.POINTER(recast_polyMesh_holder),
            ctypes.POINTER(recast_polyMeshDetail_holder),
            ctypes.c_char_p, c_int]
        recast.buildNavMesh.restype = c_int
        recast.freeNavMesh.argtypes = [
            ctypes.POINTER(recast_polyMesh_holder),
            ctypes.POINTER(recast_polyMeshDetail_holder),
            ctypes.c_char_p, c_int]
        recast.freeNavMesh.restype = c_int

        ok = recast.buildNavMesh(recastData, nverts, (c_float * vertsCount)(* verts), ntris,
                                 (c_int * trisCount)(*tris), pmesh, dmesh, reportMsg, nreportMsg)
        print("Report msg: %s" % reportMsg.raw)
        if not ok:
            self.report({'ERROR'}, 'buildNavMesh C++ error: %s' % reportMsg.value)

        if not dmesh.dmesh:
            self.report({'ERROR'}, 'buildNavMesh C++ error: %s' % 'No recast_polyMeshDetail')
        else:
            # print("ABC %i" % pmesh.pmesh.contents.nverts)
            # dmeshv1 = dmesh.dmesh.contents.verts[0]
            # print("dmeshv1 %f" % dmeshv1)

            createMesh(context, dmesh, obj=navMesh)

        # what was allocated in C/C++ should be also deallocated there
        recast.freeNavMesh(pmesh, dmesh, reportMsg, nreportMsg)

        return {'FINISHED'}


class ReacastNavmeshPropertyGroup(PropertyGroup):
    # based on https://docs.blender.org/api/2.79/bpy.types.SceneGameRecastData.html
    cell_size: FloatProperty(
        name="cell_size",
        # description="A float property",
        default=0.166,
        min=0.0,
        max=30.0)

    cell_height: FloatProperty(
        name="cell_height",
        # description="A float property",
        default=0.10,
        min=0.0,
        max=30.0)

    agent_height: FloatProperty(
        name="agent_height",
        # description="A float property",
        default=1.70,
        min=0.0,
        max=30.0)

    agent_radius: FloatProperty(
        name="agent_radius",
        # description="A float property",
        default=0.5,
        min=0.0,
        max=30.0)

    slope_max: FloatProperty(
        name="slope_max",
        # description="A float property",
        default=0.785398,
        min=0.0,
        max=1.5708,
        subtype='ANGLE')

    climb_max: FloatProperty(
        name="climb_max",
        # description="A float property",
        default=0.9,
        min=0.0,
        max=30.0)

    region_min_size: FloatProperty(
        name="region_min_size",
        # description="A float property",
        default=1.0,
        min=0.0,
        max=30.0,
        unit='AREA')

    region_merge_size: FloatProperty(
        name="region_merge_size",
        # description="A float property",
        default=20.0,
        min=0.0,
        max=30.0)

    edge_max_error: FloatProperty(
        name="edge_max_error",
        # description="A float property",
        default=1.0,
        min=0.0,
        max=30.0)

    edge_max_len: FloatProperty(
        name="edge_max_len",
        # description="A float property",
        default=12.0,
        min=0.0,
        max=30.0)

    verts_per_poly: IntProperty(
        name="verts_per_poly",
        # description="A integer property",
        default=3,
        min=3,
        max=10
    )

    sample_dist: FloatProperty(
        name="sample_dist",
        # description="A float property",
        default=13.0,
        min=0.0,
        max=30.0)

    sample_max_error: FloatProperty(
        name="sample_max_error",
        # description="A float property",
        default=1.0,
        min=0.0,
        max=30.0)

    partitioning: EnumProperty(
        name="partitioning",
        items=[("WATERSHED", "WATERSHED", "WATERSHED"),
               ("MONOTONE", "MONOTONE", "MONOTONE"),
               ("LAYERS", "LAYERS", "LAYERS")],
        default="WATERSHED")

    color: FloatVectorProperty(name="Color",
                               description="Color",
                               subtype='COLOR_GAMMA',
                               default=(0.0, 1.0, 0.0, 1.0),
                               size=4,
                               min=0,
                               max=1)


class ReacastNavmeshPanel(Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Recast navmesh"
    bl_idname = "SCENE_PT_blendcast"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        recastPropertyGroup = context.scene.recast_navmesh

        layout.operator("recast.build_navigation_mesh")
        layout.prop(recastPropertyGroup, "color", text="Color")

        layout.label(text="Rasterization:")
        flow = layout.grid_flow()
        col = flow.column()
        col.prop(recastPropertyGroup, "cell_size", text="Cell size")
        col = flow.column()
        col.prop(recastPropertyGroup, "cell_height", text="Cell height")

        layout.label(text="Agent:")
        flow = layout.grid_flow()
        col = flow.column()
        col.prop(recastPropertyGroup, "agent_height", text="Height")
        col.prop(recastPropertyGroup, "agent_radius", text="Radius")
        col = flow.column()
        col.prop(recastPropertyGroup, "slope_max", text="Max slope")
        col.prop(recastPropertyGroup, "climb_max", text="Max climb")

        layout.label(text="Region:")
        flow = layout.grid_flow()
        col = flow.column()
        col.prop(recastPropertyGroup, "region_min_size", text="Min region size")
        col = flow.column()
        col.prop(recastPropertyGroup, "region_merge_size", text="Merged region size")

        layout.prop(recastPropertyGroup, "partitioning", text="Partitioning")

        layout.label(text="Polygonization:")
        flow = layout.grid_flow()
        col = flow.column()
        col.prop(recastPropertyGroup, "edge_max_len", text="Max edge length")
        col.prop(recastPropertyGroup, "edge_max_error", text="Max edge error")
        col = flow.column()
        col.prop(recastPropertyGroup, "verts_per_poly", text="Verts per poly")

        layout.label(text="Detail mesh:")
        flow = layout.grid_flow()
        col = flow.column()
        col.prop(recastPropertyGroup, "sample_dist", text="Sample distance")
        col = flow.column()
        col.prop(recastPropertyGroup, "sample_max_error", text="Max sample error")


classes = [
    ReacastNavmeshPanel,
    ReacastNavmeshGenerateOperator
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_class(ReacastNavmeshPropertyGroup)
    bpy.types.Scene.recast_navmesh = PointerProperty(type=ReacastNavmeshPropertyGroup)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(ReacastNavmeshPropertyGroup)
    del bpy.types.Scene.recast_navmesh


if __name__ == "__main__":
    register()
