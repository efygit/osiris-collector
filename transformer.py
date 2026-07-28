import uuid
from datetime import datetime, timezone
import ai_geocoder
import config

def transform_to_geojson_feature(title, description, source, category, coords, location_type, publisher_country, link=None, original_format="API", extra_props=None):
    """
    Herhangi bir veri kaynağı girdisini standart WGS84 GeoJSON Feature formatına dönüştürür.
    """
    if extra_props is None:
        extra_props = {}
        
    feature_id = extra_props.get("id") or f"{source.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
    
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": {
            "type": "Point",
            "coordinates": coords # [longitude, latitude]
        },
        "properties": {
            "id": feature_id,
            "title": title,
            "description": description or "",
            "source": source,
            "category": category,
            "event_time": extra_props.get("event_time") or datetime.now(timezone.utc).isoformat(),
            "publisher_country": publisher_country,
            "location_type": location_type, # 'EXACT', 'CITY', 'COUNTRY', 'PUBLISHER'
            "link": link or "",
            "original_format": original_format,
            **extra_props
        }
    }

def transform_usgs_item(raw_item):
    """USGS Deprem API verisini GeoJSON Feature'a dönüştürür."""
    props = raw_item.get("properties", {})
    geom = raw_item.get("geometry", {})
    coords = geom.get("coordinates", [0.0, 0.0])[:2] # [lon, lat]
    
    time_ms = props.get("time")
    event_time = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc).isoformat() if time_ms else datetime.now(timezone.utc).isoformat()
    
    return transform_to_geojson_feature(
        title=props.get("title", "Earthquake Event"),
        description=f"Magnitude: {props.get('mag')}, Place: {props.get('place')}",
        source="USGS Earthquakes",
        category="earthquake",
        coords=coords,
        location_type="EXACT",
        publisher_country="United States",
        link=props.get("url"),
        original_format="API",
        extra_props={"event_time": event_time, "magnitude": props.get("mag")}
    )

def transform_nasa_eonet_item(raw_item):
    """NASA EONET Afet API verisini GeoJSON Feature'a dönüştürür."""
    geometries = raw_item.get("geometry", [])
    coords = [0.0, 0.0]
    if geometries and "coordinates" in geometries[0]:
        c = geometries[0]["coordinates"]
        if isinstance(c[0], list): # Polygon / Multipoint durumu
            c = c[0]
        coords = [float(c[0]), float(c[1])]
        
    categories = raw_item.get("categories", [{}])
    cat_title = categories[0].get("title", "natural_disaster") if categories else "natural_disaster"
    
    return transform_to_geojson_feature(
        title=raw_item.get("title", "Natural Event"),
        description=raw_item.get("description", ""),
        source="NASA EONET",
        category=cat_title,
        coords=coords,
        location_type="EXACT",
        publisher_country="United States",
        link=raw_item.get("link"),
        original_format="API",
        extra_props={"eonet_id": raw_item.get("id")}
    )

def transform_gdacs_item(raw_item):
    """GDACS Afet Uyarısı verisini GeoJSON Feature'a dönüştürür."""
    coords = raw_item.get("coords")
    loc_type = "EXACT"
    
    # Koordinat eksikse AI ile tahmin et
    if not coords:
        ai_res = ai_geocoder.estimate_location_with_ai(raw_item.get("title", ""), raw_item.get("description", ""), "GDACS Disasters")
        coords = ai_res["coords"]
        loc_type = ai_res["location_type"]
        
    return transform_to_geojson_feature(
        title=raw_item.get("title", "Disaster Alert"),
        description=raw_item.get("description", ""),
        source="GDACS Disasters",
        category="disaster_alert",
        coords=coords,
        location_type=loc_type,
        publisher_country="Switzerland",
        link=raw_item.get("link"),
        original_format="API"
    )

def transform_opensky_item(raw_item):
    """OpenSky Uçuş verisini GeoJSON Feature'a dönüştürür."""
    # raw_item format: [icao24, callsign, origin_country, time_position, last_contact, longitude, latitude, altitude, ...]
    callsign = (raw_item[1] or "UNKNOWN").strip()
    origin_country = raw_item[2] or "Unknown"
    lon = float(raw_item[5])
    lat = float(raw_item[6])
    
    return transform_to_geojson_feature(
        title=f"Flight {callsign} ({origin_country})",
        description=f"ICAO24: {raw_item[0]}, Country: {origin_country}, Altitude: {raw_item[7]}m",
        source="OpenSky Network",
        category="aviation",
        coords=[lon, lat],
        location_type="EXACT",
        publisher_country="Switzerland",
        original_format="API",
        extra_props={"callsign": callsign, "icao24": raw_item[0]}
    )

def transform_html_news_item(raw_item):
    """
    HTML / RSS Haber makalesini Yapay Zeka Geocoding süzgecinden geçirerek GeoJSON Feature'a dönüştürür.
    """
    site_name = raw_item.get("site_name", "News Source")
    title = raw_item.get("title", "")
    text = raw_item.get("text", "")
    
    # Yapay zeka ile konum tahmini
    ai_res = ai_geocoder.estimate_location_with_ai(title, text, site_name)
    
    publisher_info = config.PUBLISHER_COUNTRIES.get(site_name, {"country": "Unknown"})
    
    return transform_to_geojson_feature(
        title=title,
        description=text,
        source=site_name,
        category="news",
        coords=ai_res["coords"],
        location_type=ai_res["location_type"],
        publisher_country=publisher_info["country"],
        link=raw_item.get("link"),
        original_format="HTML",
        extra_props={
            "estimated_city": ai_res.get("city"),
            "estimated_country": ai_res.get("country"),
            "geocoding_rule": ai_res.get("source_rule")
        }
    )

def process_fetched_sources_to_geojson(fetched_results):
    """
    Tüm veri kaynaklarından çekilen paketleri işler ve tek bir GeoJSON FeatureCollection oluşturur.
    """
    features = []
    
    for bundle in fetched_results:
        source = bundle["source"]
        raw_items = bundle["raw_items"]
        
        for item in raw_items:
            try:
                if source == "USGS Earthquakes":
                    features.append(transform_usgs_item(item))
                elif source == "NASA EONET":
                    features.append(transform_nasa_eonet_item(item))
                elif source == "GDACS Disasters":
                    features.append(transform_gdacs_item(item))
                elif source == "OpenSky Network":
                    features.append(transform_opensky_item(item))
                else: # Al Jazeera, BBC, France 24 HTML/RSS Haberleri
                    features.append(transform_html_news_item(item))
            except Exception as e:
                print(f"[Transform Error for {source}]: {e}")
                
    return {
        "type": "FeatureCollection",
        "features": features
    }
