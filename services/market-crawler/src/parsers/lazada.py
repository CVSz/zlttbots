import httpx
from bs4 import BeautifulSoup

async def crawl_lazada(keyword):

    url = f"https://www.lazada.co.th/catalog/?q={keyword}"

    r = httpx.get(url)

    soup = BeautifulSoup(r.text,"html.parser")

    products = []

    cards = soup.select(".Bm3ON")

    for c in cards[:20]:

        name = c.select_one(".RfADt").text
        price = c.select_one(".ooOxS").text

        products.append({
            "id": name,
            "name": name,
            "price": price,
            "rating": 0,
            "sold": 0,
            "source": "lazada"
        })

    return products
