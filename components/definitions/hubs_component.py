from bpy.types import PropertyGroup
from ...io.utils import gather_properties
from ..types import Category, PanelType, NodeType


class HubsComponent(PropertyGroup):
    _definition = {
        # This is the name that it will be used when exporting the component.
        'export_name': 'hubs-component',
        # Name to be used in the panels, if not set the component name will be used
        'display_name': 'Hubs Component',
        # Category that's is shown in the "Add Component" menu
        'category': Category.MISC,
        # Node type to where the component with be registered
        'node_type': NodeType.NODE,
        # Panel where to show this component
        'panel_type': PanelType.OBJECT,
        # Wether or not this component is networked
        "networked": False,
        # The dependencies will be added as a result of adding this component
        'deps': [],
        # Id of the gizmo to show when this component is added
        'gizmo': 'gizmo',
        # Name of the icon to load
        'icon': 'icon.png'
    }

    @classmethod
    def __get_definition(cls, key, default):
        if key in cls._definition and cls._definition[key]:
            return cls._definition[key]
        return default

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def get_export_name(cls):
        return cls.__get_definition('export_name', cls.__name__.lower().replace('_', '-'))

    @classmethod
    def get_node_type(cls):
        return cls.__get_definition('node_type', NodeType.NODE)

    @classmethod
    def get_panel_type(cls):
        return cls.__get_definition('panel_type', PanelType.OBJECT)

    @classmethod
    def get_category(cls):
        return cls.__get_definition('category', Category.MISC)

    @classmethod
    def get_category_name(cls):
        return cls.get_category().value

    @classmethod
    def get_display_name(cls, default=__name__):
        return cls.__get_definition('display_name', default)

    @classmethod
    def is_nerworked(cls):
        return cls.__get_definition('networked', False)

    @classmethod
    def get_gizmo(cls):
        return cls.__get_definition('gizmo', '')

    @classmethod
    def get_deps(cls):
        return cls.__get_definition('deps', [])

    @classmethod
    def get_icon(cls):
        return cls.__get_definition('icon', None)

    def __init__(self):
        if type(self) is HubsComponent:
            raise Exception(
                'HubsComponent is an abstract class and cannot be instantiated directly')

    def draw(self, col):
        '''Draw method to be called by the panel. The base class method will print all the object properties'''
        for key in self.__annotations__.keys():
            col.prop(data=self, property=key)

    def gather(self, export_settings, object):
        '''This is called by the exporter and will return the object defined properties by default'''
        return gather_properties(export_settings, object, self)

    @classmethod
    def get_properties(cls):
        return cls.__annotations__.keys()

    @classmethod
    def poll(cls, context):
        return True

    @staticmethod
    def register():
        '''This is called by the Blender runtime when the component is registered.
        Here you can register any classes that the component is using.'''
        pass

    @staticmethod
    def unregister():
        '''This is called by the Blender runtime when the component is unregistered.
        Here you can unregister any classes that you have registered.'''
        pass
