FROM python:3.12-slim
WORKDIR /app
COPY src /app
RUN pip install fastapi uvicorn redis requests
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
