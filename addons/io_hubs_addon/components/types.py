from enum import Enum


class PanelType(Enum):
    OBJECT = 'object'
    SCENE = 'scene'
    MATERIAL = 'material'
    BONE = 'bone'


class NodeType(Enum):
    NODE = 'object'
    SCENE = 'scene'
    MATERIAL = 'material'


class Category(Enum):
    OBJECT = 'Object'
    SCENE = 'Scene'
    ELEMENTS = 'Elements'
    ANIMATION = 'Animation'
    AVATAR = 'Avatar'
    MISC = 'Misc'
    LIGHTS = 'Lights'
    MEDIA = 'Media'


class MigrationType(Enum):
    GLOBAL = 'global'
    LOCAL = 'local'
    REGISTRATION = 'registration'
