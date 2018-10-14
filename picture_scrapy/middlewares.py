# -*- coding: utf-8 -*-


from scrapy import signals
import time, random
from .util import *


from faker import Faker
_faker = Faker()
class UserAgentMiddleware():
    # add random user agent
    def process_request(self, request, spider):
        agents = [_faker.firefox(), _faker.opera(), _faker.chrome()]
        request.headers['User-Agent'] = random.choice(agents)


from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
class ChromeDownloaderMiddleware(object):
    def __init__(self, crawler, *args, **kargs):
        super(ChromeDownloaderMiddleware, self).__init__(*args, **kargs)
        self.crawler = crawler
        self.patterns = crawler.settings.get('SELENIUM_URL_RE')
        self.spiders = crawler.settings.get('SELENIUM_SPIDERS')

    @classmethod
    def from_crawler(cls, crawler):
        s = cls(crawler)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def open_driver(self, spider):
        if spider.name not in self.spiders:
            spider.logger.info("chrome is not opened since %s is not in SELENIUM_SPIDERS." %(spider.name))
            return None # for next downloader to get it

        self.options = webdriver.ChromeOptions()
        # self.options.add_argument('--headless')  # 无界面
        # self.options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2}) # 不加载图片-会获取不到图片地址
        self.driver = webdriver.Chrome(chrome_options=self.options)
        self.driver.implicitly_wait(1) # 识别对象
        self.driver.set_script_timeout(2) # 异步脚本的超时时间
        self.driver.set_page_load_timeout(8) # 页面完全加载
        spider.logger.info('webdriver opened')

    def close_driver(self, spider):
        if spider.name not in self.spiders:
            spider.logger.info("chrome don't closed since %s is not in SELENIUM_SPIDERS." %(spider.name))
            return None # for next downloader to get it
        self.driver.quit() # self.driver.close()
        spider.logger.info("chrome driver closed.")

    def spider_opened(self, spider):
        self.open_driver(spider)
        
    def spider_closed(self, spider, reason):
        self.close_driver(spider)

    def process_request(self, request, spider):
        if not filter_url_by_patterns(request.url, self.patterns):
            spider.logger.debug("chrome ignore %s since not in SELENIUM_URL_RE." %(request.url))
            return None # for next downloader to get it
        
        try:
            self.driver.get(request.url)
        except TimeoutException as e:
            spider.logger.warn("download %s timeout]" % (request.url)) # return page_source yet
            # self.driver.execute_script('window.stop()') # 停止加载内容
            time.sleep(0.5)
        except Exception as e:
            spider.logger.error("download %s failed]%s" % (request.url, e))
            self.crawler.engine.close_spider(spider, "download %s failed]%s" % (request.url, e))
            return None # do not continue parser

        try:
            return HtmlResponse(url=request.url, body=self.driver.page_source,
                                request=request, encoding='utf-8', status=200) # 超时也可以尽量返回内容
        except Exception as e:
            # 等待重启后重新访问页面
            self.close_driver(spider)
            self.open_driver(spider)
            return HtmlResponse(url=request.url, request=request, status=408)


class PictureScrapySpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class PictureScrapyDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
