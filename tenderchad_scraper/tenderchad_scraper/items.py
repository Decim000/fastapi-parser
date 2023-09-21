# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TenderItem(scrapy.Item):
    number = scrapy.Field() # номер тендера (закупки)
    date_placed = scrapy.Field() # дата размещения тендера
    date_end = scrapy.Field() # дата окончания торгов/закупки
    price = scrapy.Field() # цена тендера
    stage = scrapy.Field() # стадия тендера (не всегда актуальна на сайте, частично фиксится в pipelines)
    docs = scrapy.Field() # словарь с названиями тендерной документации и ссылок на них
    law = scrapy.Field() # номер закона (223-ФЗ/44-ФЗ)
    law_and_supplier = scrapy.Field() # закон и способ опеределения поставщика, используется только для разбиения на соответствующие поля, если не получается собрать отдельно
    supplier_extended = scrapy.Field() # расширенное название способа определения поставщика (периодически дублирует способ определения поставщика)
    supplier = scrapy.Field() # способ определения поставщика
    description = scrapy.Field() # расширенное описание тендера
    customer = scrapy.Field() # закупщик
    platform = scrapy.Field() # название платформы, где изначально размещен тендер
    platform_url = scrapy.Field() # URL на платформу
    deadline = scrapy.Field() # срок исполнения тендера в днях
    date_summing_up = scrapy.Field() # дата подведения итогов по выбору поставщика
    contract_enforcement = scrapy.Field() # размер обеспечения исполнения контракта
    all_attached_files = scrapy.Field() # все названия документов, прилагаемых к тендеру, в т.ч. внутри архивов
