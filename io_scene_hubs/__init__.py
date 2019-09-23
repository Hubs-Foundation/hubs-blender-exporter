from . import settings
from . import components
from . import operators
from . import panels

bl_info = {
    "name" : "io_scene_hubs",
    "author" : "Robert Long",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

def register():
    settings.register()
    components.register()
    operators.register()
    panels.register()

def unregister():
    settings.unregister()
    components.unregister()
    operators.unregister()
    panels.unregister()

if __name__ == "__main__":
    register()
