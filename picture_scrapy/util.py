# -*- coding: utf-8 -*-

def trimurl2filename(url):
    # http://ww3.sinaimg.cn/mw600/aaa.jpg -> aaa.jpg
    filename = url.split('/')[-1]
    suffix = filename.split('.')[-1]
    return filename, suffix

