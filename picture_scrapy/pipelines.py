# -*- coding: utf-8 -*-

import logging
import redis, json

class RedisListPipeline(object):
    def __init__(self, ip='127.0.0.1', port=6379, key="picture:mm"):
        self.ip = ip
        self.port = port
        self.key = key
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(ip=crawler.settings.get('REDIS_IP'), port=crawler.settings.get('REDIS_PORT'))
    
    def open_spider(self, spider):
        self.db = redis.StrictRedis(host=self.ip, port=self.port, password=None, decode_responses=True)
    
    def process_item(self, item, spider):
        logging.info("item %s saved." % item)
        val = json.dumps(dict(item))
        self.db.lpush(self.key, val) # use rpop(self.key)/lpop(self.key)
    
    def close_spider(self, spider):
        pass



