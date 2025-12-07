# <img src='https://raw.githubusercontent.com/stevenrskelton/flag-icon/master/png/16/country-4x3/us.png' width='21' height='15'> POE AutoMate (English)

POE AutoMate is an automated item rolling & checking tool for **Path of
Exile**.\
It reads item data from the clipboard, applies your filters, and stops
when a matching implicit/stat is detected.

------------------------------------------------------------------------

## 🔧 Features

-   Automatic clipboard item scan\
-   Custom filters (`Value → Name`)\
-   Safe auto-click loop\
-   Stuck detection (same item read multiple times)\
-   Retry on empty clipboard read\
-   Hotkey support (Start/Stop)\
-   Clean GUI with Tkinter\
-   Auto-save config (`config.json`)\
-   PoE window detection\
-   Shift auto-hold\
-   Right‑click remove filter\
-   Right‑click log clear

------------------------------------------------------------------------

## 📁 Project Structure

    main.py
    config.json

------------------------------------------------------------------------

## 📥 Installation

1.  Install Python 3.9 or newer\
2.  Install dependencies:

```{=html}
    pip install keyboard pyautogui pyperclip psutil pywin32
```

3.  Clone repository:

```{=html}
    git clone https://github.com/xAlpier/POE-AutoMate.git
```

4.  Run:

```{=html}
    python main.py
```

------------------------------------------------------------------------

## ⚙ Usage

-   Hover your mouse over an item in PoE\
-   Press **Start Hotkey** (default `F2`)\
-   Program loops, clicks, reads, and checks item\
-   When filter matches → auto stops\
-   Press **Stop Hotkey** anytime (`F3`)

### Filter Example

    Value: 75
    Name: Fire Resistance

This matches any implicit line with value ≥ 75.

------------------------------------------------------------------------

## ⚠ Notes

-   Works only when PoE is active window\
-   Safety checks prevent unwanted rolling\
-   Stops on unreadable items, empty reads, or matching filter

------------------------------------------------------------------------

## 📌 GitHub Repository

👉 https://github.com/xAlpier/POE-AutoMate.git

------------------------------------------------------------------------

------------------------------------------------------------------------

# <img src='https://raw.githubusercontent.com/yammadev/flag-icons/refs/heads/master/png/TR%402x.png' width='21' height='15'> POE AutoMate (Türkçe)

POE AutoMate, **Path of Exile** için otomatik item kontrol ve orb basma
aracıdır.\
Item verisini panodan okur, filtrelerle karşılaştırır ve eşleşme
bulduğunda otomatik olarak durur.

------------------------------------------------------------------------

## 🔧 Özellikler

-   Otomatik clipboard item okuma\
-   Özel filtreler (`Değer → İsim`)\
-   Güvenli otomatik tıklama döngüsü\
-   Takılma algılama (aynı item 3 kez okunursa durur)\
-   Boş okuma durumunda akıllı tekrar\
-   Başlat/Durdur hotkey desteği\
-   Tkinter ile modern arayüz\
-   Ayarlar otomatik kayıt (`config.json`)\
-   PoE aktif pencere kontrolü\
-   Shift otomatik basılı tutma\
-   Filtreyi sağ tık ile silme\
-   Log ekranını sağ tık ile temizleme

------------------------------------------------------------------------

## 📁 Dosya Yapısı

    main.py
    config.json

------------------------------------------------------------------------

## 📥 Kurulum

1.  Python 3.9+ kurulu olmalı\
2.  Gerekli paketleri yükle:

```{=html}
pip install keyboard pyautogui pyperclip psutil pywin32
```

3.  Reponun indirilmesi:

```{=html}
git clone https://github.com/xAlpier/POE-AutoMate.git
```

4.  Çalıştırma:

```{=html}
python main.py
```

------------------------------------------------------------------------

## ⚙ Kullanım

-   Fareyi item üzerine getir\
-   **Başlat** tuşuna bas (`F2`)\
-   Program tıklar, okur, filtre uygular\
-   Eşleşen filtre bulunursa durur\
-   **Durdur** tuşu ile istediğin zaman durdur (`F3`)

### Filtre Örneği

    Değer: 75
    İsim: Fire Resistance

Bu, 75 veya üzeri Fire Resistance implicit gördüğünde durur.

------------------------------------------------------------------------

## ⚠ Uyarılar

-   Sadece PoE aktif pencereyken çalışır\
-   Güvenlik kontrolleri istenmeyen kullanımı önler\
-   Okunamayan item, boş okumalar veya eşleşme olduğunda durur

------------------------------------------------------------------------

## 📌 GitHub Deposu

👉 https://github.com/xAlpier/POE-AutoMate.git

------------------------------------------------------------------------
