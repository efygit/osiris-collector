import http.server
import socketserver
import json
import os
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

PORT = int(os.getenv("PORT", "8080"))
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")

# OpenShift PostGIS Bağlantı Ayarları (Varsayılanlar OpenShift servis adı ve veri tabanıyla birebir eşleşir)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgis-db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "gisdb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword123")

class OsirisUIHandler(http.server.SimpleHTTPRequestHandler):
    """
    Bağımsız IRIS GEOINT Web UI & GeoJSON API Sunucusu (Son 24 Saatlik Veri Akışı)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_GET(self):
        parsed_path = urlparse(self.path).path
        
        if parsed_path == "/api/events":
            self.handle_events_api()
        elif parsed_path == "/api/stats":
            self.handle_stats_api()
        else:
            super().do_GET()

    def query_events_from_postgis(self):
        """
        PostGIS veritabanından SON 24 SAAT içindeki tüm GeoJSON olaylarını çeker.
        """
        if not PSYCOPG2_AVAILABLE:
            return None
            
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=3
            )
            cur = conn.cursor()
            
            # Son 24 saat içindeki tüm olayları zaman sırasına göre getir
            query = """
                SELECT raw_geojson FROM osiris_events 
                WHERE event_time >= NOW() - INTERVAL '24 hours' 
                   OR created_at >= NOW() - INTERVAL '24 hours'
                ORDER BY event_time DESC;
            """
            cur.execute(query)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            features = [r[0] for r in rows if r[0]]
            return {"type": "FeatureCollection", "features": features}
        except Exception as e:
            logging.info(f"[PostGIS UI Read]: DB sorgusu başarısız veya veri bekleniyor, dosyaya geçiliyor ({e})")
            return None

    def read_fallback_geojson(self):
        """PostGIS erişilemezse diskteki GeoJSON dosyasını okur."""
        possible_paths = [
            "../output/latest_osiris_events.geojson",
            "output/latest_osiris_events.geojson",
            "/tmp/latest_osiris_events.geojson"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return {"type": "FeatureCollection", "features": []}

    def handle_events_api(self):
        geojson_data = self.query_events_from_postgis()
        if not geojson_data or not geojson_data.get("features"):
            geojson_data = self.read_fallback_geojson()
            
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(geojson_data, ensure_ascii=False).encode("utf-8"))

    def handle_stats_api(self):
        geojson_data = self.query_events_from_postgis() or self.read_fallback_geojson()
        features = geojson_data.get("features", [])
        
        stats = {
          "total": len(features),
          "earthquakes": len([f for f in features if "earthquake" in (f.get("properties", {}).get("category") or "").lower()]),
          "disasters": len([f for f in features if "disaster" in (f.get("properties", {}).get("category") or "").lower() or "fire" in (f.get("properties", {}).get("category") or "").lower()]),
          "aviation": len([f for f in features if "aviation" in (f.get("properties", {}).get("category") or "").lower()]),
          "news": len([f for f in features if "news" in (f.get("properties", {}).get("category") or "").lower()])
        }
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(stats, ensure_ascii=False).encode("utf-8"))

def start_ui_server(port=PORT):
    handler = OsirisUIHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        logging.info(f"=== Bağımsız IRIS GEOINT Web UI Sunucusu http://localhost:{port} Adresinde Yayında ===")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("=== IRIS GEOINT Web UI Sunucusu Durduruldu ===")

if __name__ == "__main__":
    start_ui_server()
