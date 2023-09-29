import asyncio

from multiprocessing import Process
from typing import List, Union, Annotated
from fastapi import FastAPI, Query
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import asyncioreactor

from utils import generate_url

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
    dynamic_value = await generate_url(params)
    print(dynamic_value)
    scraping_process = Process(target=scrape, args=(spider_name,  dynamic_value))
    scraping_process.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.main())