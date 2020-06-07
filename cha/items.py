# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import Compose, MapCompose, Join, TakeFirst
clean_text = Compose(MapCompose(lambda v: v.strip()), Join(), (lambda x: x.strip()))

class AdItem(scrapy.Item):
    id = scrapy.Field(output_processor=clean_text)
    titulo = scrapy.Field(output_processor=clean_text)
    url = scrapy.Field(output_processor=clean_text)
    tipo_vendedor = scrapy.Field(output_processor=clean_text)
    locacion_vendedor = scrapy.Field(output_processor=clean_text)
    precio = scrapy.Field(output_processor=clean_text)
    kilometraje = scrapy.Field(output_processor=clean_text)
    transmision = scrapy.Field(output_processor=clean_text)
    combustible = scrapy.Field(output_processor=clean_text)
    id_automotora = scrapy.Field(output_processor=clean_text)
    patente = scrapy.Field(output_processor=clean_text)

class DealerItem(scrapy.Item):
    id = scrapy.Field(output_processor=clean_text)
    nombre = scrapy.Field(output_processor=clean_text)
    telefono = scrapy.Field(output_processor=clean_text)
    direccion = scrapy.Field(output_processor=clean_text)
    num_avisos = scrapy.Field(output_processor=clean_text)
    url = scrapy.Field(output_processor=clean_text)

    def __str__(self):
        return ""

class CarItem(scrapy.Item):
    id_seller = scrapy.Field(output_processor=clean_text)
    url = scrapy.Field(output_processor=clean_text)
    titulo = scrapy.Field(output_processor=clean_text)
    precio = scrapy.Field(output_processor=Compose(clean_text, (lambda x: x.replace(".", ""))))
    kilometros = scrapy.Field(output_processor=Compose(clean_text, (lambda x: x.replace(".", ""))))
    
    def __str__(self):
        return ""
    

