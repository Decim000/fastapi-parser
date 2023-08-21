import requests
import scrapy
import logging
import re

from tenderchad_scraper.items import TenderItem
from tenderchad_scraper.saver_service import FileSaver
from tenderchad_scraper.utils import handle_bytes
from tenderchad_scraper.title_handler import rename_title


class ZakupkiSpider(scrapy.Spider):
    name = "ZakupkiSpider"

    # def __init__(self, dynamic_value=None, *args, **kwargs):
    #     super(ZakupkiSpider, self).__init__(*args, **kwargs)
    #     self.dynamic_value = dynamic_value

    # def start_requests(self):
    #     url = f"https://https://zakupki.gov.ru/epz/order/extendedsearch/results.html?{self.dynamic_value}"  # Используйте dynamic_value в ссылке
    #     logger = logging.getLogger('spam_application')
    #     logger.setLevel(logging.DEBUG)
    #     # create file handler which logs even debug messages
    #     fh = logging.FileHandler('spam.log')
    #     fh.setLevel(logging.DEBUG)
    #     logger.addHandler(fh)
    #     logger.info(url)
    #     yield scrapy.Request(url, self.parse)

    def parse(self, response):
        # Ваш код для обработки ответа
        __URL_BASE = "https://zakupki.gov.ru"
        logging.info('в поисках тендеров')
        headers = response.css("div.search-registry-entry-block.box-shadow-search-input")
        if headers:
            
            for header in headers:
                tender = TenderItem()
                try:
                    # tender['number'] = header.css('div.registry-entry__header-mid__number').css('a *::text').get()
                    number = header.xpath('//div[@class="registry-entry__header-mid__number"]/*//text()[normalize-space()]').getall()
                    if type(number) is list:
                        tender['number'] = ''.join(number)
                    else:
                        tender['number'] = number
                except:
                    tender['number'] = None
                
                try:
                    tender['date_placed'] = header.xpath("//div[contains(text(), 'Размещено')]/following-sibling::div[1]/text()").get()
                except:
                    tender['date_placed'] = None
                
                try:
                    tender['date_end'] = header.xpath("//div[contains(text(), 'Окончание подачи заявок')]/following-sibling::div[1]/text()").get()
                except:
                    tender['date_end'] = None
                
                try:
                    tender['price'] = header.css('div.price-block__value::text').get()
                except:
                    tender['price'] = 0

                try:
                    tender['stage'] = header.css('div.registry-entry__header-mid__title.text-normal::text').get()
                except:
                    tender['stage'] = 'Закупка отменена'

                try:
                    tender['docs'] = header.css("div.registry-entry__header-mid__number").css('a::attr(href)').extract()[0]
                except:
                    tender['docs']=''
                # logging.info('tender has info -')
                # logging.info(tender)

                try:
                    law = header.css("div.col-9.p-0.registry-entry__header-top__title.text-truncate::text").get()
                    tender['law'] = re.search(r'\d+-ФЗ', law.strip()).group(0)
                except:
                    tender['law'] = None
                
                if tender['law'] is not None:
                    try:
                        tender['supplier_extended']  = law.replace(tender['law'], "").replace('\n', '').strip()
                        
                    except:
                        pass

                
                if tender['law'] == "44-ФЗ":
                    request = scrapy.Request(url=__URL_BASE+tender['docs'], callback=self.parse_fullpage_44)
                    request.meta['tender'] = tender
                    yield request

                if tender['law'] == "223-ФЗ":
                    request = scrapy.Request(url=__URL_BASE+tender['docs'], callback=self.parse_fullpage_223)
                    request.meta['tender'] = tender
                    yield request


    def parse_fullpage_44(self, response):

        tender = response.meta.get('tender')
        try:
            if not tender.get('law'):
                tender['law'] = response.css('div.cardMainInfo__title.d-flex.text-truncate::text').get()
                if tender['law'] is None:
                    raise Exception
        except:
            tender['law_and_supplier'] = response.css('div.registry-entry__header-top__title::text').get()

        if not tender.get('law_and_supplier'):
            tender['supplier'] = response.css('span.cardMainInfo__title.distancedText.ml-1::text').get()

        try:
            tender['description'] = response.xpath("//span[contains(text(), 'Объект закупки')]/following-sibling::span[1]/text()").get()
            if tender['description'] is None:
                tender['description'] = response.xpath("//div[contains(text(), 'Объект закупки')]/following-sibling::span[1]/text()").get()

        except Exception as e:
            logging.info(e)
            tender['description'] = ''

        try:
            tender['customer'] = response.xpath('//div[@class="cardMainInfo__section"]/span[contains(text(), "Организация, осуществляющая размещение")]/following-sibling::span[1]/a/text()').get()
            
            if tender['customer'] is None:
                tender['customer'] = response.xpath('//div[@class="sectionMainInfo__body"]/*/span[contains(text(), "Заказчик")]/following-sibling::span[1]/*/text()').get()
            if tender['customer'] is None:
                tender['customer'] = response.xpath('//div[@class="registry-entry__body-title" and contains(text(), "Заказчик")]/following-sibling::div/*/text()').get()
        except:
            tender['customer'] = ""

        try:
            tender['platform'] =  response.xpath('//section[@class="blockInfo__section section"]/span[contains(text(), "Наименование электронной")]/following-sibling::span[1]/text()').get()
        except:
            tender['platform'] = ""

        try:
            tender['platform_url'] = response.xpath('//section[@class="blockInfo__section section"]/span[contains(text(), "Адрес электронной площадки")]/following-sibling::span[1]/*/text()').get()
        except:
            tender['platform_url'] = ""

        try:
            tender['deadline'] = response.xpath('//section[@class="blockInfo__section"]/span[contains(text(), "Срок исполнения контракта")]/following-sibling::span[1]/text()').get()
            if tender['deadline'] is None:
                tender['deadline'] = response.xpath('//section[@class="blockInfo__section"]/span[contains(text(), "Сроки поставки товара")]/following-sibling::span[1]/text()').get()
        except:
            tender['deadline'] = ''

        try:
            for variation in [
                        "Дата подведения итогов",
                        "Дата начала исполнения контракта",
                        "Дата и время проведения закрытого аукциона",
                        "Дата и время окончания подачи котировочных заявок",
                    ]:
                date_summing_up = response.xpath('//section[@class="blockInfo__section"]/span[@class="section__title" and contains(text(), "{}")]/following-sibling::span[1]/text()'.format(variation)).get()
                if date_summing_up is None:
                    date_summing_up = response.xpath('//div[@class="col-9 mr-auto"]/div[@class="common-text__title" and contains(text(), "{}")]/following-sibling::div[1]/text()'.format(variation)).get()
                if date_summing_up is not None:
                    tender['date_summing_up'] = date_summing_up
                    break
        except:
            tender['date_summing_up'] = ""

        try:
            tender['contract_enforcement'] = response.xpath('//section[@class="blockInfo__section section"]/span[@class="section__title" and contains(text(), "Размер обеспечения исполнения")]/following-sibling::span[1]/text()').get()
        except:
            tender['contract_enforcement'] = 0

        # logging.info('tender has info -')
        # logging.info(tender)

        request = scrapy.Request(url=response.request.url.replace("common-info", "documents"), callback=self.parse_docs)
        request.meta['tender'] = tender
        yield request
        # logging.info(tender)
            
        # pages = response.css("ul.pages::text").get()
        # last_page = pages.pop()
        # logging.info("last page number: "+last_page)
        # print("last page number: "+last_page)
        # pass
    
    def parse_docs(self, response):
        tender = response.meta.get('tender')

        docs = {}

        for variation in [
        "Извещение, изменения о проведении",
        "Извещение",
        "Извещение, изменение извещения о проведении",
        "Документация, изменение документации",
        "Документация по закупке",
    ]:
            attachments_list = response.xpath('//div[@class="col-sm-12 blockInfo"]/h2[contains(text(), "{}")]/following-sibling::div[2]/div[@class="col-sm-6"]/div/*[contains(text(), "Прикрепленные файлы")]/following-sibling::div'.format(variation))
            logging.warning(f"attachments_list is type of {type(attachments_list)}")
            if attachments_list.attrib == {}:
                attachments_list = response.xpath('//div[@class="col-sm-12 blockInfo"]/h2[contains(text(), "{}")]/following-sibling::div[1]/div[@class="col-sm-6"]/div/*[contains(text(), "Прикрепленные файлы")]/following-sibling::div'.format(variation))
            if attachments_list:
                
                for attachment in attachments_list:
                    link = attachment.xpath('.//div/span/a/@href').get()
                    title = attachment.xpath('.//div/span/a/@title').get()
                    title = rename_title(title)
                    docs.update({title: link})
                    tender['docs'] = docs

                break

        for title, url in docs.items():
            resp = requests.get(url,  headers={'User-Agent': 'Custom'})
            if resp.status_code == 200:

                handle_bytes(resp, title, tender['number'])
            else:
                logging.warning(f"something went wrong on {url}")
                    
        return tender


