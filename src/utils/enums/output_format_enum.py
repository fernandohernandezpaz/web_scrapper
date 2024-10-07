from enum import Enum


class OutputFormat(str, Enum):
    JSON = 'json'
    CSV = 'csv'
    XLSX = 'xlsx'
