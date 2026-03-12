import httpx

async def crawl_shopee(keyword):

    url = "https://shopee.co.th/api/v4/search/search_items"

    params = {
        "keyword": keyword,
        "limit": 50
    }

    r = httpx.get(url, params=params)

    items = r.json()["items"]

    products = []

    for i in items:

        products.append({
            "id": i["itemid"],
            "name": i["name"],
            "price": i["price"]/100000,
            "rating": i["item_rating"]["rating_star"],
            "sold": i["sold"],
            "source": "shopee"
        })

    return products
