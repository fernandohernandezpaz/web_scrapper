from enum import Enum


class TextTypeAttrEnum(str, Enum):
    CSS_TEXT = '::text'
    XPATH_TEXT = '/text()'
