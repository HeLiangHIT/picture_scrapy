# -*- coding: utf-8 -*-
import scrapy
import logging
from picture_scrapy.items import ImageItem

_next_xpath = '//a[@title="Older Comments"]/@href'
_img_xpath = '//*[contains(@id,"comment")]/div/div/div[2]/p/img/@src'


class JandanSpider(scrapy.Spider):
    name = 'jiandan'
    start_urls = ['http://jandan.net/ooxx']

    def parse(self, response):
        logging.info("begin to parser %s" % response.url)

        # 查找下一页继续访问
        next_url = response.xpath(_next_xpath).extract_first()
        if next_url is not None:
            yield response.follow("http:" + next_url, self.parse)

        # 返回图片地址
        img_list = response.xpath(_img_xpath).extract()
        for src_url in img_list:
            yield ImageItem(url=src_url, name=src_url.split('/')[-1])


