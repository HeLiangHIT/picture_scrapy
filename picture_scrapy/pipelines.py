# -*- coding: utf-8 -*-

import redis, json

class RedisSetPipeline(object):
    def __init__(self, ip='127.0.0.1', port=6379, key="picture:mm"):
        self.ip = ip
        self.port = port
        self.key = key

    @classmethod
    def from_crawler(cls, crawler):
        return cls(ip=crawler.settings.get('REDIS_IP'), port=crawler.settings.get('REDIS_PORT'))
    
    def open_spider(self, spider):
        self.db = redis.StrictRedis(host=self.ip, port=self.port, password=None, decode_responses=True)
        self.db.delete(self.key)
        spider.logger.info("redis connected with key=%s" % self.key)
    
    def process_item(self, item, spider):
        spider.logger.info("item %s saved." % item['url'])
        val = json.dumps(dict(item))
        self.db.sadd(self.key, val) # use spop(self.key), scard(self.key), del(self.key)
    
    def close_spider(self, spider):
        pass



