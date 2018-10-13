# -*- coding: utf-8 -*-
import scrapy, re
from picture_scrapy.items import ImageItem

_title_xpath = '//div[@class="pic"]//span[@class="title"]/a/@href' # 各标题
_img_xpath = '//div[@class="content"]//img' # 图片
_next_xpath = '//div[@class="page"]/a[last()]/@href' # 下一页图片
_last_xpath = '//div[@class="page"]//a[@class="last"]/@href' # 最后一页列表

class MmjpgSpider(scrapy.Spider):
    name = 'mmjpg'
    start_urls = ['http://www.mmjpg.com/']

    def parse(self, response):
        self.logger.info("begin to parser %s" % response.url)

        # 生成所有页面
        last_page = response.xpath(_last_xpath).extract_first()
        for x in range(2, int(last_page.split('/')[-1])):
            yield response.follow('http://www.mmjpg.com/home/%d' % x, self.parse)

        # 查找本页的主题深入访问
        title_urls = response.xpath(_title_xpath).extract()
        for url in title_urls:
            yield response.follow(url, self.parser_pages)


    def parser_pages(self, response):
        self.logger.info("begin to parser %s" % response.url)
        # 返回图片地址
        img_list = response.xpath(_img_xpath)
        for img in img_list:
            src_url = img.xpath("./@src").extract_first()
            folder = re.sub(' 第\d+张', '', img.xpath("./@alt").extract_first()) # replace 正则
            yield ImageItem(url=src_url, name=src_url.split('/')[-1], folder=folder)
        # 返回爬取下一页
        next_page = response.xpath(_next_xpath).extract_first()
        if len(next_page.split('/')) == 4:
            yield response.follow('http://www.mmjpg.com' + next_page, self.parser_pages)


