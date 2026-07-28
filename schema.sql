-- PostGIS Eklentisini Etkinleştir
CREATE EXTENSION IF NOT EXISTS postgis;

-- OSIRIS Geoint Olaylar Tablosu (PostgreSQL / PostGIS Uyumlu)
CREATE TABLE IF NOT EXISTS osiris_events (
    id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    source VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    event_time TIMESTAMP WITH TIME ZONE,
    publisher_country VARCHAR(100),
    location_type VARCHAR(50), -- 'EXACT', 'CITY', 'COUNTRY', 'PUBLISHER'
    original_format VARCHAR(20), -- 'API', 'HTML'
    link TEXT,
    raw_geojson JSONB,
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PostGIS Mekansal (Spatial GiST) İndeksi
CREATE INDEX IF NOT EXISTS osiris_events_geom_idx ON osiris_events USING GIST (geom);
CREATE INDEX IF NOT EXISTS osiris_events_source_idx ON osiris_events (source);
CREATE INDEX IF NOT EXISTS osiris_events_time_idx ON osiris_events (event_time);
