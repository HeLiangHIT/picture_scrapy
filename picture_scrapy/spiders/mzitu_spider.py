# -*- coding: utf-8 -*-
import scrapy
from picture_scrapy.items import ImageItem

_title_xpath = '//ul[@class="archives"]/li/p/a'
_next_xpath = '//div[@class="pagenavi"]/a[last()]'
_img_xpath = '//div[@class="main-image"]/p/a/img'

class MzituSpider(scrapy.Spider):
    name = 'mzitu'
    start_urls = ['http://www.mzitu.com/all/']

    def parse(self, response):
        self.logger.info("begin to parser %s" % response.url)
        page_list = response.xpath(_next_xpath).extract()
        for url in page_list:
            yield response.follow(url, self.parser_pages)

    def parser_pages(self, response):
        self.logger.debug("begin to parser %s" % response.url)
        # 查找下一页继续访问
        next_url = response.xpath(_next_xpath).extract_first()
        if response.url.startswith(next_url):
            yield response.follow(next_url, self.parser_pages)
        else:
            self.logger.info("ignore next url=%s since it isn't for this pages.")

        # 返回图片地址
        img_list = response.xpath(_img_xpath)
        for img in img_list:
            src_url = img.xpath("./@src").extract_first()
            folder = img.xpath("./@alt")
            yield ImageItem(url=src_url, name=src_url.split('/')[-1], folder=folder)

