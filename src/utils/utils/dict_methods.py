def nested_itemgetter(obj, keys):
    value = obj
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value
