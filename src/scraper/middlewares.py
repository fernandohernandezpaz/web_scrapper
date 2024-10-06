# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface

from importlib import import_module
from selenium import webdriver

from time import sleep
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from scrapy_selenium.http import SeleniumRequest
from selenium.common import (InvalidSelectorException, TimeoutException,
                             NoSuchElementException, ElementNotInteractableException, )
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""
    current_request_url = None

    def __init__(self,
                 driver_name,
                 driver_executable_path,
                 browser_executable_path,
                 command_executor,
                 driver_arguments,
                 ):
        """Initialize the selenium webdriver

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_executable_path: str
            The path of the executable binary of the driver
        driver_arguments: list
            A list of arguments to initialize the driver
        browser_executable_path: str
            The path of the executable binary of the browser
        command_executor: str
            Selenium remote server endpoint
        """
        chrome_prefs = {
            "profile.managed_default_content_settings.images": 2
        }

        webdriver_base_path = f'selenium.webdriver.{driver_name}'

        driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
        driver_klass = getattr(driver_klass_module, 'WebDriver')

        driver_options_module = import_module(f'{webdriver_base_path}.options')
        driver_options_klass = getattr(driver_options_module, 'Options')

        driver_options = driver_options_klass()

        if browser_executable_path:
            driver_options.binary_location = browser_executable_path
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        driver_kwargs = {
            'executable_path': driver_executable_path,
            f'{driver_name}_options': driver_options
        }

        if driver_executable_path is not None:
            driver_kwargs = {
                'executable_path': driver_executable_path,
                f'{driver_name}_options': driver_options
            }
            self.driver = driver_klass(**driver_kwargs)
        elif command_executor is not None:
            capabilities = driver_options.to_capabilities()
            self.driver = webdriver.Remote(
                command_executor=command_executor, desired_capabilities=capabilities
            )
        else:
            # selenium4+ & webdriver-manager
            from selenium.webdriver.chrome.service import Service as ChromeService
            from webdriver_manager.chrome import ChromeDriverManager
            if driver_name and driver_name.lower() == 'chrome':
                self.driver = webdriver.Chrome(
                    options=driver_options,service=ChromeService(ChromeDriverManager().install())
                )

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        command_executor = crawler.settings.get('SELENIUM_COMMAND_EXECUTOR')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

        if driver_name is None:
            raise NotConfigured('SELENIUM_DRIVER_NAME must be set')

        if (driver_name.lower() != 'chrome') and (
            driver_executable_path is None and command_executor is None):
            raise NotConfigured('Either SELENIUM_DRIVER_EXECUTABLE_PATH '
                                'or SELENIUM_COMMAND_EXECUTOR must be set')

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            browser_executable_path=browser_executable_path,
            command_executor=command_executor,
            driver_arguments=driver_arguments,
        )

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""

        if not isinstance(request, SeleniumRequest):
            return None

        body = self._process_request(request)
        return HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def _process_request(self, request):
        errors = [NoSuchElementException, ElementNotInteractableException]
        self.driver.get(request.url)

        for cookie_name, cookie_value in request.cookies.items():
            self.driver.add_cookie(
                {
                    'name': cookie_name,
                    'value': cookie_value
                }
            )

        if request.wait_time:
            if request.wait_until:
                try:
                    WebDriverWait(
                        self.driver, request.wait_time,
                        poll_frequency=.6, ignored_exceptions=errors
                    ).until(
                        request.wait_until
                    )
                except (InvalidSelectorException, TimeoutException):
                    pass
            else:
                try:
                    WebDriverWait(self.driver, request.wait_time, poll_frequency=.6).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )
                except (InvalidSelectorException, TimeoutException):
                    pass

        if request.screenshot:
            request.meta['screenshot'] = self.driver.get_screenshot_as_png()

        if request.script:
            self.driver.execute_script(request.script)

        browser_logs = self.driver.get_log('browser')
        for _log in browser_logs:
            if 'Failed to load resource: net::ERR_NETWORK_CHANGED' in _log.get('message'):
                print('Connection was interrupted')
                self.driver.refresh()
                sleep(5)
                break

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': self.driver})

        return str.encode(self.driver.page_source)

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""

        self.driver.quit()
