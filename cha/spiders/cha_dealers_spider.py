import scrapy
import logging
import copy

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from scrapy.loader import ItemLoader
from cha.items import CarItem, DealerItem

class CHASpider(scrapy.Spider):
    name = "cha_dealers"
    allowed_domains = ['www.chileautos.cl']
    url_base = 'https://www.chileautos.cl'

    scrap_patentes = False

    def start_requests(self):
        yield scrapy.Request(
            url = self.url_base + '/automotoras/buscar',
            callback=self.parseDealerListing, 
            errback=self.errback,
        )
    
    def parseDealerListing(self, response):
        for dealerSelector in response.xpath('//div[has-class("l-content__dealer-search-results")]//div[has-class("dealer-search-item")]'):
            urlDealer = dealerSelector.xpath('div[has-class("listing-item__header")]/a/@href').re_first(r'http://www.chileautos.cl(/[a-zA-Z0-9-_%!]+)')

            l = ItemLoader(item=DealerItem(), selector=dealerSelector)
            l.add_value('url', self.url_base + urlDealer)
            l.add_xpath('nombre', 'div[has-class("listing-item__header")]/a/h2/text()')
            l.add_xpath('telefono', './/div[has-class("dealer-search-item__details")]//li[i[has-class("zmdi-phone")]]/small/text()')
            l.add_xpath('id', './/div[has-class("dealer-search-item__details")]//div[ul/li/i[has-class("zmdi-phone")]]/@id')
            l.add_xpath('direccion', './/div[has-class("dealer-search-item__details")]//small[strong/i[has-class("zmdi-map")]]/text()')
            dealerItem = l.load_item()

            yield response.follow(
                url=dealerItem['url'],
                callback=self.parseCarListing,
                errback=self.errback,
                cb_kwargs={'dealerItem':dealerItem},
            )

        next_page = response.xpath('//div[has-class("control--pagination")]/ul/li[has-class("pagination__btn-next") and not(has-class("disabled"))]/a/@href').get()
        if next_page is not None:
            yield response.follow(
                url=next_page, 
                callback=self.parseDealerListing,
                errback=self.errback,
            )
    
    def parseCarListing(self, response, dealerItem):
        num_avisos = response.xpath('//div[has-class("l-listings__content")]/h1[has-class("page-header")]/span/text()').re_first(r'([0-9]+) vehículos en venta')
        dealerItem['num_avisos'] = num_avisos or 0

        yield dealerItem
        yield from self.parseInnerCarListing(response, dealerItem['id'])


    def parseInnerCarListing(self, response, id_seller):
        for carSelector in response.xpath('//div[has-class("search-listings")]/div[has-class("search-listings__items")]/div[has-class("listing-item")]'):
            urlCar = carSelector.xpath('div[has-class("listing-item__header")]/a/@href').get()

            l = ItemLoader(item=CarItem(), selector=carSelector)
            l.add_value('id_seller', id_seller)
            l.add_xpath('id', 'div[has-class("listing-item__body")]/div[has-class("listing-item__carousel")]/@id', re='carousel--(CL-AD-[0-9]+)')
            l.add_value('url', self.url_base + urlCar)
            l.add_xpath('titulo', 'div[has-class("listing-item__header")]/a/h2/text()')
            l.add_xpath('precio', './/div[has-class("listing-item__price")]/p/text()', re='\$ ([0-9.]+)')
            l.add_xpath('kilometros', './/ul[has-class("listing-item__features")]/li[span/text()="Kilómetros"]/text()', re='([0-9.]+) kms')
            carItem = l.load_item()

            if self.scrap_patentes:
                yield response.follow(
                    url= "https://www.chileautos.cl/autofact/" + carItem['id'].lower(),
                    callback=self.parseAutofact,
                    errback=self.errback,
                    cb_kwargs={'carItem':carItem},
                )
            else:
                yield carItem

        next_page = response.xpath('//div[has-class("control--pagination")]/ul/li[has-class("pagination__btn-next") and not(has-class("disabled"))]/a/@href').get()
        if next_page is not None:
            yield response.follow(
                url=next_page, 
                callback=self.parseInnerCarListing,
                errback=self.errback,
                cb_kwargs={'id_seller':id_seller},
            )
        
    def parseAutofact(self, response, carItem):
        l = ItemLoader(item=carItem, response=response)
        l.add_xpath('patente', '//input[@id="patente"]/@value')
        yield l.load_item()
        
    
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