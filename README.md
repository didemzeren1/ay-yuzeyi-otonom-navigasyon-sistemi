# 🌕 Ay Yüzeyi Güvenli Rota Planlayıcı (LRO LOLA Pathfinding)

Bu proje, NASA'nın LRO (Lunar Reconnaissance Orbiter) verilerini temel alarak Ay yüzeyindeki eğim haritaları üzerinde en güvenli ve düşük maliyetli rotayı hesaplayan bir **A* (A-Star)** algoritması uygulamasıdır. Yazılım, tehlikeli bölgelerden kaçınan bir navigasyon simülasyonu sunar.

## 🚀 Proje Hakkında

Kod, `LRO_LOLA_ClrSlope_Global_16ppd.tif` adlı topografik eğim haritasını analiz eder. Belirlenen HSV (Renk, Doygunluk, Parlaklık) değerlerine göre yüzeyi "Güvenli" ve "Tehlikeli" olarak sınıflandırır.

### Temel Özellikler
* **Görüntü İşleme:** OpenCV ve Rasterio kütüphaneleri ile yüksek çözünürlüklü `.tif` dosyalarının işlenmesi.
* **Maliyet Analizi:** Yüzey eğimine göre dinamik bir maliyet matrisi (cost matrix) oluşturulması.
* **A* Algoritması:** Başlangıç noktasından hedef koordinata (örneğin: 800, 600) en kısa ve güvenli yolun bulunması.
* **Görselleştirme:** Hesaplanan rotanın orijinal harita üzerinde çizilerek `ay_sonuc.png` olarak kaydedilmesi.

## ⚙️ Teknik Detaylar

### Renk ve Risk Sınıflandırması
Algoritma, haritadaki renk tonlarına göre aşağıdaki risk değerlendirmesini yapar:

| Renk / Ton | Risk Durumu | Maliyet Değeri |
| :--- | :--- | :--- |
| **Sarı-Turuncu** | Güvenli Bölge | 1 |
| **Yeşil** | Orta Risk | 100 |
| **Mavi** | Yüksek Risk | 100 |
| **Kırmızı/Mor** | Tehlikeli / Geçilemez | 100 |

## 🛠️ Kullanılan Teknolojiler

* **Python 3.x**
* **NumPy:** Matris işlemleri ve maliyet hesaplamaları
* **OpenCV (`cv2`):** Görüntü işleme ve görselleştirme
* **Rasterio:** Coğrafi bilgi sistemleri (GIS) verilerini okuma
* **Heapq:** A* algoritması için öncelikli kuyruk yönetimi

## 📂 Dosya Yapısı

```text
├── new1.py                              # Rotayı hesaplayan ana Python scripti
├── LRO_LOLA_ClrSlope_Global_16ppd.tif   # Ay yüzeyi eğim verilerini içeren kaynak dosya
└── ay_sonuc.png                         # Algoritma tarafından üretilen rotayı gösteren sonuç görseli
```

## 🚀 Kurulum ve Çalıştırma

1. **Gerekli kütüphaneleri yükleyin:**
   ```bash
   pip install numpy opencv-python rasterio
   ```

2. **Ana dosyayı çalıştırın:**
   ```bash
   python new1.py
   ```
