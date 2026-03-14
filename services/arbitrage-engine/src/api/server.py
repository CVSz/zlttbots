import os

import psycopg2
from fastapi import FastAPI

app = FastAPI()


def get_db():
    return psycopg2.connect(os.environ['DB_URL'])


@app.get('/healthz')
def healthz():
    db_ok = False

    try:
        with get_db() as db:
            with db.cursor() as cur:
                cur.execute('select 1')
                cur.fetchone()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        'status': 'ok' if db_ok else 'degraded',
        'service': 'arbitrage-engine',
        'checks': {
            'db': db_ok,
        },
    }


@app.get('/arbitrage')
def list_events():
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                '''
                select product_name,buy_source,sell_source,profit
                from arbitrage_events
                order by profit desc
                limit 50
                '''
            )
            rows = cur.fetchall()

    result = []
    for r in rows:
        result.append(
            {
                'product': r[0],
                'buy': r[1],
                'sell': r[2],
                'profit': float(r[3]),
            }
        )

    return result
