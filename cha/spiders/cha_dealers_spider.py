import scrapy
import logging

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from scrapy.loader import ItemLoader
from cha.items import AdItem, DealerItem

class CHASpider(scrapy.Spider):
    name = "cha_dealers"
    allowed_domains = ['www.chileautos.cl']
    url_base = 'https://www.chileautos.cl'

    def start_requests(self):
        yield scrapy.Request(
            url = self.url_base + '/automotoras/buscar',
            callback=self.parseDealerListing, 
            errback=self.errback,
        )
    
    def parseDealerListing(self, response):
        for dealerSelector in response.xpath('//div[has-class("l-content__dealer-search-results")]//div[has-class("dealer-search-item")]'):
            urlDealer = dealerSelector.xpath('div[has-class("listing-item__header")]/a/@href').re_first(r'http://www.chileautos.cl(/[a-zA-Z0-9]+)')
            l = ItemLoader(item=DealerItem(), selector=dealerSelector)
            l.add_value('url', self.url_base + urlDealer)
            l.add_xpath('nombre', 'div[has-class("listing-item__header")]/a/h2/text()')
            dealeritem = l.load_item()

            yield response.follow(
                url=dealeritem['url'],
                callback=self.parseCarListing,
                errback=self.errback,
                cb_kwargs={'dealeritem':dealeritem},
            )

        next_page = response.xpath('//div[has-class("control--pagination")]/ul/li[has-class("pagination__btn-next")]/a/@href').get()
        if next_page is not None:
            yield response.follow(
                url=next_page, 
                callback=self.parseDealerListing,
                errback=self.errback,
                dont_filter=True,
            )
    
    def parseCarListing(self, response, dealeritem):
        l = ItemLoader(item=dealeritem, response=response)
        l.add_xpath('num_avisos','//div[has-class("l-listings__content")]/h1[has-class("page-header")]/span/text()', re='([0-9]+) vehículos en venta')
        yield l.load_item()        

    def parseCarInnerListing(self)
        
    
    def errback(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)