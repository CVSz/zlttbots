FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt update && apt install -y \
    ffmpeg \
    python3 \
    python3-pip

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python3","src/main.py"]
