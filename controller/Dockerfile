FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir requests flask
COPY app.py /app/app.py
ENV PROM_URL=http://prometheus:9090 \
    API_URL=http://go-api:8080 \
    INTERVAL=10 \
    WINDOW=2m \
    ERR_HIGH=0.05 \
    ERR_LOW=0.01 \
    LAT_HIGH=0.35 \
    LAT_LOW=0.20 \
    MIN_RATE=0.1 \
    MAX_RATE=1.0 \
    STEP=0.1 \
    COOLDOWN_SEC=30
CMD ["python", "-u", "/app/app.py"]

