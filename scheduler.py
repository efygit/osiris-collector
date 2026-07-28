import time
import logging
from datetime import datetime, timezone
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def start_periodic_scheduler(job_function, interval_minutes=config.FETCH_INTERVAL_MINUTES, run_immediately=True):
    """
    Belirtilen aralıklarla (Varsayılan 10 dakikada bir) işlevi periyodik olarak çalıştıran döngü kütüphanesi.
    """
    interval_seconds = interval_minutes * 60
    logging.info(f"=== OSIRIS Geoint Scheduler Başlatıldı (Periyot: {interval_minutes} Dakika / {interval_seconds} Saniye) ===")
    
    cycle_count = 0
    if run_immediately:
        cycle_count += 1
        logging.info(f"\n--- [Döngü #{cycle_count}] İlk Veri Çekme Başlatılıyor ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}) ---")
        try:
            job_function()
        except Exception as e:
            logging.error(f"[Scheduler Job Error]: {e}")

    while True:
        try:
            logging.info(f"Sonraki veri güncellemesine {interval_minutes} dakika var ({datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}). Bekleniyor...")
            time.sleep(interval_seconds)
            
            cycle_count += 1
            logging.info(f"\n--- [Döngü #{cycle_count}] Periyodik Veri Çekme Başlatılıyor ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}) ---")
            job_function()
        except KeyboardInterrupt:
            logging.info("=== OSIRIS Scheduler Kullanıcı Tarafından Durduruldu ===")
            break
        except Exception as e:
            logging.error(f"[Scheduler Error]: {e}")
            time.sleep(10) # Hata durumunda 10 saniye bekleyip devam et
