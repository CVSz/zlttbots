import psycopg2
import os

def get_db():
    return psycopg2.connect(
        os.environ["DB_URL"]
    )

def insert_product(p):

    db = get_db()
    cur = db.cursor()

    cur.execute(
    """
    insert into products
    (id,name,price,rating,sold,source)
    values(%s,%s,%s,%s,%s,%s)
    on conflict(id) do update
    set price=excluded.price,
        rating=excluded.rating,
        sold=excluded.sold
    """,
    (
        p["id"],
        p["name"],
        p["price"],
        p["rating"],
        p["sold"],
        p["source"]
    ))

    db.commit()
