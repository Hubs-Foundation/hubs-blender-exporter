class GizmoInfo():
    def __init__(self, name, type, color = (0.8, 0.8, 0.8), color_highlight = (0.8, 0.8, 0.8), styles=[], draw_options=[], shape=None, path=None, id=None, update=None):
        self.name = name
        self.type = type
        self.color = color
        self.color_highlight = color_highlight
        self.styles = styles
        self.draw_options = draw_options
        self.shape = shape
        self.path = path
        self.id = id
        self.update = update
