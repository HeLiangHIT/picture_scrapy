# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class ImageItem(scrapy.Item):
    name = scrapy.Field()
    url = scrapy.Field()
    folder = scrapy.Field()
    page = scrapy.Field()


