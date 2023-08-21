# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TenderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    number = scrapy.Field()
    date_placed = scrapy.Field()
    date_end = scrapy.Field()
    price = scrapy.Field()
    stage = scrapy.Field()
    docs = scrapy.Field()
    law = scrapy.Field()
    law_and_supplier = scrapy.Field()
    supplier_extended = scrapy.Field()
    supplier = scrapy.Field()
    description = scrapy.Field()
    customer = scrapy.Field()
    platform = scrapy.Field()
    platform_url = scrapy.Field()
    deadline = scrapy.Field()
    date_summing_up = scrapy.Field()
    contract_enforcement = scrapy.Field()
