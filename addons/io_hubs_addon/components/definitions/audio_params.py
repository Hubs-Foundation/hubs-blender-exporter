import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty
from ..hubs_component import HubsComponent
from ..types import PanelType, NodeType, MigrationType
from ..utils import is_linked
from ..consts import DISTANCE_MODELS, MAX_ANGLE
from math import degrees, radians

AUDIO_TYPES = [("pannernode", "Positional audio (pannernode)",
                "Volume will change depending on the listener's position relative to the source"),
               ("stereo", "Background audio (stereo)",
                "Volume will be independent of the listener's position")]


class AudioParams(HubsComponent):
    _definition = {
        'name': 'audio-params',
        'display_name': 'Audio Params',
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT, PanelType.BONE],
        'version': (1, 0, 0)
    }

    overrideAudioSettings: BoolProperty(
        name="Override Audio Settings",
        description="Override Audio Settings",
        default=True)

    audioType: EnumProperty(
        name="Audio Type",
        description="Audio Type",
        items=AUDIO_TYPES,
        default="pannernode")

    distanceModel: EnumProperty(
        name="Distance Model",
        description="Distance Model",
        items=DISTANCE_MODELS,
        default="inverse")

    gain: FloatProperty(
        name="Gain",
        description="How much to amplify the source audio by",
        default=1.0,
        min=0.0)

    refDistance: FloatProperty(
        name="Ref Distance",
        description="A double value representing the reference distance for reducing volume as the audio source moves further from the listener. For distances greater than this the volume will be reduced based on rolloffFactor and distanceModel",
        subtype="DISTANCE",
        unit="LENGTH",
        default=1.0,
        min=0.0)

    rolloffFactor: FloatProperty(
        name="Rolloff Factor",
        description="A double value describing how quickly the volume is reduced as the source moves away from the listener. This value is used by all distance models",
        default=1.0,
        min=0.0)

    maxDistance: FloatProperty(
        name="Max Distance",
        description="A double value representing the maximum distance between the audio source and the listener, after which the volume is not reduced any further. This value is used only by the linear distance model",
        subtype="DISTANCE",
        unit="LENGTH",
        default=10000.0,
        min=0.0)

    coneInnerAngle: FloatProperty(
        name="Cone Inner Angle",
        description="A double value describing the angle, in degrees, of a cone inside of which there will be no volume reduction",
        subtype="ANGLE",
        default=MAX_ANGLE,
        min=0.0,
        max=MAX_ANGLE,
        precision=2)

    coneOuterAngle: FloatProperty(
        name="Cone Outer Angle",
        description="A double value describing the angle, in degrees, of a cone outside of which the volume will be reduced by a constant value, defined by the coneOuterGain attribute",
        subtype="ANGLE",
        default=0.0,
        min=0.0,
        max=MAX_ANGLE,
        precision=2)

    coneOuterGain: FloatProperty(
        name="Cone Outer Gain",
        description="A double value describing the amount of volume reduction outside the cone defined by the coneOuterAngle attribute",
        default=0.0,
        min=0.0,
        max=1.0)

    def gather(self, export_settings, object):
        if (self.overrideAudioSettings):
            return {
                'audioType': self.audioType,
                'distanceModel': self.distanceModel,
                'gain': self.gain,
                'refDistance': self.refDistance,
                'rolloffFactor': self.rolloffFactor,
                'maxDistance': self.maxDistance,
                'coneInnerAngle': round(degrees(self.coneInnerAngle), 2),
                'coneOuterAngle': round(degrees(self.coneOuterAngle), 2),
                'coneOuterGain': self.coneOuterGain
            }

    def migrate(self, migration_type, instance_version, host, migration_report, ob=None):
        migration_occurred = False
        if instance_version < (1, 0, 0):
            migration_occurred = True
            self.coneInnerAngle = radians(
                self.coneInnerAngle)
            self.coneOuterAngle = radians(
                self.coneOuterAngle)

            if migration_type != MigrationType.GLOBAL or is_linked(ob):
                host_type = "bone" if hasattr(host, "tail") else "object"
                if host_type == "bone":
                    host_reference = f"\"{host.name}\" in \"{host.id_data.name_full}\""
                else:
                    host_reference = f"\"{host.name_full}\""
                migration_report.append(
                    f"Warning: The Media Cone angles may not have migrated correctly for the Audio Params component on the {host_type} {host_reference}")

        return migration_occurred

    def draw(self, context, layout, panel):
        layout.prop(data=self, property="overrideAudioSettings")
        if not self.overrideAudioSettings:
            return

        layout.prop(data=self, property="audioType")
        layout.prop(data=self, property="gain")

        if self.audioType == "pannernode":
            layout.prop(data=self, property="distanceModel")
            layout.prop(data=self, property="rolloffFactor")
            layout.prop(data=self, property="refDistance")
            layout.prop(data=self, property="maxDistance")
            layout.prop(data=self, property="coneInnerAngle")
            layout.prop(data=self, property="coneOuterAngle")
            layout.prop(data=self, property="coneOuterGain")
