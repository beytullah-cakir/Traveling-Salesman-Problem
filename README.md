Harika bir proje olmuş! Kod yapın oldukça düzenli ve modern bir arayüz (UI) tasarımına sahip. Özellikle Genetik Algoritma parametrelerini yan menüden dinamik olarak değiştirilebilmesi ve mesafe matrisi için OSRM API kullanımı projeyi profesyonel kılıyor.

Senin için hazırladığım, projenin tüm özelliklerini ve kurulum adımlarını içeren **README.md** dosyası aşağıdadır:

---

# 📍 Balıkesir Akıllı Rota Planlayıcı (TSP Solver)

Bu proje, **Gezgin Satıcı Problemi'ni (Traveling Salesperson Problem - TSP)** çözmek için **Genetik Algoritma** kullanan, Streamlit tabanlı interaktif bir web uygulamasıdır. Balıkesir il sınırları içerisinden rastgele seçilen 20 nokta arasında en kısa ve en verimli rotayı hesaplar.

## ✨ Öne Çıkan Özellikler

* **Dinamik Rota Optimizasyonu:** Kullanıcı tarafından belirlenen popülasyon sayısı, iterasyon ve mutasyon oranları ile Genetik Algoritma'yı anlık olarak çalıştırır.
* **Gerçek Yol Mesafeleri:** Kuş uçuşu mesafe yerine **OSRM (Open Source Routing Machine)** API'lerini kullanarak gerçek karayolu mesafeleri üzerinden hesaplama yapar.
* **İnteraktif Harita:** `Folium` ve `AntPath` kütüphaneleri ile optimize edilen rotayı hareketli çizgiler ve KM bilgileriyle harita üzerinde görselleştirir.
* **Modern UI/UX:** Karanlık tema (Dark Mode), özel yükleme animasyonları ve şık veri tabloları ile kullanıcı dostu bir deneyim sunar.
* **Hata Yönetimi:** API bağlantı sorunlarına karşı otomatik olarak kuş uçuşu (geodesic) mesafe hesaplama moduna geçiş yapar.

## 🚀 Başlangıç

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları takip edebilirsiniz.

### Gereksinimler

* Python 3.8 veya üzeri
* Pip paket yöneticisi

### Kurulum

1. **Depoyu klonlayın:**
```bash
git clone https://github.com/kullaniciadi/balikesir-rota-planlayici.git
cd balikesir-rota-planlayici

```


2. **Gerekli kütüphaneleri yükleyin:**
```bash
pip install streamlit pandas numpy requests geopy folium streamlit-folium

```


3. **Veri setini hazırlayın:**
* `dataset.json` dosyanızın projenin ana dizininde olduğundan emin olun.
* *Not: Kod içerisindeki `json_path` değişkenini kendi dosya yolunuza göre güncellemeyi unutmayın.*


4. **Uygulamayı çalıştırın:**
```bash
streamlit run main.py

```



## 🛠 Kullanılan Teknolojiler

* **Arayüz:** [Streamlit](https://streamlit.io/)
* **Harita:** [Folium](https://python-visualization.github.io/folium/)
* **Veri Analizi:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
* **Algoritma:** Genetik Algoritma (Sıralı Çaprazlama & Swap Mutasyon)
* **Mesafe API:** [OSRM Project](http://project-osrm.org/)

## 🧬 Algoritma Parametreleri

Uygulamanın yan menüsünden aşağıdaki değerleri optimize ederek sonuçları karşılaştırabilirsiniz:

* **Popülasyon Sayısı:** Aynı anda yarışan çözüm sayısı.
* **İterasyon Sayısı:** Algoritmanın kaç nesil boyunca çalışacağı.
* **Çaprazlama Oranı:** Ebeveynlerden yeni bireylerin oluşma sıklığı.
* **Mutasyon Oranı:** Rotadaki rastgele değişimlerin sıklığı (Yerel optimumdan kaçmak için kritiktir).

---

*Bu proje bir yapay zeka/optimizasyon çalışması kapsamında geliştirilmiştir.*

---