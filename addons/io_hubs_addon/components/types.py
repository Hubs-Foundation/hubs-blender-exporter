from enum import Enum


class PanelType(Enum):
    OBJECT = 'object'
    SCENE = 'scene'
    MATERIAL = 'material'
    OBJECT_DATA = 'data'
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
    AV = 'A/V Elements'
