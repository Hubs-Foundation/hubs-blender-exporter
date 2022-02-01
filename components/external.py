import bpy

class HubsComplexOperator(bpy.types.Operator):
    bl_idname = "object.hubs_complex_operator"
    bl_label = "Hubs Complex Operator"

    def execute(self, context):
        print("Complex Operator Execute")
        context.scene.HBA_complex_operator_prop = 5.0
        return {'FINISHED'}

classes = [
    HubsComplexOperator
]

def register():
    print('Register Complex Operator')
    bpy.types.Scene.HBA_complex_operator_prop = bpy.props.FloatProperty(name="Complex Operator Property")
    for clas in classes:
        bpy.utils.register_class(clas)

def unregister():
    print('Unregister Complex Operator')
    for clas in classes:
        bpy.utils.unregister_class(clas)

if __name__ == "__main__":
    register()