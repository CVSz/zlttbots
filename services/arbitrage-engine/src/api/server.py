import os
import time

import psycopg2
from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from metrics import request_counter, request_latency

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


@app.get('/metrics')
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get('/arbitrage')
def list_events():
    start = time.perf_counter()
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

    request_counter.inc()
    request_latency.observe(time.perf_counter() - start)
    return result
