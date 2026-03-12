import time
from core.queue import dequeue
from core.render import render

def worker():

    while True:

        job = dequeue()

        if not job:
            time.sleep(3)
            continue

        try:
            render(job)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    worker()
