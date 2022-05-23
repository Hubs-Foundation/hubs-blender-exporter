from bpy.types import PropertyGroup, Node
from ..io.utils import gather_properties
from .types import Category, PanelType


class HubsComponent(PropertyGroup):
    _definition = {
        # The name that will be used in the GLTF file MOZ_hubs_components object when exporting the component.
        'name': 'template',
        # Name to be used in the panels, if not set the component name will be used
        'display_name': 'Hubs Component Template',
        # Category that is shown in the "Add Component" menu
        'category': Category.MISC,
        # Node type to where the component will be registered
        'node_type': Node,
        # Panel type where to show this component
        'panel_type': PanelType.OBJECT,
        # The dependencies of this component (by id). They will be added as a result of adding this component.
        'deps': [],
        # Name of the icon to load. It can be a image file in the icons directory or one of the Blender builtin icons id
        'icon': 'icon.png'
    }

    @classmethod
    def __get_definition(cls, key, default):
        if key in cls._definition and cls._definition[key]:
            return cls._definition[key]
        return default

    @classmethod
    def get_id(cls):
        name = cls.__get_definition('name', cls.__name__)
        return 'hubs_component_' + name.replace('-', '_')

    @classmethod
    def get_name(cls):
        return cls.__get_definition('name', cls.get_id())

    @classmethod
    def get_display_name(cls, default=__name__):
        return cls.__get_definition('display_name', default)

    @classmethod
    def get_node_type(cls):
        return cls.__get_definition('node_type', Node)

    @classmethod
    def get_panel_type(cls):
        return cls.__get_definition('panel_type', PanelType.OBJECT)

    @classmethod
    def get_category(cls):
        return cls.__get_definition('category', None)

    @classmethod
    def get_category_name(cls):
        return cls.get_category().value

    @classmethod
    def create_gizmo(cls, obj, gizmo_group):
        return None

    @classmethod
    def update_gizmo(cls, obj, gizmo):
        from .gizmos import gizmo_update
        gizmo_update(obj, gizmo)

    @classmethod
    def get_deps(cls):
        return cls.__get_definition('deps', [])

    @classmethod
    def get_icon(cls):
        return cls.__get_definition('icon', None)

    @classmethod
    def is_dep_only(cls):
        return not cls.get_category()

    def __init__(self):
        if type(self) is HubsComponent:
            raise Exception(
                'HubsComponent is an abstract class and cannot be instantiated directly')

    def draw(self, context, layout):
        '''Draw method to be called by the panel. The base class method will print all the component properties'''
        for key in self.__annotations__.keys():
            layout.prop(data=self, property=key)

    def gather(self, export_settings, object):
        '''This is called by the exporter and will return all the component properties by default'''
        return gather_properties(export_settings, object, self)

    @classmethod
    def get_properties(cls):
        if hasattr(cls, '__annotations__'):
            return cls.__annotations__.keys()
        return {}

    @classmethod
    def migrate(cls):
        '''This is called when a new file is loaded to give the components a chance to migrate the data from previous add-on versions.'''
        pass

    @classmethod
    def poll(cls, context):
        '''This method will return true if this component's shown be shown or run.
        This is currently called when checking if the component should be added to the components pop-up and when the components properties panel is drawn'''
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
