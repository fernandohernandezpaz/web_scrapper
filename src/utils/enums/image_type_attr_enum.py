from enum import Enum


class ImageTypeAttrEnum(str, Enum):
    CSS_SRC = '::attr(src)'
    XPATH_SRC = '@src'
    CSS_STYLE = '::attr(style)'
    XPATH_STYLE = '@style'
