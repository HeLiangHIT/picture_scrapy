# -*- coding: utf-8 -*-
import re


def trimurl2filename(url):
    # http://ww3.sinaimg.cn/mw600/aaa.jpg -> aaa.jpg
    filename = url.split('/')[-1]
    suffix = filename.split('.')[-1]
    return filename, suffix


def filter_url_by_patterns(url, patterns):
    # 判断 url 是否包含 patterns 定义的正则匹配规则，这里主要用于在下载器中间件中过滤爬虫
    for p in patterns:
        if re.search(p, url) is not None:
            return True
    return False
    




