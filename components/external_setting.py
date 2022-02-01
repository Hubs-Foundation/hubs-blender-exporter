import bpy


class RENDER_PT_hba_external_setting(bpy.types.Panel):
    bl_idname = "OBJECT_PT_External_Setting"
    bl_label = "External"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hubs'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='External Setting')
        row = layout.row()


def register():
    print('Register External Setting')
    bpy.utils.register_class(RENDER_PT_hba_external_setting)


def unregister():
    print('Unregister External Setting')
    bpy.utils.unregister_class(RENDER_PT_hba_external_setting)


if __name__ == "__main__":
    register()
