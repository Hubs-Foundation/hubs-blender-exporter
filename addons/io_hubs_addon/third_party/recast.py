# ***** BEGIN GPL LICENSE BLOCK *****
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
# ***** END GPL LICENCE BLOCK *****

import os
import traceback
import bpy

from bpy.props import IntProperty, FloatProperty, EnumProperty, PointerProperty, FloatVectorProperty, BoolProperty
from bpy.types import Panel, PropertyGroup
from mathutils import Matrix, Vector
from math import radians
from ..preferences import get_addon_pref
from ..components.utils import add_component, get_objects_with_component, has_component

import ctypes
import ctypes.util
from ctypes import c_int, c_float

import bmesh


CELL_SIZE_DEFAULT = 0.166
CELL_HEIGHT_DEFAULT = 0.10
SLOPE_MAX_DEFAULT = radians(45)
CLIMB_MAX_DEFAULT = 0.3
AGENT_HEIGHT_DEFAULT = 1.70
AGENT_RADIUS_DEFAULT = 0.5
EDGE_MAX_LENGTH = 12.0
EDGE_MAX_ERROR = 1.0
REGION_MIN_SIZE = 4.0
REGION_MERGE_SIZE = 20.0
VERTS_PER_POLY_DEFAULT = 3
SAMPLE_DIST_DEFAULT = 13.0
SAMPLE_MAX_ERROR_DEFAULT = 1.0
PARTITIONING_DEFAULT = 'WATERSHED'
COLOR_DEFAULT = (0.0, 1.0, 0.0, 1.0)
AUTO_CELL_DEFAULT = True

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

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = obj  # set as the active object in the scene
    obj.select_set(True)  # select object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

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


def get_auto_cell_size(context):
    bounding_boxes = []
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            bbox = [obj.matrix_world @ Vector(point) for point in obj.bound_box]
            bounding_boxes.extend(bbox)

    bound_box_x_coords = []
    bound_box_y_coords = []
    for point in bounding_boxes:
        bound_box_x_coords.append(point.x)
        bound_box_y_coords.append(point.y)

    size_x = abs(min(bound_box_x_coords) - max(bound_box_x_coords))
    size_y = abs(min(bound_box_y_coords) - max(bound_box_y_coords))
    area = size_x * size_y

    return pow(area, 1 / 3) / 50


class RecastNavMeshResetOperator(bpy.types.Operator):
    bl_idname = "recast.reset_navigation_mesh"
    bl_label = "Reset"
    bl_description = "Reset navigation mesh properties to default."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        scene.recast_navmesh.cell_size = CELL_SIZE_DEFAULT
        scene.recast_navmesh.cell_height = CELL_HEIGHT_DEFAULT
        scene.recast_navmesh.slope_max = SLOPE_MAX_DEFAULT
        scene.recast_navmesh.climb_max = CLIMB_MAX_DEFAULT
        scene.recast_navmesh.agent_height = AGENT_HEIGHT_DEFAULT
        scene.recast_navmesh.agent_radius = AGENT_RADIUS_DEFAULT
        scene.recast_navmesh.edge_max_len = EDGE_MAX_LENGTH
        scene.recast_navmesh.edge_max_error = EDGE_MAX_ERROR
        scene.recast_navmesh.region_min_size = REGION_MIN_SIZE
        scene.recast_navmesh.region_merge_size = REGION_MERGE_SIZE
        scene.recast_navmesh.verts_per_poly = VERTS_PER_POLY_DEFAULT
        scene.recast_navmesh.sample_dist = SAMPLE_DIST_DEFAULT
        scene.recast_navmesh.sample_max_error = SAMPLE_MAX_ERROR_DEFAULT
        scene.recast_navmesh.partitioning = PARTITIONING_DEFAULT
        scene.recast_navmesh.color = COLOR_DEFAULT
        scene.recast_navmesh.auto_cell = AUTO_CELL_DEFAULT

        return {'FINISHED'}


class RecastNavMeshGenerateOperator(bpy.types.Operator):
    bl_idname = "recast.build_navigation_mesh"
    bl_label = "Build Navigation Mesh"
    bl_description = "Build navigation mesh from the selected objects using recast."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # bpy.ops.wm.call_menu(name="ADDITIVE_ANIMATION_insert_keyframe_menu")

        active_object = context.active_object
        selected_objects = context.selected_objects
        if len([obj for obj in selected_objects if obj.type == 'MESH']) == 0:
            self.report({'WARNING'}, 'No meshes selected')
            return {"CANCELLED"}

        from ..components.definitions.nav_mesh import NavMesh
        nav_mesh_id = NavMesh.get_name()
        for ob in context.selected_objects:
            if has_component(ob, nav_mesh_id):
                self.report({'ERROR'}, 'A Navmesh cannot be part of the selection')
                return {'CANCELLED'}

        navMesh = None
        navMeshes = get_objects_with_component(nav_mesh_id)
        if navMeshes:
            navMesh = navMeshes[0]

        addon_prefs = get_addon_pref(context)
        libpath = os.path.abspath(addon_prefs.recast_lib_path)
        libpathr = libpath.replace("\\", "/")
        if not os.path.exists(libpathr):
            self.report({'ERROR'}, 'File not exists: %s\n' % libpathr)
            return {'CANCELLED'}

        verts, tris = extractTriangulatedInputMesh(context)
        vertsCount = len(verts)
        trisCount = len(tris)
        nverts = (int)(len(verts) / 3)
        ntris = (int)(len(tris) / 3)
        recastData = recastDataFromBlender(context.scene)
        if context.scene.recast_navmesh.auto_cell:
            recastData.cellsize = get_auto_cell_size(context)

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

        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            obj.select_set(True)
        context.view_layer.objects.active = active_object

        return {'FINISHED'}


class RecastNavMeshPropertyGroup(PropertyGroup):
    # based on https://docs.blender.org/api/2.79/bpy.types.SceneGameRecastData.html
    cell_size: FloatProperty(
        name="cell_size",
        description="Cell size",
        default=CELL_SIZE_DEFAULT,
        min=0.0,
        max=30.0,
        subtype='DISTANCE')

    cell_height: FloatProperty(
        name="cell_height",
        description="Cell height",
        default=CELL_HEIGHT_DEFAULT,
        min=0.0,
        max=30.0,
        subtype='DISTANCE')

    agent_height: FloatProperty(
        name="agent_height",
        description="Agent height",
        default=AGENT_HEIGHT_DEFAULT,
        min=0.0,
        max=30.0,
        subtype='DISTANCE')

    agent_radius: FloatProperty(
        name="agent_radius",
        description="Agent radius",
        default=AGENT_RADIUS_DEFAULT,
        min=0.0,
        max=30.0,
        subtype='DISTANCE')

    slope_max: FloatProperty(
        name="slope_max",
        description="Maximum slope",
        default=SLOPE_MAX_DEFAULT,
        min=0.0,
        max=radians(90),
        subtype='ANGLE')

    climb_max: FloatProperty(
        name="climb_max",
        description="Maximum step height",
        default=CLIMB_MAX_DEFAULT,
        min=0.0,
        max=30.0,
        subtype='DISTANCE')

    region_min_size: FloatProperty(
        name="region_min_size",
        description="Minimum region size",
        default=REGION_MIN_SIZE,
        min=0.0,
        max=30.0,
        unit='AREA')

    region_merge_size: FloatProperty(
        name="region_merge_size",
        description="Merged region size",
        default=REGION_MERGE_SIZE,
        min=0.0,
        max=30.0,
        unit='AREA')

    edge_max_error: FloatProperty(
        name="edge_max_error",
        description="Max edge error",
        default=EDGE_MAX_ERROR,
        min=0.0,
        max=30.0,
        subtype='DISTANCE')

    edge_max_len: FloatProperty(
        name="edge_max_len",
        description="Max edge length",
        default=EDGE_MAX_LENGTH,
        min=0.0,
        max=30.0,
        subtype='DISTANCE')

    verts_per_poly: IntProperty(
        name="verts_per_poly",
        description="Verts per poly",
        default=VERTS_PER_POLY_DEFAULT,
        min=3,
        max=10
    )

    sample_dist: FloatProperty(
        name="sample_dist",
        description="Sample distance",
        default=SAMPLE_DIST_DEFAULT,
        min=0.0,
        max=30.0,
        subtype='DISTANCE')

    sample_max_error: FloatProperty(
        name="sample_max_error",
        description="Max sample error",
        default=SAMPLE_MAX_ERROR_DEFAULT,
        min=0.0,
        max=30.0,
        subtype='DISTANCE')

    partitioning: EnumProperty(
        name="partitioning",
        items=[("WATERSHED", "WATERSHED", "WATERSHED"),
               ("MONOTONE", "MONOTONE", "MONOTONE"),
               ("LAYERS", "LAYERS", "LAYERS")],
        default=PARTITIONING_DEFAULT)

    color: FloatVectorProperty(name="Color",
                               description="Color",
                               subtype='COLOR_GAMMA',
                               default=COLOR_DEFAULT,
                               size=4,
                               min=0,
                               max=1)
    expanded: BoolProperty(name="expanded", default=True)

    auto_cell: BoolProperty(name="Auto cell size", default=AUTO_CELL_DEFAULT)


class RecastAdvancedNavMeshPanel(bpy.types.Panel):
    bl_idname = "SCENE_PT_blendcast_adv"
    bl_parent_id = "SCENE_PT_blendcast"
    bl_label = "Advanced Settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        recastPropertyGroup = context.scene.recast_navmesh

        box = layout.box()
        if recastPropertyGroup.expanded:
            col = box.column()
            col.row().label(text="Region:")
            col.row().prop(recastPropertyGroup, "region_merge_size", text="Merged region size")
            col.row().prop(recastPropertyGroup, "partitioning", text="Partitioning")

            col.row().label(text="Polygonization:")
            col.row().prop(recastPropertyGroup, "edge_max_len", text="Max edge length")
            col.row().prop(recastPropertyGroup, "edge_max_error", text="Max edge error")
            col.row().prop(recastPropertyGroup, "verts_per_poly", text="Verts per poly")

            col.row().label(text="Detail mesh:")
            col.row().prop(recastPropertyGroup, "sample_dist", text="Sample distance")
            col.row().prop(recastPropertyGroup, "sample_max_error", text="Max sample error")


class RecastNavMeshPanel(Panel):
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
        layout.operator("recast.reset_navigation_mesh")
        layout.prop(recastPropertyGroup, "color", text="Color")

        layout.label(text="Rasterization:")
        col = layout.column()
        col.row().prop(recastPropertyGroup, "auto_cell", text="Auto Cell")
        if not recastPropertyGroup.auto_cell:
            col.row().prop(recastPropertyGroup, "cell_size", text="Cell size")
        col.row().prop(recastPropertyGroup, "cell_height", text="Cell height")

        layout.label(text="Agent:")
        col = layout.column()
        col.row().prop(recastPropertyGroup, "agent_height", text="Height")
        col.row().prop(recastPropertyGroup, "agent_radius", text="Radius")
        col.row().prop(recastPropertyGroup, "climb_max", text="Maximum step height")
        col.row().prop(recastPropertyGroup, "slope_max", text="Maximum slope")

        layout.label(text="Region:")
        col = layout.column()
        col.row().prop(recastPropertyGroup, "region_min_size", text="Min region size")


classes = [
    RecastNavMeshPropertyGroup,
    RecastNavMeshPanel,
    RecastAdvancedNavMeshPanel,
    RecastNavMeshGenerateOperator,
    RecastNavMeshResetOperator
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.recast_navmesh = PointerProperty(type=RecastNavMeshPropertyGroup)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.recast_navmesh


if __name__ == "__main__":
    register()
