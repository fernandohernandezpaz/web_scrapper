from json import loads
from re import split
from time import sleep, time
from traceback import clear_frames

from scrapy import Spider, signals
from scrapy.http import HtmlResponse
from scrapy.selector.unified import SelectorList
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from urllib3.exceptions import MaxRetryError, NewConnectionError

from src.data_structure.product_request_payload import ProductRequestPayload
from src.data_structure.product_response import Product
from src.utils.enums import ImageTypeAttrEnum, TextTypeAttrEnum, TypeAttributeEnum
from src.utils.utils.dict_methods import nested_itemgetter
from src.utils.utils.string_methods import get_text_from_quotes, get_url_from_string
from src.utils.utils.url_methods import build_url, get_web_site_url, not_allowed_img_url


class ProductInfoCollectorSpider(Spider):
    name = 'product_info_collector_spider'
    allowed_domains = []
    collection = []
    depth_limit = 1
    start_urls = []
    wait_time = 60
    _class_http_request = None

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        request = kwargs.get('request', {})

        if isinstance(request, str):
            request = loads(request)
        self._request = self._cast_request(request)

        self.start_urls = self._request.list_product_url

        self.main_url = self.start_urls[0]
        _extra_args = {
            'wait_time': self.wait_time,
        }

        self._class_http_request = SeleniumRequest
        # setting extra attrs for selenium request and keep waiting
        # until CSS_SELECTOR section be located
        css_selector = self._request.get_one_css_class()
        self._extra_args_for_detail_view = {
            **_extra_args,
        }
        if css_selector:
            if 'contains("' in css_selector:
                text_to_find = get_text_from_quotes(css_selector)
                self._extra_args_for_detail_view.update({
                    'wait_until': ec.presence_of_element_located(
                        (By.XPATH, f'//*[contains(text(), "{text_to_find}")]'),
                    ),
                })
            else:
                self._extra_args_for_detail_view.update({
                    'wait_until': ec.presence_of_element_located(
                        (By.CSS_SELECTOR, css_selector),
                    ),
                })

    def start_requests(self):
        self.logger.info(f'payload: {str(self._request.__dict__())}')

        for url in self.start_urls:

            try:
                self.logger.info(f'Sending request to {url}')
                yield self._class_http_request(
                    url=url,
                    callback=self.parse,
                    **self._extra_args_for_detail_view
                )
            finally:
                print('Request sent')

    def parse(self, response):
        response = self._wait_the_page_be_loaded(response)
        url, status = response.url, response.status
        if self._check_the_site_return_404(response):
            yield {
                'page_not_found': True,
                'url': url,
            }
        elif self._check_the_site_return_403(response):
            yield {
                'blocked': True,
                'url': url,
            }
        else:
            self.logger.info(f'Collecting the information of the vehicle: {response.url}')

            product = Product({'final_url': response.url, 'image_url': []})
            for _property in self._request.get_attrs_product():
                value = None
                try:
                    value = self._get_value(response, _property)
                except Exception as e:
                    self.logger.error(f"Error in parse_detail_view method: {e}")
                    self.logger.error(f"Error getting information of the property {_property}")
                    clear_frames(e.__traceback__)
                finally:
                    if isinstance(value, str):
                        value = value.strip()
                    product.set_value(_property, value)

            self.collection.append(product.to_dict())
            yield product

    def spider_closed(self):
        # data = {
        #     'products_info': self.collection,
        # }
        self.logger.info('Finished')

    def _cast_request(self, request):
        if not request:
            return None

        return ProductRequestPayload(request)

    def _wait_the_page_be_loaded(self, response, wait_time: int = 30):
        driver = response.meta.get('driver', None)
        if not driver:
            return response

        try:
            current_url = response.url
            driver.get(current_url)
            pause_time, elapsed_time = 2, 0
            start_time = time()
            while elapsed_time < wait_time:
                elapsed_time = time() - start_time
                sleep(pause_time)
                page_ready = driver.execute_script(f"return document.readyState == 'complete';")
                if page_ready:
                    break

            response = HtmlResponse(
                current_url,
                body=driver.page_source,
                encoding='utf-8',
                request=response
            )
        except (MaxRetryError, NewConnectionError) as mix_error:
            clear_frames(mix_error.__traceback__)
        finally:
            return response

    def _wait_to_image_section_be_loaded(self, response, css_expression, wait_time=20):
        driver = response.meta.get('driver', None)
        if not driver:
            return response
        try:
            image_section = response.css(css_expression)
            tries = 0
            if len(image_section) <= 2:
                current_url = response.url
                driver.get(current_url)
                pause_time, elapsed_time = 1, 0
                start_time = time()
                while elapsed_time < wait_time:
                    elapsed_time = time() - start_time
                    sleep(pause_time)
                    images_len = driver.execute_script(
                        f"return document.querySelectorAll('{css_expression}').length"
                    )
                    if images_len > 2:
                        break
                    tries += 1
                    if tries == 4:
                        break

                response = HtmlResponse(
                    current_url,
                    body=driver.page_source,
                    encoding='utf-8',
                    request=response
                )
        except (MaxRetryError, NewConnectionError) as mix_error:
            clear_frames(mix_error.__traceback__)
        finally:
            return response

    def _check_the_site_return_404(self, response):
        driver = response.meta.get('driver')
        if not driver:
            return None

        return driver.execute_script(
            "window.performance.getEntriesByType('navigation')[0].responseStatus === 404"
        )

    def _check_the_site_return_403(self, response):
        driver = response.meta.get('driver')
        if not driver:
            return None

        return driver.execute_script(
            "window.performance.getEntriesByType('navigation')[0].responseStatus === 403"
        )

    def _get_css_search_and_positions(self, _value: str):
        new_value = _value.replace(']', '').replace('[', '|')
        _new_value, positions = new_value.split('|')

        if positions == 'full':
            return _new_value, []

        if len(positions) == 1:
            return _new_value, [int(positions)]

        _positions = []
        for _position in positions.split(','):
            _positions.append(int(_position))

        return _new_value, _positions

    def _get_value(self, response, _property):
        _type, _value = self._request.get_attr(_property)

        if not _type or not _value:
            return None

        extract_text = TextTypeAttrEnum.CSS_TEXT

        if _property == 'image_url':
            return self._get_images(response, _type, _value)
        elif extract_text in _value and f'{extract_text}[' in _value and ']' in _value:
            return self._extract_text_by_position(response, _type, _value)
        elif extract_text in _value and ('[' not in _value and ']' not in _value):
            return self._get_element(response, _type, _value).get()
        elif _property in ['title', 'description']:
            return self._get_multiples_values(response, _type, _value)

        element = self._get_element(response, _type, _value)
        return element.css(extract_text).get() if isinstance(element, SelectorList) else element

    def _get_element(self, response, _type, _value):
        if _type == TypeAttributeEnum.CLASS:
            return response.css(_value)
        elif _type == TypeAttributeEnum.XPATH:
            driver = response.meta.get('driver')
            data = driver.find_element(By.XPATH, _value)
            if not data:
                return ''
            if isinstance(data, str):
                return data.strip()

            return data.text.strip() if data else ''
        elif _type == TypeAttributeEnum.META_INFORMATION:
            if '="' in _value:
                meta_tags = response.css(_value)
            else:
                meta_tags = response.css(f'meta[name="{_value}"]') + \
                            response.css(f'meta[property="{_value}"]')
            for meta_tag in meta_tags:
                content = meta_tag.css('::attr(content)').get()
                if content:
                    return content
        elif _type == TypeAttributeEnum.SCHEMA:
            properties = _value.split('.')
            _value = None
            scripts = response.css('script[type="application/ld+json"]::text').extract()
            objects_car = list(map(lambda _script: loads(_script), scripts))
            for object_car in objects_car:
                if properties[0] not in object_car.keys():
                    continue
                _value = nested_itemgetter(object_car, properties)

            return _value
        return ''

    def _extract_text_by_position(self, response, _type, _value):
        _new_value, _positions = self._get_css_search_and_positions(_value)

        if len(_positions) == 0:
            return self._get_element(response, _type, _new_value).get().strip()
        else:
            _strings = []
            text = (self._get_element(response, _type, _new_value).get() or ''). \
                strip().split(' ')
            if len(text) > 1:
                values = []
                for pos in _positions:
                    values.append(text[pos].strip())
                return ' '.join(values).strip()

        return None

    def _get_images(self, response, _type, _value):
        images_url = []
        if (not _type and not _value) or (not _type or not _value):
            return images_url

        is_type_xpath = _type == TypeAttributeEnum.XPATH

        if is_type_xpath:
            _attr, new_value = ImageTypeAttrEnum.XPATH_SRC, _value
            image_section = response.xpath(_value)
            if not image_section:
                return images_url

            response = self._wait_to_image_section_be_loaded(response, new_value)
            image_section = response.xpath(new_value)
        else:
            _attr, new_value = ImageTypeAttrEnum.CSS_SRC, _value
            if ':' in _value:
                new_value, _attr = _value.split(':', 1)
                _attr = ':' + _attr

            new_value = new_value.replace(':first-child', '').replace(':last-child', ''). \
                replace(':first-of-type', '')

            image_section = response.css(new_value)
            if not image_section:
                return images_url

            response = self._wait_to_image_section_be_loaded(response, new_value)
            image_section = response.css(new_value)

        for _image in image_section:
            _url = _image.xpath(_attr).get() if is_type_xpath else _image.css(_attr).get()
            if _attr not in [ImageTypeAttrEnum.CSS_SRC, ImageTypeAttrEnum.XPATH_SRC]:
                _url = get_url_from_string(_url)

            if not_allowed_img_url(_url):
                continue
            domain = get_web_site_url(self._request.list_product_url[0])
            _full_url = build_url(domain, _url)
            if _full_url not in images_url:
                images_url.append(_full_url)

            if images_url:
                break

        return images_url

    def _get_multiples_values(self, response, _type, _value):
        css_for_title = [_value]
        if ',' in _value:
            css_for_title = list(
                map(lambda x: x.strip(), split(r',(?![^\[]*\])', _value))
            )
        unique_strings = []

        is_type_xpath = _type == TypeAttributeEnum.XPATH

        for _css in css_for_title:
            if TextTypeAttrEnum.CSS_TEXT in _css or TextTypeAttrEnum.XPATH_TEXT in _css:
                _strings = response.xpath(_css) if is_type_xpath else response.css(_css)
                _strings = _strings.extract()
            else:
                if is_type_xpath:
                    _strings = response.xpath(_css)
                    _strings = response.xpath(TextTypeAttrEnum.XPATH_TEXT)
                else:
                    _strings = response.css(_css)
                    _strings = _strings.css(TextTypeAttrEnum.CSS_TEXT)
                _strings = _strings.get()
            if not _strings:
                break

            unique_strings = list(set(_strings))

        return ' '.join(unique_strings).strip()
