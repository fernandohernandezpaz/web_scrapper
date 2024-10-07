from urllib.parse import urljoin, urlparse


def not_allowed_img_url(url_string):
    not_allowed_urls = [
        'data:image/svg+xml;base64',
        '/resources/components/utilityImages/expand.svg',
        'data:image/gif;base64',
        'None',
        '/static/images/blank.gif',
        'business_badge.png',
        'https://media.assets.ansira.net/',
        'x100',
        'kia-logo-black-transparent.png',
        'photo_unavailable_148.gif'
    ]
    if url_string == '':
        return True

    if url_string.startswith('//'):
        return True

    if url_string is None:
        return True

    for not_allow_string in not_allowed_urls:
        if not_allow_string in url_string:
            return True
        if url_string == not_allow_string or url_string.startswith(not_allow_string):
            return True
    return False


def get_web_site_url(url_string):
    _url = urlparse(url_string)
    scheme = _url.scheme
    domain = _url.netloc
    return f'{scheme}://{domain}'


def join_urls(domain, path_string):
    return urljoin(domain, path_string)


def get_domain(url_string):
    try:
        _url = urlparse(url_string)
        domain = '.'.join(_url.hostname.split('.')[-2:])
        return domain
    except AttributeError:
        return url_string


def build_url(domain, _path):
    if not domain:
        return _path

    if domain in _path:
        return _path

    return join_urls(domain, _path)
