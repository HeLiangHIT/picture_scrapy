# -*- coding: utf-8 -*-
import scrapy
from picture_scrapy.items import ImageItem

_title_xpath = '//ul[@class="archives"]/li/p/a/@href' # 标题
_next_xpath = '//div[@class="pagenavi"]/a[last()]/@href' # 下一页
_img_xpath = '//div[@class="main-image"]/p/a/img' # 图片

class MzituSpider(scrapy.Spider):
    name = 'mzitu'
    start_urls = ['http://www.mzitu.com/all/']
    custom_settings = { # 和 settings.py 中不一样的配置
        'LOG_FILE':'log/mzitu.log'
    }

    def parse(self, response):
        self.logger.info("begin to parser %s" % response.url)
        page_list = response.xpath(_title_xpath).extract()
        for url in page_list:
            yield response.follow(url, self.parser_pages)

    def parser_pages(self, response):
        self.logger.info("begin to parser %s" % response.url)
        # 查找下一页继续访问
        next_url = response.xpath(_next_xpath).extract_first()
        if len(next_url.split('/')) == 5: 
            # the len of first page is 4, while others 5
            yield response.follow(next_url, self.parser_pages)
        else:
            self.logger.info("ignore next url=%s whose length do not enough." % (next_url))

        # 返回图片地址
        img_list = response.xpath(_img_xpath)
        for img in img_list:
            src_url = img.xpath("./@src").extract_first()
            folder = img.xpath("./@alt").extract_first()
            yield ImageItem(url=src_url, name=src_url.split('/')[-1], folder=folder, page=response.url)

