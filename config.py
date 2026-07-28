import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# OpenAI / Gemini API Yapılandırması (Gizli anahtarlar .env dosyasından okunur, hardcoded key yazılmaz)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "models/gemini-2.0-flash")

# Veri toplama sıklığı (Dakika)
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "10"))

# OpenShift & Yerel PostGIS PostgreSQL Yapılandırması (OpenShift varsayılanları)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgis-db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "gisdb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword123")

# Yayın yapan sitelerin varsayılan yayıncı ülkeleri ve merkez koordinatları (Lon, Lat)
PUBLISHER_COUNTRIES = {
    "Al Jazeera": {"country": "Qatar", "coords": [51.5310, 25.2854]},
    "BBC News": {"country": "United Kingdom", "coords": [-3.4360, 55.3781]},
    "France 24": {"country": "France", "coords": [2.3522, 48.8566]},
    "USGS Earthquakes": {"country": "United States", "coords": [-95.7129, 37.0902]},
    "NASA EONET": {"country": "United States", "coords": [-95.7129, 37.0902]},
    "OpenSky Network": {"country": "Switzerland", "coords": [8.2275, 46.8182]},
    "GDACS Disasters": {"country": "Switzerland", "coords": [6.1432, 46.2044]},
    "OpenSanctions": {"country": "Germany", "coords": [10.4515, 51.1657]},
}

# Şehir, Eyalet ve Ülke merkez koordinatları (Lon, Lat) - AI Geocoder fallback & Kural motoru için
LOCATION_CENTROIDS = {
    # ABD Eyaletleri ve Şehirleri
    "texas": [-99.9018, 31.9686],
    "california": [-119.4179, 36.7783],
    "florida": [-81.5158, 27.6648],
    "new york": [-74.0060, 40.7128],
    "washington": [-120.7401, 47.7511],
    "ice": [-95.7129, 37.0902],
    "united states": [-95.7129, 37.0902],
    "usa": [-95.7129, 37.0902],
    "america": [-95.7129, 37.0902],
    "us": [-95.7129, 37.0902],

    # Ortadoğu ve Avrupa Şehir/Ülkeleri
    "turkey": [35.2433, 38.9637],
    "türkiye": [35.2433, 38.9637],
    "istanbul": [28.9784, 41.0082],
    "ankara": [32.8597, 39.9334],
    "london": [-0.1276, 51.5074],
    "united kingdom": [-3.4360, 55.3781],
    "uk": [-3.4360, 55.3781],
    "france": [2.3522, 48.8566],
    "paris": [2.3522, 48.8566],
    "germany": [10.4515, 51.1657],
    "berlin": [13.4050, 52.5200],
    "qatar": [51.5310, 25.2854],
    "doha": [51.5310, 25.2854],
    "ukraine": [31.1656, 48.3794],
    "kyiv": [30.5234, 50.4501],
    "russia": [105.3188, 61.5240],
    "moscow": [37.6173, 55.7558],
    "syria": [38.9968, 34.8021],
    "damascus": [36.2765, 33.5138],
    "iraq": [43.6793, 33.2232],
    "baghdad": [44.3661, 33.3152],
    "israel": [34.8516, 31.0461],
    "tel aviv": [34.7818, 32.0853],
    "palestine": [35.2332, 31.9522],
    "gaza": [34.4668, 31.5017],
    "beirut": [35.5018, 33.8938],
    "lebanon": [35.5017, 33.8547],
    "japan": [138.2529, 36.2048],
    "tokyo": [139.6917, 35.6895],
    "china": [104.1954, 35.8617],
    "beijing": [116.4074, 39.9042],
    "india": [78.9629, 20.5937],
    "brazil": [-51.9253, -14.2350],
    "greece": [21.8243, 39.0742],
    "iran": [53.6880, 32.4279],
    "tehran": [51.3890, 35.6892]
}

# Geriye dönük uyumluluk
COUNTRY_CENTROIDS = LOCATION_CENTROIDS
