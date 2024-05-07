from bpy.props import BoolProperty, FloatProperty, EnumProperty, FloatVectorProperty
from ..hubs_component import HubsComponent
from ..types import NodeType, PanelType, Category
from mathutils import Vector


class PhysicsShape(HubsComponent):
    _definition = {
        'name': 'physics-shape',
        'display_name': 'Physics Shape',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'SCENE_DATA',
        'version': (1, 0, 1)
    }

    type: EnumProperty(
        name="Type", description="Type",
        items=[("box", "Box Collider", "A box-shaped primitive collision shape"),
               ("sphere", "Sphere Collider", "A primitive collision shape which represents a sphere"),
               ("hull", "Convex Hull",
                "A convex hull wrapped around the object's vertices. A good analogy for a convex hull is an elastic membrane or balloon under pressure which is placed around a given set of vertices. When released the membrane will assume the shape of the convex hull"),
               ("mesh", "Mesh Collider",
                "A shape made of the actual vertices of the object. This can be expensive for large meshes")],
        default="hull")

    fit: EnumProperty(
        name="Fit Mode",
        description="Shape fitting mode",
        items=[("all", "Automatic fit all", "Automatically match the shape to fit the object's vertices"),
               ("manual", "Manual", "Use the manually specified dimensions to define the shape, ignoring the object's vertices")],
        default="all")

    halfExtents: FloatVectorProperty(
        name="Half Extents",
        description="Half dimensions of the collider. (Only used when fit is set to \"manual\" and type is set to \"box\")",
        unit='LENGTH',
        subtype="XYZ",
        default=(0.5, 0.5, 0.5))

    minHalfExtent: FloatProperty(
        name="Min Half Extent",
        description="The minimum size to use when automatically generating half extents. (Only used when fit is set to \"all\" and type is set to \"box\")",
        unit="LENGTH",
        default=0.0)

    maxHalfExtent: FloatProperty(
        name="Max Half Extent",
        description="The maximum size to use when automatically generating half extents. (Only used when fit is set to \"all\" and type is set to \"box\")",
        unit="LENGTH",
        default=1000.0)

    sphereRadius: FloatProperty(
        name="Sphere Radius",
        description="Radius of the sphere collider. (Only used when fit is set to \"manual\" and type is set to \"sphere\")",
        unit="LENGTH", default=0.5)

    offset: FloatVectorProperty(
        name="Offset", description="An offset to apply to the collider relative to the object's origin",
        unit='LENGTH',
        subtype="XYZ",
        default=(0.0, 0.0, 0.0))

    includeInvisible: BoolProperty(
        name="Include Invisible",
        description="Include invisible objects when generating a collider. (Only used if \"fit\" is set to \"all\")",
        default=False)

    def draw(self, context, layout, panel):
        layout.prop(self, "type")
        layout.prop(self, "fit")
        if self.fit == "manual":
            if self.type == "box":
                layout.prop(self, "halfExtents")
            elif self.type == "sphere":
                layout.prop(self, "sphereRadius")
        else:
            if self.type == "box":
                layout.prop(self, "minHalfExtent")
                layout.prop(self, "maxHalfExtent")
            layout.prop(self, "includeInvisible")
        layout.prop(self, "offset")

        if self.fit == "manual" and (self.type == "mesh" or self.type == "hull"):
            col = layout.column()
            col.alert = True
            col.label(
                text="'Hull' and 'Mesh' do not support 'manual' fit mode", icon='ERROR')

    def gather(self, export_settings, object):
        props = super().gather(export_settings, object)
        props['offset'] = {
            'x': self.offset.x,
            'y': self.offset.z if export_settings['gltf_yup'] else self.offset.y,
            'z': self.offset.y if export_settings['gltf_yup'] else self.offset.z,
        }
        props['halfExtents'] = {
            'x': self.halfExtents.x,
            'y': self.halfExtents.z if export_settings['gltf_yup'] else self.halfExtents.y,
            'z': self.halfExtents.y if export_settings['gltf_yup'] else self.halfExtents.z,
        }
        return props

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version <= (1, 0, 0):
            migration_occurred = True

            offset = self.offset.copy()
            offset = Vector((offset.x, offset.z, offset.y))
            self.offset = offset

            halfExtents = self.halfExtents.copy()
            halfExtents = Vector((halfExtents.x, halfExtents.z, halfExtents.y))
            self.halfExtents = halfExtents

        return migration_occurred
