import scrapy
import logging

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from scrapy.loader import ItemLoader

class CHASpider(scrapy.Spider):
    name = "cha"
    allowed_domains = ['www.chileautos.cl']
    url_base = 'https://www.chileautos.cl/vehiculos/'

    def start_requests(self):
        yield scrapy.Request(
            #url='/' + operacion, 
            url = self.url_base, #TEST
            callback=self.parseListing, 
            errback=self.errback,
            cb_kwargs=dict(depth=0),
            dont_filter=True,
        )
    
    def parseListing(self, response, depth):
        if response.xpath('//h1[@class="title"]/text()').get() is None:
            logging.warning("Retrying listing: " + response.url)
            yield response.request.replace(dont_filter=True) # Retry
        else:
            quantity_results = int(response.xpath('//h1[@class="title"]/text()').get().split(' ')[0].replace(',',''))
            logging.debug("Visiting: " + response.url + " (Qty: " + str(quantity_results) + ")" + "(Depth: " + str(depth) + ")")

            if quantity_results > 1000: #Chileautos muestra un maximo de 1000 avisos por listado, por lo que debemos seguir aplicando filtros.
                yield from self.divideNConquer(response, depth, quantity_results)
            else:
                yield from self.parseInnerListing(response)
    
    def divideNConquer(self, response, depth, qty):
        if depth == 0:  # Navigate by tipo vehículo (auto, aereos, buses, etc.)
            logging.info("Total ads: " + str(qty))

            if response.xpath('//div[@data-aspect-name="tipovehículo"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                for url in response.xpath('//div[@data-aspect-name="tipovehículo"]/ul/li/a/@href'):
                    yield response.follow(
                        url=url.get(),
                        callback=self.parseListing,
                        errback=self.errback,
                        cb_kwargs=dict(depth=1),
                        dont_filter=True,
                    )
        elif depth == 1: # Navegamos por tipo de categoria (Anfibio, bote, etc.)
            if response.xpath('//div[@data-aspect-name="tipocategoria"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                for url in response.xpath('//div[@data-aspect-name="tipocategoria"]/ul/li/a/@href'):
                    yield response.follow(
                        url=url.get(),
                        callback=self.parseListing,
                        errback=self.errback,
                        cb_kwargs=dict(depth=2),
                        dont_filter=True,
                    )
        elif depth == 2: # Navegamos por marca (BMW, Toyota, etc.)
            if response.xpath('//div[@data-aspect-name="marca"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                for url in response.xpath('//div[@data-aspect-name="marca"]/ul/li/a/@href'):
                    yield response.follow(
                        url=url.get(),
                        callback=self.parseListing,
                        errback=self.errback,
                        cb_kwargs=dict(depth=3),
                        dont_filter=True,
                    )
        elif depth == 3: # Navegamos por modelo (Yaris, Montero, Spark, Morning, etc.)
            if response.xpath('//div[@data-aspect-name="modelo"]').get() is None: # Pasamos el siguiente nivel si el filtro no existe
                depth += 1
                yield from self.divideNConquer(response, depth, qty)
            else:
                for url in response.xpath('//div[@data-aspect-name="modelo"]/ul/li/a/@href'):
                    yield response.follow(
                        url=url.get(),
                        callback=self.parseListing,
                        errback=self.errback,
                        cb_kwargs=dict(depth=4),
                        dont_filter=True,
                    )
        else:
            logging.warning("Still too big: " + response.url + " (" + str(qty) + ")" + "(" + str(depth) + ")")
    
    def parseInnerListing(self, response):
        
        next_page = response.xpath('//nav[@class="pager"]/ul/li/a[@class="page-link next "]/@href').get()
        if next_page is not None:
            yield response.follow(
                url=next_page, 
                callback=self.parseInnerListing,
                errback=self.errback,
                dont_filter=True,
            )
    
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