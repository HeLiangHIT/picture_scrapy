# -*- coding: utf-8 -*-
import scrapy
from picture_scrapy.items import ImageItem

_title_xpath = '//ul[@class="wp-list clearfix"]//h3/a/@href' # 各标题
_img_xpath = '//div[@id="picture"]//img' # 图片
_img_folder = '//head/title/text()' # 图片目录
_next_xpath = '//div[@id="wp_page_numbers"]/ul/li[last()-1]/a/@href' # 下一页

class MeizituSpider(scrapy.Spider):
    name = 'meizitu'
    start_urls = ['http://www.meizitu.com/a/more_1.html']

    def parse(self, response):
        self.logger.info("begin to parser %s" % response.url)

        # 查找本页的主题深入访问
        title_urls = response.xpath(_title_xpath).extract()
        for url in title_urls:
            yield response.follow(url, self.parser_pages)

        # 查找下一页继续访问
        next_url = response.xpath(_next_xpath).extract_first()
        if next_url is not None:
            yield response.follow('http://www.meizitu.com/a/' + next_url, self.parse)


    def parser_pages(self, response):
        self.logger.info("begin to parser %s" % response.url)
        # 返回图片地址
        folder = response.xpath(_img_folder).extract_first().replace(" | 妹子图", "")
        img_list = response.xpath(_img_xpath)
        for img in img_list:
            src_url = img.xpath("./@src").extract_first()
            yield ImageItem(url=src_url, name=src_url.split('/')[-1], folder=folder, page=response.url)

