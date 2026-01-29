import streamlit as st  
import pandas as pd     
import numpy as np      
import random           
import requests         
from geopy import distance 
import folium           
from streamlit_folium import st_folium 
import time             
import json             
import os  # Dosya yolları için eklendi

# Sayfa yapılandırması
st.set_page_config(layout="wide", page_title="Balıkesir Rota Optimizasyonu", page_icon="📍")

# Modern CSS Tasarımı
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background: radial-gradient(circle at top right, #1e1b4b, #0f172a) !important; background-attachment: fixed !important; }
    * { font-family: 'Inter', sans-serif; color: #f8fafc; }
    .hero-title { font-size: 3rem !important; font-weight: 800 !important; text-align: center; margin-bottom: 2rem !important;
        background: linear-gradient(to right, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5rem; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); 
        color: white !important; font-weight: 700; border: none; box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4); transition: all 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6); }
    .loader-container { display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 80px 20px; 
        background: rgba(15, 23, 42, 0.5); border-radius: 20px; border: 1px solid rgba(99, 102, 241, 0.2); margin: 20px 0; }
    .ring-loader { position: relative; width: 100px; height: 100px; display: flex; justify-content: center; align-items: center; }
    .ring-loader span { position: absolute; width: 100%; height: 100%; border-radius: 50%; border: 4px solid transparent; 
        border-top-color: #6366f1; animation: rotate 1.5s linear infinite; }
    .ring-loader span:nth-child(2) { width: 70%; height: 70%; border-top-color: #c084fc; animation-direction: reverse; }
    @keyframes rotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .loading-pulse { font-size: 1.4rem; font-weight: 600; margin-top: 25px; color: #818cf8; animation: pulse 2s infinite; text-align: center; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---

def show_professional_loader(text):
    st.markdown(f"""
        <div class="loader-container">
            <div class="ring-loader"><span></span><span></span></div>
            <div class="loading-pulse">{text}</div>
        </div>
    """, unsafe_allow_html=True)

def create_distance_matrix(points):
    n = len(points)
    coords = ";".join([f"{p[1]},{p[0]}" for p in points])
    endpoints = [
        f"https://router.project-osrm.org/table/v1/car/{coords}?annotations=distance",
        f"https://routing.openstreetmap.de/routed-car/table/v1/car/{coords}?annotations=distance"
    ]
    
    for url in endpoints:
        try:
            r = requests.get(url, timeout=15) 
            if r.status_code == 200:
                data = r.json()
                if 'distances' in data: return np.array(data['distances'])
        except: continue 
    
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            dist = distance.geodesic(points[i], points[j]).meters * 1.2
            matrix[i][j] = matrix[j][i] = dist
    return matrix

class GeneticAlgorithm:
    def __init__(self, dist_matrix, pop_size, crossover_rate, mutation_rate, iterations):
        self.dist_matrix, self.pop_size = dist_matrix, pop_size
        self.crossover_rate, self.mutation_rate = crossover_rate, mutation_rate
        self.iterations = iterations
        self.n = len(dist_matrix)

    def create_individual(self):
        route = list(range(self.n))
        random.shuffle(route)
        return route

    def calculate_fitness(self, route):
        dist = sum(self.dist_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
        dist += self.dist_matrix[route[-1]][route[0]]
        return 1/dist, dist

    def solve(self):
        pop = [self.create_individual() for _ in range(self.pop_size)]
        best_r, min_d = None, float('inf')
        
        for _ in range(self.iterations):
            pop = sorted(pop, key=lambda r: self.calculate_fitness(r)[1])
            if self.calculate_fitness(pop[0])[1] < min_d:
                min_d = self.calculate_fitness(pop[0])[1]
                best_r = pop[0]
                
            new_pop = pop[:2]
            while len(new_pop) < self.pop_size:
                p1, p2 = random.sample(pop[:10], 2)
                if random.random() < self.crossover_rate:
                    start, end = sorted(random.sample(range(self.n), 2))
                    child = [-1]*self.n
                    child[start:end] = p1[start:end]
                    p2_rem = [it for it in p2 if it not in child]
                    idx = 0
                    for i in range(self.n):
                        if child[i] == -1:
                            child[i] = p2_rem[idx]
                            idx += 1
                else: child = p1[:]
                
                if random.random() < self.mutation_rate:
                    i1, i2 = random.sample(range(self.n), 2)
                    child[i1], child[i2] = child[i2], child[i1]
                new_pop.append(child)
            pop = new_pop
        return best_r, min_d

def get_premium_table_html(df, is_matrix=False):
    bg_main, bg_zebra, bg_header = "#0f172a", "#1e293b", "#1e1b4b"
    text_main, border_color = "#e2e8f0", "#334155"
    container_style = f"overflow-x: auto; border-radius: 15px; border: 1px solid {border_color}; margin-bottom: 30px;"
    table_style = f"width: 100%; border-collapse: collapse; background-color: {bg_main}; font-size: 13px;"
    header_style = f"background-color: {bg_header}; color: #818cf8; padding: 18px; font-weight: 800; border-bottom: 3px solid #4f46e5;"
    cell_style = f"padding: 14px; text-align: center; border-bottom: 1px solid {border_color}; color: {text_main};"
    
    html = f'<div style="{container_style}"><table style="{table_style}"><thead><tr><th style="{header_style}">#</th>'
    html += "".join([f'<th style="{header_style}">{c}</th>' for c in df.columns]) + '</tr></thead><tbody>'
    for i, row in df.iterrows():
        bg = bg_main if i % 2 == 0 else bg_zebra
        html += f'<tr style="background-color: {bg};"><td style="{cell_style} font-weight: bold;">{i}</td>'
        for val in row:
            v_str = f"{val:.2f}" if isinstance(val, (float, np.float64)) else str(val)
            html += f'<td style="{cell_style}">{v_str}</td>'
        html += '</tr>'
    return html + '</tbody></table></div>'

# --- YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ GA Parametreleri")
    pop_size = st.slider("Popülasyon Sayısı", 10, 200, 50)
    iterations = st.number_input("İterasyon Sayısı", 10, 1000, 100)
    c_rate = st.slider("Çaprazlama Oranı", 0.1, 1.0, 0.8)
    m_rate = st.slider("Mutasyon Oranı", 0.01, 0.5, 0.1)
    st.divider()
    run_btn = st.button("🚀 Rotayı Optimize Et")
    if st.button("🔄 Noktaları Yenile"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

st.markdown('<h1 class="hero-title">Akıllı Rota Planlayıcı</h1>', unsafe_allow_html=True)

# --- VERİ VE HAZIRLIK ---
if 'points' not in st.session_state:
    show_professional_loader("Sistem Hazırlanıyor...")
    
    # Dinamik dosya yolu: dataset.json ana klasörde olmalı
    base_path = os.path.dirname(__file__)
    json_path = os.path.join(base_path, 'dataset.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            all_pts = json.load(f)
        sel = random.sample(all_pts, 20)
        st.session_state.points = [{"Lat": p["lat"], "Lon": p["lng"], "İlçe": p["ilce"]} for p in sel]
    except Exception as e:
        # Hata durumunda rastgele Balıkesir koordinatları
        st.session_state.points = [{"Lat": random.uniform(39.3, 39.9), "Lon": random.uniform(27.5, 28.3), "İlçe": "Bilinmiyor"} for _ in range(20)]
    
    plist = [(p['Lat'], p['Lon']) for p in st.session_state.points]
    st.session_state.dist_matrix = create_distance_matrix(plist)
    time.sleep(1)
    st.rerun()

display_df = pd.DataFrame(st.session_state.points)
best_route = st.session_state.get('best_route')

if run_btn:
    show_professional_loader("Algoritma Çalışıyor...")
    ga = GeneticAlgorithm(st.session_state.dist_matrix, pop_size, c_rate, m_rate, iterations)
    br, bd = ga.solve()
    st.session_state.best_route, st.session_state.best_dist = br, bd
    st.rerun()

# --- HARİTA VE SONUÇLAR ---
if st.session_state.get('best_dist'):
    st.success(f"✅ En Kısa Rota Bulundu: {st.session_state.best_dist/1000:.2f} km")

m = folium.Map(location=[39.6484, 27.8826], zoom_start=9, tiles='CartoDB dark_matter')

for i, p in enumerate(st.session_state.points):
    folium.CircleMarker([p['Lat'], p['Lon']], radius=7, color="#818cf8", fill=True, popup=f"Durak {i}").add_to(m)

if best_route:
    colors = ['#e11d48', '#d946ef', '#8b5cf6', '#6366f1', '#3b82f6']
    for idx in range(len(best_route)):
        i1, i2 = best_route[idx], best_route[(idx+1)%len(best_route)]
        p1, p2 = st.session_state.points[i1], st.session_state.points[i2]
        folium.plugins.AntPath(locations=[[p1['Lat'],p1['Lon']],[p2['Lat'],p2['Lon']]], color=colors[idx%5]).add_to(m)

st_folium(m, width=1200, height=500)

st.subheader("📊 Durak Detayları")
st.markdown(get_premium_table_html(display_df), unsafe_allow_html=True)