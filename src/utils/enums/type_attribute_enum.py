from enum import Enum


class TypeAttributeEnum(str, Enum):
    CLASS = 'class'
    XPATH = 'xpath'
    ATTRIBUTE = 'attribute'
    META_INFORMATION = 'meta_information'
    SCHEMA = 'schema'
