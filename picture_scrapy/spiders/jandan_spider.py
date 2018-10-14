# -*- coding: utf-8 -*-
import scrapy
from picture_scrapy.items import ImageItem

_next_xpath = '//a[@title="Older Comments"]/@href' # 下一页
_img_xpath = '//*[contains(@id,"comment")]/div/div/div[2]/p/img' # 图片包括动图 @src or @org_src


class JandanSpider(scrapy.Spider):
    name = 'jiandan'
    start_urls = ['http://jandan.net/ooxx']

    def parse(self, response):
        self.logger.info("begin to parser %s" % response.url)

        # 查找下一页继续访问
        next_url = response.xpath(_next_xpath).extract_first()
        if next_url is not None:
            yield response.follow("http:" + next_url, self.parse)

        # 返回图片地址
        img_list = response.xpath(_img_xpath)
        for img in img_list:
            org_src = img.xpath("./@org_src").extract_first() # gif src
            src = img.xpath("./@src").extract_first()
            src_url = org_src if org_src is not None else src
            yield ImageItem(url=src_url, name=src_url.split('/')[-1], folder="jiandan", page=response.url)

