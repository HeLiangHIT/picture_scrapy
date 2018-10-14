# picture_scrapy

#### 项目介绍
使用 scrapy 实现的图片爬取框架，融合了 UserAgentMiddleware/ChromeDownloaderMiddleware 中间件，RedisSetPipeline 管道用于将爬取到的图片保存到redis的set类型中，另外提供一个多线程异步下载器从redis中依次取出图片地址进行批量下载并保存。

#### 软件架构

实现了四个美女图片的爬虫：
+ http://jandan.net/ooxx ： [./picture_scrapy/spiders/jandan_spider.py](./picture_scrapy/spiders/jandan_spider.py)  `scrapy crawl jiandan`
+ http://www.mzitu.com/all/： [./picture_scrapy/spiders/mzitu_spider.py](./picture_scrapy/spiders/mzitu_spider.py)  `scrapy crawl mzitu`
+ http://www.meizitu.com/： [./picture_scrapy/spiders/meizitu_spider.py](./picture_scrapy/spiders/meizitu_spider.py)  `scrapy crawl meizitu`
+ http://www.mmjpg.com/： [./picture_scrapy/spiders/mmjpg_spider.py](./picture_scrapy/spiders/mmjpg_spider.py) `scrapy crawl mmjpg`

这样做的优势是"支持分布式爬取 + 分布式下载"，比如我就使用 mac 爬取图片地址，然后用 windows 连上移动硬盘下载图片， win/mac 搭配，干活不累。如果有更多电脑的话可以更好的配合。




#### 安装教程 && 使用说明

1. 在某台机器上启动 `redis-server path/to/redis.conf` 注意配置中注释掉 `bind 127.0.0.1 ::1`
2. 在多个电脑上分别 `git clone 本项目地址`， 然后到工厂目录下使用 `pip install -r requirement.txt` 或者使用 `pipenv shell`
3. 在 settings.py 中设置正确的 `REDIS_IP` 和 `REDIS_PORT` 参数。
4. 分别使用 `scrapy crawl xxx` 爬取指定的网站
5. 分别使用 `python picture_downloader.py --key='xxx' --dir='xxx'` 下载指定网站的图片，更多参数`python picture_downloader.py --help`：
```
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
```
example of mine: 
```sh
function start_crawl(){
    name=$1
    rm -f log/name.log
    scrapy crawl ${name} &
    sleep 2 && python picture_downloader.py --key=picture:${name} --dir=/Users/heliang/Pictures/scrapy/${name} --empty_exit=0 --concurrency=20
}
function stop_crawl(){
    name=$1
    while [ $(ps -ef | grep "scrapy crawl ${name}" | grep -v grep | wc -l) -ge 1 ]; do
        ps -ef | grep "scrapy crawl ${name}" | awk '{print $2}' | xargs kill # 停止爬虫
        sleep 1
    done
}
function clear_all(){
    while [ $(ps -ef | grep "scrapy crawl" | grep -v grep | wc -l) -ge 1 ]; do
        ps -ef | grep 'scrapy crawl' | awk '{print $2}' | xargs kill # 停止所有爬虫
    done
    while [ $(ps -ef | grep "chromedriver" | grep -v grep | wc -l) -ge 1 ]; do
        ps -ef | grep chromedriver | awk '{print $2}' | xargs kill -9 # 清理后台可能残留的 chromedriver 进程
    done
    rm -f log/*.log
}

start_crawl jiandan # meizitu mzitu mmjpg
```



#### todo

1. 代理ip： 当前没有遇到封锁ip的现象，所以未实现ip池，如果后期有需要可以增加。
2. 下载文件去重复功能，发现本地已经存在的文件就不再下载了。 -- done
3. 爬取网页去重复功能，爬取过的网页就不再爬了（某些主页列表例外） - 即使重启机器/爬虫，如何实现？ -- 使用`RedisCrawlSpider`？


#### 参与贡献

1. Fork 本项目
2. 新建 Feat_xxx 分支
3. 提交代码
4. 新建 Pull Request
