// IRIS GEOINT Web UI Frontend Engine

let map;
let markerGroup;
let allFeatures = [];
let currentCategory = 'all';
let searchQuery = '';

// Zaman Filtresi Değişkenleri
let selectedMapHours = 24; // Harita ve KPI'lar için toplam saat seçeneği (6, 12, 18, 24)
let visibleFeedHours = 6;  // Yan panelde görüntülenen varsayılan saat dilimi (6'şar saat artar)

// Harita Tile Katmanları
const tileLayers = {
  dark: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    maxZoom: 19
  }),
  satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri',
    maxZoom: 18
  }),
  street: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  })
};

// Uygulama Başlatma
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  setupEventListeners();
  loadData();
  
  // Her 30 saniyede bir harita verilerini otomatik tazele
  setInterval(loadData, 30000);
});

// Harita İlklendirme
function initMap() {
  map = L.map('map', {
    center: [25.0, 30.0],
    zoom: 3,
    zoomControl: false,
    layers: [tileLayers.dark]
  });

  L.control.zoom({ position: 'bottomleft' }).addTo(map);
  markerGroup = L.layerGroup().addTo(map);
}

// Olay Dinleyicileri
function setupEventListeners() {
  // Sidebar Açılıp Kapanma Dinleyicisi
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const reopenBtn = document.getElementById('reopen-sidebar-btn');
  const toggleIcon = document.getElementById('toggle-icon');

  function toggleSidebar() {
    sidebar.classList.toggle('collapsed');
    const isCollapsed = sidebar.classList.contains('collapsed');
    
    if (isCollapsed) {
      if (toggleIcon) toggleIcon.className = 'fa-solid fa-chevron-right';
    } else {
      if (toggleIcon) toggleIcon.className = 'fa-solid fa-chevron-left';
    }
    
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 360);
  }

  if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
  if (reopenBtn) reopenBtn.addEventListener('click', toggleSidebar);

  // Zaman Filtresi Seçimi (Harita & KPI Saat Filtresi)
  const timeSelect = document.getElementById('time-range-select');
  if (timeSelect) {
    timeSelect.addEventListener('change', (e) => {
      selectedMapHours = parseInt(e.target.value, 10) || 24;
      visibleFeedHours = Math.min(6, selectedMapHours); // Haber akışını ilk 6 saate sıfırla
      renderFeedAndMap();
    });
  }

  // Daha Fazla Olay Göster (+6 Saat) Butonu
  const btnLoadMore = document.getElementById('btn-load-more');
  if (btnLoadMore) {
    btnLoadMore.addEventListener('click', () => {
      visibleFeedHours += 6;
      if (visibleFeedHours > selectedMapHours) visibleFeedHours = selectedMapHours;
      renderFeedAndMap();
    });
  }

  document.getElementById('btn-refresh').addEventListener('click', () => {
    const icon = document.getElementById('refresh-icon');
    icon.classList.add('fa-spin');
    loadData().finally(() => icon.classList.remove('fa-spin'));
  });

  document.getElementById('search-input').addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    renderFeedAndMap();
  });

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      const target = e.currentTarget;
      target.classList.add('active');
      currentCategory = target.getAttribute('data-category');
      renderFeedAndMap();
    });
  });

  document.getElementById('layer-dark').addEventListener('click', (e) => switchMapLayer('dark', e.currentTarget));
  document.getElementById('layer-satellite').addEventListener('click', (e) => switchMapLayer('satellite', e.currentTarget));
  document.getElementById('layer-street').addEventListener('click', (e) => switchMapLayer('street', e.currentTarget));

  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('event-modal').addEventListener('click', (e) => {
    if (e.target.id === 'event-modal') closeModal();
  });
}

function switchMapLayer(layerKey, btnElem) {
  document.querySelectorAll('.map-layer-btn').forEach(b => b.classList.remove('active'));
  btnElem.classList.add('active');

  Object.values(tileLayers).forEach(layer => map.removeLayer(layer));
  map.addLayer(tileLayers[layerKey]);
}

// Verileri API Uç Noktasından Çekme
async function loadData() {
  try {
    const response = await fetch('/api/events');
    if (!response.ok) throw new Error('API yanıt vermedi');
    const geojson = await response.json();
    
    allFeatures = geojson.features || [];
    renderFeedAndMap();
    
    document.getElementById('last-updated-time').innerText = new Date().toLocaleTimeString('tr-TR');
  } catch (err) {
    console.error('Veri yükleme hatası:', err);
  }
}

// Zaman Farkı Hesaplayıcı (Kaç Saat Önce?)
function getHoursAgo(eventTimeStr) {
  if (!eventTimeStr) return 0;
  const eventDate = new Date(eventTimeStr);
  const now = new Date();
  const diffMs = now - eventDate;
  return Math.max(0, diffMs / (1000 * 60 * 60));
}

// KPI Sayacı Güncelleme
function updateKPIs(features) {
  let eqCount = 0;
  let disCount = 0;
  let avCount = 0;
  let newsCount = 0;

  features.forEach(f => {
    const cat = (f.properties.category || '').toLowerCase();
    const src = (f.properties.source || '').toLowerCase();

    if (cat.includes('earthquake') || src.includes('usgs')) eqCount++;
    else if (cat.includes('disaster') || cat.includes('fire') || cat.includes('storm') || src.includes('eonet') || src.includes('gdacs')) disCount++;
    else if (cat.includes('aviation') || src.includes('opensky')) avCount++;
    else newsCount++;
  });

  document.getElementById('kpi-total').innerText = features.length;
  document.getElementById('kpi-earthquakes').innerText = eqCount;
  document.getElementById('kpi-disasters').innerText = disCount;
  document.getElementById('kpi-aviation').innerText = avCount;
  document.getElementById('kpi-news').innerText = newsCount;
}

// Filtrelenmiş Verileri Harita ve Yan Panele Basma
function renderFeedAndMap() {
  markerGroup.clearLayers();
  const listContainer = document.getElementById('events-list');
  listContainer.innerHTML = '';

  // 1. HARİTA & KPI FİLTRESİ (Seçilen Saat Aralığındaki Tüm Veriler)
  let mapFeatures = allFeatures.filter(f => {
    const hoursAgo = getHoursAgo(f.properties.event_time);
    // Eğer saat geçersiz ise veya seçilen zaman dilimi içindeyse
    return hoursAgo <= selectedMapHours;
  });

  updateKPIs(mapFeatures);

  // 2. KATEGORİ VE ARAMA FİLTRESİ
  let filtered = mapFeatures.filter(f => {
    const props = f.properties || {};
    const title = (props.title || '').toLowerCase();
    const desc = (props.description || '').toLowerCase();
    const cat = (props.category || '').toLowerCase();
    const src = (props.source || '').toLowerCase();

    let categoryMatch = false;
    if (currentCategory === 'all') categoryMatch = true;
    else if (currentCategory === 'earthquake' && (cat.includes('earthquake') || src.includes('usgs'))) categoryMatch = true;
    else if (currentCategory === 'disaster' && (cat.includes('disaster') || cat.includes('fire') || cat.includes('storm') || src.includes('eonet') || src.includes('gdacs'))) categoryMatch = true;
    else if (currentCategory === 'aviation' && (cat.includes('aviation') || src.includes('opensky'))) categoryMatch = true;
    else if (currentCategory === 'news' && !cat.includes('earthquake') && !cat.includes('disaster') && !cat.includes('aviation')) categoryMatch = true;

    let searchMatch = true;
    if (searchQuery) {
      searchMatch = title.includes(searchQuery) || desc.includes(searchQuery) || src.includes(searchQuery);
    }

    return categoryMatch && searchMatch;
  });

  // 3. Tarih/Saate Göre Sıralama (En Yeni Olay En Üstte)
  filtered.sort((a, b) => {
    const timeA = new Date(a.properties.event_time || 0).getTime();
    const timeB = new Date(b.properties.event_time || 0).getTime();
    return timeB - timeA;
  });

  // 4. HARİTAYA TÜM SEÇİLİ ZAMAN ARALIĞINDAKİ PİNLERİ EKLE
  filtered.forEach(feat => {
    const coords = feat.geometry.coordinates; // [lon, lat]
    const latLng = [coords[1], coords[0]];
    const marker = createCustomMarker(feat, latLng);
    markerGroup.addLayer(marker);
  });

  // 5. YAN PANEL HABER AKIŞI (6'şar Saatlik Kademeli Gösterim)
  let feedFeatures = filtered.filter(f => {
    const hoursAgo = getHoursAgo(f.properties.event_time);
    return hoursAgo <= visibleFeedHours;
  });

  if (feedFeatures.length === 0) {
    listContainer.innerHTML = `
      <div class="feed-loader">
        <i class="fa-solid fa-filter-circle-xmark"></i>
        <p>Seçilen ${visibleFeedHours} saatlik dilimde olay bulunamadı.</p>
      </div>`;
  } else {
    feedFeatures.forEach(feat => {
      const coords = feat.geometry.coordinates;
      const latLng = [coords[1], coords[0]];
      const card = createEventCard(feat, latLng);
      listContainer.appendChild(card);
    });
  }

  // 6. "DAHA FAZLA GÖSTER (+6 SAAT)" BUTONU GÜNCELLEMESİ
  const btnLoadMore = document.getElementById('btn-load-more');
  const rangeIndicator = document.getElementById('range-indicator-text');
  
  if (rangeIndicator) {
    rangeIndicator.innerText = `Panelde Gösterilen: Son ${Math.min(visibleFeedHours, selectedMapHours)} Saat (${feedFeatures.length} / ${filtered.length} Olay)`;
  }

  if (btnLoadMore) {
    if (visibleFeedHours >= selectedMapHours || feedFeatures.length >= filtered.length) {
      btnLoadMore.style.display = 'none';
    } else {
      btnLoadMore.style.display = 'flex';
      const nextLimit = Math.min(visibleFeedHours + 6, selectedMapHours);
      btnLoadMore.innerHTML = `<i class="fa-solid fa-angles-down"></i> Daha Fazla Göster (Son ${nextLimit} Saat)`;
    }
  }
}

// Özel İkonlu Harita Marker'ı
function createCustomMarker(feat, latLng) {
  const props = feat.properties;
  const cat = (props.category || '').toLowerCase();
  const src = (props.source || '').toLowerCase();

  let colorClass = 'primary';
  let iconHtml = '<i class="fa-solid fa-newspaper"></i>';

  if (cat.includes('earthquake') || src.includes('usgs')) {
    colorClass = 'danger';
    iconHtml = '<i class="fa-solid fa-house-crack"></i>';
  } else if (cat.includes('disaster') || src.includes('eonet') || src.includes('gdacs')) {
    colorClass = 'warning';
    iconHtml = '<i class="fa-solid fa-fire"></i>';
  } else if (cat.includes('aviation') || src.includes('opensky')) {
    colorClass = 'info';
    iconHtml = '<i class="fa-solid fa-plane"></i>';
  }

  const customHtmlIcon = L.divIcon({
    className: 'custom-map-pin',
    html: `<div class="marker-pin ${colorClass}">${iconHtml}</div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17]
  });

  const marker = L.marker(latLng, { icon: customHtmlIcon });
  marker.on('click', () => openModal(feat));
  return marker;
}

// Yan Panel Olay Kartı
function createEventCard(feat, latLng) {
  const props = feat.properties;
  const cat = (props.category || '').toLowerCase();
  const src = (props.source || '').toLowerCase();

  let badgeClass = 'news';
  let badgeLabel = 'Haber';

  if (cat.includes('earthquake') || src.includes('usgs')) { badgeClass = 'earthquake'; badgeLabel = 'Deprem'; }
  else if (cat.includes('disaster') || src.includes('eonet') || src.includes('gdacs')) { badgeClass = 'disaster'; badgeLabel = 'Afet'; }
  else if (cat.includes('aviation') || src.includes('opensky')) { badgeClass = 'aviation'; badgeLabel = 'Uçuş'; }

  const card = document.createElement('div');
  card.className = `event-card ${badgeClass}`;
  
  const formattedTime = props.event_time ? new Date(props.event_time).toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';

  card.innerHTML = `
    <div class="card-header">
      <span class="badge ${badgeClass}">${badgeLabel}</span>
      <span class="time-str">${formattedTime}</span>
    </div>
    <div class="card-title">${escapeHtml(props.title || 'Başlıksız Olay')}</div>
    <div class="card-meta">
      <span><i class="fa-solid fa-building"></i> ${escapeHtml(props.source || 'Bilinmiyor')}</span>
      <span class="location-type-tag">${props.location_type || 'EXACT'}</span>
    </div>
  `;

  card.addEventListener('click', () => {
    map.flyTo(latLng, 7, { duration: 1.5 });
    openModal(feat);
  });

  return card;
}

// Detay Modalını Açma
function openModal(feat) {
  const props = feat.properties;
  const modal = document.getElementById('event-modal');

  document.getElementById('modal-title').innerText = props.title || 'Başlıksız Olay';
  document.getElementById('modal-description').innerText = props.description || 'Detaylı açıklama bulunmuyor.';
  document.getElementById('modal-source').innerText = props.source || '-';
  document.getElementById('modal-publisher').innerText = props.publisher_country || '-';
  document.getElementById('modal-location-type').innerText = props.location_type || 'EXACT';
  document.getElementById('modal-time').innerText = props.event_time ? new Date(props.event_time).toLocaleString('tr-TR') : '-';
  document.getElementById('modal-coords').innerText = JSON.stringify(feat.geometry.coordinates);

  const linkBtn = document.getElementById('modal-link-btn');
  if (props.link) {
    linkBtn.href = props.link;
    linkBtn.style.display = 'inline-flex';
  } else {
    linkBtn.style.display = 'none';
  }

  modal.classList.add('open');
}

function closeModal() {
  document.getElementById('event-modal').classList.remove('open');
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
