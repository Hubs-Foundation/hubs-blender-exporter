import bpy, blf, gpu
from bpy.props import FloatProperty, EnumProperty, FloatVectorProperty, StringProperty
from bpy.types import Gizmo
from math import radians
from mathutils import Matrix, Vector
from ..hubs_component import HubsComponent
from ..types import Category, PanelType, NodeType
from ..gizmos import bone_matrix_world



class TextGizmo(Gizmo):
    """Text gizmo"""
    bl_idname = "GIZMO_GT_hba_text_gizmo"

    anchorX_map = {
        "left": 0,
        "center": -0.5,
        "right":-1
        }

    breaker_map = {
        "normal": " ",
        "break-word": ""
        }

    whitespace_map = {
        "normal": True,
        "nowrap": False
        }

    def __init__(self):
        self.component = None
        self.host = None

    def _update_matrix(self):
        gpu.matrix.push()
        text_size = self.component.fontSize * 0.009
        rot_offset = Matrix.Rotation(radians(90), 4, 'X').to_4x4()
        loc, rot, scale = self.host.matrix_basis.decompose()
        scale = scale * text_size
        print("scale: ", scale)
        mat_out = (Matrix.Translation(loc)
                @ rot.normalized().to_matrix().to_4x4() @ rot_offset
                @ Matrix.Diagonal(scale).to_4x4())
        gpu.matrix.multiply_matrix(mat_out)

    def draw(self, context):
        self._update_matrix()

        text_size = self.component.fontSize * 9

        text = self.component.value
        text_color = self.component.color[:3]
        font_id = 0
        blf.size(font_id, 100, 72)
        anchor = self.anchorX_map[self.component.anchorX]
        line = []
        line_count = 0
        line_count_modifier = (self.component.lineHeight * 100) * -1
        breaker = self.breaker_map[self.component.overflowWrap]
        text_split = text.split(breaker) if breaker == " " else list(text)

        block_w = 0
        #block_blueprint = {}

        if self.whitespace_map[self.component.whiteSpace]:
            for word in text_split:
                line.append(word)
                text_w, text_h = blf.dimensions(font_id, breaker.join(line))
                print("mwc: ", text_w * text_size)
                if text_w * text_size > self.component.maxWidth * 1000:
                    print("w: ", text_w)
                    new_line = [line.pop()]
                    text_w, text_h = blf.dimensions(font_id, breaker.join(line))
                    block_w = text_w if not block_w else block_w
                    # block_blueprint[line_count] = {
                    #     "line":breaker.join(line),
                    #     "position": (anchor * block_w, line_count * line_count_modifier)
                    #     }
                    blf.position(font_id, anchor * block_w, line_count * line_count_modifier, 0)
                    blf.color(font_id, text_color[0], text_color[1], text_color[2], 1)
                    blf.draw(font_id, breaker.join(line))
                    line = new_line
                    line_count += 1

            if line:
                text_w, text_h = blf.dimensions(font_id, breaker.join(line))
                block_w = text_w if not block_w else block_w
                print("w: ", text_w)
                # block_blueprint[line_count] = {
                #         "line":breaker.join(line),
                #         "position": (anchor * block_w, line_count * line_count_modifier)
                #         }
                blf.position(font_id, anchor * block_w, line_count * line_count_modifier, 0)
                blf.color(font_id, text_color[0], text_color[1], text_color[2], 1)
                blf.draw(font_id, breaker.join(line))

        else:
            text_w, text_h = blf.dimensions(font_id, text)
            blf.position(font_id, anchor * text_w, 0, 0)
            blf.color(font_id, text_color[0], text_color[1], text_color[2], 1)
            blf.draw(font_id, text)

        gpu.matrix.pop()

class Text(HubsComponent):
    _definition = {
        'name': 'text',
        'display_name': 'Text',
        'category': Category.ELEMENTS,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'icon': 'FONT_DATA',
        'version': (1, 0, 0)
    }

    value: StringProperty(
        name="Text",
        description="The string of text to be rendered. Newlines and repeating whitespace characters are honored",
        default="Hello world!")

    fontSize: FloatProperty(
        name="Font Size",
        description="Font size, in local meters",
        unit='LENGTH',
        default=0.075)

    textAlign: EnumProperty(
        name="Alignment",
        description="The horizontal alignment of each line of text within the overall text bounding box",
        items=[("left", "Left", "Text will be aligned to the left"),
               ("right", "Right", "Text will be aligned to the right"),
               ("center", "Center", "Text will be centered"),
               ("justify", "Justify", "Text will be justified")],
        default="left")

    anchorX: EnumProperty(
        name="Anchor X",
        description="Defines the horizontal position in the text block that should line up with the local origin",
        items=[("left", "Left", "Left side of the text will be at the pivot point of this object"),
               ("center", "Center",
                "Center of the text will be at the pivot point of this object"),
               ("right", "Right", "Right side of the text will be at the pivot point of this object")],
        default="center")

    anchorY: EnumProperty(
        name="Anchor Y",
        description="Defines the vertical position in the text block that should line up with the local origin",
        items=[("top", "Top", "Top of the text will be at the pivot point of this object"),
               ("top-baseline", "Top Baseline",
                "Top baseline of the text will be at the pivot point of this object"),
               ("middle", "Middle",
                "Middle of the text will be at the pivot point of this object"),
               ("bottom-baseline", "Bottom Baseline",
                "Bottom baseline of the text will be at the pivot point of this object"),
               ("bottom", "Bottom", "Bottom of the text will be at the pivot point of this object")],
        default="middle")

    color: FloatVectorProperty(name="Color",
                               description="Color",
                               subtype='COLOR_GAMMA',
                               default=(1.0, 1.0, 1.0, 1.0),
                               size=4,
                               min=0,
                               max=1)

    letterSpacing: FloatProperty(
        name="Letter Space",
        description="Sets a uniform adjustment to spacing between letters after kerning is applied, in local meters. Positive numbers increase spacing and negative numbers decrease it",
        unit='LENGTH',
        default=0.0)

    lineHeight: FloatProperty(
        name="Line Height",
        description="Sets the height of each line of text. If 0, a reasonable height based on the chosen font's ascender/descender metrics will be used, otherwise it is interpreted as a multiple of the fontSize",
        default=1.0)

    outlineWidth: StringProperty(
        name="Outline Width",
        description="The width of an outline/halo to be drawn around each text glyph using the outlineColor and outlineOpacity. This can help improve readability when the text is displayed against a background of low or varying contrast.\n\n The width can be specified as either an absolute number in local units, or as a percentage string e.g. \"10%\" which is interpreted as a percentage of the fontSize",
        default="0")

    outlineColor: FloatVectorProperty(
        name="Outline Color",
        description="The color to use for the text outline when outlineWidth, outlineBlur, and/or outlineOffsetX/Y are set",
        subtype='COLOR_GAMMA', default=(0.0, 0.0, 0.0, 1.0),
        size=4, min=0, max=1)

    outlineBlur: StringProperty(name="Outline Blur",
                                description="Specifies a blur radius applied to the outer edge of the text's outlineWidth. If the outlineWidth is zero, the blur will be applied at the glyph edge, like CSS's text-shadow blur radius. A blur plus a nonzero outlineWidth can give a solid outline with a fuzzy outer edge.\n\nThe blur radius can be specified as either an absolute number in local meters, or as a percentage string e.g. \"12%\" which is treated as a percentage of the fontSize",
                                default="0")

    outlineOffsetX: StringProperty(
        name="Outline X Offset",
        description="This defines a horizontal offset of the text outline. Using an offset with outlineWidth: 0 creates a drop-shadow effect like CSS's text-shadow; also see outlineBlur.\n\n The offsets can be specified as either an absolute number in local units, or as a percentage string e.g. \"12%\" which is treated as a percentage of the fontSize",
        default="0")

    outlineOffsetY: StringProperty(
        name="Outline Y Offset",
        description="This defines a vertical offset of the text outline. Using an offset with outlineWidth: 0 creates a drop-shadow effect like CSS's text-shadow; also see outlineBlur.\n\n The offsets can be specified as either an absolute number in local units, or as a percentage string e.g. \"12%\" which is treated as a percentage of the fontSize",
        default="0")

    outlineOpacity: FloatProperty(
        name="Outline Opacity",
        description="Sets the opacity of a configured text outline, in the range 0 to 1",
        min=0.0,
        max=1.0,
        default=1.0)

    fillOpacity: FloatProperty(
        name="Fill Opacity",
        description="Controls the opacity of just the glyph's fill area, separate from any configured strokeOpacity, outlineOpacity, and the material's opacity. A fillOpacity of 0 will make the fill invisible, leaving just the stroke and/or outline",
        min=0.0,
        max=1.0,
        default=1.0)

    strokeWidth: StringProperty(
        name="Stroke Width",
        description="Sets the width of a stroke drawn inside the edge of each text glyph, using the strokeColor and strokeOpacity.\n\n The width can be specified as either an absolute number in local units, or as a percentage string e.g. \"10%\" which is interpreted as a percentage of the fontSize",
        default="0")

    strokeColor: FloatVectorProperty(name="Stroke Color",
                                     description="The color of the text stroke, when strokeWidth is nonzero",
                                     subtype='COLOR_GAMMA',
                                     default=(0.0, 0.0, 0.0, 1.0),
                                     size=4,
                                     min=0,
                                     max=1)

    strokeOpacity: FloatProperty(name="Stroke Opacity",
                                 description="The opacity of the text stroke, when strokeWidth is nonzero",
                                 min=0.0,
                                 max=1.0,
                                 default=1.0)

    textIndent: FloatProperty(
        name="Text Indent",
        description="An indentation applied to the first character of each hard newline. Behaves like CSS text-indent",
        default=0.0)

    whiteSpace: EnumProperty(
        name="Wrapping",
        description="Defines whether text should wrap when a line reaches the maxWidth",
        items=[("normal", "Normal", "Allow wrapping according to the 'wrapping mode'"),
               ("nowrap", "No Wrapping", "Prevent wrapping")],
        default="normal")

    overflowWrap: EnumProperty(
        name="Wrapping Mode",
        description="Defines how text wraps if the whiteSpace property is 'normal'",
        items=[("normal", "Normal", "Break only at whitespace characters"),
               ("break-word", "Break Word", "Allow breaking within words")],
        default="normal")

    opacity: FloatProperty(
        name="Opacity",
        description="The opacity of the entire text object",
        min=0.0,
        max=1.0,
        default=1.0)

    side: EnumProperty(
        name="Display Side",
        description="Defines how text wraps if the whiteSpace property is 'normal'",
        items=[("front", "Show on front", "Text will be shown on the front (-Y)"),
               ("back", "Show on back", "Text will be shown on the back (+Y)"),
               ("double", "Show on both", "Text will be shown on both sides")],
        default="front")

    maxWidth: FloatProperty(
        name="Max Width",
        description="The maximum width of the text block, above which text may start wrapping according to the whiteSpace and overflowWrap properties",
        unit='LENGTH',
        default=1.0)

    curveRadius: FloatProperty(
        name="Curve Radius",
        description="Defines a cylindrical radius along which the text's plane will be curved. Positive numbers put the cylinder's centerline (oriented vertically) that distance in front of the text, for a concave curvature, while negative numbers put it behind the text for a convex curvature. The centerline will be aligned with the text's local origin; you can use anchorX to offset it",
        unit='LENGTH',
        default=0.0)

    direction: EnumProperty(
        name="Direction",
        description="Sets the base direction for the tex",
        items=[("auto", "Auto", "Use the default text direction defined by the system and font"),
               ("ltr", "Left to Right", "Order text left to right"),
               ("rtl", "Right to Left", "Order text right to left")],
        default="auto")

    @staticmethod
    def register():
        bpy.utils.register_class(TextGizmo)

    @staticmethod
    def unregister():
        bpy.utils.unregister_class(TextGizmo)

    @classmethod
    def update_gizmo(cls, ob, bone, target, gizmo):
        return
        if bone:
            mat = bone_matrix_world(ob, bone)
        else:
            mat = ob.matrix_world.copy()

        gizmo.hide = not ob.visible_get()
        gizmo.matrix_basis = mat

    @classmethod
    def create_gizmo(cls, ob, gizmo_group):
        component = getattr(ob, cls.get_id())
        gizmo = gizmo_group.gizmos.new(TextGizmo.bl_idname)
        gizmo.component = component
        gizmo.host = ob
        gizmo.use_draw_scale = False
        gizmo.use_draw_modal = False

        return gizmo

