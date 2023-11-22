from twisted.internet import reactor

from scrapy.crawler import CrawlerRunner
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from apscheduler.schedulers.twisted import TwistedScheduler
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from scrapy.utils.log import configure_logging

from tenderchad_scraper.spiders.zakupki_spider import ZakupkiSpider
from utils import generate_url


SEARCH_STRINGS = ['сайт', 'разработка сайта', 'мобильное приложение']

def search_task(search_string: str) -> None:
    params = {"search": search_string, "federalLaw": ['223-ФЗ', '44-ФЗ'], "purchaseStage": ["Подача заявок"]}
    print(params)
    dynamic_value = generate_url(params, False)
    print(dynamic_value)
    configure_logging()
    runner = CrawlerRunner()
    runner.crawl(ZakupkiSpider, start_urls=[dynamic_value])

def cycle_parsing():
    """ Enables parsing once in a day by search string, laws: 223, 44, and purchase stage - 'Подача заявок'.
    Script must be running on the background.
    """    
    for search_string in SEARCH_STRINGS:
        print(search_string)
        search_task(search_string)

task = LoopingCall(lambda: cycle_parsing())
task.start(60 * 60 * 24)
reactor.run()