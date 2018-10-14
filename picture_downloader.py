#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-10-13 23:25:04
# @Author  : He Liang (heianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT

'''
异步协程下载器：从 redis 里面连续读取图片json信息，然后使用协程下载保存到指定文件夹中。有效的json举例如下：
`{"url": "http://www.a.com/a/a.jpg", "name": "a.jpg", "folder": "a", "page":"www.a.com"}`

Usage:
  picture_download.py [--dir=dir] [--ip=ip] [--port=port] [--key=key] [--empty_exit=empty_exit] [--concurrency=concurrency]
  picture_download.py --version
Options:
  --dir=dir                    select picture save dir. * default: '$HOME/Pictures/scrapy/'
  --ip=ip                      select redis ip. [default: 127.0.0.1]
  --port=port                  select redis ip. [default: 6379]
  --key=key                    select redis key. [default: picture:jiandan]
  --empty_exit=empty_exit      select if exit when redis set empty. [default: true]
  --concurrency=concurrency    select the concurrency number of downloader. [default: 20]
'''


import redis, json, os, logging, trio, asks, random
from faker import Faker # https://faker.readthedocs.io/en/master/index.html
from docopt import docopt


# 基本配置和默认参数
asks.init('trio')
logging.basicConfig(level=logging.INFO, 
                format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
_SAVE_DIR = "%s/Pictures/scrapy/" % os.path.expanduser('~') # os.environ['HOME']
_DOWNLOAD_TIMEOUT = 30
_RETRIES_TIMES = 10

# redis 相关操作
class RedisSetHelper(object):
    def __init__(self, ip='127.0.0.1', port=6379, key='picture:jiandan'):
        super(RedisSetHelper, self).__init__()
        self.db = redis.StrictRedis(host=ip, port=port, password=None, decode_responses=True)
        self.key = key

    def get_picture_item(self):
        # {"url": "http://www.aaa.com/a/a.jpg", "name": "a.jpg", "folder": "a", "page":"www.xxx.com"}
        data = self.db.srandmember(self.key) # srandmember for debug, spop for produce
        return json.loads(data) if data is not None else None

    def get_picture_num(self):
        return self.db.scard(self.key)

    def save_failed_item(self, item=None):
        if isinstance(item, dict):
            self.db.sadd("%s:failed" % self.key, json.dumps(item))
            logging.info(f"{item['name']} was saved in redis]key={self.key}:failed!")


# 异步下载/保存器
class AsyncDownloader(object):
    def __init__(self, save_dir=_SAVE_DIR):
        super(AsyncDownloader, self).__init__()
        self.faker = Faker()
        self.save_dir = save_dir
        
    async def download_picture(self, url, referer, res_time=_RETRIES_TIMES):
        if res_time <= 0: # 重试超过了次数
            return None
        header = {"Referer": referer, 
                  "User-Agent":self.faker.chrome()}
        try:
            res = await asks.get(url, headers=header, timeout=_DOWNLOAD_TIMEOUT, retries=3)
        except (trio.BrokenResourceError, trio.TooSlowError, asks.errors.RequestTimeout) as e:
            logging.error(f"download from {url} fail, timeout or resource error!")
            await trio.sleep(0) # for scheduler
            return await self.download_picture(url, referer, res_time-1)
        
        if res.status_code not in [200, 202]:
            logging.warn(f"download from {url} fail]response={res}")
            await trio.sleep(random.randint(3, 10))
            return await self.download_picture(url, referer, res_time-1)
        return res.content

    # 异步文件保存
    async def save_item(self, folder, name, content):
        _folder = os.path.join(self.save_dir, folder)
        os.system("mkdir -p '%s'" % _folder)
        file_path = os.path.join(_folder, name)
        fd = await trio.open_file(file_path, 'wb')
        await fd.write(content)
        await fd.aclose()


# 生产-消费 流程控制
async def download_items(_receiver, downloader, redisHelper):
    async with _receiver:
        while True:
            item = await _receiver.receive()
            if item is None:
                return # 结束下载
            logging.debug(f"downloading {item['url']}...")
            content = await downloader.download_picture(item['url'], item.get('page', item['url']))
            if content is not None:
                await downloader.save_item(item['folder'], item['name'], content)
                logging.info(f"download {item['name']} from {item['url']} to {item['folder']} succ")
            else:
                redisHelper.save_failed_item(item)
                logging.error(f"download {item['name']} from {item['url']} to {item['folder']} FAIL!")

async def get_items(_sender, redisHelper, empty_exit):
    async with _sender:
        while True:
            item = redisHelper.get_picture_item()
            if item:
                logging.debug(f"sending {item['name']}...")
                await _sender.send(item)
            elif empty_exit.lower() in ['false', '0']: # do not exit, wait for crawler set val
                total_num = redisHelper.get_picture_num()
                logging.info(f"there are {total_num} pictures in set]key={redisHelper.key}")
                await trio.sleep(random.randint(3, 10))
                continue
            else:
                logging.info(f"stop the downloader since not items got!")
                await _sender.send(None)
                return # 结束获取


async def main(save_dir, ip, port, key, empty_exit, concurrency):
    logging.info(f"start download from redis://{ip}:{port}/{key} to {save_dir} with {concurrency} concurrency ...")
    redisHelper = RedisSetHelper(ip, port, key)
    downloader = AsyncDownloader(save_dir)
    total_num = redisHelper.get_picture_num()
    logging.info(f"there are {total_num} pictures in set]key={redisHelper.key}")

    async with trio.open_nursery() as nursery:
        _sender, _receiver = trio.open_memory_channel(concurrency) # 并行数量
        nursery.start_soon(get_items, _sender, redisHelper, empty_exit)
        nursery.start_soon(download_items, _receiver, downloader, redisHelper)

    logging.info("picture downloads over")


if __name__ == '__main__':
    arguments = docopt(__doc__, version="picture_downloader 0.0.1")
    save_dir = arguments["--dir"] if arguments["--dir"] else _SAVE_DIR # 不会取doc里`*default`的值
    ip = arguments["--ip"] # 默认取doc里`[default:val]`的值
    port = int(arguments["--port"])
    key = arguments["--key"]
    empty_exit = arguments["--empty_exit"]
    concurrency = int(arguments["--concurrency"])

    trio.run(main, save_dir, ip, port, key, empty_exit, concurrency)







