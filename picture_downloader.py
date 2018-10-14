#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-10-13 23:25:04
# @Author  : He Liang (heianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT

'''
异步协程下载器： 从redis里面读取类似
`{"url": "http://www.aaa.com/a/a.jpg", "name": "a.jpg", "folder": "a", "page":"www.xxx.com"}`
的图片信息协程下载。

Usage:
  picture_download.py [--key=key] [--dir=dir]
  picture_download.py --version
Options:
  --key=key         select redis key. [default: 'picture:jiandan']
  --dir=dir         picture save dir. *default: '$HOME/Pictures/scrapy/'

'''


import redis, json, os, logging, trio, asks, random
from faker import Faker
from docopt import docopt

# 基本配置和默认参数
asks.init('trio')
logging.basicConfig(level=logging.INFO, 
                format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
_SAVE_DIR = "%s/Pictures/scrapy/" % os.path.expanduser('~') # os.environ['HOME']
_KEY = 'picture:jiandan'


# redis 相关操作
_db = redis.StrictRedis(host='127.0.0.1', port=6379, password=None, decode_responses=True)
def get_picture_item(key=_KEY):
    # {"url": "http://www.aaa.com/a/a.jpg", "name": "a.jpg", "folder": "a", "page":"www.xxx.com"}
    data = _db.spop(key) # await ?
    return json.loads(data) if data is not None else None

def get_picture_num(key=_KEY):
    return _db.scard(key)

def save_failed_item(key=_KEY, item=None):
    if isinstance(item, dict):
        _db.sadd("%s:failed" % key, json.dumps(item))
        logging.info(f"{item['name']} was saved in redis]key={key}:failed!")


# 异步下载器
async def download_picture(url, referer, res_time=10):
    if res_time <= 0: # 重试超过了次数
        return None
    header = {"Referer": referer, 
              "User-Agent":Faker(locale='zh').chrome()}
    res = await asks.get(url, headers=header)
    if res.status_code not in [200, 202]:
        logging.warn(f"download from {url} fail]response={res}")
        await trio.sleep(random.randint(3, 10))
        return await download_picture(url, referer, res_time-1)
    return res.content


# 异步文件保存
async def save_item(folder, name, content):
    _folder = os.path.join(_SAVE_DIR, folder)
    os.system("mkdir -p '%s'" % _folder)
    file_path = os.path.join(_folder, name)
    fd = await trio.open_file(file_path, 'wb')
    await fd.write(content)
    await fd.aclose()


# 生产-消费 流程控制
async def download_items(_receiver):
    async with _receiver:
        while True:
            item = await _receiver.receive()
            if item is None:
                return # 结束下载
            logging.info(f"downloading {item['name']}...")
            content = await download_picture(item['url'], item.get('page', item['url']))
            if content is not None:
                await save_item(item['folder'], item['name'], content)
                logging.info(f"download {item['name']} from {item['url']} to {item['folder']} succ")
            else:
                save_failed_item(item)
                logging.error(f"download {item['name']} from {item['url']} to {item['folder']} FAIL!")

async def get_items(_sender):
    async with _sender:
        while True:
            item = get_picture_item()
            if item:
                logging.info(f"sending {item['name']}...")
                await _sender.send(item)
            else:
                logging.warn(f"sending None to finish the downloader!")
                await _sender.send(None)
                return # 结束获取


async def main():
    total_num = get_picture_num()
    logging.info(f"there are {total_num} pictures in set]key={_KEY}")
    async with trio.open_nursery() as nursery:
        _sender, _receiver = trio.open_memory_channel(5)
        nursery.start_soon(get_items, _sender)
        nursery.start_soon(download_items, _receiver)
    logging.info("picture download over")


if __name__ == '__main__':
    arguments = docopt(__doc__, version="picture_downloader 0.0.1")
    _SAVE_DIR = arguments["--dir"] if arguments["--dir"] else _SAVE_DIR
    _KEY = arguments["--key"] if arguments["--key"] else _KEY
    trio.run(main)







