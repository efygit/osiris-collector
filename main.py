import sys
import os
import logging
from datetime import datetime, timezone

import fetcher
import transformer
import database
import scheduler
import generate_excel
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_osiris_data_pipeline():
    """
    OSIRIS Geoint Veri Çekme, Dönüştürme, AI Konumlandırma ve PostGIS Kayıt Pipeline'ı
    """
    start_time = datetime.now(timezone.utc)
    logging.info("=" * 60)
    logging.info("OSIRIS DATA PIPELINE WORKER BAŞLATILDI")
    logging.info(f"Yapay Zeka Modeli: {config.OPENAI_MODEL} ({config.OPENAI_BASE_URL})")
    logging.info("=" * 60)
    
    # 1. VERİ ÇEKME (API & HTML)
    logging.info("\n[Aşama 1/4] OSIRIS Veri Kaynaklarından Veriler Çekiliyor...")
    raw_results = fetcher.fetch_all_sources()
    
    # 2. DÖNÜŞTÜRME & YAPAY ZEKA GEOCÖDİNG
    logging.info("\n[Aşama 2/4] Veriler GeoJSON Formatına Dönüştürülüyor ve Eksik Konumlar İçin AI Analizi Yapılıyor...")
    geojson_collection = transformer.process_fetched_sources_to_geojson(raw_results)
    feature_count = len(geojson_collection.get("features", []))
    logging.info(f"-> Toplam {feature_count} adet konumlandırılmış GeoJSON Feature oluşturuldu.")
    
    # 3. YEREL GeoJSON & PostGIS SQL ÇIKTISI OLUŞTURMA
    logging.info("\n[Aşama 3/4] Çıktılar Dosya Sistemine Kaydediliyor...")
    geojson_path = "output/latest_osiris_events.geojson"
    sql_path = "output/insert_osiris_events.sql"
    
    database.save_to_geojson_file(geojson_collection, output_path=geojson_path)
    database.export_postgis_sql_script(geojson_collection, output_sql_path=sql_path)
    
    # 4. PostGIS PostgreSQL VERİTABANINA KAYIT (Eğer DB Erişilebilir İse)
    logging.info("\n[Aşama 4/4] PostGIS PostgreSQL Veritabanı Güncelleniyor...")
    database.save_to_postgis_db(geojson_collection)
    
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logging.info("=" * 60)
    logging.info(f"OSIRIS PIPELINE WORKER BAŞARIYLA TAMAMLANDI! ({elapsed:.2f} saniye sürdü)")
    logging.info(f"Özet: {feature_count} olay işlendi | GeoJSON: {geojson_path} | PostGIS SQL: {sql_path}")
    logging.info("=" * 60)

def main():
    # 1. Excel Kataloğunu Hazırla (İzin korumalı)
    try:
        generate_excel.create_sources_excel("osiris_data_sources.xlsx")
    except Exception as e:
        logging.warning(f"[Excel Warning] Excel dosyası oluşturma atlandı: {e}")

    # 2. Komut satırı argümanı kontrolü (--once bayrağı tek seferlik çalıştırma içindir)
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        logging.info("Tek seferlik çalıştırma modu (--once)...")
        run_osiris_data_pipeline()
    else:
        # Her 10 dakikada bir çalışacak zamanlayıcıyı başlat
        scheduler.start_periodic_scheduler(
            job_function=run_osiris_data_pipeline,
            interval_minutes=config.FETCH_INTERVAL_MINUTES,
            run_immediately=True
        )

if __name__ == "__main__":
    main()
