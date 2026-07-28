import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def parse_xml_safely(content):
    """BS4 xml ve html.parser arasında esnek geçiş sağlar."""
    try:
        return BeautifulSoup(content, "xml")
    except Exception:
        try:
            return BeautifulSoup(content, "lxml")
        except Exception:
            return BeautifulSoup(content, "html.parser")

def fetch_usgs_earthquakes(limit=15):
    """
    USGS Deprem API'sinden en güncel deprem verilerini JSON (GeoJSON) olarak çeker.
    """
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit={limit}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info(f"[USGS API] {len(data.get('features', []))} deprem verisi çekildi.")
        return {
            "source": "USGS Earthquakes",
            "type": "API",
            "raw_items": data.get("features", [])
        }
    except Exception as e:
        logging.error(f"[USGS API Error]: {e}")
        return {"source": "USGS Earthquakes", "type": "API", "raw_items": []}

def fetch_nasa_eonet(limit=15):
    """
    NASA EONET API'sinden güncel doğal afet ve çevre olaylarını JSON olarak çeker.
    """
    url = f"https://eonet.gsfc.nasa.gov/api/v3/events?limit={limit}&status=open"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        events = data.get("events", [])
        logging.info(f"[NASA EONET API] {len(events)} afet olayı çekildi.")
        return {
            "source": "NASA EONET",
            "type": "API",
            "raw_items": events
        }
    except Exception as e:
        logging.error(f"[NASA EONET API Error]: {e}")
        return {"source": "NASA EONET", "type": "API", "raw_items": []}

def fetch_gdacs_events():
    """
    GDACS (Global Disaster Alert System) API'sinden güncel afet uyarılarını JSON/XML olarak çeker.
    """
    url = "https://www.gdacs.org/xml/rss.xml"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = parse_xml_safely(response.content)
        items = soup.find_all("item")
        parsed_items = []
        for item in items[:15]:
            title = item.find("title").text if item.find("title") else ""
            desc = item.find("description").text if item.find("description") else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") else ""
            link = item.find("link").text if item.find("link") else ""
            point = item.find("georss:point") or item.find("point")
            coords = None
            if point and point.text:
                parts = point.text.strip().split()
                if len(parts) == 2:
                    coords = [float(parts[1]), float(parts[0])]
            
            parsed_items.append({
                "title": title,
                "description": desc,
                "pub_date": pub_date,
                "link": link,
                "coords": coords
            })
        logging.info(f"[GDACS API] {len(parsed_items)} küresel afet uyarısı çekildi.")
        return {"source": "GDACS Disasters", "type": "API", "raw_items": parsed_items}
    except Exception as e:
        logging.error(f"[GDACS API Error]: {e}")
        return {"source": "GDACS Disasters", "type": "API", "raw_items": []}

def fetch_opensky_flights(limit=10):
    """
    OpenSky Network API'sinden uçuş pozisyonlarını JSON olarak çeker.
    """
    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        states = data.get("states", []) or []
        valid_flights = [s for s in states if s[5] is not None and s[6] is not None][:limit]
        logging.info(f"[OpenSky API] {len(valid_flights)} canlı uçuş verisi çekildi.")
        return {"source": "OpenSky Network", "type": "API", "raw_items": valid_flights}
    except Exception as e:
        logging.error(f"[OpenSky API Error]: {e}")
        return {"source": "OpenSky Network", "type": "API", "raw_items": []}

def fetch_html_news_source(site_name, feed_url):
    """
    Haber sitelerinin RSS/HTML akışından en güncel haber metinlerini, başlıklarını ve tarihlerini çeker.
    """
    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        
        items = []
        if "xml" in content_type or feed_url.endswith(".xml") or feed_url.endswith("/rss"):
            soup = parse_xml_safely(response.content)
            raw_items = soup.find_all("item")
            for item in raw_items[:10]:
                title = item.find("title").text if item.find("title") else ""
                desc = item.find("description").text if item.find("description") else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") else ""
                link = item.find("link").text if item.find("link") else ""
                
                desc_text = BeautifulSoup(desc, "html.parser").get_text(strip=True) if desc else ""
                
                items.append({
                    "title": title.strip(),
                    "text": desc_text,
                    "pub_date": pub_date,
                    "link": link,
                    "site_name": site_name
                })
        else:
            soup = BeautifulSoup(response.content, "html.parser")
            articles = soup.find_all("article") or soup.find_all("h3")
            for art in articles[:10]:
                title = art.get_text(strip=True)
                link_tag = art.find("a")
                link = link_tag["href"] if link_tag and link_tag.has_attr("href") else feed_url
                items.append({
                    "title": title,
                    "text": title,
                    "pub_date": datetime.now(timezone.utc).isoformat(),
                    "link": link,
                    "site_name": site_name
                })
                
        logging.info(f"[{site_name} HTML/RSS] {len(items)} haber makalesi çekildi.")
        return {"source": site_name, "type": "HTML", "raw_items": items}
    except Exception as e:
        logging.error(f"[{site_name} Scraping Error]: {e}")
        return {"source": site_name, "type": "HTML", "raw_items": []}

def fetch_all_sources():
    """
    Tüm OSIRIS veri kaynaklarından en güncel verileri toplar.
    """
    results = []
    # 1. API kaynakları (JSON / XML API)
    results.append(fetch_usgs_earthquakes())
    results.append(fetch_nasa_eonet())
    results.append(fetch_gdacs_events())
    results.append(fetch_opensky_flights())
    
    # 2. HTML / RSS Haber kaynakları
    news_sources = [
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("BBC News", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("France 24", "https://www.france24.com/en/rss")
    ]
    
    for name, url in news_sources:
        results.append(fetch_html_news_source(name, url))
        
    return results
