import json
import logging
from openai import OpenAI
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_openai_client():
    if not config.OPENAI_API_KEY:
        return None
    try:
        client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL
        )
        return client
    except Exception as e:
        logging.error(f"[AI Geocoder] Client hatası: {e}")
        return None

def estimate_location_with_ai(title, text, publisher_source_name):
    """
    Yapay Zeka (OpenAI SDK / Gemini API formatı) kullanarak konum ve koordinat tahmini yapar.
    
    Kurallar:
    1. Şehir/Eyalet metinde varsa -> Şehrin/Eyaletin koordinatı ve adı.
    2. Şehir yok ama Ülke varsa -> Ülke merkez koordinatı.
    3. Metinde hiç ülke ipucu yoksa -> Yayıncı sitenin ülkesi ve koordinatı.
    """
    publisher_info = config.PUBLISHER_COUNTRIES.get(publisher_source_name, {"country": "International", "coords": [0.0, 0.0]})
    publisher_country = publisher_info["country"]
    publisher_coords = publisher_info["coords"]
    
    prompt = f"""Metin ve Başlığı analiz ederek olayın gerçekleştiği coğrafi konumu tespit et.
Metin Başlığı: {title}
Metin İçeriği: {text}
Yayıncı Sitenin Ülkesi: {publisher_country}

Aşağıdaki JSON formatında yanıt ver (Başka hiçbir açıklama yazma):
{{
  "city": "Şehir veya Eyalet adı (Metinden tespit edilebiliyorsa yaz, edilemiyorsa null)",
  "country": "Ülke adı (Metinden tespit edilebiliyorsa yaz, edilemiyorsa null)",
  "latitude": 0.0 (Enlem float - Tespit edilen şehir, eyalet veya ülkenin merkez enlemi. Metinde hiç ipucu yoksa null),
  "longitude": 0.0 (Boylam float - Tespit edilen şehir, eyalet veya ülkenin merkez boylamı. Metinde hiç ipucu yoksa null),
  "location_type": "CITY" veya "COUNTRY" veya "PUBLISHER"
}}
"""

    client = get_openai_client()
    if client:
        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Sen hassas coğrafi konum analizi yapan bir GeoINT yapay zekasısın. Sadece istenen JSON formatında yanıt üretirsin."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            res_json = json.loads(content)
            
            lat = res_json.get("latitude")
            lon = res_json.get("longitude")
            city = res_json.get("city")
            country = res_json.get("country")
            
            if lat is not None and lon is not None and (lat != 0.0 or lon != 0.0):
                return {
                    "coords": [float(lon), float(lat)], # GeoJSON [Longitude, Latitude]
                    "city": city,
                    "country": country or publisher_country,
                    "location_type": "CITY" if city else ("COUNTRY" if country else "PUBLISHER"),
                    "source_rule": "AI_ESTIMATED"
                }
        except Exception as e:
            logging.warning(f"[AI Geocoder API Çağrısı Başarısız / Kural Motoruna Geçiliyor]: {e}")

    # --- KURAL VE KELİME TABANLI GEOCÖDİNG ---
    full_text = f"{title} {text}".lower()
    
    # 1. Metinde bilinen Şehir/Eyalet veya Ülke ismi geçiyor mu? (Örn: Texas, California, Washington, Gaza)
    for loc_name, coords in config.LOCATION_CENTROIDS.items():
        if loc_name in full_text:
            return {
                "coords": coords,
                "city": loc_name.title(),
                "country": loc_name.title(),
                "location_type": "CITY" if loc_name in ["texas", "california", "florida", "london", "paris", "tokyo", "gaza", "beirut", "kyiv", "moscow"] else "COUNTRY",
                "source_rule": "RULE_LOCATION_MATCH"
            }
            
    # 2. Hiçbir ülke/şehir ipucu bulunamazsa yayıncı sitenin merkez ülkesini ve koordinatını ata
    return {
        "coords": publisher_coords,
        "city": None,
        "country": publisher_country,
        "location_type": "PUBLISHER",
        "source_rule": "PUBLISHER_COUNTRY_FALLBACK"
    }
