# <img src='https://raw.githubusercontent.com/stevenrskelton/flag-icon/master/png/16/country-4x3/us.png' width='21' height='15'> POE AutoMate (English)

POE AutoMate is an automated item rolling & checking tool for **Path of Exile**.

It reads item data directly from the game, applies your filters (Modifiers or Socket Colors), and stops when a match is detected.

<p align="center">
  <img src="https://i.imgur.com/BdFnZkU.png" alt="POE AutoMate Interface EN">
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

### **2️⃣ Download the Repository**

    git clone https://github.com/xAlpier/POE-AutoMate.git

*Note: Make sure the `data` folder is in the same directory as `main.py` for the Library to work.*

------------------------------------------------------------------------

### **3️⃣ Run the Program**

In your command prompt (cmd/terminal), run:

    python main.py

------------------------------------------------------------------------

## ⚙ Usage

1.  Open the program and select your **Search Mode**:
    * **Modifiers:** Search for specific stats using the **Library** or custom filters.
    * **Socket Colors:** Search for specific socket colors (e.g., 4 Red, 2 Green).
2.  Configure your filters (see examples below).
    * *Tip: Set "Max Tries" to **0** for unlimited attempts.*
3.  Hover your mouse over an item in PoE.
4.  Press **Start Hotkey** (default `F2`).
5.  Program loops (clicks -> reads -> checks).
6.  When a match is found, it stops automatically with a sound alert.
7.  Press **Stop Hotkey** anytime (`F3`).

### 🔹 Mode 1: Modifiers & Library
Matches numerical values or text. You can select pre-defined mods from the **Database/Library** list or add them manually.

    Value: 75
    Name: Fire Resistance

*This matches any line containing "Fire Resistance" with a value ≥ 75.*

### 🔹 Mode 2: Socket Colors Filter
Matches the count of socket colors.

    R (Red): 4
    G (Green): 2
    B (Blue): 0

*This stops when the item has at least 4 Red sockets AND 2 Green sockets.*

------------------------------------------------------------------------

## 🔧 Features

-   **Dual Modes:** Switch between Modifiers scanning and Socket Color scanning.
-   **Database Library:** Built-in library for common modifiers (Life, Resistances, etc.).
-   **Multi-Language:** Interface supports both English (EN) and Turkish (TR).
-   **Audio Alerts:** Sound notifications when a match is found or an error occurs.
-   **Smart Filters:** Regex-based value checking or socket counting.
-   **Safety First:** Stuck detection, empty read retry, and auto-stop on match.
-   **Configurable:** Custom hotkeys, safety limits (0=Unlimited), and auto-save settings.

------------------------------------------------------------------------

## ⚠ Notes

-   **Active Window:** Works only when PoE is the active window.
-   **Safety:** Stops immediately on unreadable items or matches to prevent accidents.

------------------------------------------------------------------------

## 📌 GitHub Repository

👉 https://github.com/xAlpier/POE-AutoMate.git

------------------------------------------------------------------------

## ⚠️ Legal Disclaimer

This software was developed for educational and hobby purposes. The Path of Exile Terms of Service may prohibit or restrict "performing multiple server-side actions with a single keypress" (macros).

Although this program includes delays close to human reaction speed and various safety measures, any account restrictions or ban risks that may arise from its use are entirely the responsibility of the user.

The developer **(xAlpier)** cannot be held liable for any account loss or related issues.

------------------------------------------------------------------------
------------------------------------------------------------------------

# <img src='https://raw.githubusercontent.com/yammadev/flag-icons/refs/heads/master/png/TR%402x.png' width='21' height='15'> POE AutoMate (Türkçe)

POE AutoMate, **Path of Exile** için otomatik item kontrol ve orb basma aracıdır.

Item verisini oyun içinden okur, belirlediğiniz filtrelere (Modlar veya Soket Renkleri) göre kontrol eder ve eşleşme olduğunda otomatik durur.

<p align="center">
  <img src="https://i.imgur.com/MbxYrNg.png" alt="POE AutoMate Arayüz TR">
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

*Not: Kütüphanenin çalışması için `data` klasörünün `main.py` ile aynı yerde olduğundan emin olun.*

------------------------------------------------------------------------

### **3️⃣ Programı Çalıştırın**

Komut satırınızda (cmd/terminal) programı çalıştırın:

    python main.py

------------------------------------------------------------------------

## ⚙ Kullanım

1.  Programı açın ve **Arama Modunu** seçin:
    * **Modlar:** Stat/Özellik aramak için (Kütüphaneden veya manuel).
    * **Soket Renkleri:** Soket renklerini aramak için (örn. 4 Kırmızı, 2 Yeşil).
2.  Filtrelerinizi ayarlayın (aşağıdaki örneklere bakın).
    * *İpucu: "Deneme Sınırı"nı (Max Tries) **0** yaparsanız sınırsız döner.*
3.  Oyunda farenizi item üzerine getirin (Shift tuşuna basmanıza gerek yok, program basar).
4.  **Başlat** tuşuna basın (`F2`).
5.  Program otomatik tıklar, okur ve kontrol eder.
6.  Eşleşme bulunduğunda sesli uyarı verir ve durur.
7.  İsterseniz **Durdur** tuşu (`F3`) ile manuel durdurabilirsiniz.

### 🔹 Mod 1: Mod Filtreleri & Kütüphane
Sayısal değer veya metin arar. **Veritabanı / Kütüphane** listesinden hazır özellikleri seçip ekleyebilirsiniz.

    Değer: 75
    İsim: Fire Resistance

*Bu ayar, "Fire Resistance" içeren ve değeri 75 veya üzeri olan bir item geldiğinde durur.*

### 🔹 Mod 2: Soket Renkleri Filtresi
Soket renk sayılarına bakar.

    R (Kırmızı): 4
    G (Yeşil): 2
    B (Mavi): 0

*Bu ayar, itemde EN AZ 4 Kırmızı VE 2 Yeşil soket olduğunda durur.*

------------------------------------------------------------------------

## 🔧 Özellikler

-   **Çift Mod:** Mod tarama ve Renk/Soket tarama arasında geçiş.
-   **Veritabanı Kütüphanesi:** Sık kullanılan özellikleri listeden seçebilme imkanı.
-   **Çoklu Dil:** İngilizce (EN) ve Türkçe (TR) dil desteği.
-   **Sesli Uyarı:** İşlem bittiğinde veya hata olduğunda sesli bildirim.
-   **Akıllı Filtreler:** Regex tabanlı değer kontrolü veya soket sayma.
-   **Güvenlik:** Takılma algılama, boş okumalarda tekrar deneme.
-   **Ayarlanabilir:** Tuş atamaları, güvenlik limitleri (0=Sınırsız) ve otomatik kayıt.

------------------------------------------------------------------------

## ⚠ Uyarılar

-   Yalnızca PoE aktif penceredeyken çalışır.
-   Okunamayan veya boş item verisinde güvenlik için durur.

------------------------------------------------------------------------

## 📌 GitHub Deposu

👉 https://github.com/xAlpier/POE-AutoMate.git

------------------------------------------------------------------------

## ⚠️ Yasal Uyarı (Disclaimer)

Bu yazılım eğitim ve hobi amaçlı geliştirilmiştir. Path of Exile Hizmet Koşulları (Terms of Service), "tek tuşla birden fazla sunucu taraflı işlem yapmayı" (macro) yasaklayabilir veya kısıtlayabilir.

Bu program, insan hızına yakın gecikmeler ve güvenlik önlemleri içerse de, kullanımdan doğabilecek hesap kısıtlamaları veya ban riskleri tamamen kullanıcının sorumluluğundadır.

Geliştirici **(xAlpier)**, oluşabilecek herhangi bir hesap kaybından sorumlu tutulamaz.