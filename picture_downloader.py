#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-10-13 23:25:04
# @Author  : He Liang (heianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT

'''
异步协程下载器：从 redis 里面连续读取图片json信息，然后使用协程下载保存到指定文件夹中。有效的json举例如下：
`{"url": "http://www.a.com/a/a.jpg", "name": "a.jpg", "folder": "a", "page":"www.a.com"}`

Usage:
  picture_download.py [--dir=dir] [--ip=ip] [--port=port] [--key=key]
  picture_download.py --version
Options:
  --dir=dir         selett picture save dir. * default: '$HOME/Pictures/scrapy/'
  --ip=ip           select redis ip. [default: '127.0.0.1']
  --port=port       select redis ip. [default: 6379]
  --key=key         select redis key. [default: 'picture:jiandan']
'''


import redis, json, os, logging, trio, asks, random
from faker import Faker # https://faker.readthedocs.io/en/master/index.html
from docopt import docopt


# 基本配置和默认参数
asks.init('trio')
logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
_SAVE_DIR = "%s/Pictures/scrapy/" % os.path.expanduser('~') # os.environ['HOME']
_KEY = 'picture:jiandan'
_IP = '127.0.0.1'
_PORT = 6379


# redis 相关操作
_db = redis.StrictRedis(host=_IP, port=_PORT, password=None, decode_responses=True)
def get_picture_item(key=_KEY):
    # {"url": "http://www.aaa.com/a/a.jpg", "name": "a.jpg", "folder": "a", "page":"www.xxx.com"}
    data = _db.spop(key) # srandmember for debug, spop for produce
    return json.loads(data) if data is not None else None

def get_picture_num(key=_KEY):
    return _db.scard(key)

def save_failed_item(key=_KEY, item=None):
    if isinstance(item, dict):
        _db.sadd("%s:failed" % key, json.dumps(item))
        logging.info(f"{item['name']} was saved in redis]key={key}:failed!")


# 异步下载器
_faker = Faker()
async def download_picture(url, referer, res_time=10):
    if res_time <= 0: # 重试超过了次数
        return None
    header = {"Referer": referer, 
              "User-Agent":_faker.chrome()}
    try:
        res = await asks.get(url, headers=header, timeout=10, retries=3)
    except trio.BrokenResourceError as e:
        logging.error(f"download from {url} fail]reson={e}!")
        await trio.sleep(0) # for scheduler
        return await download_picture(url, referer, res_time-1)
    
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
                logging.debug(f"sending {item['name']}...")
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
    _SAVE_DIR = arguments["--dir"] if arguments["--dir"] else _SAVE_DIR # 不会取doc里`*default`的值
    _IP = arguments["--ip"] if arguments["--ip"] else _IP # 默认取doc里`[default:val]`的值
    _PORT = arguments["--port"] if arguments["--port"] else _PORT
    _KEY = arguments["--key"] if arguments["--key"] else _KEY
    logging.info(f"start download from redis://{_IP}:{_PORT}/{_KEY} to {_SAVE_DIR} ...")
    trio.run(main)







