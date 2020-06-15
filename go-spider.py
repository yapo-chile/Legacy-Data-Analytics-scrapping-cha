from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from cha.spiders.cha_dealers_spider import CHASpider

process = CrawlerProcess(get_project_settings())
process.crawl(CHASpider)
process.start()