FROM python:3.11-slim

WORKDIR /app

# PostgreSQL bağlantı kütüphanesini yükle
RUN pip install --no-cache-dir psycopg2-binary

COPY . .

RUN chmod -R 777 /app

EXPOSE 8080

CMD ["python", "server.py"]
