#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-10-13 23:25:04
# @Author  : He Liang (heianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT


from downloader_async import FileDownloader, ProgressBar
import redis, json, os, logging, trio


_SAVE_DIR = "%s/Pictures/scrapy/" % os.path.expanduser('~') # os.environ['HOME']
logging.basicConfig(level=logging.DEBUG, 
    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


_db = redis.StrictRedis(host='127.0.0.1', port=6379, password=None, decode_responses=True)
def get_picture_item(key='picture:mmjpg'):
    # {"url": "http://www.aaa.com/a/a.jpg", "name": "a.jpg", "folder": "a"}
    data = _db.spop(key) # await ?
    return json.loads(data) if data is not None else None


_downloader = FileDownloader()
async def download_item(item):
    header = {"Host": item['url'].split('/')[3]}
    isok, file_name, file_size = await _downloader.download(item['url'], 
        _SAVE_DIR + item['folder'],
        progress_callback = ProgressBar("download %s..." % item['name']), 
        headers = header)
    return isok


async def main():
    while True:
        item = get_picture_item()
        logging.debug(f"downloading {item['name']} from {item['url']} to {item['folder']}...")
        if item is None:
            break
        isok = await download_item(item)
        if isok:
            logging.info(f"{item['name']} downloaded from {item['url']} to {item['folder']}")
        else:
            logging.error(f"download {item['name']} from {item['url']} FAIL!")

    logging.info("picture download over")


if __name__ == '__main__':
    trio.run(main)







