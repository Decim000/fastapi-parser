import asyncio

from multiprocessing import Process, Queue
from typing import List, Union, Annotated
from fastapi import FastAPI, Query
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import asyncioreactor
from scrapy.utils.reactor import install_reactor

from utils import generate_url

asyncioreactor.install()

app = FastAPI()

# Очередь для получения результатов скрапинга
result_queue = Queue()

def async_run(spider_name, result_queue, dynamic_value):
    asyncio.run(scrape(spider_name, result_queue, dynamic_value))

def scrape(spider_name, result_queue, dynamic_value):
    process = CrawlerProcess(get_project_settings())
    # params = {"search": search, "federalLaw": federalLaw, "purchaseStage": purchaseStage, "minDate": minDate, "maxDate": maxDate, "minPrice": minPrice, "maxPrice": maxPrice}
    # dynamic_value = await generate_url(params)
    # scraping_loop = asyncio.new_event_loop()

    # spider = process.create_crawler(spider_name)
    # process.crawl(spider, dynamic_value=dynamic_value)
    # process.start()

    # runner = CrawlerRunner(get_project_settings())
    process.crawl(spider_name, start_urls=[dynamic_value])
    process.start()

    # process.crawl("ZakupkiSpider", dynamic_value=dynamic_value)  # Замените "your_spider_name" на имя вашего паука Scrapy
    # process.start()
    # runner = CrawlerRunner(get_project_settings())

    # await runner.crawl(ZakupkiSpider, dynamic_value=dynamic_value)  # Замените на ваш паук
    # await runner.join()
    return {"status": "Scraping initiated"}

@app.get("/scrape")
async def run_scraping(search: Union[str, None] = None, federalLaw: Annotated[Union[str, list[str], None], Query()] = None, purchaseStage: Annotated[Union[str, list[str], None], Query()] = None, minDate: Union[str, None] = None, maxDate: Union[str, None] = None, minPrice: Union[str, None] = None, maxPrice: Union[str, None] = None):
    spider_name = 'ZakupkiSpider'
    params = {"search": search, "federalLaw": federalLaw, "purchaseStage": purchaseStage, "minDate": minDate, "maxDate": maxDate, "minPrice": minPrice, "maxPrice": maxPrice}
    print(params)
    dynamic_value = await generate_url(params)
    print(dynamic_value)
    scraping_process = Process(target=scrape, args=(spider_name, result_queue, dynamic_value))
    scraping_process.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.main())