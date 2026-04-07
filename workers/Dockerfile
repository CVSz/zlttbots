FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 10001 appuser \
  && chown -R appuser:appuser /app

USER appuser
VOLUME ["/tmp"]

CMD ["python", "kafka_event_worker.py"]
