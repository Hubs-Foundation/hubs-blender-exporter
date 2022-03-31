from . import (component, object, scene)

def register():
    component.register()
    object.register()
    scene.register()


def unregister():
    object.unregister()
    scene.unregister()
    component.unregister()
