# POE-AutoMate - Proje Mimarisi ve Geliştirme Kuralları

## 1. Proje Ortamı ve Teknoloji Yığını
- **Ortam:** Windows (Masaüstü otomasyon + yerel web sunucusu), Python 3.9+ (geliştirme ortamı Python 3.14.6).
- **Çalıştırma Yolları:**
  - Masaüstü GUI + Web/Mobil Panel: `python main.py` veya `Start.bat`
  - Yalnızca Web & Mobil Panel (Headless): `python main.py --web-only --lan --port 8765`
  - Web Sunucusuz Masaüstü: `python main.py --no-web`
- **Dosya Yolu Disiplini:** Tüm dosya yolları (`config.json`, `data/`, `web/`) çalışma dizinine (CWD) değil `poe_automate/config.py` içindeki `BASE_DIR` sabitine göre çözümlenmelidir. Yeni dosya/kaynak eklerken göreceli CWD varsayımı yapma.
- **Altyapı ve Bağımlılıklar:**
  - Masaüstü Arayüzü: Python Standart Kütüphanesi `tkinter` / `ttk` (Windows DPI farkındalığı aktif).
  - Otomasyon: `keyboard`, `pyautogui`, `pyperclip`, `psutil`, `pywin32` (`requirements.txt`). Opsiyonel/platform dışı ortamlarda testlerin çalışabilmesi için bu importlar güvenli `try/except` ile korunur.
  - Web & Mobil Arayüz: Sıfır harici bağımlılık — Python `http.server.ThreadingHTTPServer` + SSE (`/api/events`) + Vanilla HTML5 / CSS3 / ES6 (`web/`). Dış CDN kullanma; yerel ağda tamamen çevrimdışı çalışabilmelidir.
- **Dil:** Arayüz çift dillidir (`TR` ve `EN`, varsayılan `TR`). Tüm çeviriler tek kaynak olan `poe_automate/i18n.py` içindeki `TRANSLATIONS` sözlüğünde tutulur. Commit mesajları, changelog kayıtları ve geliştirici notları Türkçe olmalıdır.

## 2. Otomasyon, Girdi ve Güvenlik Kuralları (KRİTİK)
- **Shift Tuşu Koruması:** `poe_automate/automation.py` içindeki `_auto_loop()` döngüsünde `Shift` tuşu yalnızca `try ... finally: self._release_shift()` bloğu içinde basılı tutulur. `stop()`, `shutdown()`, `atexit` ve GUI `WM_DELETE_WINDOW` akışlarındaki `Shift` serbest bırakma güvencesini **ASLA bozma**.
- **Global Keyboard Hook Kuralı:** `keyboard.add_hotkey()` geri çağrıları Windows düşük seviyeli klavye kancası thread'inde çalışır. Bu geri çağrıların içinde **ASLA** `time.sleep()`, `winsound.Beep()`, `pyperclip` veya `pyautogui` çalıştırma; uzun/bloklayıcı işlemleri daima arka plan thread'ine (`start_async`) devret.
- **Güvenlik Duruşlarını Koru:** Aşağıdaki koruma katmanları kullanıcı onayı olmadan devre dışı bırakılamaz:
  - Yalnızca Path of Exile aktif pencereyken çalışma (`is_poe_active()`, yükseltilmiş/Admin pencere için `GetWindowText` yedeği dahil).
  - Başlamadan önce eşyanın halihazırda filtreye uyup uymadığını kontrol etme (`FOUND` güvenlik duruşu).
  - `Corrupted`, `Mirrored` veya `Unidentified` eşyalarda işlem yapmama (`UNMODIFIABLE`).
  - Soket modunda eşyanın toplam soket sayısından fazla hedef istenmesi halinde anında durma (`IMPOSSIBLE_SOCKETS`).
  - Hiç aktif filtre veya renk hedefi yoksa başlamama (`NO_FILTERS` / `NO_COLOR_REQ`).
  - Ardışık 3 aynı eşya ve ardışık 3 boş okuma için **iki ayrı sayaç** kullanma; boş okuma tekrarında (`skip_click`) deneme hakkı düşmeme.
- **Zararlı Kod ve Ağ Güvenliği:** Projeye gizlenmiş (`obfuscated`), `eval`/`exec` tabanlı veya izinsiz dış ağ bağlantısı kuran hiçbir kod eklenemez. Web sunucusu varsayılan olarak yalnızca `127.0.0.1` dinler; `0.0.0.0` (LAN/Mobil erişim) yalnızca kullanıcı ayarlarından açıkça etkinleştirildiğinde kullanılır. Statik dosya servisindeki `os.path.commonpath` koruması ve 256 KB gövde sınırı korunmalıdır.

## 3. Açık/Koyu Tema ve Masaüstü + Web/Mobil Uyumluluk Disiplini
- Sistemde hem **Koyu Mod (`dark`)** hem de **Açık Mod (`light`)** desteklenir:
  - Masaüstü tema paletleri `poe_automate/gui.py` içindeki `PALETTES` sözlüğünde tutulur.
  - Web & Mobil tema değişkenleri `web/style.css` içindeki `:root` ve `[data-theme="light"]` seçicilerinde tutulur.
- Yeni bir bileşen, sekme, modal, kart veya durum etiketi eklerken **ASLA yalnızca tek temaya veya yalnızca masaüstüne odaklanma**:
  1. Hem `dark` hem `light` görünümünü aynı anda tasarla ve doğrula.
  2. Web arayüzünde `< 900px` mobil kırılımını (alt navigasyon çubuğu, yatay taşmasız tasarım, minimum 40px dokunmatik alan, `safe-area-inset-bottom`) koru.
  3. Masaüstü GUI'de Minimal Mod (`toggle_minimal_mode`) ve hem `attribute` hem `color` modları arası geçişin yerleşimi bozmadığını doğrula.
  4. Eklenen her metnin `TR` ve `EN` karşılığını `poe_automate/i18n.py` dosyasına ekle.

## 4. Yapılandırma, Veri Kütüphanesi ve Performans Standartları
- **Atomik ve Geriye Dönük Uyumlu `config.json`:** Tüm ayar okuma/yazma işlemleri `ConfigManager` (`poe_automate/config.py`) üzerinden yapılmalıdır. Yeni bir ayar alanı eklendiğinde `DEFAULT_CONFIG` ve `sanitize_config()` içine varsayılanı ile sınır doğrulamasını ekle; eski `config.json` dosyaları hatasız açılmaya devam etmelidir.
- **Thread-Safe Arayüz İletişimi:** Arka plan thread'lerinden Tkinter widget'larına **ASLA** doğrudan erişme. Tüm durum/log/ayar bildirimleri `AutomationEngine` olay yayıncısı -> GUI `queue.Queue` -> `root.after(50, _drain_events)` hattından geçmelidir.
- **Sınırlı Bellek & Hızlı Arama:**
  - `AutomationEngine._logs` (`maxlen=500`) ve Tkinter `log_box` (`MAX_LOG_LINES=600`) üst sınırlarını koru; sınırsız büyümeye izin verme.
  - `data/*.txt` dosyaları `LibraryManager` tarafından bellekte önbelleklenir; listeye eklemeler Tkinter'da tek Tcl çağrısı (`insert(tk.END, *items)`) ve debounce ile yapılmalıdır.
- **Veri Kütüphanesi (`data/*.txt`) Bütünlüğü:** Yeni kategori veya `.txt` dosyası eklendiğinde `poe_automate/library.py` içindeki `ITEM_DATABASE_MAP` güncellenmelidir. Veri dosyalarına tekrar eden satır veya `1 %` gibi hatalı boşluklar ekleme.
- **Ayrıştırıcı (`poe_automate/parser.py`) Standartları:** Path of Exile eşyaları `--------` ayraçlarıyla bölümlere ayrılır. Çoklu `(implicit)` / `(enchant)` satırları, `(fractured)` / `(crafted)` etiketleri, ondalıklı sayılar, boş değerli (boolean) modlar ve `~Open prefix~`/`~Open suffix~` kuralları için mevcut `tests/test_core.py` testlerini bozma; her yeni ayrıştırma kuralına mutlaka birim testi ekle.

## 5. Kodlama ve Çalışma Prensipleri
- **Önce Oku ve Dosya/Sembol Varlığını Doğrula:** Ezbere varsayımla kod yazma; değişiklik yapmadan önce ilgili modül, fonksiyon ve API uç noktalarının projede gerçekten var olduğunu doğrula.
- **Önem Sırasına Göre Adım Adım İlerle ve Doğrula:** Büyük değişiklikleri kritik önem sırasına göre adımlara böl. Değişiklik sonrası mutlaka otomatik testleri çalıştır (`python -B -m unittest discover -s tests -v`), JS dosyaları değiştiyse `node --check web/app.js` kontrolünü yap ve kullanıcıya hangi ekranda/modda neyi test edeceğini net biçimde belirt.
- **Kalıcı Çözüm Üret (Geçici Yama Yapma):** Bir özelliği veya alanı kaldırıyorsan geçici değerler bırakma; ilgili referansı `config.py`, `i18n.py`, `gui.py`, `web_server.py`, `web/*` ve testlerden kökünden temizle.
- **İşi Kullanıcıya Bırakma:** Talep edilen değişikliğin doğru ve eksiksiz çalışması için zorunlu olan bağımlı dosyaları, çevirileri, Web/Desktop senkronizasyonunu ve testleri kendin güncelle.
- **Benzer Kullanımlar ve Kapsam Onayı (KRİTİK):** Kullanıcı belirli bir dosya, bileşen veya işlevde değişiklik istediğinde proje genelinde benzer kullanımları tara. Önce talep edilen değişikliği (ve teknik olarak zorunlu bağımlı düzenlemeleri) uygula; ardından başka yerlerde tespit ettiğin bağımsız benzer kullanımları listeleyerek kullanıcıdan onay almadan değiştirme.
- **Onaylı İlerleme:** Kullanıcının açıkça talep ettiği değişiklikler için gereksiz onay isteme; kapsam belirsizse veya talep dışı riskli bir değişiklik (yeni pip bağımlılığı, otomasyon güvenlik kuralı değişikliği vb.) gerekiyorsa önce kullanıcıya danış.
- **Commit, Changelog ve Geçmiş Hafıza Yönetimi (KRİTİK):**
  - **Geçmiş Bağlamı Okuma (Dış Hafıza):** Kullanıcı önceki değişikliklerden bahsettiğinde tahminde bulunma; önce proje kökündeki `changelog.md` ve `commit.md` dosyalarını (ve `git log` kayıtlarını) okuyarak kapsamı doğrula.
  - **Commit Metnini Kaydet (`commit.md`):** Her görevin sonunda yapılan değişiklikleri özetleyen kısa ve net bir Türkçe Git commit metni oluştur. Proje ana dizinindeki `commit.md` dosyası yoksa oluştur; varsa yeni commit metnini dosyanın **en üstüne** ekle ve eski kayıtlarla araya `---` ayraç koy.
  - **Değişiklik Günlüğünü Güncelle (`changelog.md`):** Proje ana dizinindeki `changelog.md` dosyası yoksa oluştur; varsa yeni değişikliği dosyanın **en üstüne** ekle ve eski kayıtlarla araya `---` ayraç koy.
- **Haritayı Güncel Tut:** Projeye yeni bir dosya eklediğinde, sildiğinde veya adını değiştirdiğinde aşağıdaki 6. bölümü (`HARITA_BASLANGIC` – `HARITA_BITIS`) aynı işlemde güncelle.

## 6. Proje Klasör ve Dosya Haritası (Hızlı Erişim Önbelleği)
<!-- HARITA_BASLANGIC -->
- **Giriş Noktası ve Başlatıcılar:** `main.py` (CLI + Masaüstü/Web başlatıcı), `Start.bat` (Windows konsolsuz başlatıcı)
- **Yapılandırma, Bağımlılık ve Kurallar:** `config.json`, `requirements.txt`, `.gitignore`, `README.md`, `GEMINI.md`, `changelog.md`, `commit.md`
- **Çekirdek Python Paketi (`poe_automate/`):**
  - `__init__.py` — Sürüm ve uygulama sabitleri (`__version__`)
  - `config.py` — Thread-safe `ConfigManager`, `BASE_DIR`, atomik JSON kaydı ve şema doğrulama
  - `i18n.py` — Ortak TR/EN çeviri sözlüğü (`TRANSLATIONS`, `get_text`)
  - `library.py` — `ITEM_DATABASE_MAP` ve önbellekli çoklu kelime arama motoru (`LibraryManager`)
  - `parser.py` — Path of Exile eşya pano ayrıştırıcısı (`ParsedItem`), mod/soket eşleştirme ve `evaluate_item()`
  - `automation.py` — Thread-safe `AutomationEngine`, Shift güvenliği, global kısayollar, ses ve event pub/sub
  - `web_server.py` — Sıfır harici bağımlılıklı `ThreadingHTTPServer`, REST API ve SSE (`/api/events`) sunucusu
  - `gui.py` — Yüksek DPI uyumlu, Koyu/Açık temalı, Minimal Modlu Tkinter masaüstü arayüzü (`AutoMateGUI`)
- **Web & Mobil Arayüz (`web/`):** `index.html`, `style.css`, `app.js`, `manifest.json`, `favicon.svg`
- **Mod Veritabanı Dosyaları (`data/`):** `0ptional.txt`, `abyss_p.txt`, `abyss_s.txt`, `cluster_p.txt`, `cluster_s.txt`, `flask_p.txt`, `flask_s.txt`, `heist_p.txt`, `heist_s.txt`, `implicit.txt`, `item_p.txt`, `item_s.txt`, `jewel_p.txt`, `jewel_s.txt`, `map.txt`, `sextant.txt`, `tincture_p.txt`, `tincture_s.txt`
- **Otomatik Testler (`tests/`):** `test_core.py` (config, kütüphane, ayrıştırıcı, eşleştirme), `test_web_and_engine.py` (otomasyon güvenlik kuralları, REST/SSE API ve statik dosya güvenliği)
<!-- HARITA_BITIS -->
