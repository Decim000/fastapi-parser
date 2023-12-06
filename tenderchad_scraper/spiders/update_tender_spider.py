import scrapy
import logging
import re

from tenderchad_scraper.items import TenderItem


class UpdateSpider(scrapy.Spider):
    name = "UpdateSpider"
    custom_settings = {
        "ITEM_PIPELINES": {"tenderchad_scraper.pipelines.HeaderClearDataPipeline": 300,
                           "tenderchad_scraper.pipelines.SaveStagePipeline": 400},
    }


    def parse(self, response):
        """ Entrypoint for starting parsing with this spider.
        Collects info from each card on page from from zakupki.gov
        Info: number, placement date, end date, law, price, stage, link to tender-related documents, extended supplier definition method (if provided).

        Args:
            response (Response): Neccessary var for framework

        Yields:
            Request: Request to function collecting tender's extended info from main page.
        """        
        __URL_BASE = "https://zakupki.gov.ru"
        logging.info('в поисках тендеров')

        # cards pf tenders
        headers = response.css("div.search-registry-entry-block.box-shadow-search-input")

        if headers:
            for header in headers:
                # get Tender item to store info
                tender = TenderItem()

                # get tender number
                try:
                    number = header.xpath('//div[@class="registry-entry__header-mid__number"]/*//text()[normalize-space()]').getall()
                    if type(number) is list:
                        tender['number'] = ''.join(number)
                    else:
                        tender['number'] = number
                except Exception:
                    tender['number'] = None
                
                # get date of placing tender 
                try:
                    tender['date_placed'] = header.xpath("//div[contains(text(), 'Размещено')]/following-sibling::div[1]/text()").get()
                except Exception:
                    tender['date_placed'] = None
                
                # get date when tender will be expired
                try:
                    tender['date_end'] = header.xpath("//div[contains(text(), 'Окончание подачи заявок')]/following-sibling::div[1]/text()").get()
                except Exception:
                    tender['date_end'] = None
                
                # get full price of the tender
                try:
                    tender['price'] = header.css('div.price-block__value::text').get()
                except Exception:
                    tender['price'] = 0

                # get current stage of the tender
                try:
                    tender['stage'] = header.css('div.registry-entry__header-mid__title.text-normal::text').get()
                except Exception:
                    tender['stage'] = 'Закупка отменена'

                # get link to documents of the tender
                try:
                    tender['docs'] = header.css("div.registry-entry__header-mid__number").css('a::attr(href)').extract()[0]
                except Exception:
                    tender['docs']=''

                # get law type
                try:
                    law = header.css("div.col-9.p-0.registry-entry__header-top__title.text-truncate::text").get()
                    tender['law'] = re.search(r'\d+-ФЗ', law.strip()).group(0)
                except Exception:
                    tender['law'] = None
                
                # if law is specified, can extract extended name of supplier definition method
                if tender.get('law') is not None:
                    try:
                        tender['supplier_extended']  = law.replace(tender['law'], "").replace('\n', '').strip()
                        
                    except Exception:
                        pass
        
            return tender