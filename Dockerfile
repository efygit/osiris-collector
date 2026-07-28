FROM python:3.11-slim

WORKDIR /app

# Bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Red Hat OpenShift rastgele non-root kullanıcısı için çalışma dizinine tam yazma izni ver
RUN chmod -R 777 /app

# Web UI portunu aç
EXPOSE 8080

# Uygulamayı başlat (Veri Toplama Pipeline + Web UI Sunucusu)
CMD ["python", "main.py"]
