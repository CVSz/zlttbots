from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

def get_db():
    return psycopg2.connect(os.environ["DB_URL"])

@app.get("/arbitrage")

def list_events():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
    select product_name,buy_source,sell_source,profit
    from arbitrage_events
    order by profit desc
    limit 50
    """)

    rows = cur.fetchall()

    result = []

    for r in rows:

        result.append({
            "product": r[0],
            "buy": r[1],
            "sell": r[2],
            "profit": float(r[3])
        })

    return result
