import json
import os
import logging
from datetime import datetime, timezone
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

def save_to_geojson_file(geojson_data, output_path="output/latest_osiris_events.geojson"):
    """
    GeoJSON FeatureCollection verisini yere kaydeder.
    OpenShift / Konteyner ortamı için /tmp fallback korumalıdır.
    """
    try:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)
        logging.info(f"[GeoJSON Saver] Veriler '{output_path}' dosyasına başarıyla kaydedildi.")
    except (PermissionError, OSError) as e:
        tmp_path = f"/tmp/{os.path.basename(output_path)}"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, ensure_ascii=False, indent=2)
            logging.info(f"[GeoJSON Saver] Veriler yazılabilir '{tmp_path}' konumuna kaydedildi.")
        except Exception:
            logging.warning(f"[GeoJSON Saver Warning] Konteyner dosya yazma engeli: {e}")

def generate_postgis_sql_insert(feature):
    """
    Tek bir GeoJSON Feature'ından PostGIS ST_GeomFromGeoJSON uyumlu SQL INSERT cümlesi oluşturur.
    """
    props = feature["properties"]
    geometry_json = json.dumps(feature["geometry"])
    raw_geojson = json.dumps(feature, ensure_ascii=False).replace("'", "''")
    
    id_val = props.get("id", "").replace("'", "''")
    title_val = props.get("title", "").replace("'", "''")
    desc_val = props.get("description", "").replace("'", "''")
    source_val = props.get("source", "").replace("'", "''")
    cat_val = props.get("category", "").replace("'", "''")
    event_time_val = props.get("event_time", datetime.now(timezone.utc).isoformat())
    pub_country = props.get("publisher_country", "").replace("'", "''")
    loc_type = props.get("location_type", "EXACT")
    orig_fmt = props.get("original_format", "API")
    link_val = props.get("link", "").replace("'", "''")
    
    sql = f"""INSERT INTO osiris_events (id, title, description, source, category, event_time, publisher_country, location_type, original_format, link, raw_geojson, geom)
VALUES (
  '{id_val}',
  '{title_val}',
  '{desc_val}',
  '{source_val}',
  '{cat_val}',
  '{event_time_val}',
  '{pub_country}',
  '{loc_type}',
  '{orig_fmt}',
  '{link_val}',
  '{raw_geojson}'::jsonb,
  ST_SetSRID(ST_GeomFromGeoJSON('{geometry_json}'), 4326)
)
ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  event_time = EXCLUDED.event_time,
  geom = EXCLUDED.geom;
"""
    return sql

def export_postgis_sql_script(geojson_data, output_sql_path="output/insert_osiris_events.sql"):
    """
    GeoJSON koleksiyonunu toplu PostGIS SQL betiğine dönüştürür.
    """
    features = geojson_data.get("features", [])
    try:
        dir_name = os.path.dirname(output_sql_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(output_sql_path, "w", encoding="utf-8") as f:
            f.write("-- OSIRIS PostGIS Toplu Veri Ekleme Betiği\n")
            f.write("BEGIN;\n\n")
            for feat in features:
                f.write(generate_postgis_sql_insert(feat))
                f.write("\n")
            f.write("COMMIT;\n")
        logging.info(f"[PostGIS SQL Saver] '{output_sql_path}' SQL betiği oluşturuldu ({len(features)} kayıt).")
    except (PermissionError, OSError):
        tmp_sql_path = f"/tmp/{os.path.basename(output_sql_path)}"
        try:
            with open(tmp_sql_path, "w", encoding="utf-8") as f:
                f.write("-- OSIRIS PostGIS Toplu Veri Ekleme Betiği\nBEGIN;\n\n")
                for feat in features:
                    f.write(generate_postgis_sql_insert(feat))
                    f.write("\n")
                f.write("COMMIT;\n")
            logging.info(f"[PostGIS SQL Saver] SQL betiği yazılabilir '{tmp_sql_path}' konumuna kaydedildi.")
        except Exception:
            pass

def save_to_postgis_db(geojson_data):
    """
    PostgreSQL / PostGIS veritabanına doğrudan kayıt yapar (Eğer veritabanı aktif ise).
    """
    if not PSYCOPG2_AVAILABLE:
        logging.warning("[PostGIS DB] psycopg2 kütüphanesi yüklü değil, veritabanına doğrudan yazılamıyor.")
        return False
        
    try:
        conn = psycopg2.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            dbname=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            connect_timeout=3
        )
        cur = conn.cursor()
        
        # Tablonun varlığından emin ol (schema.sql oku veya direkt DDL çalıştır)
        schema_file_path = "schema.sql"
        if os.path.exists(schema_file_path):
            with open(schema_file_path, "r", encoding="utf-8") as s_file:
                cur.execute(s_file.read())
        else:
            # Inline schema fallback
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS osiris_events (
                    id VARCHAR(255) PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    source VARCHAR(100) NOT NULL,
                    category VARCHAR(100),
                    event_time TIMESTAMP WITH TIME ZONE,
                    publisher_country VARCHAR(100),
                    location_type VARCHAR(50),
                    original_format VARCHAR(20),
                    link TEXT,
                    raw_geojson JSONB,
                    geom GEOMETRY(Point, 4326),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
        features = geojson_data.get("features", [])
        for feat in features:
            sql = generate_postgis_sql_insert(feat)
            cur.execute(sql)
            
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"[PostGIS DB] {len(features)} olay PostGIS veritabanına başarıyla kaydedildi.")
        return True
    except Exception as e:
        logging.info(f"[PostGIS DB Bağlantısı Beklemede]: Bağlantı kurulamadı ({e}). Çıktılar SQL/GeoJSON dosyalarına aktarıldı.")
        return False
