import time

from core.database import fetch_products, insert_event
from engine.arbitrage import detect

def worker():

    while True:

        products = fetch_products()

        opportunities = detect(products)

        for o in opportunities:
            insert_event(o)

        time.sleep(30)

if __name__ == "__main__":
    worker()
