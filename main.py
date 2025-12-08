import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
import json
import threading
import time
import keyboard
import pyautogui
import pyperclip
import re
import os
import psutil
import winsound

CONFIG_FILE = "config.json"
DATA_DIR = "data"  # Txt dosyalarinin aranacagi klasor

# Dosya eslesmeleri (Kategori Adi: [Dosya Listesi])
ITEM_DATABASE_MAP = {
    "Abyss Jewel": ["abyss_p.txt", "abyss_s.txt"],
    "Cluster Jewel": ["cluster_p.txt", "cluster_s.txt"],
    "Flask": ["flask_p.txt", "flask_s.txt"],
    "Heist": ["heist_p.txt", "heist_s.txt"],
    "Implicit": ["implicit.txt"],
    "Item (General)": ["item_p.txt", "item_s.txt"],
    "Jewel (Regular)": ["jewel_p.txt", "jewel_s.txt"],
    "Map": ["map.txt"],
    "Sextant": ["sextant.txt"],
    "Tincture": ["tincture_p.txt", "tincture_s.txt"],
    "Optional/General": ["0ptional.txt"]
}

# --- DIL KUTUPHANESI (TRANSLATIONS) ---
TRANSLATIONS = {
    "TR": {
        "status_stopped": "● DURDU",
        "status_running": "● ÇALIŞIYOR",
        "status_found": "● BULUNDU",
        "control_panel": "Kontrol Paneli",
        "settings": "Ayarlar",
        "max_tries": "Deneme Sınırı:",
        "mode": "| Mod:",
        "attribute": "Modlar",
        "color": "Soket Renkleri",
        "start": "Başlat:",
        "stop": "Durdur:",
        "attr_filters_library": "Mod Filtreleri & Kütüphane",
        "color_filters": "Renk Filtreleri",
        "database_library": "Veritabanı / Kütüphane",
        "type": "Tip:",
        "search_lib": "Kütüphanede Ara:",
        "active_filters": "Aktif Filtreler (Çift Tık: Pasif/Aktif)", 
        "value_min": "Değer (Min)",
        "modifier_name": "Mod İsmi",
        "add_filter": "Filtre Ekle",
        "delete_selected": "Seçileni Sil",
        "system_log": "Sistem Günlüğü",
        "red": "Kırmızı:",
        "green": "Yeşil:",
        "blue": "Mavi:",
        "lang": "Dil:",
        "log_limit_unlimited": "Sınırsız deneme aktif.",
        "log_limit_set": "Limit {} deneme olarak ayarlandı.",
        "log_hotkey_error": "Hata: '{}' zaten {} için ayarlı!",
        "log_hotkey_cancel": "Tuş ayarlama iptal edildi.",
        "log_poe_active": "PoE aktif değil - duraklatılıyor...",
        "log_poe_not_active_start": "HATA: Path of Exile aktif değil! Başlatılamaz.",
        "log_scanning": "Başlamadan önce eşya taranıyor...",
        "log_already_match": ">>> GÜVENLİK DURUŞU: Eşya ZATEN filtreye uyuyor! Başlatılmadı.",
        "log_no_implicit": ">>> GÜVENLİK DURUŞU: Implicit bulunamadı (Mouse eşyada değil?). Başlatılmadı.",
        "log_read_fail": ">>> GÜVENLİK DURUŞU: Eşya verisi okunamadı. Başlatılmadı.",
        "log_start_loop": "Eşya kontrol edildi. DÖNGÜ BAŞLIYOR.",
        "log_stopping": "Durduruluyor...",
        "log_stop_key_loop": "Durdurma tuşuna basıldı (döngü başı).",
        "log_stop_key_read": "Durdurma tuşuna basıldı (okuma sonrası).",
        "log_same_item": "!!! AYNI EŞYA 3 KEZ ALGILANDI (Takıldı/Mouse kaydı?) - DURDURULUYOR !!!",
        "log_match_found": "===== EŞLEŞME BULUNDU - DURDURULUYOR =====",
        "log_invalid_item": "!!! Mouse eşya üzerinde değil veya geçersiz. DURDURULUYOR. !!!",
        "log_read_retry": "Okuma hatası. Tekrar deneniyor...",
        "log_read_empty_3": "!!! OKUMA 3 KEZ BOŞ (Mouse uzaklaştı mı?) - DURDURULUYOR !!!",
        "log_attempt": "--- Deneme {}/{} ---",
        "log_retry_click": "--- Okuma Tekrarı (Deneme {}) ---",
        "log_checking": "---- EŞYA KONTROL EDİLİYOR ----",
        "log_color_match": "RENK EŞLEŞTİ: {}",
        "log_color_fail": "Renk kontrolü başarısız veya eşleşme yok.",
        "log_matched": "Eşleşti: {} -> {} ({})",
        "log_saw": "Görüldü: {}",
        "log_no_socket": "Soket satırı bulunamadı",
        "log_no_req": "Renk gereksinimi yok",
        "log_socket_match_detail": "Soketler eşleşti: Bulunan(R:{}, G:{}, B:{})",
        "log_match_simplified": "\nMod bulundu;\nAranan: '{}'\nBulunan: '{}'",
        "log_substring_match": "Alt metin eşleşmesi '{}'",
        "log_thresh_match": "Eşik eşleşmesi: {} >= {} -> '{}' için",
        "log_hotkeys_reg": "Kısayollar kaydedildi: {} (Başlat) / {} (Durdur)",
        "log_hotkey_reg_err": "Kısayol kayıt hatası: {}",
        "log_filter_toggled": "Filtre durumu değiştirildi: {} -> {}",
        "passive_tag": "[PASİF]",
        "status_active": "Aktif",
        "status_passive": "Pasif"
    },
    "EN": {
        "status_stopped": "● STOPPED",
        "status_running": "● RUNNING",
        "status_found": "● FOUND",
        "control_panel": "Control Panel",
        "settings": "Settings",
        "max_tries": "Max Tries:",
        "mode": "| Mode:",
        "attribute": "Modifiers",
        "color": "Socket Colors",
        "start": "Start:",
        "stop": "Stop:",
        "attr_filters_library": "Modifier Filters & Library",
        "color_filters": "Color Filters",
        "database_library": "Database / Library",
        "type": "Type:",
        "search_lib": "Search in Library:",
        "active_filters": "Active Filters (Dbl Click: Toggle)", 
        "value_min": "Value (Min)",
        "modifier_name": "Modifier Name",
        "add_filter": "Add Filter",
        "delete_selected": "Delete Selected",
        "system_log": "System Log",
        "red": "Red:",
        "green": "Green:",
        "blue": "Blue:",
        "lang": "Lang:",
        "log_limit_unlimited": "Unlimited attempts active.",
        "log_limit_set": "Limit set to {} attempts.",
        "log_hotkey_error": "Error: '{}' is already set for {}!",
        "log_hotkey_cancel": "Hotkey setup cancelled.",
        "log_poe_active": "PoE not active - pausing...",
        "log_poe_not_active_start": "ERROR: Path of Exile is not active! Cannot start.",
        "log_scanning": "Scanning item before starting loop...",
        "log_already_match": ">>> SAFETY STOP: Item ALREADY MATCHES the filter! Not starting.",
        "log_no_implicit": ">>> SAFETY STOP: No implicit found (Mouse not over item?). Not starting.",
        "log_read_fail": ">>> SAFETY STOP: Could not read item data. Not starting.",
        "log_start_loop": "Item checked. STARTING LOOP.",
        "log_stopping": "Stopping...",
        "log_stop_key_loop": "Stop key pressed (loop start).",
        "log_stop_key_read": "Stop key pressed (after read).",
        "log_same_item": "!!! SAME ITEM DETECTED 3 TIMES (Stuck/Mouse moved?) - STOPPING !!!",
        "log_match_found": "===== MATCH FOUND - STOPPING =====",
        "log_invalid_item": "!!! Mouse not over item or invalid item. STOPPING. !!!",
        "log_read_retry": "Read failed. Retrying...",
        "log_read_empty_3": "!!! READ EMPTY 3 TIMES (Mouse moved away?) - STOPPING !!!",
        "log_attempt": "--- Attempt {}/{} ---",
        "log_retry_click": "--- Retry Read (Attempt {}) ---",
        "log_checking": "---- CHECKING ITEM ----",
        "log_color_match": "COLOR MATCH: {}",
        "log_color_fail": "Color check failed or no match.",
        "log_matched": "Matched: {} -> {} ({})",
        "log_saw": "Saw: {}",
        "log_no_socket": "No Sockets line found",
        "log_no_req": "No color requirements set",
        "log_socket_match_detail": "Sockets matched: Found(R:{}, G:{}, B:{})",
        "log_match_simplified": "\nModifier found;\nSearched: '{}'\nFound: '{}'",
        "log_substring_match": "Substring match '{}'",
        "log_thresh_match": "Threshold match: {} >= {} for '{}'",
        "log_hotkeys_reg": "Hotkeys registered: {} (Start) / {} (Stop)",
        "log_hotkey_reg_err": "Hotkey registration error: {}",
        "log_filter_toggled": "Filter status toggled: {} -> {}",
        "passive_tag": "[PASSIVE]",
        "status_active": "Active",
        "status_passive": "Passive"
    }
}

running = False
# Config variables
filters = []
safety_limit = 40
hotkey_start = "F2"
hotkey_stop = "F3"
search_mode = "attribute"
color_targets = {"R": 0, "G": 0, "B": 0}
last_category = "" 
current_language = "TR"

# Hotkey dinleme durumu
listening_key = {"active": False, "type": None, "hook": None}

# Loglama zamanlayicisi (Debounce icin)
limit_log_timer = None
last_logged_limit = 40 

# ---------------- DATA LOADER -----------------
def load_library_data(category):
    if not os.path.exists(DATA_DIR):
        try: os.makedirs(DATA_DIR)
        except: pass
        return ["'data' klasörü bulunamadı!"]

    files_to_read = ITEM_DATABASE_MAP.get(category, [])
    combined_lines = set()

    for filename in files_to_read:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        clean_line = line.strip()
                        if clean_line and not clean_line.startswith("//"):
                            combined_lines.add(clean_line)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return sorted(list(combined_lines))

# ---------------- CONFIG LOAD / SAVE -----------------
def load_config():
    global filters, safety_limit, hotkey_start, hotkey_stop, search_mode, color_targets, last_category, last_logged_limit, current_language
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                filters[:] = data.get("filters", [])
                
                # Eski config dosyalari icin 'active' anahtarini varsayilan olarak True yap
                for f_item in filters:
                    if "active" not in f_item:
                        f_item["active"] = True
                        
                safety_limit = data.get("safety_limit", 40)
                hotkey_start = data.get("hotkey_start", "f2").lower()
                hotkey_stop = data.get("hotkey_stop", "f3").lower()
                search_mode = data.get("search_mode", "attribute")
                color_targets = data.get("color_targets", {"R": 0, "G": 0, "B": 0})
                last_category = data.get("last_category", "")
                current_language = data.get("language", "TR")
                
                last_logged_limit = safety_limit
        except Exception as e:
            print("Config load error:", e)

def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "filters": filters,
                "safety_limit": safety_limit,
                "hotkey_start": hotkey_start,
                "hotkey_stop": hotkey_stop,
                "search_mode": search_mode,
                "color_targets": color_targets,
                "last_category": last_category,
                "language": current_language
            }, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Config save error:", e)

# ---------------- HELPER: GET TEXT -----------------
def get_text(key, *args):
    lang_dict = TRANSLATIONS.get(current_language, TRANSLATIONS["TR"])
    text = lang_dict.get(key, key)
    if args:
        try:
            return text.format(*args)
        except:
            return text
    return text

# ---------------- PROCESS CHECK -----------------
def is_poe_active():
    try:
        import win32gui
        import win32process
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                proc_name = process.name().lower()
                return "pathofexile" in proc_name
            except:
                pass
    except:
        pass
    return False

# ---------------- SOUND -----------------
def play_sound(sound_type):
    def _play():
        try:
            if sound_type == "success":
                winsound.Beep(1568, 150)
                winsound.Beep(1046, 150)
            elif sound_type == "error":
                winsound.Beep(200, 400)
        except Exception as e:
            print(f"Sound error: {e}")
    _play()

# ---------------- SHIFT CONTROL -----------------
def hold_shift_once():
    try: pyautogui.keyDown('shift')
    except: pass

def release_shift_once():
    try: pyautogui.keyUp('shift')
    except: pass

# ---------------- LOG -----------------
def log(text):
    def _log():
        try:
            log_box.insert(tk.END, text + "\n")
            log_box.see(tk.END)
        except:
            pass
    if root:
        root.after(0, _log)

# ---------------- READ CLIPBOARD -----------------
def read_clipboard_after_copy():
    try: pyperclip.copy("")
    except: pass
    try: pyautogui.hotkey('ctrl', 'c')
    except: keyboard.send('ctrl+c')
    time.sleep(0.06)
    try: return pyperclip.paste() or ""
    except: return ""

# ---------------- MATCHING LOGIC -----------------
def filter_matches_item(filt, item_text):
    name = (filt.get("name") or "").strip()
    val_str = (filt.get("value") or "").strip()

    if not val_str: return False, None
    txt = item_text

    try:
        target_values = [int(x.strip()) for x in val_str.split(',') if x.strip()]
    except:
        if val_str.lower() in txt.lower():
            return True, get_text("log_substring_match", val_str)
        return False, None

    if not target_values: return False, None
    lines = txt.split('\n')

    if "#" in name:
        parts = name.split('#')
        escaped_parts = [re.escape(p) for p in parts]
        pattern_str = r'([+-]?\d+)'.join(escaped_parts)
        
        for line in lines:
            match = re.search(pattern_str, line, re.IGNORECASE)
            if match:
                found_groups = match.groups()
                check_count = min(len(found_groups), len(target_values))
                if check_count == 0: continue

                all_conditions_met = True
                
                for i in range(check_count):
                    try:
                        f_val = int(found_groups[i])
                        t_val = target_values[i]
                        if f_val < t_val:
                            all_conditions_met = False
                            break
                    except:
                        all_conditions_met = False
                        break
                if all_conditions_met:
                    # Eslesti, simdi log icin duzgun format olusturalim
                    # 1. Filtre ismindeki # isaretlerini aranan degerlerle doldur
                    display_name = name
                    for i in range(check_count):
                        display_name = display_name.replace("#", str(target_values[i]), 1)
                    
                    # 2. Return olarak (Tuple) dondur ki analyze_item bunu anlasin
                    return True, (display_name, line.strip())
        return False, None

    thresh = target_values[0]
    for line in lines:
        if name.lower() in line.lower():
            nums = re.findall(r'([+-]?\d+)', line)
            for numstr in nums:
                try:
                    val_num = int(numstr)
                except:
                    continue
                if val_num >= thresh:
                    reason = get_text("log_thresh_match", val_num, thresh, name)
                    return True, reason
    return False, None

def check_color_match(item_text):
    socket_line = None
    for line in item_text.splitlines():
        if line.strip().startswith("Sockets:"):
            socket_line = line.strip()
            break
    if not socket_line: return False, get_text("log_no_socket")

    sockets_str = socket_line.replace("Sockets:", "").strip()
    count_r = sockets_str.count('R')
    count_g = sockets_str.count('G')
    count_b = sockets_str.count('B')
    req_r, req_g, req_b = color_targets.get("R", 0), color_targets.get("G", 0), color_targets.get("B", 0)

    if count_r >= req_r and count_g >= req_g and count_b >= req_b:
        if req_r == 0 and req_g == 0 and req_b == 0: return False, get_text("log_no_req")
        return True, get_text("log_socket_match_detail", count_r, count_g, count_b)
    return False, None

def analyze_item(item_text):
    cleaned = item_text.strip()
    if not cleaned: return 'EMPTY'
    log(get_text("log_checking"))
    
    if search_mode == "color":
        ok, reason = check_color_match(cleaned)
        if ok:
            log(get_text("log_color_match", reason))
            log("-----------------------")
            return 'FOUND'
        else:
            log(get_text("log_color_fail"))
            for line in cleaned.splitlines():
                if "Sockets:" in line:
                    log(get_text("log_saw", line.strip()))
            log("-----------------------")
            return 'CONTINUE'
    else:
        lines = cleaned.splitlines()
        start_index = None
        for i, line in enumerate(lines):
            if "(implicit)" in line:
                start_index = i + 1
                break
        if start_index is None:
            for i, line in enumerate(lines):
                if "Item Level:" in line:
                    start_index = i + 1
                    break
        if start_index is not None:
            for line in lines[start_index:]:
                if line.strip() == "" or "--------" in line:
                    continue
                log(line)

            search_text = "\n".join(lines[start_index:])
            if search_text.strip():
                for f in filters:
                    # --- STATUS CHECK EKLENDI ---
                    if not f.get("active", True): 
                        continue # Eger aktif degilse bu filtreyi atla
                    
                    ok, result = filter_matches_item(f, search_text)
                    if ok:
                        if isinstance(result, tuple):
                            req_text, found_text = result
                            log(get_text("log_match_simplified", req_text, found_text))
                        else:
                            log(get_text("log_matched", f.get('name','?'), f.get('value'), result))
                        
                        log("-----------------------")
                        return 'FOUND'
        else:
            log(get_text("log_no_implicit"))
            log("-----------------------")
            return 'NO_IMPLICIT'
    log("-----------------------")
    return 'CONTINUE'

# ---------------- AUTO LOOP -----------------
def auto_loop():
    global running, safety_limit
    attempt = 0
    prev_item_text = ""
    consecutive_same_count = 0
    skip_click = False

    while running and (safety_limit == 0 or attempt < safety_limit):
        
        if keyboard.is_pressed(hotkey_stop):
            log(get_text("log_stop_key_loop"))
            root.after(0, stop)
            return

        if not is_poe_active():
            log(get_text("log_poe_active"))
            root.after(0, stop)
            return
        
        attempt += 1
        limit_display = "∞" if safety_limit == 0 else str(safety_limit)
        
        if not running: break
        
        if not skip_click:
            log(get_text("log_attempt", attempt, limit_display))
            try: pyautogui.click()
            except Exception as e: log(f"Click error: {e}")
        else:
            log(get_text("log_retry_click", attempt))
            skip_click = False

        if not running: break
        item_text = read_clipboard_after_copy()
        
        if keyboard.is_pressed(hotkey_stop):
            log(get_text("log_stop_key_read"))
            root.after(0, stop)
            return
        
        if item_text and item_text == prev_item_text and item_text.strip() != "":
            consecutive_same_count += 1
            if consecutive_same_count >= 3:
                log(get_text("log_same_item"))
                play_sound("error")
                root.after(0, stop)
                return
        else:
            if item_text.strip() != "":
                consecutive_same_count = 0
                prev_item_text = item_text
        
        status = analyze_item(item_text)

        if status == 'FOUND':
            log(get_text("log_match_found"))
            play_sound("success")
            root.after(0, lambda: stop(from_found=True))
            return
        elif status == 'NO_IMPLICIT':
            log(get_text("log_invalid_item"))
            play_sound("error")
            root.after(0, stop)
            return
        elif status == 'EMPTY':
            log(get_text("log_read_retry"))
            skip_click = True
            
            consecutive_same_count += 1
            if consecutive_same_count >= 3:
                log(get_text("log_read_empty_3"))
                play_sound("error")
                root.after(0, stop)
                return
        
        time.sleep(0.12)

    root.after(0, stop)

# ---------------- START / STOP -----------------
def start():
    global running
    if listening_key["active"]:
        return
    if running:
        return
    
    if not is_poe_active():
        log(get_text("log_poe_not_active_start"))
        play_sound("error")
        return
    
    log(get_text("log_scanning"))
    item_text = read_clipboard_after_copy()
    status = analyze_item(item_text)
    
    if status == 'FOUND':
        log(get_text("log_already_match"))
        play_sound("success")
        root.after(0, lambda: status_label.config(text=get_text("status_found"), fg="#ffaa00", bg="#1a1a1a"))
        return
        
    elif status == 'NO_IMPLICIT':
        log(get_text("log_no_implicit"))
        play_sound("error")
        return
        
    elif status == 'EMPTY':
        log(get_text("log_read_fail"))
        play_sound("error")
        return
    
    log(get_text("log_start_loop"))
    
    running = True
    
    def _update_ui():
        status_label.config(text=get_text("status_running"), fg="#00ff88", bg="#1a1a1a")
    root.after(0, _update_ui)
    
    hold_shift_once()
    threading.Thread(target=auto_loop, daemon=True).start()

def stop(from_found=False):
    global running
    if listening_key["active"]:
        return

    if not running and not from_found:
        return

    running = False 
    log(get_text("log_stopping"))
    
    def _update_ui():
        if from_found:
            status_label.config(text=get_text("status_found"), fg="#ffaa00", bg="#1a1a1a")
        else:
            status_label.config(text=get_text("status_stopped"), fg="#ff4444", bg="#1a1a1a")
            
    root.after(0, _update_ui)
    release_shift_once()

# ---------------- GUI -----------------
load_config()

root = tk.Tk()
root.title("PoE Orb Tool - Advanced")
root.geometry("900x700")
root.attributes("-topmost", True)
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")

root.configure(bg="#2b2b2b")
style.configure("TLabelframe", background="#2b2b2b", foreground="#ffffff")
style.configure("TLabelframe.Label", background="#2b2b2b", foreground="#00d4ff", font=("Arial", 10, "bold"))
style.configure("TLabel", background="#2b2b2b", foreground="#ffffff")
style.configure("TButton", padding=6)
style.configure("TFrame", background="#2b2b2b")

style.layout('Custom.TRadiobutton', [
    ('Radiobutton.padding', {'sticky': 'nswe', 'children': [
        ('Radiobutton.indicator', {'side': 'left', 'sticky': ''}),
        ('Radiobutton.label', {'side': 'left', 'sticky': ''})
    ]})
])
style.configure("Custom.TRadiobutton", 
    background="#2b2b2b", 
    foreground="#ffffff", 
    font=("Arial", 9),
    indicatorbackground="#2b2b2b", 
    indicatorforeground="#ffffff" 
)
style.map("Custom.TRadiobutton",
    background=[('active', '#2b2b2b'), ('!disabled', '#2b2b2b'), ('focus', '#2b2b2b'), ('hover', '#2b2b2b')],
    foreground=[('active', '#ffffff'), ('!disabled', '#ffffff')],
    indicatorbackground=[('active', '#2b2b2b'), ('!disabled', '#2b2b2b')],
    indicatorforeground=[('selected', '#ffffff'), ('pressed', '#ffffff'), ('active', '#ffffff')]
)

# --- GLOBAL CLICK HANDLER ---
def on_global_click(event):
    if listening_key["active"]:
        listening_key["active"] = False
        k_type = listening_key["type"]
        original = hotkey_start if k_type == "start" else hotkey_stop
        target_btn = start_key_btn if k_type == "start" else stop_key_btn
        target_btn.config(text=original.upper())
        if listening_key["hook"]:
            keyboard.unhook(listening_key["hook"])
            listening_key["hook"] = None
        log(get_text("log_hotkey_cancel"))
        return

    widget = event.widget
    if not isinstance(widget, (ttk.Entry, tk.Entry, tk.Text, tk.Listbox, ttk.Button, tk.Button, ttk.Combobox)):
        root.focus()
        try: filters_list.selection_clear(0, tk.END)
        except: pass

root.bind("<Button-1>", on_global_click)

# --- VALIDATION FUNCTIONS ---
def validate_number_list_input(P):
    if P == "": return True
    return all(char.isdigit() or char == ',' for char in P)

def validate_single_digit_input(P):
    if P == "": return True
    return P.isdigit() and len(P) <= 1

vcmd_multi = (root.register(validate_number_list_input), '%P')
vcmd_single = (root.register(validate_single_digit_input), '%P')

# --- SELECT ALL ON FOCUS HELPER ---
def select_all(event):
    event.widget.after(10, lambda: event.widget.select_range(0, tk.END))

# --- OVERWRITE BEHAVIOR FOR COLORS ---
def on_color_keypress_overwrite(event):
    if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab"):
        return
    if event.char.isdigit():
        event.widget.delete(0, tk.END)

# ---------------- CONTROL PANEL -----------------
status_frame = ttk.LabelFrame(root, text="Control Panel", padding=10)
status_frame.pack(fill="x", padx=10, pady=5)

control_row = ttk.Frame(status_frame)
control_row.pack(fill="x")

status_label = tk.Label(control_row, text="● STOPPED", font=("Arial", 14, "bold"), 
                        fg="#ff4444", bg="#1a1a1a", padx=15, pady=6, relief="sunken")
status_label.pack(side="left", padx=(0, 20))

# Max Tries
lbl_max_tries = ttk.Label(control_row, text="Max Tries:", font=("Arial", 9))
lbl_max_tries.pack(side="left", padx=5)
limit_var = tk.StringVar(value=str(safety_limit))

# --- DEBOUNCED LIMIT LOGGING ---
def log_limit_change():
    global limit_log_timer, last_logged_limit
    val_str = limit_var.get()
    
    if val_str == "" or not val_str.isdigit():
        current_val = 0
    else:
        current_val = int(val_str)
        
    if current_val != last_logged_limit:
        if current_val == 0:
            log(get_text("log_limit_unlimited"))
        else:
            log(get_text("log_limit_set", current_val))
        
        last_logged_limit = current_val
    
    limit_log_timer = None

def on_limit_change(*args):
    global safety_limit, limit_log_timer
    val = limit_var.get()
    
    if val.isdigit():
        safety_limit = int(val)
        save_config()
    elif val == "":
        safety_limit = 0
        save_config()
    
    if limit_log_timer:
        root.after_cancel(limit_log_timer)
    
    limit_log_timer = root.after(800, log_limit_change)

limit_var.trace_add("write", on_limit_change)
entry_limit = tk.Entry(control_row, textvariable=limit_var, width=5, 
                       font=("Consolas", 11), justify="center", bg="white", fg="black")
def on_limit_focus_out(event):
    if limit_var.get() == "":
        limit_var.set("0")
entry_limit.bind("<FocusOut>", on_limit_focus_out)
entry_limit.bind("<FocusIn>", select_all, add="+") 

entry_limit.config(validate="key", validatecommand=(root.register(lambda P: P.isdigit() or P == ""), '%P'))
entry_limit.pack(side="left")

# Mode Selection
lbl_mode = ttk.Label(control_row, text="| Mode:", font=("Arial", 9, "bold"))
lbl_mode.pack(side="left", padx=(15, 5))
mode_var = tk.StringVar(value=search_mode)

def update_ui_for_mode():
    global search_mode
    search_mode = mode_var.get()
    save_config()
    
    # Text guncellemeleri
    if search_mode == "attribute":
        frame_filters.config(text=get_text("attr_filters_library"))
        frame_color_contents.pack_forget()
        frame_attr_contents.pack(fill="both", expand=True)
        
        frame_filters.pack_configure(fill="both", expand=True)
        frame_log.pack_configure(fill="x", expand=False)
        
    else:
        frame_filters.config(text=get_text("color_filters"))
        frame_attr_contents.pack_forget()
        frame_color_contents.pack(fill="x", pady=10)
        
        frame_filters.pack_configure(fill="x", expand=False)
        frame_log.pack_configure(fill="both", expand=True)

rb_attr = ttk.Radiobutton(control_row, text="Attribute", variable=mode_var, value="attribute", 
                          command=update_ui_for_mode, style="Custom.TRadiobutton")
rb_attr.pack(side="left", padx=2)
rb_color = ttk.Radiobutton(control_row, text="Color", variable=mode_var, value="color", 
                           command=update_ui_for_mode, style="Custom.TRadiobutton")
rb_color.pack(side="left", padx=2)

# Hotkeys Frame
hotkey_frame = ttk.Frame(control_row)
hotkey_frame.pack(side="right")

# --- LANGUAGE SELECT ---
lbl_lang = ttk.Label(hotkey_frame, text="Lang:")
lbl_lang.pack(side="left", padx=(5, 2))

lang_var = tk.StringVar(value=current_language)
lang_combo = ttk.Combobox(hotkey_frame, textvariable=lang_var, state="readonly", values=["TR", "EN"], width=3)
lang_combo.pack(side="left", padx=(0, 10))

start_label = ttk.Label(hotkey_frame, text="Start:")
start_label.pack(side="left", padx=(5, 2))
start_key_btn = ttk.Button(hotkey_frame, text=hotkey_start.upper(), width=6, takefocus=False)
start_key_btn.pack(side="left", padx=2)

stop_label = ttk.Label(hotkey_frame, text="Stop:")
stop_label.pack(side="left", padx=(10, 2))
stop_key_btn = ttk.Button(hotkey_frame, text=hotkey_stop.upper(), width=6, takefocus=False)
stop_key_btn.pack(side="left", padx=2)

# ---------------- MAIN CONTENT AREA -----------------
frame_filters = ttk.LabelFrame(root, text="Attribute Filters & Library", padding=5)
frame_filters.pack(fill="both", expand=True, padx=10, pady=5)

# --- 1. ATTRIBUTE & LIBRARY UI ---
frame_attr_contents = ttk.Frame(frame_filters)

# LEFT COLUMN: LIBRARY
library_frame = ttk.LabelFrame(frame_attr_contents, text="Database / Library", padding=5)
library_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

# Category Selector
lib_top_frame = ttk.Frame(library_frame)
lib_top_frame.pack(fill="x", pady=2)
lbl_type = ttk.Label(lib_top_frame, text="Type:")
lbl_type.pack(side="left")

category_var = tk.StringVar()
category_combo = ttk.Combobox(lib_top_frame, textvariable=category_var, state="readonly", values=list(ITEM_DATABASE_MAP.keys()))
category_combo.pack(side="left", fill="x", expand=True, padx=5)

# Init logic moved to bottom

# Library List & Logic
lib_list_frame = ttk.Frame(library_frame)
lib_list_frame.pack(fill="both", expand=True, pady=5)

lib_scrollbar = ttk.Scrollbar(lib_list_frame, orient="vertical")
lib_listbox = tk.Listbox(lib_list_frame, font=("Consolas", 9), bg="#222", fg="#ddd",
                         selectbackground="#555", yscrollcommand=lib_scrollbar.set)
lib_scrollbar.config(command=lib_listbox.yview)
lib_listbox.pack(side="left", fill="both", expand=True)
lib_scrollbar.pack(side="right", fill="y")

current_lib_data = []

def update_library_list(search_text=""):
    lib_listbox.delete(0, tk.END)
    search_lower = search_text.lower()
    for item in current_lib_data:
        if search_lower in item.lower():
            lib_listbox.insert(tk.END, item)

def on_category_change(event):
    global current_lib_data, last_category
    cat = category_var.get()
    last_category = cat 
    save_config() 
    
    current_lib_data = load_library_data(cat)
    search_var.set("")
    update_library_list("")
    
    if event:
        event.widget.selection_clear()
    root.focus()

category_combo.bind("<<ComboboxSelected>>", on_category_change)

# Library Search
lbl_search = ttk.Label(library_frame, text="Search in Library:")
lbl_search.pack(anchor="w")
search_var = tk.StringVar()
search_entry = ttk.Entry(library_frame, textvariable=search_var)
search_entry.pack(fill="x", pady=(0, 5))

def on_search_change(*args):
    update_library_list(search_var.get())
search_var.trace_add("write", on_search_change)

# RIGHT COLUMN: ACTIVE FILTERS
active_filter_frame = ttk.LabelFrame(frame_attr_contents, text="Active Filters (Dbl Click: Toggle)", padding=5)
active_filter_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

# Filter List
af_list_frame = ttk.Frame(active_filter_frame)
af_list_frame.pack(fill="both", expand=True)

af_scrollbar = ttk.Scrollbar(af_list_frame, orient="vertical")
filters_list = tk.Listbox(af_list_frame, font=("Consolas", 9), bg="#1a1a1a", fg="#00ff88",
                          selectbackground="#4a4a4a", yscrollcommand=af_scrollbar.set)
af_scrollbar.config(command=filters_list.yview)
filters_list.pack(side="left", fill="both", expand=True)
af_scrollbar.pack(side="right", fill="y")

# --- REFRESH FILTERS UI (Helper) ---
def refresh_filters_ui():
    filters_list.delete(0, tk.END)
    for i, f in enumerate(filters):
        display_text = f"{f.get('value','')} → {f.get('name','')}"
        
        is_active = f.get("active", True)
        if is_active:
            filters_list.insert(tk.END, display_text)
            filters_list.itemconfigure(i, fg="#00ff88") # Aktif: Yesil
        else:
            # Listbox satir bazli font desteklemedigi icin text degisikligi ve renk ile gosteriyoruz
            p_tag = get_text("passive_tag")
            filters_list.insert(tk.END, f"{p_tag} {display_text}")
            filters_list.itemconfigure(i, fg="#777777") # Pasif: Gri

# Initial load
refresh_filters_ui()

# Edit Controls
edit_frame = ttk.Frame(active_filter_frame)
edit_frame.pack(fill="x", pady=5)

header_frame = ttk.Frame(edit_frame)
header_frame.pack(fill="x")
lbl_header_value = ttk.Label(header_frame, text="Value (Min)", width=10)
lbl_header_value.pack(side="left")
lbl_header_name = ttk.Label(header_frame, text="Modifier Name")
lbl_header_name.pack(side="left", padx=5)

input_frame = ttk.Frame(edit_frame)
input_frame.pack(fill="x", pady=2)

value_var = tk.StringVar()
entry_value = tk.Entry(input_frame, textvariable=value_var, width=12, 
                       font=("Consolas", 11, "bold"), justify="center", bg="white", fg="black")
entry_value.config(validate="key", validatecommand=vcmd_multi)
entry_value.pack(side="left")

# --- INPUT SAG TIK TEMIZLEME ---
def on_input_right_click(event):
    event.widget.delete(0, tk.END)

entry_value.bind("<Button-3>", on_input_right_click)

name_var = tk.StringVar()
entry_name = tk.Entry(input_frame, textvariable=name_var, font=("Consolas", 10), bg="white", fg="black")
entry_name.pack(side="left", fill="x", expand=True, padx=5)

entry_name.bind("<Button-3>", on_input_right_click)

def add_filter(event=None):
    name = name_var.get().strip()
    value = value_var.get().strip()
    if not name or not value: return
    
    # Yeni filtre varsayilan olarak active=True
    f = {"name": name, "value": value, "active": True}
    filters.append(f)
    save_config()
    
    refresh_filters_ui() # Listeyi yeniden ciz
    
    name_var.set("") 
    value_var.set("")
    entry_value.focus()

def del_filter():
    sel = filters_list.curselection()
    if not sel: return
    idx = sel[0]
    filters.pop(idx)
    save_config()
    refresh_filters_ui() # Listeyi yeniden ciz

# Right click to edit
def on_active_filter_right_click(event):
    index = filters_list.nearest(event.y)
    if index < 0 or index >= len(filters): return
    filters_list.selection_clear(0, tk.END)
    filters_list.selection_set(index)
    filters_list.activate(index)
    f = filters[index]
    name_var.set(f.get("name", ""))
    value_var.set(f.get("value", ""))
    filters.pop(index)
    save_config()
    refresh_filters_ui()
    entry_value.focus()

filters_list.bind("<Button-3>", on_active_filter_right_click)

# --- DOUBLE CLICK TO TOGGLE STATUS ---
def toggle_filter_status(event):
    sel = filters_list.curselection()
    if not sel: return
    idx = sel[0]
    
    # Mevcut durumu tersine cevir
    current_status = filters[idx].get("active", True)
    new_status = not current_status
    filters[idx]["active"] = new_status
    
    save_config()
    refresh_filters_ui()
    
    status_msg = get_text("status_active") if new_status else get_text("status_passive")
    log(get_text("log_filter_toggled", filters[idx].get("name"), status_msg))

filters_list.bind("<Double-Button-1>", toggle_filter_status)

btn_frame = ttk.Frame(active_filter_frame)
btn_frame.pack(fill="x")
btn_add = ttk.Button(btn_frame, text="Add Filter", command=add_filter)
btn_add.pack(side="left", fill="x", expand=True, padx=(0,2))
btn_del = ttk.Button(btn_frame, text="Delete Selected", command=del_filter)
btn_del.pack(side="left", fill="x", expand=True, padx=(2,0))

entry_value.bind("<Return>", add_filter)
entry_name.bind("<Return>", lambda e: entry_value.focus())

def on_lib_double_click(event):
    sel = lib_listbox.curselection()
    if not sel: return
    text = lib_listbox.get(sel[0])
    name_var.set(text)
    value_var.set("")
    entry_value.focus()
lib_listbox.bind("<Double-Button-1>", on_lib_double_click)

# --- 2. COLOR FILTER UI ---
frame_color_contents = ttk.Frame(frame_filters)
color_input_frame = ttk.Frame(frame_color_contents)
color_input_frame.pack(anchor="center")

def setup_color_input(parent, key, color_hex, lbl_color, label_widget_ref):
    f = ttk.Frame(parent)
    f.pack(side="left", padx=10)
    
    l = tk.Label(f, text="", fg=lbl_color, bg="#2b2b2b", font=("Arial", 12, "bold"))
    l.pack(side="left")
    label_widget_ref[key] = l 
    
    e = tk.Entry(f, width=2, font=("Consolas", 14, "bold"), bg=color_hex, fg="white", justify="center")
    e.config(validate="key", validatecommand=vcmd_single)
    
    e.insert(0, str(color_targets.get(key, 0)))
    e.pack(side="left", padx=5)
    
    e.bind("<KeyPress>", on_color_keypress_overwrite)
    
    def on_release(ev):
        val = "".join([c for c in e.get() if c.isdigit()])
        if not val: val = "0"
        if len(val) > 1: val = val[-1]
        
        if val != e.get():
            e.delete(0, tk.END); e.insert(0, val)
        color_targets[key] = int(val)
        save_config()
        
    e.bind("<KeyRelease>", on_release)

# Renk etiketleri icin global referanslar
lbl_r, lbl_g, lbl_b = None, None, None
color_labels = {}

setup_color_input(color_input_frame, "R", "#880000", "#ff5555", color_labels)
setup_color_input(color_input_frame, "G", "#006600", "#55ff55", color_labels)
setup_color_input(color_input_frame, "B", "#000088", "#5555ff", color_labels)

lbl_r = color_labels["R"]
lbl_g = color_labels["G"]
lbl_b = color_labels["B"]

# ---------------- LOG AREA -----------------
frame_log = ttk.LabelFrame(root, text="System Log", padding=5)
# Fill x yerine both yapildi ki buyuyebilsin
frame_log.pack(fill="x", padx=10, pady=(5, 10))

log_box = tk.Text(frame_log, height=13, font=("Consolas", 8), bg="#1a1a1a", fg="#00ff88")
log_box.pack(fill="both", expand=True)

def on_log_clear(event):
    log_box.delete("1.0", tk.END)
log_box.bind("<Button-3>", on_log_clear)

# ---------------- INITIALIZATION -----------------
def listen_for_key(k_type):
    if listening_key["active"]: return
    listening_key["active"] = True
    listening_key["type"] = k_type
    target_btn = start_key_btn if k_type == "start" else stop_key_btn
    target_btn.config(text="...")
    
    def hook(e):
        global hotkey_start, hotkey_stop
        if not listening_key["active"]: return
        
        if e.event_type == 'down':
            key_name = e.name.lower()
            
            # 1. KONTROL: Diger tus ile cakisma var mi?
            other_key = hotkey_stop if k_type == "start" else hotkey_start
            other_action = "Stop" if k_type == "start" else "Start"
            
            if key_name == other_key:
                log(get_text("log_hotkey_error", key_name.upper(), other_action))
                return 

            # 2. IPTAL: Kendisi ile ayni tusa basilirsa iptal et
            current_key = hotkey_start if k_type == "start" else hotkey_stop
            if key_name == current_key:
                listening_key["active"] = False
                target_btn.config(text=e.name.upper())
                keyboard.unhook(listening_key["hook"])
                listening_key["hook"] = None
                return

            try: keyboard.remove_hotkey(hotkey_start)
            except: pass
            try: keyboard.remove_hotkey(hotkey_stop)
            except: pass

            if k_type == "start": hotkey_start = key_name
            else: hotkey_stop = key_name
            
            target_btn.config(text=key_name.upper(), state="normal")
            save_config()
            
            try:
                keyboard.add_hotkey(hotkey_start, start, suppress=True)
                keyboard.add_hotkey(hotkey_stop, stop, suppress=True)
                log(get_text("log_hotkeys_reg", hotkey_start.upper(), hotkey_stop.upper()))
            except Exception as ex: 
                log(get_text("log_hotkey_reg_err", ex))
            
            listening_key["active"] = False
            keyboard.unhook(listening_key["hook"])
            listening_key["hook"] = None

    listening_key["hook"] = keyboard.on_press(hook, suppress=False)

start_key_btn.config(command=lambda: listen_for_key("start"))
stop_key_btn.config(command=lambda: listen_for_key("stop"))

try:
    keyboard.add_hotkey(hotkey_start, start, suppress=True)
    keyboard.add_hotkey(hotkey_stop, stop, suppress=True)
    log(get_text("log_hotkeys_reg", hotkey_start.upper(), hotkey_stop.upper()))
except Exception as e:
    log(get_text("log_hotkey_reg_err", e))

# --- UPDATE UI LANGUAGE DEFINITION ---
def update_ui_language():
    status_frame.config(text=get_text("control_panel"))
    lbl_max_tries.config(text=get_text("max_tries"))
    lbl_mode.config(text=get_text("mode"))
    rb_attr.config(text=get_text("attribute"))
    rb_color.config(text=get_text("color"))
    
    start_label.config(text=get_text("start"))
    stop_label.config(text=get_text("stop"))
    
    if search_mode == "attribute":
        frame_filters.config(text=get_text("attr_filters_library"))
    else:
        frame_filters.config(text=get_text("color_filters"))
        
    library_frame.config(text=get_text("database_library"))
    lbl_type.config(text=get_text("type"))
    lbl_search.config(text=get_text("search_lib"))
    
    active_filter_frame.config(text=get_text("active_filters"))
    lbl_header_value.config(text=get_text("value_min"))
    lbl_header_name.config(text=get_text("modifier_name"))
    
    btn_add.config(text=get_text("add_filter"))
    btn_del.config(text=get_text("delete_selected"))
    
    frame_log.config(text=get_text("system_log"))
    
    lbl_r.config(text=get_text("red"))
    lbl_g.config(text=get_text("green"))
    lbl_b.config(text=get_text("blue"))
    lbl_lang.config(text=get_text("lang"))
    
    if running:
        status_label.config(text=get_text("status_running"))
    else:
        current_text = status_label.cget("text")
        if "FOUND" in current_text or "BULUNDU" in current_text:
             status_label.config(text=get_text("status_found"))
        else:
             status_label.config(text=get_text("status_stopped"))
    
    # Dil degisince listedeki [PASİF] yazilarinin guncellenmesi icin
    refresh_filters_ui()

def on_language_change(event):
    global current_language
    current_language = lang_var.get()
    save_config()
    update_ui_language()
    
    if event:
        event.widget.selection_clear()
    root.focus()

lang_combo.bind("<<ComboboxSelected>>", on_language_change)

# Initial Load
update_ui_for_mode()
update_ui_language() 
refresh_filters_ui() # Ensure visuals are correct

if list(ITEM_DATABASE_MAP.keys()):
    if last_category and last_category in ITEM_DATABASE_MAP:
        category_combo.set(last_category)
    else:
        category_combo.current(0)
    
    on_category_change(None)

root.mainloop()