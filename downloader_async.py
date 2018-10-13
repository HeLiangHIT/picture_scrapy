#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-08-12 23:07:50
# @Author  : He Liang (heianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT

import json, os, time
import trio, asks
asks.init('trio')

_HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Connection": "keep-alive",
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0"} # Applies-to all requests


def text_progress(percent):
    '''打印文字显示进度条'''
    print('download %.2f%%' % (percent * 100))

class ProgressBar(object):
    """下载显示进度条
    pip install progressbar2
    https://github.com/WoLpH/python-progressbar
    """
    def __init__(self, msg=''):
        super(ProgressBar, self).__init__()
        # print(msg)
        import progressbar
        widgets=[
            '(', progressbar.Percentage(), ')',
            progressbar.Bar(),
            '[', progressbar.Timer(), ']',
        ]
        self.bar = progressbar.ProgressBar(max_value=100, redirect_stdout=True, widgets=widgets)
        self.bar.start()
    def __call__(self, percent):
        percent = 1 if percent > 0.99 else percent
        self.bar.update(percent * 100)


import attr
@attr.s(hash=True)
class DownloadItem(object):
    ''' 保存基本下载内容，并执行下载文件的保存+进度控制
    >>> print(DownloadItem('url', 'max_len', 'file_name', 'progress_callback'))
    DownloadItem(url='url', max_len='max_len', file_name='file_name', progress_callback='progress_callback')
    '''
    url = attr.ib(repr=True, cmp=True, hash=True)
    max_len = attr.ib(repr=True, cmp=False, hash=False)
    file_name = attr.ib(repr=True, cmp=False, hash=False)
    progress_callback = attr.ib(default=None, repr=True, cmp=False, hash=False)
    fd = attr.ib(default=None, repr=False, cmp=False, hash=False)
    progress = attr.ib(default=0, repr=False, cmp=False, hash=False)
    
    def add_progress(self, start, end):
        self.progress += (end - start)/self.max_len
        if self.progress_callback is not None:
            self.progress_callback(self.progress)

    async def open(self):
        self.lock = trio.Lock() # 加锁避免多线程同时写文件导致文件被写坏
        if self.fd is None:
            self.fd = await trio.open_file(self.file_name, 'wb')
        return self

    async def save(self, start, content):
        if not self.fd or not self.lock:
            return False
        async with self.lock:
            await self.fd.seek(start)
            await self.fd.write(content)
        return True

    async def close(self):
        if self.fd:
            await self.fd.aclose()
            self.fd = None
        return self


class FileDownloader(object):
    """文件下载器--多线程"""
    def __init__(self, offset=2**16, timeout=20, concurrency=10, retries=3):
        super(FileDownloader, self).__init__()
        self.offset = offset
        self.timeout = timeout
        self.concurrency = concurrency
        self.retries = retries

    async def get_content_len(self, url, headers={}):
        head = await asks.head(url, headers=dict(headers, **_HEADERS), retries=self.retries)
        content_len = int(head.headers['Content-Length'])
        return content_len

    async def _get_ranges(self, url, headers={}):
        '''获取内容的长度，以及分段下载的分段起止坐标'''
        head = await asks.head(url, headers=headers, retries=self.retries)
        content_len = int(head.headers['Content-Length']) # content-length
        ranges = [(start, start + self.offset if start + self.offset < content_len else content_len)
                    for start in range(0, content_len, self.offset)]
        return content_len, ranges

    async def _download(self, info, result):
        '''分段下载线程主函数
        info = (url, start, end, header, item)'''
        url, start, end, headers, item = info
        res = await asks.get(url, headers=dict({'Range':'Bytes=%d-%d' % (start, end)}, **headers, **_HEADERS), 
            timeout=self.timeout, retries=self.retries)
        # print(res, res.headers['Content-Range'])
        if res.status_code not in [206, 200, 202]:
            result.append(False)
        if not await item.save(start, res.content):
            result.append(False)
        item.add_progress(start, end)
        result.append(True)

    async def download(self, url, file=None, progress_callback=text_progress, headers={}):
        '''执行下载操作
        >>> beauty = 'http://fm.shiyunjj.com/2018/1493/4ia1.jpg'
        >>> header = {"Referer": "http://fm.shiyunjj.com"} # imzitu need Preferer header for safety
        >>> ok, filename, _ = trio.run(FileDownloader(offset=2**14).download, beauty, None, text_progress, header) # doctest: +ELLIPSIS
        download 15.39%
        ...
        >>> print(ok, filename)
        True 16c01.jpg
        >>> os.remove(filename)
        '''
        suffix = url.split('/')[-1] # file_name
        file_name = file if isinstance(file, str) else suffix
        max_len, ranges = await self._get_ranges(url, headers)
        item = DownloadItem(url, max_len, file_name, progress_callback)
        result = []
        await item.open()
        async with trio.CapacityLimiter(self.concurrency):
            async with trio.open_nursery() as nursery:
                for start, end in ranges:
                    nursery.start_soon(self._download, (url, start, end, headers, item), result)
        await item.close()
        if not all(result):
            # os.remove(item.file_name)
            return (False, None, None)
        return (True, file_name, max_len)



if __name__ == '__main__':
    # import doctest
    # doctest.testmod(verbose=False)  # verbose=True shows the output
    # print('doc test run over')
    # pass
    beauty = 'http://ww3.sinaimg.cn/mw600/0073tLPGgy1fvqkepmw13j31f826yqhg.jpg'
    header = {"Referer": "http://ww3.sinaimg.cn/mw600"} # imzitu need Preferer header for safety
    ok, filename, filesize = trio.run(FileDownloader(offset=2**16).download, beauty, 'yqhg.jpg', text_progress, header)
    print(ok, filename, filesize)

