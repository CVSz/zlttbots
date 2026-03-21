FROM python:3.12-slim

WORKDIR /app

ENV OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    ORT_ENABLE_CPU_MEM_ARENA=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY src ./src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
