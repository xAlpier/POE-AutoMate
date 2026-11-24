[<img src='https://raw.githubusercontent.com/yammadev/flag-icons/refs/heads/master/png/TR%402x.png' width='21' height='15'> **Türkçe Dokümana Git**](#-poe-automate-türkçe)

# <img src='https://raw.githubusercontent.com/stevenrskelton/flag-icon/master/png/16/country-4x3/us.png' width='21' height='15'> POE AutoMate v2.0 (English)

POE AutoMate is an automated item rolling, filtering, and checking utility for **Path of Exile**, now featuring a modular architecture and a built-in **Responsive Web & Mobile Companion Dashboard**.

It reads item data directly from the game clipboard, evaluates your modifier or socket color filters with strict safety checks, and stops immediately with an audio alert when a match is detected.

<p align="center">
  <img src="https://i.imgur.com/N36HANx.png" alt="POE AutoMate Interface EN">
</p>

---

## 📥 Installation

### 0️⃣ Install Python (Required)
1. Download **Python 3.9 or newer** from https://www.python.org/downloads/
2. Check **Add Python to PATH** during installation.

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
*(Or manually: `pip install keyboard pyautogui pyperclip psutil pywin32` — the built-in Web & Mobile Dashboard uses Python's standard library and requires **zero extra packages**.)*

### 2️⃣ Run the Program
- **Desktop GUI + Local Web Companion:**
  ```bash
  python main.py
  ```
  *(Or double-click `Start.bat` on Windows.)*
- **Headless Web & Mobile Mode (with Wi-Fi/LAN access):**
  ```bash
  python main.py --web-only --lan --port 8765
  ```
- **Desktop GUI Only (without web server):**
  ```bash
  python main.py --no-web
  ```

---

## 📱 Web & Mobile Companion Dashboard
- Open `http://127.0.0.1:8765` in any desktop browser (or click the **🌐 Web** button in the app).
- To use from your **phone or tablet** on the same Wi-Fi network, enable **Allow LAN / Mobile Access (Same Wi-Fi)** in `⚙ Settings` (or launch with `--lan`) and open the shown `http://<PC-IP>:8765` address on your mobile browser.
- Features real-time SSE sync with the desktop app, touch-friendly mobile navigation, Dark/Light themes, filter & library management, live logs, and an **Item Filter Tester** where you can paste any copied PoE item to test filters safely.

---

## ⚙ Features & Usage

### 🔹 Mode 1: Modifiers & Library
- **Multi-Word Cached Search:** Search across any category or **All Categories** (e.g. `fire res`, `movement speed`).
- **Flexible Value Matching:**
  - Single integer or decimal thresholds: `75`, `0.4`, `1.5`
  - Multi-value `# to #` mods (comma-separated): `2, 15` for `Adds # to # Lightning Damage`
  - **Boolean / Fixed Mods:** Leave the Value field **empty** for mods without variable thresholds (e.g., `Instant Recovery`, `Used when Charges reach full`, `25% increased effect`, `~Open suffix~`).
- **Match Logic (`OR` / `AND`):** Match **any** active filter (`OR`) or require **all** active filters simultaneously (`AND`).
- **Mod Scope:** Choose `Explicit`, `Implicit / Enchant`, or `All`.
- **Quick Actions:** Double-click an active filter to toggle Active/Passive; right-click to edit.

### 🔹 Mode 2: Socket Colors Filter
- Configure target counts for **Red (`R`)**, **Green (`G`)**, **Blue (`B`)**, and **White (`W`)** sockets.
- Optional **White Wildcard** mode counts White sockets toward missing R/G/B requirements.
- **Impossible Target Guard:** Automatically stops before spending Chromatic Orbs if required sockets exceed the item's total socket count.

### 🛡️ Built-in Safety & Stability
- Works only while **Path of Exile** is the active foreground window (including elevated/Admin fallback).
- Stops immediately if the item **already matches**, is **Corrupted / Mirrored / Unidentified**, has **no active filters**, or fails/repeats 3 reads in a row.
- Guaranteed `Shift` key release on stop, error, or window close.
- Configurable click & clipboard delays in Settings.

### 🧪 Running Tests
```bash
python -B -m unittest discover -s tests -v
```

---

## ⚠️ Legal Disclaimer
This software was developed for educational and hobby purposes. Path of Exile's Terms of Service may restrict automation/macros. Any account restrictions arising from its use are solely the responsibility of the user.

---
---

[<img src='https://raw.githubusercontent.com/stevenrskelton/flag-icon/master/png/16/country-4x3/us.png' width='21' height='15'> **Click for English Documentation**](#-poe-automate-v20-english)

# <img src='https://raw.githubusercontent.com/yammadev/flag-icons/refs/heads/master/png/TR%402x.png' width='21' height='15'> POE AutoMate v2.0 (Türkçe)

POE AutoMate, **Path of Exile** için geliştirilmiş otomatik eşya tarama, orb basma ve filtre kontrol aracıdır. v2.0 sürümüyle birlikte modüler mimari, gelişmiş güvenlik korumaları ve yerleşik **Web & Mobil Kontrol Paneli** sunar.

<p align="center">
  <img src="https://i.imgur.com/4h0pg4H.png" alt="POE AutoMate Arayüz TR">
</p>

---

## 📥 Kurulum

### 0️⃣ Python Kurulumu (Zorunlu)
1. https://www.python.org/downloads/ adresinden **Python 3.9 veya üstü** sürümü indirin.
2. Kurulum sırasında **Add Python to PATH** seçeneğini işaretleyin.

### 1️⃣ Gerekli Paketleri Kurun
```bash
pip install -r requirements.txt
```
*(Yerleşik Web & Mobil Arayüz, Python standart kütüphanesi ile çalışır ve **ek paket gerektirmez**.)*

### 2️⃣ Programı Çalıştırın
- **Masaüstü Arayüz + Web Kontrol Paneli:**
  ```bash
  python main.py
  ```
  *(Windows'ta doğrudan `Start.bat` dosyasına çift tıklayabilirsiniz.)*
- **Sadece Web & Mobil Modu (Aynı Wi-Fi'dan telefon/tablet erişimiyle):**
  ```bash
  python main.py --web-only --lan --port 8765
  ```
- **Sadece Masaüstü Arayüz (Web sunucusu kapalı):**
  ```bash
  python main.py --no-web
  ```

---

## 📱 Web & Mobil Kontrol Paneli
- Program çalışırken **🌐 Web** butonuna tıklayarak veya tarayıcıdan `http://127.0.0.1:8765` adresine giderek paneli açabilirsiniz.
- **Telefon veya tabletten** bağlanmak için `⚙ Ayarlar` içinden **Yerel Ağ / Mobil Erişime İzin Ver (Wi-Fi)** seçeneğini açın (veya `--lan` ile başlatın) ve gösterilen `http://<PC-IP>:8765` adresini mobil tarayıcınızda açın.
- Gerçek zamanlı SSE senkronizasyonu, mobil alt menü, Koyu/Açık tema, kütüphane arama, filtre yönetimi, canlı günlük ve oyundan kopyalanan eşyaları güvenle denemenizi sağlayan **Canlı Eşya Test Aracı** içerir.

---

## ⚙ Özellikler ve Kullanım

### 🔹 Mod 1: Mod Filtreleri & Kütüphane
- **Hızlı Çoklu Kelime Arama:** Seçili kategoride veya **Tüm Kategoriler** içinde çoklu kelimeyle anında arama (`fire res`, `movement speed` vb.).
- **Esnek Değer Desteği:**
  - Tam sayı ve ondalıklı eşik değerleri: `75`, `0.4`, `1.5`
  - Çoklu `# to #` değerleri (virgülle ayrılmış): `2, 15` (`Adds # to # Lightning Damage`)
  - **Değersiz / Sabit Modlar:** Sayısal eşik gerektirmeyen modlar için Değer alanını **boş bırakabilirsiniz** (örn. `Instant Recovery`, `Used when Charges reach full`, `25% increased effect`, `~Open suffix~`).
- **Eşleşme Mantığı (`VEYA` / `VE`):** Aktif filtrelerden herhangi biri (`OR`) veya tamamı aynı anda (`AND`) tuttuğunda durma seçeneği.
- **Mod Kapsamı:** `Explicit`, `Implicit / Enchant` veya `Tümü`.
- **Hızlı İşlemler:** Aktif filtreye çift tıklayarak Aktif/Pasif yapabilir, sağ tıklayarak düzenleyebilirsiniz.

### 🔹 Mod 2: Soket Renk Filtreleri
- **Kırmızı (`R`)**, **Yeşil (`G`)**, **Mavi (`B`)** ve **Beyaz (`W`)** soket hedefleri belirlenebilir.
- **Beyaz Soket Joker** seçeneği ile beyaz soketler eksik renklerin yerine sayılır.
- **İmkansız Hedef Koruması:** İstenen toplam soket sayısı eşyanın soket sayısından fazlaysa orb harcamadan otomatik durur.

### 🛡️ Güvenlik ve Kararlılık
- Yalnızca **Path of Exile** aktif pencereyken çalışır.
- Eşya zaten eşleşiyorsa, `Corrupted` / `Mirrored` / `Unidentified` ise, aktif filtre yoksa veya 3 kez art arda aynı/boş okuma olursa anında durur.
- Hata, durdurma veya pencere kapanışında `Shift` tuşunun takılı kalmasını önleyen garantili temizlik mekanizması bulunur.
- Tıklama ve pano okuma gecikmeleri Ayarlar penceresinden özelleştirilebilir.

### 🧪 Testleri Çalıştırma
```bash
python -B -m unittest discover -s tests -v
```

---

## ⚠️ Yasal Uyarı (Disclaimer)
Bu yazılım eğitim ve hobi amaçlı geliştirilmiştir. Path of Exile Hizmet Koşulları (Terms of Service) makro/otomasyon kullanımını kısıtlayabilir. Kullanımdan doğabilecek tüm sorumluluk kullanıcıya aittir.
