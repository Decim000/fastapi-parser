import requests
import scrapy
import logging
import re

from tenderchad_scraper.items import TenderItem
from tenderchad_scraper.database import PostgresConnection
from tenderchad_scraper.utils import handle_bytes
from tenderchad_scraper.title_util import rename_title


class ZakupkiSpider(scrapy.Spider):
    name = "ZakupkiSpider"
    
    custom_settings = {
        "ITEM_PIPELINES": {'tenderchad_scraper.pipelines.HeaderClearDataPipeline': 300,
                            'tenderchad_scraper.pipelines.FullpageClearDataPipeline': 400,
                            'tenderchad_scraper.pipelines.DocsClearDataPipeline': 500,
                            'tenderchad_scraper.pipelines.PostgresPipeline': 1000,
                            },
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
            for i, header in enumerate(headers):

                # get tender number
                tender = {}
                try:
                    number = header.xpath('//div[@class="registry-entry__header-mid__number"]/*//text()[normalize-space()]').getall()[i]
                    if not re.search(r'\d+', number):
                        number = header.xpath('//div[@class="registry-entry__header-mid__number"]/*/*/text()[normalize-space()]').getall()[i]
                    print(f'Number of tender: {number}')
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
        
                # route further scraping
                if tender['law'] == "44-ФЗ":
                    request = response.follow(url=__URL_BASE+tender['docs'], callback=self.parse_fullpage_44)
                    request.meta['tender'] = tender
                    yield request

                if tender['law'] == "223-ФЗ":
                    request = response.follow(url=__URL_BASE+tender['docs'], callback=self.parse_fullpage_223)
                    request.meta['tender'] = tender
                    yield request


    def parse_fullpage_223(self, response):
        """ Function for scraping extended info from 223-FZ-tender's page.

        Args:
            response (scrapy.Response): Neccessary arg for framework
        """        
        # retrieve TenderInfo object to continue storing data
        tender_dict = response.meta.get('tender')

        tender = TenderItem()

        tender['number'] = tender_dict['number']
        tender['date_placed'] = tender_dict['date_placed']
        tender['date_end'] = tender_dict['date_end']
        tender['price'] = tender_dict['price']
        tender['stage'] = tender_dict['stage']
        tender['docs'] = tender_dict['docs']
        tender['law'] = tender_dict['law']
        # if couldn't get law from card
        try:
            # try to retrieve law 
            if not tender.get('law'):
                tender['law'] = response.css('div.cardMainInfo__title.d-flex.text-truncate::text').get()
                if tender['law'] is None:
                    raise Exception
        # try to get string containing both law and supplier as they are in the same element
        except Exception:
            tender['law_and_supplier'] = response.xpath('//div[@class="registry-entry__header-top__title"]/text()').get()

        if not tender.get('law_and_supplier'):
            tender['law_and_supplier'] = response.xpath('//div[@class="registry-entry__header-top__title"]/text()').get()


        # if could't collect both law and supplier, law and supplier are in separate elements
        if not tender.get('law_and_supplier'):
            tender['supplier'] = response.css('span.cardMainInfo__title.distancedText.ml-1::text').get()

        # two ways for extracting description
        try:
            tender['description'] = response.xpath("//span[contains(text(), 'Объект закупки')]/following-sibling::span[1]/text()").get()
            if tender['description'] is None:
                tender['description'] = response.xpath("//div[contains(text(), 'Объект закупки')]/following-sibling::span[1]/text()").get()
                if tender['description'] is None:
                    tender['description'] = response.xpath("//div[@class='registry-entry__body-value']/text()").get()
        except Exception as exception:
            logging.info(exception)
            tender['description'] = ''

        # three ways for extracting customer's name
        try:
            tender['customer'] = response.xpath('//div[@class="cardMainInfo__section"]/span[contains(text(), "Организация, осуществляющая размещение")]/following-sibling::span[1]/a/text()').get()
            
            if tender['customer'] is None:
                tender['customer'] = response.xpath('//div[@class="sectionMainInfo__body"]/*/span[contains(text(), "Заказчик")]/following-sibling::span[1]/*/text()').get()
            if tender['customer'] is None:
                tender['customer'] = response.xpath('//div[@class="registry-entry__body-title" and contains(text(), "Заказчик")]/following-sibling::div/*/text()').get()
        except Exception:
            tender['customer'] = ""

        # get tender origin plaform name 
        try:
            tender['platform'] =  response.xpath('//section[@class="blockInfo__section section"]/span[contains(text(), "Наименование электронной")]/following-sibling::span[1]/text()').get()
            if tender['platform'] is None:
                tender['platform'] =  response.xpath('//div[contains(text(), "Наименование электронной")]/following-sibling::div/text()').get()
        except Exception:
            tender['platform'] = ""

        # get URL of this platform
        try:
            tender['platform_url'] = response.xpath('//section[@class="blockInfo__section section"]/span[contains(text(), "Адрес электронной площадки")]/following-sibling::span[1]/*/text()').get()
            if tender['platform_url'] is None:
                tender['platform_url'] = response.xpath('//div[contains(text(), "Адрес электронной")]/following-sibling::div/*/text()').get()
        except Exception:
            tender['platform_url'] = ""

        # try to get deadline of the tender. Can collect date or days
        try:
            tender['deadline'] = response.xpath('//section[@class="blockInfo__section"]/span[contains(text(), "Срок исполнения контракта")]/following-sibling::span[1]/text()').get()
            if tender['deadline'] is None:
                tender['deadline'] = response.xpath('//section[@class="blockInfo__section"]/span[contains(text(), "Сроки поставки товара")]/following-sibling::span[1]/text()').get()
        except Exception:
            tender['deadline'] = ''

        # support field to get summing up date
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
        except Exception:
            tender['date_summing_up'] = ""

        # get contract enforcement amount
        try:
            tender['contract_enforcement'] = response.xpath('//section[@class="blockInfo__section section"]/span[@class="section__title" and contains(text(), "Размер обеспечения исполнения")]/following-sibling::span[1]/text()').get()
        except Exception:
            tender['contract_enforcement'] = 0

        # run downloading the docs
        request = scrapy.Request(url=response.request.url.replace("common-info", "documents"), callback=self.parse_docs)
        request.meta['tender'] = tender
        yield request

        # tender['all_attached_files'] = None

        # return tender


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
        tender['docs'] = tender_dict['docs']
        tender['law'] = tender_dict['law']

        # if couldn't get law from card
        try:
            # try to retrieve law 
            if not tender.get('law'):
                tender['law'] = response.css('div.cardMainInfo__title.d-flex.text-truncate::text').get()
                if tender['law'] is None:
                    raise Exception
        # try to get string containing both law and supplier as they are in the same element
        except Exception:
            tender['law_and_supplier'] = response.css('div.registry-entry__header-top__title::text').get()

        # if could't collect both law and supplier, law and supplier are in separate elements
        if not tender.get('law_and_supplier'):
            tender['supplier'] = response.css('span.cardMainInfo__title.distancedText.ml-1::text').get()

        # two ways for extracting description
        try:
            tender['description'] = response.xpath("//span[contains(text(), 'Объект закупки')]/following-sibling::span[1]/text()").get()
            if tender['description'] is None:
                tender['description'] = response.xpath("//div[contains(text(), 'Объект закупки')]/following-sibling::span[1]/text()").get()
                if tender['description'] is None:
                    tender['description'] = response.xpath("/html/body/div[2]/div/div[1]/div[2]/div[2]/div/div/div/div[1]/div[2]/div[1]/div[2]/text()").get()
        except Exception as exception:
            logging.info(exception)
            tender['description'] = ''

        # three ways for extracting customer's name
        try:
            tender['customer'] = response.xpath('//div[@class="cardMainInfo__section"]/span[contains(text(), "Организация, осуществляющая размещение")]/following-sibling::span[1]/a/text()').get()
            
            if tender['customer'] is None:
                tender['customer'] = response.xpath('//div[@class="sectionMainInfo__body"]/*/span[contains(text(), "Заказчик")]/following-sibling::span[1]/*/text()').get()
            if tender['customer'] is None:
                tender['customer'] = response.xpath('//div[@class="registry-entry__body-title" and contains(text(), "Заказчик")]/following-sibling::div/*/text()').get()
        except Exception:
            tender['customer'] = ""

        # get tender origin plaform name 
        try:
            tender['platform'] =  response.xpath('//section[@class="blockInfo__section section"]/span[contains(text(), "Наименование электронной")]/following-sibling::span[1]/text()').get()
        except Exception:
            tender['platform'] = ""

        # get URL of this platform
        try:
            tender['platform_url'] = response.xpath('//section[@class="blockInfo__section section"]/span[contains(text(), "Адрес электронной площадки")]/following-sibling::span[1]/*/text()').get()
        except Exception:
            tender['platform_url'] = ""

        # try to get deadline of the tender. Can collect date or days
        try:
            tender['deadline'] = response.xpath('//section[@class="blockInfo__section"]/span[contains(text(), "Срок исполнения контракта")]/following-sibling::span[1]/text()').get()
            if tender['deadline'] is None:
                tender['deadline'] = response.xpath('//section[@class="blockInfo__section"]/span[contains(text(), "Сроки поставки товара")]/following-sibling::span[1]/text()').get()
        except Exception:
            tender['deadline'] = ''

        # support field to get summing up date
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
        except Exception:
            tender['date_summing_up'] = ""

        # get contract enforcement amount
        try:
            tender['contract_enforcement'] = response.xpath('//section[@class="blockInfo__section section"]/span[@class="section__title" and contains(text(), "Размер обеспечения исполнения")]/following-sibling::span[1]/text()').get()
        except Exception:
            tender['contract_enforcement'] = 0

        # run downloading the docs
        request = scrapy.Request(url=response.request.url.replace("common-info", "documents"), callback=self.parse_docs)
        request.meta['tender'] = tender
        yield request

        # tender['all_attached_files'] = None

        # return tender


    def parse_docs(self, response):
        """_summary_

        Args:
            response (_type_): _description_
        """
        tender = response.meta.get('tender')

        # dict for storing documents {'doc_name': url}
        docs = {}

        for variation in [
        "Извещение, изменения о проведении",
        "Извещение",
        "Извещение, изменение извещения о проведении",
        "Документация, изменение документации",
        "Документация по закупке",
        ]:
            attachments_list = response.xpath('//div[@class="col-sm-12 blockInfo"]/h2[contains(text(), "{}")]/following-sibling::div[2]/div[@class="col-sm-6"]/div/*[contains(text(), "Прикрепленные файлы")]/following-sibling::div'.format(variation))
            
            if attachments_list.attrib == {} or attachments_list is None:
                attachments_list = response.xpath('//div[@class="col-sm-12 blockInfo"]/h2[contains(text(), "{}")]/following-sibling::div[1]/div[@class="col-sm-6"]/div/*[contains(text(), "Прикрепленные файлы")]/following-sibling::div'.format(variation))
                if attachments_list.attrib == {} or attachments_list is None:
                    attachments_list = response.xpath('//div[contains(text(), "{}")]/following-sibling::div[1]/div/div[2]/*/*/*[contains(text(), "Прикрепленные файлы")]/following-sibling::div/div'.format(variation))
            
            if attachments_list:
                logging.warning('files found')
                logging.warning(attachments_list)
               # get titles and links
                for attachment in attachments_list:
                    try:
                        link = attachment.xpath('.//span[2]/a[2]/@href').get()
                        url = "https://zakupki.gov.ru" + link
                        title = attachment.xpath('.//span[2]/a[2]/text()').get()
                        title = title.replace("\r\n","")
                        title = title.strip()
                        logging.warning(title)
                        docs.update({title: url})
                        tender['docs'] = docs
                    except:
                        link = attachment.xpath('.//div/span/a/@href').get()
                        logging.warning(link)
                        title = attachment.xpath('.//div/span/a/@title').get()
                        title = title.replace("\r\n","")
                        title = title.strip()
                        logging.warning(title)
                        docs.update({title: link})
                        tender['docs'] = docs

                break

        if attachments_list.attrib == {} or attachments_list is None:
            logging.warning('files not found')      

        # list containing all files, including files from rar- and zi-archives
        all_attached_files = []
        tender_has_docs = self.check_tender_has_docs_in_db(tender['number'])

        if not tender_has_docs:
            for title, url in docs.items():
                resp = requests.get(url,  headers={'User-Agent': 'Custom'})
                if resp.status_code == 200:
                    # working with file's payload to save
                    logging.warning('start downloading files')
                    attached_files = handle_bytes(resp, title, tender['number'])
                    all_attached_files.append(attached_files)
                    logging.warning(all_attached_files)
                    
                else:
                    logging.warning(f"something went wrong on {url}")
        else:
            logging.warning(f"files for tender {tender['number']} are in database")


        tender['all_attached_files'] = all_attached_files
                    
        yield tender


    def check_tender_has_docs_in_db(self, number):
        try:
            connection = PostgresConnection()._instance.connection
        
            ## Create cursor, used to execute commands
            cursor = connection.cursor()
            cursor.execute("SELECT public.parser_script_tenderdocument.id \
                            FROM public.parser_script_tenderdocument \
                            JOIN public.parser_script_tender ON public.parser_script_tenderdocument.tender_id = public.parser_script_tender.id \
                            where public.parser_script_tender.number = %s;", (number,))
            existing_item = cursor.fetchone()
            if existing_item:
                logging.warning(f'Tender {number} has docs in database')
                return True
            else:
                return False

        except Exception as e:
            print(f'troubles from fetching docs for tender {number}')
            raise Exception(e)
