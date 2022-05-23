from enum import Enum


class PanelType(Enum):
    OBJECT = 'object'
    SCENE = 'scene'
    MATERIAL = 'material'
    OBJECT_DATA = 'data'
    BONE = 'bone'


class Category(Enum):
    OBJECT = 'Object'
    SCENE = 'Scene'
    ELEMENTS = 'Elements'
    ANIMATION = 'Animation'
    AVATAR = 'Avatar'
    MISC = 'Misc'
