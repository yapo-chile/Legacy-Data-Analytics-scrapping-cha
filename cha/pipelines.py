# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exporters import CsvItemExporter
from datetime import datetime
from cha.items import CarItem, DealerItem

class ExportPipeline(object):
    def open_spider(self, spider):
        timestamp = datetime.today().strftime('%Y%m%d%H%M')

        dealersFile = open('cha_{}_dealers.csv'.format(timestamp), 'wb')
        self.dealersExporter = CsvItemExporter(dealersFile)
        self.dealersExporter.fields_to_export = ['id', 'nombre', 'num_avisos', 'direccion', 'telefono', 'url']
        self.dealersExporter.start_exporting()

        carsFile = open('cha_{}_cars.csv'.format(timestamp), 'wb')
        self.carsExporter = CsvItemExporter(carsFile)
        self.carsExporter.fields_to_export = ['id_seller', 'titulo', 'precio', 'kilometros', 'url']
        self.carsExporter.start_exporting()

    def close_spider(self, spider):
        self.dealersExporter.finish_exporting()
        self.carsExporter.finish_exporting()

    def process_item(self, item, spider):
        if isinstance(item, DealerItem):
            self.dealersExporter.export_item(item)
        
        if isinstance(item, CarItem):
            self.carsExporter.export_item(item)

        return item
