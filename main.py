import streamlit as st  # Web tabanlı arayüz oluşturmak için kullanılan kütüphane
import pandas as pd     # Veri çerçeveleri (DataFrame) ve analizi için
import numpy as np      # Matematiksel hesaplamalar ve matris işlemleri için
import random           # Rastgele sayı ve seçim işlemleri için
import requests         # OSRM gibi harici API'lere HTTP istekleri göndermek için
from geopy import distance # Coğrafi koordinatlar arası mesafe hesaplama
import folium           # İnteraktif haritalar oluşturmak için
from streamlit_folium import st_folium # Folium haritalarını Streamlit'te göstermek için
import time             # Gecikme ve zamanlama işlemleri için
import json             # JSON dosyalarını okumak ve işlemek için


st.set_page_config(layout="wide", page_title="Balıkesir Rota Optimizasyonu", page_icon="📍")


st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #0f172a) !important;
        background-attachment: fixed !important;
    }
    
    * { font-family: 'Inter', sans-serif; color: #f8fafc; }
    
    .hero-title { 
        font-size: 3rem !important; 
        font-weight: 800 !important; 
        text-align: center; 
        margin-bottom: 2rem !important;
        background: linear-gradient(to right, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.5rem; 
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); 
        color: white !important; 
        font-weight: 700; 
        border: none;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6);
    }
    
    #MainMenu {visibility: hidden;}
    header {background: rgba(0,0,0,0) !important;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border-right: 1px solid #334155;
    }

    /* Merkezi Profesyonel Loader */
    .loader-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 80px 20px;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 20px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        margin: 20px 0;
    }
    .ring-loader {
        position: relative;
        width: 100px;
        height: 100px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .ring-loader span {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 4px solid transparent;
        border-top-color: #6366f1;
        animation: rotate 1.5s linear infinite;
    }
    .ring-loader span:nth-child(2) {
        width: 70%;
        height: 70%;
        border-top-color: #c084fc;
        animation-direction: reverse;
    }
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .loading-pulse {
        font-size: 1.4rem;
        font-weight: 600;
        margin-top: 25px;
        color: #818cf8;
        letter-spacing: 1px;
        animation: pulse 2s infinite;
        text-align: center;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    </style>
""", unsafe_allow_html=True)



# --- YARDIMCI FONKSİYONLAR ---

def show_professional_loader(text):
    """
    Uygulama yüklenirken veya hesaplama yaparken şık bir yükleme ekranı gösterir.
    
    Args:
        text (str): Yükleme ekranında görünecek metin.
    """
    st.markdown(f"""
        <div class="loader-container">
            <div class="ring-loader">
                <span></span>
                <span></span>
            </div>
            <div class="loading-pulse">{text}</div>
        </div>
    """, unsafe_allow_html=True)

def create_distance_matrix(points):
    """
    Verilen koordinat noktaları arasındaki mesafeleri hesaplayarak bir mesafe matrisi oluşturur.
    Öncelikle OSRM (Open Source Routing Machine) API'sini denir, başarısız olursa kuş uçuşu mesafe hesaplar.
    
    Args:
        points (list): (Lat, Lon) çiftlerinden oluşan liste.
    Returns:
        np.array: Noktalar arası mesafeleri içeren NxN boyutunda matris.
    """
    n = len(points)
    # OSRM API formatına uygun koordinat dizisi oluşturma (Lon,Lat;Lon,Lat...)
    coords = ";".join([f"{p[1]},{p[0]}" for p in points])
    # Kullanılacak API uç noktaları
    endpoints = [
        f"https://router.project-osrm.org/table/v1/car/{coords}?annotations=distance",
        f"https://routing.openstreetmap.de/routed-car/table/v1/car/{coords}?annotations=distance"
    ]
    
    # API'lerden veri çekmeyi dene
    for url in endpoints:
        try:
            r = requests.get(url, timeout=15) 
            if r.status_code == 200:
                data = r.json()
                if 'distances' in data: return np.array(data['distances'])
        except: continue # Hata durumunda bir sonraki API'ye geç
    
    # API'ler çalışmazsa Geodesic (kuş uçuşu) mesafe hesapla ve %20 yol payı ekle
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            dist = distance.geodesic(points[i], points[j]).meters * 1.2
            matrix[i][j] = matrix[j][i] = dist
    return matrix

class GeneticAlgorithm:
    """
    Gezgin Satıcı Problemi'ni (TSP) çözmek için Genetik Algoritma sınıfı.
    """
    def __init__(self, dist_matrix, pop_size, crossover_rate, mutation_rate, iterations):
        self.dist_matrix, self.pop_size = dist_matrix, pop_size
        self.crossover_rate, self.mutation_rate = crossover_rate, mutation_rate
        self.iterations = iterations
        self.n = len(dist_matrix)

    def create_individual(self):
        """Rastgele bir rota (birey) oluşturur."""
        route = list(range(self.n))
        random.shuffle(route)
        return route

    def calculate_fitness(self, route):
        """
        Rotanın toplam mesafesini hesaplar. Fitness değeri mesafenin tersidir.
        (Mesafe azaldıkça fitness artar)
        """
        dist = sum(self.dist_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
        dist += self.dist_matrix[route[-1]][route[0]] # Başlangıca geri dönüş
        return 1/dist, dist

    def solve(self):
        """
        Genetik algoritmayı çalıştırarak en iyi rotayı bulur.
        """
        # Başlangıç popülasyonunu oluştur
        pop = [self.create_individual() for _ in range(self.pop_size)]
        best_r, min_d = None, float('inf')
        
        for _ in range(self.iterations):
            # Popülasyonu mesafeye göre sırala (Seçilim basamağı için hazırlık)
            pop = sorted(pop, key=lambda r: self.calculate_fitness(r)[1])
            
            # En iyi çözümü güncelle
            if self.calculate_fitness(pop[0])[1] < min_d:
                min_d = self.calculate_fitness(pop[0])[1]
                best_r = pop[0]
                
            # Yeni nesil oluşturma
            new_pop = pop[:2] # Seçkinlik (Elitism): En iyi 2 bireyi doğrudan koru
            while len(new_pop) < self.pop_size:
                # Ebeveyn seçimi (Turnuva benzeri: ilk 10 birey arasından rastgele 2 tane)
                p1, p2 = random.sample(pop[:10], 2)
                
                # Çaprazlama (Crossover) - Sıralı Çaprazlama (Order Crossover)
                if random.random() < self.crossover_rate:
                    start, end = sorted(random.sample(range(self.n), 2))
                    child = [-1]*self.n
                    # Birinci ebeveynden bir kesiti kopyala
                    child[start:end] = p1[start:end]
                    # İkinci ebeveyndeki elemanlardan eksikleri tamamla (sırayı koruyarak)
                    p2_rem = [it for it in p2 if it not in child]
                    idx = 0
                    for i in range(self.n):
                        if child[i] == -1:
                            child[i] = p2_rem[idx]
                            idx += 1
                else: child = p1[:] # Çaprazlama olmazsa ebeveynin kopyasını al
                
                # Mutasyon - İki noktanın yerini değiştirme (Swap Mutation)
                if random.random() < self.mutation_rate:
                    i1, i2 = random.sample(range(self.n), 2)
                    child[i1], child[i2] = child[i2], child[i1]
                
                new_pop.append(child)
            pop = new_pop
            
        return best_r, min_d

def get_premium_table_html(df, is_matrix=False):
    """
    Pandas DataFrame'i şık bir HTML tabloya dönüştürür.
    """
    bg_main, bg_zebra, bg_header = "#0f172a", "#1e293b", "#1e1b4b"
    text_main, border_color = "#e2e8f0", "#334155"
    container_style = f"overflow-x: auto; border-radius: 15px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); border: 1px solid {border_color}; margin-bottom: 30px;"
    table_style = f"width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; background-color: {bg_main}; font-size: 13px;"
    header_style = f"background-color: {bg_header}; color: #818cf8; text-align: center; padding: 18px; font-weight: 800; border-bottom: 3px solid #4f46e5; text-transform: uppercase; letter-spacing: 0.05em;"
    cell_style = f"padding: 14px; text-align: center; border-bottom: 1px solid {border_color}; color: {text_main};"
    if is_matrix:
        table_style = table_style.replace("13px", "11px")
        cell_style += "white-space: nowrap;"
    html = f'<div style="{container_style}"><table style="{table_style}"><thead><tr><th style="{header_style}">#</th>'
    html += "".join([f'<th style="{header_style}">{c}</th>' for c in df.columns]) + '</tr></thead><tbody>'
    for i, row in df.iterrows():
        bg = bg_main if i % 2 == 0 else bg_zebra
        html += f'<tr style="background-color: {bg};"><td style="{cell_style} font-weight: bold; background-color: {bg_header}; color: #818cf8; border-right: 1px solid #4f46e5;">{i}</td>'
        for val in row:
            v_str = f"{val:.4f}" if isinstance(val, (float, np.float64)) else str(val)
            html += f'<td style="{cell_style}">{v_str}</td>'
        html += '</tr>'
    return html + '</tbody></table></div>'

# --- YAN MENÜ ---
with st.sidebar:
    st.header("GA Parametreleri")
    pop_size = st.slider("Popülasyon Sayısı", 10, 200, 50)
    iterations = st.number_input("İterasyon Sayısı", 10, 1000, 100)
    c_rate = st.slider("Çaprazlama Oranı", 0.1, 1.0, 0.8)
    m_rate = st.slider("Mutasyon Oranı", 0.01, 0.5, 0.1)
    st.divider()
    run_btn = st.button("Rotayı Optimize Et")
    
    # Noktaları Yenile: Tüm hafızayı temizle ve başa dön
    if st.button("Noktaları Yenile"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- ANA SAYFA ---
st.markdown('<h1 class="hero-title">Akıllı Rota Planlayıcı</h1>', unsafe_allow_html=True)

# --- HAZIRLIK AŞAMASI ---
# Sistem ilk açıldığında veya noktalar yenilendiğinde çalışır
if 'points' not in st.session_state:
    show_professional_loader("Sistem Hazırlanıyor: Veriler ve Mesafeler Alınıyor...")
    
    try:
        # JSON dosyasından veri çekme (Balıkesir ilçeleri/noktaları)
        json_path = r'c:\Users\Beytullah\Desktop\.PROJECTS\yapayzekafinal\dataset.json'
        with open(json_path, 'r', encoding='utf-8') as f:
            all_pts = json.load(f)
        # Mevcut veriler arasından rastgele 20 nokta seç
        sel = random.sample(all_pts, 20)
        st.session_state.points = [{"Lat": p["lat"], "Lon": p["lng"], "İlçe": p["ilce"]} for p in sel]
    except:
        # Dosya bulunamazsa veya hata oluşursa rastgele koordinatlar üret
        st.session_state.points = [{"Lat": random.uniform(39.5, 40.0), "Lon": random.uniform(27.5, 28.0), "İlçe": "Bilinmiyor"} for _ in range(20)]
    
    # Mesafe matrisini hesapla ve session_state'e kaydet (Tekrar hesaplamamak için)
    plist = [(p['Lat'], p['Lon']) for p in st.session_state.points]
    st.session_state.dist_matrix = create_distance_matrix(plist)
    
    time.sleep(1.5) # Loader'ın görünmesi için kısa bir bekleme
    st.rerun() # Sayfayı yenileyerek ana içeriğe geç
    st.stop() # Alt kısmın yüklenmesini kesin olarak engeller

# VERİ MEVCUTSA ANA İÇERİK
display_df = pd.DataFrame(st.session_state.points).rename(columns={"Lat": "Enlem", "Lon": "Boylam"})
best_route = st.session_state.get('best_route')

# --- OPTİMİZASYON İŞLEMİ ---
# Kullanıcı butona bastığında Genetik Algoritma tetiklenir
if run_btn:
    show_professional_loader("Genetik Algoritma Çalışıyor: En Kısa Rota Hesaplanıyor...")
    # Algoritma parametrelerini kullanıcı girişlerinden alarak nesne oluştur
    ga = GeneticAlgorithm(st.session_state.dist_matrix, pop_size, c_rate, m_rate, iterations)
    # Çözümü bul
    br, bd = ga.solve()
    # Sonuçları kaydet
    st.session_state.best_route, st.session_state.best_dist = br, bd
    time.sleep(1)
    st.rerun()

# SONUÇLAR VE HARİTA
if st.session_state.get('best_dist'):
    c1, c2 = st.columns(2)
    with c1: st.success(f"Optimizasyon Tamamlandı! | Mesafe: {st.session_state.best_dist/1000:.2f} km")
    with c2: st.info(f"Sıralama: {' ➔ '.join([f'**{idx}**' for idx in best_route])}")

st.divider()
st.subheader("Balıkesir Optimizasyon Haritası")
# Haritayı Balıkesir merkezli olarak başlat
m = folium.Map(location=[39.6484, 27.8826], zoom_start=9, tiles='CartoDB dark_matter')

all_coords = []
# Noktaları (Durakları) haritaya işaretle
for i, p in enumerate(st.session_state.points):
    coord = [p['Lat'], p['Lon']]
    all_coords.append(coord)
    # Modern 'Cyber' Nokta Tasarımı
    folium.CircleMarker(
        location=coord,
        radius=8,
        popup=f"<b>Durak {i}</b><br>İlçe: {p['İlçe']}",
        tooltip=f"Durak {i}",
        color="#818cf8",
        weight=3,
        fill=True,
        fill_color="#1e1b4b",
        fill_opacity=1
    ).add_to(m)

# Eğer en iyi rota hesaplanmışsa harita üzerinde göster
if best_route:
    # Rota çizgileri için renk paleti
    colors = ['#e11d48', '#d946ef', '#8b5cf6', '#6366f1', '#3b82f6', '#0ea5e9', '#06b6d4', '#14b8a6', '#10b981', '#22c55e', '#84cc16', '#eab308', '#f59e0b', '#f97316', '#ef4444']
    s_p, e_p = st.session_state.points[best_route[0]], st.session_state.points[best_route[-1]]
    # Başlangıç ve bitiş noktalarına özel ikon ekle
    folium.Marker([s_p['Lat'], s_p['Lon']], popup="🚀 BAŞLANGIÇ", icon=folium.Icon(color='green', icon='play', prefix='fa')).add_to(m)
    folium.Marker([e_p['Lat'], e_p['Lon']], popup="🏁 BİTİŞ", icon=folium.Icon(color='red', icon='flag', prefix='fa')).add_to(m)
    
    # Rota üzerinden döngü kurarak yolları ve mesafeleri çiz
    for idx in range(len(best_route)):
        # İki nokta arası bağlantıyı al (Son noktayı başlangıca bağlamak için modül alıyoruz)
        i1, i2 = best_route[idx], best_route[(idx+1)%len(best_route)]
        p1, p2 = st.session_state.points[i1], st.session_state.points[i2]
        
        # İki nokta arası mesafe (KM cinsinden)
        dist_km = st.session_state.dist_matrix[i1][i2] / 1000
        
        # Orta nokta hesapla (Mesafe yazısını yolun ortasına koymak için)
        mid_lat = (p1['Lat'] + p2['Lat']) / 2
        mid_lon = (p1['Lon'] + p2['Lon']) / 2
        
        # Hareketli (Karınca) Yol Çizgisi (AntPath)
        folium.plugins.AntPath(
            locations=[[p1['Lat'],p1['Lon']],[p2['Lat'],p2['Lon']]], 
            color=colors[idx%len(colors)], 
            weight=5,
            delay=1000
        ).add_to(m)
        
        # KM Yazısını Haritaya Ekle (Kalıcı Yazı)
        folium.Marker(
            [mid_lat, mid_lon],
            icon=folium.DivIcon(
                html=f"""<div style="
                    font-family: 'Inter', sans-serif; 
                    color: white; 
                    font-weight: 800; 
                    font-size: 11px;
                    background-color: rgba(15, 23, 42, 0.7);
                    padding: 2px 6px;
                    border-radius: 8px;
                    border: 1px solid {colors[idx%len(colors)]};
                    white-space: nowrap;
                    box-shadow: 0 0 10px {colors[idx%len(colors)]};
                    ">{dist_km:.1f} km</div>"""
            )
        ).add_to(m)

st_folium(m, width=1200, returned_objects=[])

st.divider()
st.subheader("Durak Bilgileri")
st.markdown(get_premium_table_html(display_df), unsafe_allow_html=True)
if st.session_state.get('dist_matrix') is not None:
    st.divider()
    st.subheader("Mesafe Matrisi (Metre)")
    df_m = pd.DataFrame(st.session_state.dist_matrix).astype(int)
    st.markdown(get_premium_table_html(df_m, is_matrix=True), unsafe_allow_html=True)