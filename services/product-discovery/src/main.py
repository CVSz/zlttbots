from fastapi import FastAPI
import requests
import random

app = FastAPI()

@app.get("/discover")
def discover():

    products = requests.get("http://market-crawler:8000/products").json()

    scored = []

    for p in products:
        p["score"] = random.random()
        scored.append(p)

    scored.sort(key=lambda x:x["score"],reverse=True)

    return scored[:10]
