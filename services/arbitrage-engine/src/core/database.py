import psycopg2
import os

def get_db():
    return psycopg2.connect(os.environ["DB_URL"])

def fetch_products():

    db = get_db()
    cur = db.cursor()

    cur.execute("""
    select id,name,price,source
    from products
    """)

    rows = cur.fetchall()

    data = []

    for r in rows:
        data.append({
            "id": r[0],
            "name": r[1],
            "price": float(r[2]),
            "source": r[3]
        })

    return data

def insert_event(event):

    db = get_db()
    cur = db.cursor()

    cur.execute("""
    insert into arbitrage_events
    (product_name,buy_source,sell_source,buy_price,sell_price,profit)
    values(%s,%s,%s,%s,%s,%s)
    """,
    (
        event["product"],
        event["buy"],
        event["sell"],
        event["buy_price"],
        event["sell_price"],
        event["profit"]
    ))

    db.commit()
