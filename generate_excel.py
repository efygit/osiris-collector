import pandas as pd
import os

def create_sources_excel(file_path="osiris_data_sources.xlsx"):
    """
    OSIRIS platformunun kullandığı veri kaynaklarının detaylı Excel kataloğunu oluşturur.
    OpenShift / Konteyner izin kısıtlamalarına karşı esnek yazma mantığı içerir.
    """
    data = [
        {
            "Kaynak Adı": "USGS Earthquakes",
            "Veri Formatı": "API (JSON/GeoJSON)",
            "URL / Endpoint": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson",
            "Kategori": "Seismology / Earthquakes",
            "Yayıncı Ülke": "United States",
            "Çekilme Sıklığı": "Her 10 Dakikada Bir",
            "Konum Tipi": "Doğrudan Hassas Koordinat (EXACT)",
            "Açıklama": "Küresel 2.5+ büyüklükteki depremleri gerçek zamanlı GeoJSON API olarak sunar."
        },
        {
            "Kaynak Adı": "NASA EONET",
            "Veri Formatı": "API (JSON)",
            "URL / Endpoint": "https://eonet.gsfc.nasa.gov/api/v3/events",
            "Kategori": "Environmental / Wildfires & Storms",
            "Yayıncı Ülke": "United States",
            "Çekilme Sıklığı": "Her 10 Dakikada Bir",
            "Konum Tipi": "Doğrudan Hassas Koordinat (EXACT)",
            "Açıklama": "NASA Dünya Gözlemevi doğal afet, yangın ve fırtına olaylarını sunar."
        },
        {
            "Kaynak Adı": "GDACS Disasters",
            "Veri Formatı": "API (RSS / XML)",
            "URL / Endpoint": "https://www.gdacs.org/xml/rss.xml",
            "Kategori": "Global Disaster Alerts",
            "Yayıncı Ülke": "Switzerland (UN / EC)",
            "Çekilme Sıklığı": "Her 10 Dakikada Bir",
            "Konum Tipi": "Doğrudan Koordinat / AI Tahmin",
            "Açıklama": "BM ve AB Küresel Afet Uyarısı ve Koordinasyon Sistemi olay akışı."
        },
        {
            "Kaynak Adı": "OpenSky Network",
            "Veri Formatı": "API (JSON)",
            "URL / Endpoint": "https://opensky-network.org/api/states/all",
            "Kategori": "Aviation Tracking",
            "Yayıncı Ülke": "Switzerland",
            "Çekilme Sıklığı": "Her 10 Dakikada Bir",
            "Konum Tipi": "Doğrudan Hassas Koordinat (EXACT)",
            "Açıklama": "Canlı ticari ve askeri uçuş pozisyonları ve uçak transponder verileri."
        },
        {
            "Kaynak Adı": "Al Jazeera News",
            "Veri Formatı": "HTML / RSS Scraping",
            "URL / Endpoint": "https://www.aljazeera.com/xml/rss/all.xml",
            "Kategori": "Global News / Conflict",
            "Yayıncı Ülke": "Qatar",
            "Çekilme Sıklığı": "Her 10 Dakikada Bir",
            "Konum Tipi": "Yapay Zeka Tahminli (Gemini 3.1 Flash)",
            "Açıklama": "Küresel haberler ve sıcak gelişme metinleri (AI ile Şehir/Ülke geocoded)."
        },
        {
            "Kaynak Adı": "BBC News World",
            "Veri Formatı": "HTML / RSS Scraping",
            "URL / Endpoint": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "Kategori": "Global News",
            "Yayıncı Ülke": "United Kingdom",
            "Çekilme Sıklığı": "Her 10 Dakikada Bir",
            "Konum Tipi": "Yapay Zeka Tahminli (Gemini 3.1 Flash)",
            "Açıklama": "Dünya haber başlıkları ve metin içerikleri."
        },
        {
            "Kaynak Adı": "France 24",
            "Veri Formatı": "HTML / RSS Scraping",
            "URL / Endpoint": "https://www.france24.com/en/rss",
            "Kategori": "Global News / Security",
            "Yayıncı Ülke": "France",
            "Çekilme Sıklığı": "Her 10 Dakikada Bir",
            "Konum Tipi": "Yapay Zeka Tahminli (Gemini 3.1 Flash)",
            "Açıklama": "Uluslararası haberler ve jeopolitik gelişmeler."
        }
    ]

    df = pd.DataFrame(data)
    
    # Yazılabilir hedef yolları sırayla dene (Kök dizin -> output/ -> /tmp/)
    target_paths = [file_path, "output/osiris_data_sources.xlsx", "/tmp/osiris_data_sources.xlsx"]
    
    for path in target_paths:
        try:
            parent_dir = os.path.dirname(path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
                
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="OSIRIS Veri Kaynakları", index=False)
                worksheet = writer.sheets["OSIRIS Veri Kaynakları"]
                
                for col in worksheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = col[0].column_letter
                    worksheet.column_dimensions[col_letter].width = max(max_len + 4, 15)

            print(f"[Excel Catalog] Excel dosyası kaydedildi: {os.path.abspath(path)}")
            return path
        except (PermissionError, OSError) as e:
            print(f"[Excel Catalog Warning] '{path}' konumuna yazma izni yok ({e}). Alternatif deneniyor...")
            
    print("[Excel Catalog Warning] Konteyner dosya sistemi yazma korumalı, Excel oluşturma atlandı.")
    return None

if __name__ == "__main__":
    create_sources_excel()
