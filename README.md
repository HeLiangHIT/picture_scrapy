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
2. 在多个电脑上分别 `git clone 本项目地址`， 然后到工厂目录下使用 `pip install -r requirement.tx` 或者使用 pipenv
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
```
scrapy crawl jiandan &
python picture_downloader.py --key='picture:jiandan' --dir='/Users/heliang/Pictures/scrapy' --empty_exit=0 --concurrency=20

scrapy crawl meizitu &
python picture_downloader.py --key='picture:meizitu' --dir='/Users/heliang/Pictures/scrapy/meizitu' --empty_exit=0 --concurrency=20

scrapy crawl mzitu &
python picture_downloader.py --key='picture:mzitu' --dir='/Users/heliang/Pictures/scrapy/mzitu' --empty_exit=0 --concurrency=20

scrapy crawl mmjpg &
python picture_downloader.py --key='picture:mmjpg' --dir='/Users/heliang/Pictures/scrapy/mmjpg' --empty_exit=0 --concurrency=20
```



#### todo

1. 由于当前使用 scrapy 爬取较慢（相比自己编写的异步爬虫而言却是慢了挺多），而且爬取的几个网站都没有遇到封锁ip的现象，所以未实现ip池中间件，如果后期有需要可以增加。
2. 多线程异步下载器下载时由于速度太快很可能被封ip，所以代理ip池还是有必要增加的。偶尔会下载不全，为啥？
3. 依赖库文件的生成。


#### 参与贡献

1. Fork 本项目
2. 新建 Feat_xxx 分支
3. 提交代码
4. 新建 Pull Request
