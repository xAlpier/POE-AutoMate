# <img src='https://raw.githubusercontent.com/stevenrskelton/flag-icon/master/png/16/country-4x3/us.png' width='21' height='15'> POE AutoMate (English)

POE AutoMate is an automated item rolling & checking tool for **Path of
Exile**.\
It reads item data from the clipboard, applies your filters, and stops
when a matching implicit/stat is detected.

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

-   Hover your mouse over an item in PoE
-   Press **Start Hotkey** (default `F2`)
-   Program loops, clicks, reads, and checks item
-   When filter matches → auto stops
-   Press **Stop Hotkey** anytime (`F3`)

### Filter Example

    Value: 75
    Name: Fire Resistance

This matches any value ≥ 75.

------------------------------------------------------------------------

## 🔧 Features

-   Automatic item scan
-   Custom filters (`Value → Name`)
-   Safe auto-click loop
-   Stuck detection
-   Retry on empty read
-   Hotkey support
-   Tkinter GUI
-   Auto-save config
-   Shift auto‑hold
-   PoE window detection
-   Right‑click remove filter
-   Right‑click clear log

------------------------------------------------------------------------

## ⚠ Notes

-   Works only when PoE is active window
-   Stops on unreadable items, empty reads, or matching filter

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

POE AutoMate, **Path of Exile** için otomatik item kontrol ve orb basma
aracıdır.\
Item verisini panodan okur, filtrelerle karşılaştırır ve eşleşme
olduğunda otomatik durur.

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

-   Fareyi item üzerine getir
-   **Başlat** tuşuna bas (`F2`)
-   Program tıklar, okur, filtre uygular
-   Filtre eşleşirse durur
-   İstersen **Durdur** tuşu (`F3`) ile kapatabilirsin

### Filtre Örneği

    Değer: 75
    İsim: Fire Resistance

75 veya üzeri olduğunda durur.

------------------------------------------------------------------------

## 🔧 Özellikler

-   Otomatik item okuma
-   Filtre sistemi (`Değer → İsim`)
-   Güvenli otomatik tıklama döngüsü
-   Takılma algılama sistemi
-   Boş okumalarda akıllı tekrar
-   Hotkey desteği
-   Modern Tkinter arayüz
-   Ayarlar otomatik kayıt
-   Shift otomatik basılı tutma
-   PoE aktif pencere kontrolü
-   Sağ tık ile filtre silme
-   Sağ tık ile log temizleme

------------------------------------------------------------------------

## ⚠ Uyarılar

-   Yalnızca PoE aktif penceredeyken çalışır
-   Güvenlik kontrolleri istenmeyen döngüyü engeller
-   Okunamayan veya boş item verisinde durur

------------------------------------------------------------------------

## 📌 GitHub Deposu

👉 https://github.com/xAlpier/POE-AutoMate.git

------------------------------------------------------------------------

## ⚠️ Yasal Uyarı (Disclaimer)

Bu yazılım eğitim ve hobi amaçlı geliştirilmiştir. Path of Exile Hizmet Koşulları (Terms of Service), "tek tuşla birden fazla sunucu taraflı işlem yapmayı" (macro) yasaklayabilir veya kısıtlayabilir.

Bu program, insan hızına yakın gecikmeler ve güvenlik önlemleri içerse de, kullanımdan doğabilecek hesap kısıtlamaları veya ban riskleri tamamen kullanıcının sorumluluğundadır.

Geliştirici (xAlpier), oluşabilecek herhangi bir hesap kaybından sorumlu tutulamaz.
------------------------------------------------------------------------