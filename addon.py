import bpy

class HubsSimpleOperator(bpy.types.Operator):
    bl_idname = "object.hubs_simple_operator"
    bl_label = "Hubs Simple Operator"

    def execute(self, context):
        print("Simple Operator Execute")
        context.scene.HBA_simple_operator_prop = 5.0
        return {'FINISHED'}

classes = [
    HubsSimpleOperator
]

def register():
    print('Register Simple Operator')
    bpy.types.Scene.HBA_simple_operator_prop = bpy.props.FloatProperty(name="Simple Operator Property")
    for clas in classes:
        bpy.utils.register_class(clas)

def unregister():
    print('Unregister Simple Operator')
    for clas in classes:
        bpy.utils.unregister_class(clas)

if __name__ == "__main__":
    register()