import httpx
from bs4 import BeautifulSoup

async def crawl_amazon(keyword):

    url = f"https://www.amazon.com/s?k={keyword}"

    r = httpx.get(url)

    soup = BeautifulSoup(r.text,"html.parser")

    products = []

    cards = soup.select(".s-result-item")

    for c in cards[:20]:

        title = c.select_one("h2")

        if not title:
            continue

        products.append({
            "id": title.text,
            "name": title.text,
            "price": 0,
            "rating": 0,
            "sold": 0,
            "source": "amazon"
        })

    return products
