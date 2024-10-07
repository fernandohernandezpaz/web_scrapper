from re import findall


def get_url_from_string(_string):
    result = findall(
        r'(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])',
        _string
    )
    if result and result[0]:
        _url = ''
        for index, piece in enumerate(result[0]):
            if index == 0:
                _url = f'{piece}://'
            else:
                _url += piece
        return _url

    return None

def get_text_from_quotes(_string):
    matches = findall(r'"([^"]*)"', _string)
    if matches:
        return matches[0]
    return ''
