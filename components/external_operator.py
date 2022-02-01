import bpy


class OBJECT_OT_hba_external_operator(bpy.types.Operator):
    bl_idname = "object.hba_external_operator"
    bl_label = "Hubs External Operator"

    def execute(self, context):
        print("External Operator Execute")
        context.scene.HBA_external_operator_prop = 5.0
        return {'FINISHED'}


def register():
    bpy.types.Scene.HBA_external_operator_prop = bpy.props.FloatProperty(
        name="External Operator Property")
    bpy.utils.register_class(OBJECT_OT_hba_external_operator)


def unregister():
    del bpy.types.Scene.HBA_external_operator_prop
    bpy.utils.unregister_class(OBJECT_OT_hba_external_operator)


if __name__ == "__main__":
    register()
