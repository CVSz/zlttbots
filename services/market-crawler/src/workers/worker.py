import asyncio

from core.queue import dequeue
from core.database import insert_product

from parsers.shopee import crawl_shopee
from parsers.lazada import crawl_lazada
from parsers.amazon import crawl_amazon

async def process(job):

    keyword = job["keyword"]

    data = []

    data += await crawl_shopee(keyword)
    data += await crawl_lazada(keyword)
    data += await crawl_amazon(keyword)

    for p in data:
        insert_product(p)

async def worker():

    while True:

        job = dequeue()

        if not job:
            await asyncio.sleep(5)
            continue

        try:
            await process(job)
        except Exception as e:
            print(e)

asyncio.run(worker())
