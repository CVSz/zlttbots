FROM python:3.12-slim
WORKDIR /app
COPY src ./src
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "src.engine"]
