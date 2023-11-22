import asyncio
import psycopg2

from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from scrapy.utils.log import configure_logging
from scrapy.crawler import CrawlerRunner
from tenderchad_scraper.spiders.update_tender_spider import UpdateSpider

from utils import generate_url
from tenderchad_scraper.settings import DATABASE_NAME, DATABASE_PASSWORD, DATABASE_USER, DATABASE_HOST, AWS_DOCS_FOLDER, AWS_DOCS 

hostname = DATABASE_HOST
username = DATABASE_USER
password = DATABASE_PASSWORD 
database = DATABASE_NAME

## Create/Connect to database
connection = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)

## Create cursor, used to execute commands
cursor = connection.cursor()
query = """SELECT public.parser_script_tender.number, public.parser_script_tender.federal_law_id, public.parser_script_federallaw.name, public.parser_script_tender.purchase_stage_id,public.parser_script_tender.placement_date
                FROM public.parser_script_tender 
                JOIN public.parser_script_federallaw ON public.parser_script_tender.federal_law_id = public.parser_script_federallaw.id 
                WHERE (public.parser_script_tender.purchase_stage_id = 1 OR public.parser_script_tender.purchase_stage_id = 5) 
                    AND public.parser_script_tender.end_date <= CURRENT_TIMESTAMP;
        """

# get supplier definition
cursor.execute(query)
all_tenders_to_update =  [(r[0], r[1], r[2], r[3], r[4]) for r in cursor.fetchall()]
print(all_tenders_to_update)


# create the shared semaphore
semaphore = asyncio.Semaphore(2)


def update_task(params:tuple) -> None:
    params = {"search": params[0], "federalLaw": [params[2]], "minDate": params[4].strftime("%d.%m.%Y")}
    dynamic_value = generate_url(params, False)
    print(dynamic_value)
    configure_logging()
    runner = CrawlerRunner()
    runner.crawl(UpdateSpider, start_urls=[dynamic_value])

def cycle_updating():
    for item in all_tenders_to_update:
        update_task(item)
    

task = LoopingCall(lambda: cycle_updating())
task.start(60 * 60 * 12)
reactor.run()