from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..gizmos import CustomModelGizmo
from ..models import scene_preview_camera
from mathutils import Matrix
from math import radians
from bpy.types import Operator
from bpy.props import FloatProperty
import bpy
from ...utils import rgetattr, rsetattr

def render_post(scene, depsgraph):
    bpy.context.scene.collection.objects.unlink(camera_object)
    bpy.data.cameras.remove(camera_data)

    for prop in saved_props:
        rsetattr(bpy.context, prop, saved_props[prop])

    bpy.app.handlers.render_cancel.remove(render_post)
    bpy.app.handlers.render_complete.remove(render_post)

class RenderOperator(Operator):
    bl_idname = "render.hubs_render"
    bl_label = "Hubs Render"
    bl_options = { "REGISTER" }

    fov: FloatProperty(name="FOV", min=0, max=radians(180), default=radians(80), subtype="ANGLE", unit="ROTATION")

    def execute(self, context):
        bpy.app.handlers.render_complete.append(render_post)
        bpy.app.handlers.render_cancel.append(render_post)

        global camera_data
        camera_data = bpy.data.cameras.new(name="Temp Hubs Camera Data")
        camera_data.type = "PERSP"
        camera_data.clip_start = 0.1
        camera_data.clip_end = 2000
        camera_data.lens_unit = "FOV"
        camera_data.angle = self.fov

        global camera_object
        camera_object = bpy.data.objects.new("Temp hubs Camera Object", camera_data)
        context.scene.collection.objects.link(camera_object)
        camera_object.matrix_world = context.active_object.matrix_world.copy()
        rot_offset = Matrix.Rotation(radians(90), 4, 'X')
        camera_object.matrix_world = camera_object.matrix_world @ rot_offset

        overrides = [
            ("preferences.view.render_display_type", "NONE"),
            ("scene.camera", camera_object),
            ("scene.render.resolution_x", 1920),
            ("scene.render.resolution_y", 1080),
            ("scene.render.resolution_percentage", 100),
            ("scene.render.image_settings.file_format", "PNG"),
            ("scene.render.filepath", f"{context.scene.render.filepath}/scene-preview-camera.png"),
        ]

        global saved_props
        saved_props = {}
        for (prop, value) in overrides:
            if prop not in saved_props:
                saved_props[prop] = rgetattr(bpy.context, prop)
            rsetattr(bpy.context, prop, value)

        bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)

        return {'FINISHED'}

class ScenePreviewCamera(HubsComponent):
    _definition = {
        'name': 'scene-preview-camera',
        'display_name': 'Scene Preview Camera',
        'category': Category.SCENE,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'CAMERA_DATA',
        'version': (1, 0, 0)
    }

    fov: FloatProperty(name="FOV", min=0, max=radians(180), default=radians(80), subtype="ANGLE", unit="ROTATION")

    def pre_export(self, export_settings, host, ob=None):
        global backup_name
        backup_name = host.name
        host.name = 'scene-preview-camera'

    def post_export(self, export_settings, host, ob=None):
        global backup_name
        host.name = backup_name
        backup_name = ""

    @classmethod
    def update_gizmo(cls, ob, bone, target, gizmo):
        mat = ob.matrix_world.copy()
        
        rot_offset = Matrix.Rotation(radians(180), 4, 'Z')
        gizmo.hide = not ob.visible_get()
        gizmo.matrix_basis = mat @ rot_offset

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        gizmo = gizmo_group.gizmos.new(CustomModelGizmo.bl_idname)
        gizmo.object = ob
        setattr(gizmo, "hubs_gizmo_shape", scene_preview_camera.SHAPE)
        gizmo.setup()
        gizmo.use_draw_scale = False
        gizmo.use_draw_modal = False
        gizmo.alpha = 0.5
        gizmo.scale_basis = 1.0
        gizmo.hide_select = True
        gizmo.color_highlight = (0.8, 0.8, 0.8)
        gizmo.alpha_highlight = 1.0

        return gizmo
    
    def draw(self, context, layout, panel):
        row = layout.row()
        row.prop(data=self, property="fov")
        row = layout.row()
        op = row.operator("render.hubs_render", text="Render Preview Camera")
        op.fov = self.fov
    
    @ staticmethod
    def register():
        bpy.utils.register_class(RenderOperator)

    @ staticmethod
    def unregister():
        bpy.utils.unregister_class(RenderOperator)