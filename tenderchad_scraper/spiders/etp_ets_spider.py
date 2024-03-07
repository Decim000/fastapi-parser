import requests
import scrapy
import logging
import re
import psycopg2

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from tenderchad_scraper.items import TenderItem
from tenderchad_scraper.utils import handle_bytes
from tenderchad_scraper.title_util import rename_title
from utils import generate_url
from tenderchad_scraper.settings import DATABASE_NAME, DATABASE_PASSWORD, DATABASE_USER, DATABASE_HOST, AWS_DOCS_FOLDER, AWS_DOCS 


class LotOnlineSpider(scrapy.Spider):
    name = "EtpEtsSpider"

    allowed_domains = ['etp-ets.ru']
    start_urls = ['https://etp-ets.ru/44/catalog/procedure']

    custom_settings = {
        "ITEM_PIPELINES": {
            'tenderchad_scraper.pipelines.HeaderClearDataPipeline': 300,
        },
    }

    def parse(self, response):
        """ Entrypoint for starting parsing with this spider.
        Collects info from each card on page from from gz.lot-online.ru/
        Info: number, placement date, end date, law, price, stage, link to tender-related documents, extended supplier definition method (if provided).

        Args:
            response (Response): Neccessary var for framework

        Yields:
            Request: Request to function collecting tender's extended info from main page.
        """        
        __URL_BASE = "https://etp-ets.ru"
        logging.info('в поисках тендеров')

        items = response.xpath('//table/tbody/tr')

        if items:
            for i, item in enumerate(items):
                # get Tender item to store info

                # get tender number
                tender = {}
                try:
                    number = item.xpath('//td[has-class("row-procedure_number")]//text()').getall()[i]
                    if not re.search(r'\d+', number):
                        raise Exception()
                    print(f'Number of tender: {number}')
                    tender['number'] = number
                except Exception:
                    tender['number'] = None

                # get date of placing tender
                try:
                    dt = item.xpath('//td[has-class("row-publication_datetime")]//text()').get()
                    # dt = dt.split()[0]
                    tender['date_placed'] = dt
                except Exception:
                    tender['date_placed'] = None

                # get date when tender will be expired
                try:
                    tender['date_end'] = item.xpath('//td[has-class("row-request_end_give_datetime")]//text()').get()
                except Exception:
                    tender['date_end'] = None

                # get full price of the tender
                try:
                    price = item.css('td.row-contract_start_price::text').get()
                    price = ''.join([i for i in price if i.isdigit() or i == '.'])
                    tender['price'] = price
                except Exception:
                    tender['price'] = 0

                # get current stage of the tender
                try:
                    tender['stage'] = item.css('td.row-status::text').get()
                except Exception:
                    tender['stage'] = 'Закупка отменена'

                # get link to documents of the tender
                #empty

                # get law type
                try:
                    tender['law'] = "44-ФЗ"
                except Exception:
                    tender['law'] = None

                # route further scraping
                if tender['law'] == "44-ФЗ":
                    full_page_link = item.css('td.row-procedure_name a::attr(href)').get()

                    request = response.follow(url=full_page_link, callback=self.parse_fullpage_44)
                    request.meta['tender'] = tender
                    yield request

    def parse_fullpage_44(self, response):
        """ Function for scraping extended info from 44-FZ-tender's page.
        Info: law (if was None), supplier, law_and_supplier, customer, platform, platform URL, deadline, summing up date, contract enforcement amount.
        Summing up date is field for calculating deadline with (deadline date - summing up date).

        Args:
            response (scrapy.Response): Neccessary arg for framework

        Raises:
            Exception: exception

        Yields:
            scrapy.Request: Request to function for downloading docs
        """

        # retrieve TenderInfo object to continue storing data
        tender_dict = response.meta.get('tender')

        tender = TenderItem()

        tender['number'] = tender_dict['number']
        tender['date_placed'] = tender_dict['date_placed']
        tender['date_end'] = tender_dict['date_end']
        tender['price'] = tender_dict['price']
        tender['stage'] = tender_dict['stage']
        # tender['docs'] = tender_dict['docs']
        tender['law'] = tender_dict['law']
        print(tender)

        # run downloading the docs

        request = scrapy.Request(url=response.request.url.replace("procedure", "documentation"), callback=self.parse_docs)
        request.meta['tender'] = tender
        yield request

    def parse_docs(self, response):
        """_summary_

        Args:
            response (_type_): _description_
        """
        tender = response.meta.get('tender')
        tender['all_attached_files'] = []

        yield tender



