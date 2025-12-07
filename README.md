# <img src='https://raw.githubusercontent.com/stevenrskelton/flag-icon/master/png/16/country-4x3/us.png' width='21' height='15'> POE AutoMate (English)

POE AutoMate is an automated item rolling & checking tool for **Path of Exile**.

It reads item data from the clipboard, applies your filters (Attributes or Socket Colors), and stops when a match is detected.

<p align="center">
  <img src="https://i.imgur.com/EvFfWGI.png" alt="POE AutoMate Interface">
</p>

------------------------------------------------------------------------

## 📥 Installation (For Complete Beginners)

### **0️⃣ Install Python (Required)**

If you don't have Python installed:

1.  Go to: https://www.python.org/downloads/
2.  Download **Python 3.9 or newer**
3.  During installation **check the box**:
    ✅ *Add Python to PATH*
4.  Complete installation.

------------------------------------------------------------------------

### **1️⃣ Install Required Python Modules**

Open **Command Prompt (cmd)** and run:

    pip install keyboard pyautogui pyperclip psutil pywin32

------------------------------------------------------------------------

### **2️⃣ Download/Clone the Repository**

    git clone https://github.com/xAlpier/POE-AutoMate.git

------------------------------------------------------------------------

### **3️⃣ Run the Program**

    python main.py

------------------------------------------------------------------------

## ⚙ Usage

1.  Open the program and select your **Search Mode**:
    * **Attribute:** Search for specific stats (e.g., Life, Resistances).
    * **Color:** Search for specific socket colors (e.g., 4 Red, 2 Green).
2.  Configure your filters (see examples below).
3.  Hover your mouse over an item in PoE.
4.  Press **Start Hotkey** (default `F2`).
5.  Program loops (clicks -> copies -> checks).
6.  When a match is found, it stops automatically.
7.  Press **Stop Hotkey** anytime (`F3`).

### 🔹 Mode 1: Attribute Filter Example
Matches numerical values or text.

    Value: 75
    Name: Fire Resistance

*This matches any line containing "Fire Resistance" with a value ≥ 75.*

### 🔹 Mode 2: Color Filter Example
Matches the count of socket colors.

    R (Red): 4
    G (Green): 2
    B (Blue): 0

*This stops when the item has at least 4 Red sockets AND 2 Green sockets.*

------------------------------------------------------------------------

## 🔧 Features

-   **Dual Modes:** Switch between Attribute scanning and Socket Color scanning.
-   **Automatic Scanning:** Fast and safe auto-click loop.
-   **Smart Filters:** regex-based value checking or socket counting.
-   **Safety First:** Stuck detection, empty read retry, and auto-stop on match.
-   **Configurable:** Custom hotkeys, safety limits, and auto-save settings.
-   **GUI:** Modern dark-themed Tkinter interface.
-   **PoE Detection:** Only works when Path of Exile is active.

------------------------------------------------------------------------

## ⚠ Notes

-   Works only when PoE is the active window.
-   Make sure your clipboard is not locked by another app.
-   Stops immediately on unreadable items or matches.

------------------------------------------------------------------------

## 📌 GitHub Repository

👉 https://github.com/xAlpier/POE-AutoMate.git

------------------------------------------------------------------------

## ⚠️ Legal Disclaimer

This software was developed for educational and hobby purposes. The Path of Exile Terms of Service may prohibit or restrict "performing multiple server-side actions with a single keypress" (macros).

Although this program includes delays close to human reaction speed and various safety measures, any account restrictions or ban risks that may arise from its use are entirely the responsibility of the user.

The developer (xAlpier) cannot be held liable for any account loss or related issues.

------------------------------------------------------------------------
------------------------------------------------------------------------

# <img src='https://raw.githubusercontent.com/yammadev/flag-icons/refs/heads/master/png/TR%402x.png' width='21' height='15'> POE AutoMate (Türkçe)

POE AutoMate, **Path of Exile** için otomatik item kontrol ve orb basma aracıdır.

Item verisini panodan okur, belirlediğiniz filtrelere (Özellik veya Renk) göre kontrol eder ve eşleşme olduğunda otomatik durur.

<p align="center">
  <img src="https://i.imgur.com/EvFfWGI.png" alt="POE AutoMate Arayüz">
</p>

------------------------------------------------------------------------

## 📥 Kurulum (Hiç Bilmeyenler İçin)

### **0️⃣ Python Kurulumu (Zorunlu)**

Bilgisayarınızda Python yoksa:

1.  https://www.python.org/downloads/ adresine gidin
2.  **Python 3.9 veya üstü** sürümü indirin
3.  Kurulum sırasında şu seçeneği işaretleyin:
    ✅ *Add Python to PATH*
4.  Sonraki → Sonraki → Install diyerek kurulumu tamamlayın.

------------------------------------------------------------------------

### **1️⃣ Gerekli Modülleri Kurun**

Windows'ta **cmd** açın ve:

    pip install keyboard pyautogui pyperclip psutil pywin32

------------------------------------------------------------------------

### **2️⃣ Projeyi İndirin**

    git clone https://github.com/xAlpier/POE-AutoMate.git

------------------------------------------------------------------------

### **3️⃣ Programı Çalıştırın**

    python main.py

------------------------------------------------------------------------

## ⚙ Kullanım

1.  Programı açın ve **Arama Modunu** seçin:
    * **Attribute (Özellik):** Stat aramak için (örn. Can, Direnç).
    * **Color (Renk):** Soket renklerini aramak için (örn. 4 Kırmızı, 2 Yeşil).
2.  Filtrelerinizi ayarlayın (aşağıdaki örneklere bakın).
3.  Oyunda farenizi item üzerine getirin.
4.  **Başlat** tuşuna basın (`F2`).
5.  Program otomatik tıklar, okur ve kontrol eder.
6.  Eşleşme bulunduğunda otomatik durur.
7.  İsterseniz **Durdur** tuşu (`F3`) ile manuel durdurabilirsiniz.

### 🔹 Mod 1: Attribute (Özellik) Filtre Örneği
Sayısal değer veya metin arar.

    Değer: 75
    İsim: Fire Resistance

*Bu ayar, "Fire Resistance" içeren ve değeri 75 veya üzeri olan bir item geldiğinde durur.*

### 🔹 Mod 2: Color (Renk) Filtre Örneği
Soket renk sayılarına bakar.

    R (Kırmızı): 4
    G (Yeşil): 2
    B (Mavi): 0

*Bu ayar, itemde EN AZ 4 Kırmızı VE 2 Yeşil soket olduğunda durur.*

------------------------------------------------------------------------

## 🔧 Özellikler

-   **Çift Mod:** Özellik tarama ve Renk/Soket tarama arasında geçiş.
-   **Otomatik Tarama:** Hızlı ve güvenli tıklama döngüsü.
-   **Akıllı Filtreler:** Regex tabanlı değer kontrolü veya soket sayma.
-   **Güvenlik:** Takılma algılama, boş okumalarda tekrar deneme.
-   **Ayarlanabilir:** Tuş atamaları, güvenlik limitleri ve otomatik kayıt.
-   **Arayüz:** Modern, karanlık temalı arayüz.
-   **PoE Algılama:** Sadece oyun penceresi aktifken çalışır.

------------------------------------------------------------------------

## ⚠ Uyarılar

-   Yalnızca PoE aktif penceredeyken çalışır.
-   Panonuzun (clipboard) başka bir uygulama tarafından kilitlenmediğinden emin olun.
-   Okunamayan veya boş item verisinde güvenlik için durur.

------------------------------------------------------------------------

## 📌 GitHub Deposu

👉 https://github.com/xAlpier/POE-AutoMate.git

------------------------------------------------------------------------

## ⚠️ Yasal Uyarı (Disclaimer)

-   Bu yazılım eğitim ve hobi amaçlı geliştirilmiştir. Path of Exile Hizmet Koşulları (Terms of Service), "tek tuşla birden fazla sunucu taraflı işlem yapmayı" (macro) yasaklayabilir veya kısıtlayabilir.

-   Bu program, insan hızına yakın gecikmeler ve güvenlik önlemleri içerse de, kullanımdan doğabilecek hesap kısıtlamaları veya ban riskleri tamamen kullanıcının sorumluluğundadır.

-   Geliştirici (xAlpier), oluşabilecek herhangi bir hesap kaybından sorumlu tutulamaz.