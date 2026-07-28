import http.server
import socketserver
import json
import os
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

PORT = int(os.getenv("PORT", "8080"))
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")

class OsirisWebHandler(http.server.SimpleHTTPRequestHandler):
    """
    OSIRIS Web UI ve REST API Sunucusu İstek Yöneticisi
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_GET(self):
        parsed_path = urlparse(self.path).path
        
        # REST API Uç Noktaları
        if parsed_path == "/api/events":
            self.handle_events_api()
        elif parsed_path == "/api/stats":
            self.handle_stats_api()
        else:
            # Statik Dosya Sunumu (public/index.html, style.css, app.js vb.)
            super().do_GET()

    def handle_events_api(self):
        """GeoJSON canlı olay verilerini sunar."""
        # Okunacak muhtemel GeoJSON yolları
        possible_paths = [
            "output/latest_osiris_events.geojson",
            "/tmp/latest_osiris_events.geojson"
        ]
        
        geojson_data = {"type": "FeatureCollection", "features": []}
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        geojson_data = json.load(f)
                    break
                except Exception as e:
                    logging.error(f"[Web API] GeoJSON okuma hatası ({path}): {e}")
                    
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(geojson_data, ensure_ascii=False).encode("utf-8"))

    def handle_stats_api(self):
        """Kategori ve kaynak bazlı istatistik özetini döner."""
        possible_paths = [
            "output/latest_osiris_events.geojson",
            "/tmp/latest_osiris_events.geojson"
        ]
        
        features = []
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        features = json.load(f).get("features", [])
                    break
                except Exception:
                    pass
                    
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

def start_web_server(port=PORT):
    """Web UI sunucusunu başlatır."""
    handler = OsirisWebHandler
    # Reuse address
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        logging.info(f"=== OSIRIS Web UI Sunucusu Başlatıldı: http://localhost:{port} ===")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("=== OSIRIS Web UI Sunucusu Durduruldu ===")

if __name__ == "__main__":
    start_web_server()
