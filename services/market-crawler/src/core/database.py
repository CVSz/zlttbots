import os

import psycopg2


def get_db():
    return psycopg2.connect(os.environ["DB_URL"])


def insert_product(p):
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                """
                insert into products
                (id,name,price,rating,sold,source)
                values(%s,%s,%s,%s,%s,%s)
                on conflict(id) do update
                set price=excluded.price,
                    rating=excluded.rating,
                    sold=excluded.sold,
                    source=excluded.source
                """,
                (
                    p["id"],
                    p["name"],
                    p["price"],
                    p["rating"],
                    p["sold"],
                    p["source"],
                ),
            )
