from bpy.types import PropertyGroup
from ...io.utils import gather_properties
from ..types import Category, PanelType, NodeType


class HubsComponent(PropertyGroup):
    _definition = {
        # The name that will be used in the GLTF file MOZ_hubs_components object when exporting the component.
        'id': 'hubs-component-template',
        # The component name to be used in the components registry (historically Hubs component follow the format [hubs_component_abc])
        'name': 'hubs_component_template',
        # Name to be used in the panels, if not set the component name will be used
        'display_name': 'Hubs Component Template',
        # Category that is shown in the "Add Component" menu
        'category': Category.MISC,
        # Node type to where the component will be registered
        'node_type': NodeType.NODE,
        # Panel type where to show this component
        'panel_type': PanelType.OBJECT,
        # The dependencies of this component (by id). They will be added as a result of adding this component.
        'deps': [],
        # Name of the icon to load. It can be a image file in the icons directory or one of the Blender builtin icons id
        'icon': 'icon.png',
        # Tag the component as dependecy only so it doens't whow up in the comonents list
        'dep_only': False
    }

    @classmethod
    def __get_definition(cls, key, default):
        if key in cls._definition and cls._definition[key]:
            return cls._definition[key]
        return default

    @classmethod
    def get_id(cls):
        return cls.__get_definition('id', cls.__name__)

    @classmethod
    def get_name(cls):
        return cls.__get_definition('name', cls.get_id())

    @classmethod
    def get_display_name(cls, default=__name__):
        return cls.__get_definition('display_name', default)

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
    def create_gizmo(cls, obj, gizmo_group):
        return None, None

    @classmethod
    def get_deps(cls):
        return cls.__get_definition('deps', [])

    @classmethod
    def get_icon(cls):
        return cls.__get_definition('icon', None)

    @classmethod
    def is_dep_only(cls):
        return cls.__get_definition('dep_only', False)

    def __init__(self):
        if type(self) is HubsComponent:
            raise Exception(
                'HubsComponent is an abstract class and cannot be instantiated directly')

    def draw(self, context, layout):
        '''Draw method to be called by the panel. The base class method will print all the component properties'''
        for key in self.__annotations__.keys():
            layout.prop(data=self, property=key)

    def gather(self, export_settings, object):
        '''This is called by the exporter and will return the component properties by default'''
        return gather_properties(export_settings, object, self)

    @classmethod
    def get_properties(cls):
        if hasattr(cls, '__annotations__'):
            return cls.__annotations__.keys()
        return {}

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
