#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-10-13 23:25:04
# @Author  : He Liang (heianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT

from faker import Faker
import redis, json, os, logging, trio, asks, random
asks.init('trio')


logging.basicConfig(level=logging.INFO, 
                format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

_db = redis.StrictRedis(host='127.0.0.1', port=6379, password=None, decode_responses=True)
def get_picture_item(key='picture:mmjpg'):
    # {"url": "http://www.aaa.com/a/a.jpg", "name": "a.jpg", "folder": "a"}
    data = _db.spop(key) # await ?
    return json.loads(data) if data is not None else None

def is_picture_exists(key='picture:mmjpg'):
    return _db.scard(key)

def save_failed_item(key='picture:mmjpg', item=None):
    if isinstance(item, dict):
        _db.sadd("%s:failed" % key, json.dumps(item))
        logging.info(f"{item} was saved in redis]key={key}:failed.")


async def download_picture(url, referer=None, res_time=10):
    if res_time <= 0: # 重试超过了次数
        return None
    header = {"Host": url.split('/')[3], 
              "Referer": referer if referer else url, 
              "User-Agent":Faker(locale='zh').chrome()}
    res = await asks.get(url, headers=dict(**header, **_HEADERS), timeout=60, retries=5)
    if res.status_code not in [200, 202]:
        await trio.sleep(random.randint(3, 10))
        return await download_picture(url, res_time-1)
    return res.content


_SAVE_DIR = "%s/Pictures/scrapy/" % os.path.expanduser('~') # os.environ['HOME']
async def save_item(folder, name, content):
    _folder = os.path.join(_SAVE_DIR, folder)
    os.system("mkdir -p '%s'" % _folder)
    file_path = os.path.join(_folder, name)
    fd = await trio.open_file(file_path, 'wb')
    await fd.write(content)
    await fd.aclose()


async def main():
    async with trio.CapacityLimiter(10):
        while is_picture_exists():
            item = get_picture_item()
            logging.info(f"downloading {item['name']} from {item['url']} to {item['folder']}...")
            content = await download_picture(item['url'], item.get('page', None))
            if content is not None:
                await save_item(item['folder'], item['name'], content)
                logging.info(f"download {item['name']} from {item['url']} to {item['folder']} succ.")
            else:
                save_failed_item(item)
                logging.error(f"download {item['name']} from {item['url']} to {item['folder']} FAIL!")

    logging.info("picture download over")


if __name__ == '__main__':
    trio.run(main)







