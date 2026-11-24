feat(v2.0): modüler mimari, performans iyileştirmeleri ve Web/Mobil kontrol paneli

- Mimari: Monolitik main.py; poe_automate/ (config, i18n, library, parser, automation, web_server, gui) paketine ayrıştırıldı.
- Web & Mobil UI: Sıfır ek bağımlılıkla yerel HTTP + SSE sunucusu ve mobil uyumlu Koyu/Açık temalı kontrol paneli (web/) ile canlı Eşya Filtre Test Aracı eklendi.
- Ayrıştırıcı & Eşleştirme: Ondalıklı sayı desteği, değersiz (boolean/sabit) mod eşleştirme, VE/VEYA (AND/OR) mantığı, Explicit/Implicit-Enchant/Tümü kapsam seçimi, Beyaz soket (W) joker desteği, imkansız soket ve Corrupted/Mirrored/Unidentified güvenlik duruşları eklendi.
- Kararlılık & Performans: Shift tuşu garantili serbest bırakma, non-blocking hotkey & ses yürütme, önbellekli ve debounce'lu çoklu kelime kütüphane araması, sınırlı/renkli log tamponu, atomik config.json yazımı, Minimal Mod/Ayarlar penceresi ve hotkey iptal hatalarının giderilmesi sağlandı.
- Veri & Testler: data/*.txt dosyalarındaki tekrar eden ve hatalı boşluklu satırlar temizlendi; 15 adet birim ve entegrasyon testi (tests/), requirements.txt, .gitignore, GEMINI.md ve changelog.md eklendi.
