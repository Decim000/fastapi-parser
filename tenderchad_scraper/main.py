import asyncio

from multiprocessing import Process
from typing import List, Union, Annotated
from fastapi import FastAPI, Query
import psycopg2
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import asyncioreactor

from utils import generate_url
from tenderchad_scraper.settings import DATABASE_NAME, DATABASE_PASSWORD, DATABASE_USER, DATABASE_HOST, AWS_DOCS_FOLDER, AWS_DOCS 

asyncioreactor.install()

app = FastAPI()


def scrape(spider_name, dynamic_value):
    process = CrawlerProcess(get_project_settings())

    process.crawl(spider_name, start_urls=[dynamic_value])
    process.start()

    return {"status": "Scraping initiated"}

@app.get("/scrape")
async def run_scraping(search: Union[str, None] = None, federalLaw: Annotated[Union[str, list[str], None], Query()] = None, purchaseStage: Annotated[Union[str, list[str], None], Query()] = None, minDate: Union[str, None] = None, maxDate: Union[str, None] = None, minPrice: Union[str, None] = None, maxPrice: Union[str, None] = None):
    spider_name = 'ZakupkiSpider'
    params = {"search": search, "federalLaw": federalLaw, "purchaseStage": purchaseStage, "minDate": minDate, "maxDate": maxDate, "minPrice": minPrice, "maxPrice": maxPrice}
    print(params)
    dynamic_value = generate_url(params)
    print(dynamic_value)
    scraping_process = Process(target=scrape, args=(spider_name,  dynamic_value))
    scraping_process.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.main())


@app.get("/update-tender")
async def update():
    ## Connection Details
    hostname = DATABASE_HOST
    username = DATABASE_USER
    password = DATABASE_PASSWORD 
    database = DATABASE_NAME

    ## Create/Connect to database
    connection = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)
    
    ## Create cursor, used to execute commands
    cursor = connection.cursor()
    query = """SELECT public.parser_script_tender.number, public.parser_script_tender.federal_law_id, public.parser_script_federallaw.name, public.parser_script_tender.purchase_stage_id
                    FROM public.parser_script_tender 
                    JOIN public.parser_script_federallaw ON public.parser_script_tender.federal_law_id = public.parser_script_federallaw.id 
                    WHERE (public.parser_script_tender.purchase_stage_id = 1 OR public.parser_script_tender.purchase_stage_id = 5) 
                        AND public.parser_script_tender.end_date <= CURRENT_TIMESTAMP and public.parser_script_tender.number = '0171100000314000035'
            """

    # get supplier definition
    cursor.execute(query)
    all_tenders_to_update =  [(r[0], r[1], r[2], r[3]) for r in cursor.fetchall()]


    # create the shared semaphore
    semaphore = asyncio.Semaphore(2)
    # create and schedule tasks
    tasks = [asyncio.create_task(update_task(semaphore, i)) for i in all_tenders_to_update]
    # wait for all tasks to complete
    _ = await asyncio.wait(tasks)


async def update_task(semaphore, params:tuple) -> None:
    async with semaphore:
        params = {"search": params[0], "federalLaw": params[2]}
        dynamic_value = await generate_url(params)
        print(dynamic_value)
        spider_name = 'UpdateTenderStageSpider'
        scraping_process = Process(target=scrape, args=(spider_name,  dynamic_value))
        scraping_process.start()

