from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

def db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST","postgres"),
        user="zttato",
        password="zttato",
        dbname="zttato"
    )

@app.post("/optimize")
def optimize():

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT campaign_id, SUM(clicks) as c FROM clicks GROUP BY campaign_id")

    rows = cur.fetchall()

    best = max(rows,key=lambda x:x[1]) if rows else None

    return {"best_campaign":best}
