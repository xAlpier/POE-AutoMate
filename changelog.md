# Değişiklik Günlüğü (Changelog)

## [2.0.0] - 2026-11-24

### 🏗️ Mimari ve Performans İyileştirmeleri
- **Modüler Paket Yapısı:** 1.432 satırlık tek dosya (`main.py`) temiz ve bakımı kolay modüllere ayrıldı:
  - `poe_automate/config.py`: Thread-safe `ConfigManager`, atomik disk yazımı (`tmp` + `os.replace`), şema doğrulama ve eski `config.json` ile tam geriye dönük uyumluluk.
  - `poe_automate/i18n.py`: Masaüstü GUI ve Web/Mobil arayüzün ortak kullandığı TR/EN çeviri merkezi.
  - `poe_automate/library.py`: Bellek içi önbellekli (`cache`) kütüphane yükleyici, `All Categories` (Tüm Kategoriler) görünümü ve çoklu kelime destekli hızlı arama (~0.35 ms).
  - `poe_automate/parser.py`: Bölüm tabanlı Path of Exile pano ayrıştırıcısı (`ParsedItem`) ve `lru_cache` önbellekli regex eşleştirme motoru.
  - `poe_automate/automation.py`: `RLock` ve `Event` tabanlı thread-safe otomasyon motoru ve canlı olay yayıncısı (pub/sub).
  - `poe_automate/web_server.py`: Ek pip paketi gerektirmeyen `ThreadingHTTPServer` + SSE (Server-Sent Events) gerçek zamanlı sunucusu.
  - `poe_automate/gui.py`: Yüksek DPI uyumlu, kuyruk tabanlı (50 ms toplu güncelleme), Koyu/Açık temalı ve yeniden boyutlandırılabilir Tkinter arayüzü.
- **Kütüphane ve Log Performansı:**
  - Kütüphane aramasına debounce (90 ms) ve tek seferde toplu Tcl ekleme (`insert(tk.END, *items)`) eklendi.
  - Sistem günlüğüne üst sınır (500/600 satır) konularak uzun süreli sınırsız taramalarda oluşan bellek artışı ve arayüz donması giderildi.
  - `is_poe_active()` kontrolü üst seviye import + 5 sn PID önbelleği + Yönetici (Admin) yetkisi durumunda pencere başlığı (`GetWindowText`) yedeği ile hızlandırıldı ve kararlı hale getirildi.
  - Ses efektleri (`winsound.Beep`) arka plan thread'ine alınarak arayüz ve döngü bloklanması giderildi.
  - Global kısayol tetiklemeleri (`keyboard.add_hotkey`) doğrudan bloklama yapmadan arka plan thread'ine (`start_async`) devredildi.

### 🐛 Hata Düzeltmeleri
- **Kısayol Dinleme Çökmesi (`NameError`):** Tuş ataması sırasında pencere dışına tıklandığında `start_key_btn` tanımsız hatasıyla uygulamanın kilitlenmesi ve Ayarlar penceresi kapatıldığında klavye kancasının (`hook`) sızması giderildi; `ESC` ile iptal desteği eklendi.
- **Shift Tuşu Takılı Kalma Riski:** Döngü içindeki `try...finally` bloğu, `atexit` ve pencere kapatma (`WM_DELETE_WINDOW`) kancalarıyla `Shift` tuşunun her koşulda güvenli serbest bırakılması garanti altına alındı.
- **Çoklu Implicit Yanlış Eşleşmesi:** Birden fazla `(implicit)` satırı olan eşyalarda (Eldritch, Synthesis, Vaal) 2. implicit'in explicit mod gibi taranması hatası düzeltildi.
- **Sayaç ve Deneme Limiti Hataları:** Ardışık aynı eşya ve ardışık boş okuma sayaçları ayrıldı; boş okuma tekrarlarının (`skip_click`) deneme sınırından düşmesi engellendi.
- **Minimal Mod Düzen Hatası:** Soket Renkleri modundayken Minimal Mod'dan Normal Mod'a dönüldüğünde yerleşimin bozulması düzeltildi.
- **Ayarlar Penceresi Konumu:** Minimal Mod'da veya ekran kenarındayken Ayarlar penceresinin ekran dışına taşması koordinat sınırlamasıyla giderildi.
- **Çalışma Dizini (CWD) Bağımlılığı:** `config.json`, `data/` ve `web/` yolları `BASE_DIR` üzerinden mutlak olarak çözümlendi; `Start.bat` içine `cd /d "%~dp0"` ve `python` yedeği eklendi.

### ✨ Yeni Özellikler
- **Responsive Web & Mobil Kontrol Paneli (`web/`):**
  - Telefon, tablet ve ikinci ekran web tarayıcılarında sorunsuz çalışan mobil öncelikli arayüz (alt sekme çubuğu, dokunmatik uyumlu kontroller, Koyu/Açık tema, TR/EN dil senkronizasyonu, PWA manifest).
  - SSE ile masaüstü uygulaması arasında anlık çift yönlü durum, log, filtre ve ayar senkronizasyonu.
  - **Canlı Eşya Filtre Test Aracı (Simülatör):** Oyundan kopyalanan herhangi bir eşya metnini tarayıcı veya mobilden yapıştırıp aktif filtreleri anında test etme imkânı.
  - CLI seçenekleri: `python main.py --web-only`, `--lan`, `--port`, `--no-web`, `--open-browser`.
- **Gelişmiş Filtreleme ve Eşleştirme:**
  - Ondalıklı sayı (`0.4`, `1.5`) ve negatif değer desteği.
  - Boş değerle boolean / sabit metin modlarını (örn. `Instant Recovery`, `Used when Charges reach full`, `25% increased effect`) eşleştirebilme.
  - `VE (AND)` / `VEYA (OR)` eşleşme mantığı seçimi.
  - Mod kapsamı seçimi: `Explicit`, `Implicit / Enchant`, `Tümü` (artık `Implicit` ve `0ptional.txt` kategorileri eksiksiz çalışır).
  - `~Open prefix~` ve `~Open suffix~` filtre desteği.
- **Gelişmiş Soket Renk Filtresi & Güvenlik Korumaları:**
  - Beyaz soket (`W`) hedefi ve "Beyaz soketleri joker say" seçeneği eklendi.
  - İmkansız soket hedefi (ör. 4 soketli eşyada 6 soket isteme) ve `Corrupted` / `Mirrored` / `Unidentified` eşyalar için başlangıç güvenlik duruşu eklendi.
  - Hiç aktif filtre veya renk hedefi yokken döngünün boşa dönmesini engelleyen ön kontrol eklendi.
- **Ayarlanabilir Zamanlama & Canlı İstatistikler:** Tıklama gecikmesi, pano okuma gecikmesi ayarları ile canlı deneme sayacı ve hız (`deneme/sn`) göstergesi eklendi.

### 🔒 Ağ Güvenliği, Veri Temizliği ve Testler
- Yerel Web & Mobil sunucusunda varsayılan `127.0.0.1` bağlama (LAN erişimi yalnızca kullanıcı onayıyla `0.0.0.0`), `os.path.commonpath` ile dizin aşımı (path traversal) koruması, 256 KB gövde boyut sınırı ve arayüzde XSS önleyici `textContent` kullanımı uygulandı.
- `data/` altındaki 7 veri dosyasındaki (`abyss_s.txt`, `flask_p.txt`, `heist_s.txt`, `item_p.txt`, `item_s.txt`, `map.txt`, `tincture_s.txt`) tekrar eden satırlar ve eşleşmeyi bozan `1 %` / `66 %` boşluk yazım hataları temizlendi.
- Kurulumu kolaylaştırmak için `requirements.txt` ve `.gitignore` yapılandırıldı.
- `tests/test_core.py` ve `tests/test_web_and_engine.py` altında 15 adet birim ve entegrasyon testi yazıldı ve tamamı başarıyla doğrulandı.
- Proje dokümantasyonu (`README.md`, `GEMINI.md`, `commit.md`, `changelog.md`) oluşturuldu/güncellendi.

---
