FROM python:3.12-slim

WORKDIR /app

ARG ENABLE_SGX=0

ENV OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    ORT_ENABLE_CPU_MEM_ARENA=1 \
    PYTHONUNBUFFERED=1 \
    ENABLE_SGX=${ENABLE_SGX}

RUN set -eux; \
    mkdir -p /tmp/apt-cache/archives/partial; \
    install_ok=0; \
    for attempts in 1 2 3 4 5; do \
      if apt-get update \
        && apt-get -o Dir::Cache::archives=/tmp/apt-cache/archives install -y --no-install-recommends libgomp1; then \
        install_ok=1; \
        break; \
      fi; \
      echo "apt-get failed on attempt ${attempts}; retrying..."; \
      rm -rf /var/lib/apt/lists/*; \
      sleep $((attempts * 2)); \
    done; \
    if [ "$install_ok" -ne 1 ]; then \
      echo "Failed to install libgomp1 after 5 attempts"; \
      exit 1; \
    fi; \
    rm -rf /var/lib/apt/lists/* /tmp/apt-cache

COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY sgx_entry.sh ./sgx_entry.sh

RUN chmod +x ./sgx_entry.sh

CMD ["sh", "-c", "if [ \"${ENABLE_SGX}\" = \"1\" ]; then ./sgx_entry.sh; else uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1; fi"]
