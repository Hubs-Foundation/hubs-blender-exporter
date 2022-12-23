from bpy.types import PropertyGroup
from bpy.props import IntVectorProperty
from ..io.utils import gather_properties
from .types import Category, PanelType, NodeType


class HubsComponent(PropertyGroup):
    _definition = {
        # The name that will be used in the GLTF file MOZ_hubs_components object when exporting the component.
        'name': 'template',
        # Name to be used in the panels, if not set the component name will be used
        'display_name': 'Hubs Component Template',
        # Category that is shown in the "Add Component" menu
        'category': Category.MISC,
        # Node type to where the component will be registered
        'node_type': NodeType.NODE,
        # Panel types where this component will be shown
        'panel_type': [PanelType.OBJECT],
        # The dependencies of this component (by id). They will be added as a result of adding this component.
        'deps': [],
        # Name of the icon to load. It can be a image file in the icons directory or one of the Blender builtin icons id
        'icon': 'icon.png',
        # Version of the component. This will be used to trigger component migrations.
        'version': (0, 0, 1)
    }

    # Properties defined here are for internal use and won't be displayed by default in components or exported.

    # The internal version of the component.  This is first set when a component is added and is updated during migrations, if necessary.
    instance_version: IntVectorProperty(size=3)

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
        return cls.__get_definition('node_type', NodeType.NODE)

    @classmethod
    def get_panel_type(cls):
        return cls.__get_definition('panel_type', [PanelType.OBJECT])

    @classmethod
    def get_category(cls):
        return cls.__get_definition('category', None)

    @classmethod
    def get_category_name(cls):
        return cls.get_category().value

    @classmethod
    def get_definition_version(cls):
        return cls.__get_definition('version', (0, 0, 0))

    @classmethod
    def init(cls, obj):
        '''Called right after the component is added to give the component a chance to initialize'''
        pass

    @classmethod
    def init_instance_version(cls, obj):
        component = getattr(obj, cls.get_id())
        component.instance_version = cls.get_definition_version()

    @classmethod
    def create_gizmo(cls, obj, gizmo_group):
        return None

    @classmethod
    def update_gizmo(cls, obj, bone, target, gizmo):
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

    def draw(self, context, layout, panel):
        '''Draw method to be called by the panel. The base class method will print all the component properties'''
        for key in self.get_properties():
            if not self.bl_rna.properties[key].is_hidden:
                layout.prop(data=self, property=key)

    def pre_export(self, export_settings, host, ob=None):
        '''This is called by the exporter before starting the export process'''
        pass

    def gather(self, export_settings, object):
        '''This is called by the exporter and will return all the component properties by default'''
        return gather_properties(export_settings, object, self)

    def post_export(self, export_settings, host, ob=None):
        '''This is called by the exporter after the export process has finished'''
        pass

    def migrate(self, migration_type, panel_type, instance_version, host, migration_report, ob=None):
        '''This is called when an object component needs to migrate the data from previous add-on versions.
        The migration_type argument is the type of migration, GLOBAL represents file loads, and LOCAL represents things like append/link.
        The panel_type argument is used to determine what data-block the component is on.
        The instance_version argument represents the version of the component that will be migrated from, as a tuple.
        The host argument is what the component is attached to, object/bone.
        The migration_report argument is a list that you can append messages to and they will be displayed to the user after the migration has finished.
        The ob argument is used for bone migrations and is the armature object that the bone is part of.  Note: this is passed for object migrations as well, and will fall back to passing the armature if the object isn't available.
        Returns a boolean to indicate whether a migration was performed.
        '''
        return False

    @classmethod
    def draw_global(cls, context, layout, panel):
        '''Draw method to be called by the panel. This can be used to draw global component properties in a panel before the component properties.'''

    @classmethod
    def get_properties(cls):
        if hasattr(cls, '__annotations__'):
            # Python versions below 3.10 will sometimes return the base class' annotations if there are none in the subclass, so make sure only the subclass' annotations are returned.
            baseclass_properties = HubsComponent.__annotations__.keys()
            subclass_properties = cls.__annotations__.keys()
            return [prop for prop in subclass_properties if prop not in baseclass_properties]
        return {}

    @classmethod
    def poll(cls, panel_type, host, ob=None):
        '''This method will return true if this component's shown be shown or run.
        This is currently called when checking if the component should be added to the components pop-up, when the components properties panel is drawn, and during migrations to warn about unsupported hosts.
        The ob argument is guaranteed to be present only for objects/bones, although it will fall back to using the armature for bones if the object isn't available.'''
        return True

    @classmethod
    def get_unsupported_host_message(cls, panel_type, host, ob=None):
        '''This method will return the message to use if this component isn't supported on this host.
        This is currently called during migrations.
        The ob argument will fall back to an armature for bones if an object isn't available.'''
        from .utils import get_host_reference_message
        host_reference = get_host_reference_message(panel_type, host, ob=ob)
        host_type = panel_type.value
        message = f"Warning: Unsupported component on {host_type} {host_reference}, {host_type}s don't support {cls.get_display_name()} components"

        return message

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
