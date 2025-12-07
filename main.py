import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
import keyboard
import pyautogui
import pyperclip
import re
import os
import psutil

CONFIG_FILE = "config.json"

running = False
filters = []
safety_limit = 40
hotkey_start = "F2"
hotkey_stop = "F3"

# ---------------- CONFIG LOAD / SAVE -----------------
def load_config():
    global filters, safety_limit, hotkey_start, hotkey_stop
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                filters[:] = data.get("filters", [])
                safety_limit = data.get("safety_limit", 40)
                hotkey_start = data.get("hotkey_start", "f2").lower()
                hotkey_stop = data.get("hotkey_stop", "f3").lower()
        except Exception as e:
            print("Config load error:", e)

def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "filters": filters,
                "safety_limit": safety_limit,
                "hotkey_start": hotkey_start,
                "hotkey_stop": hotkey_stop
            }, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Config save error:", e)

# ---------------- PROCESS CHECK -----------------
def is_poe_active():
    """Path of Exile (Steam) aktif mi kontrol eder"""
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

# ---------------- SHIFT CONTROL -----------------
def hold_shift_once():
    try:
        pyautogui.keyDown('shift')
    except Exception:
        pass

def release_shift_once():
    try:
        pyautogui.keyUp('shift')
    except Exception:
        pass

# ---------------- LOG -----------------
def log(text):
    def _log():
        log_box.insert(tk.END, text + "\n")
        log_box.see(tk.END)
    root.after(0, _log)

# ---------------- READ CLIPBOARD -----------------
def read_clipboard_after_copy():
    try:
        # ONLEM 1: Kopyalamadan once panoyu temizle. 
        # Boylece fare item uzerinde degilse eski veri kalmaz, bos doner.
        pyperclip.copy("")
    except:
        pass

    try:
        pyautogui.hotkey('ctrl', 'c')
    except Exception:
        keyboard.send('ctrl+c')
    time.sleep(0.06)
    try:
        return pyperclip.paste() or ""
    except Exception:
        return ""

# ---------------- MATCHING LOGIC -----------------
def filter_matches_item(filt, item_text):
    name = (filt.get("name") or "").strip()
    val = (filt.get("value") or "").strip()

    if not val:
        return False, None

    txt = item_text

    m_num = re.match(r'^([+-]?\d+)%?$', val)
    if m_num and name:
        thresh = int(m_num.group(1))
        lines = txt.split('\n')
        for line in lines:
            if name.lower() in line.lower():
                nums = re.findall(r'([+-]?\d+)', line)
                for numstr in nums:
                    try:
                        val_num = int(numstr)
                    except:
                        continue
                    if val_num >= thresh:
                        reason = f"threshold match: {val_num} >= {thresh} for '{name}' in line: {line.strip()}"
                        return True, reason
        return False, None

    if val.lower() in txt.lower():
        reason = f"substring match '{val}'"
        return True, reason

    return False, None

# ---------------- ITEM ANALYSIS -----------------
def analyze_item(item_text):
    """
    Item metnini analiz eder, loglar ve duruma gore kod doner:
    Returns: 'FOUND', 'NO_IMPLICIT', 'EMPTY', 'CONTINUE'
    """
    cleaned = item_text.strip()
    if not cleaned:
        # log("Clipboard empty or couldn't read.") # Log kirliligi yapmasin diye kapattik
        return 'EMPTY'

    log("---- CHECKING ITEM ----")
    lines = cleaned.splitlines()

    implicit_index = None
    for i, line in enumerate(lines):
        if "(implicit)" in line:
            implicit_index = i
            break

    if implicit_index is not None:
        # Implicit satirlarini logla
        for line in lines[implicit_index+1:]:
            if line.strip() == "" or "--------" in line:
                continue
            log(line)
        
        # Filtre kontrolu
        implicit_text = "\n".join(lines[implicit_index+1:])
        if implicit_text.strip():
            for f in filters:
                ok, reason = filter_matches_item(f, implicit_text)
                if ok:
                    log(f"Matched filter: {f.get('name','?')} -> {f.get('value')}; reason: {reason}")
                    log("-----------------------")
                    return 'FOUND'
    else:
        log("(No implicit found)")
        log("-----------------------")
        return 'NO_IMPLICIT'

    log("-----------------------")
    return 'CONTINUE'

# ---------------- AUTO LOOP -----------------
def auto_loop():
    global running, safety_limit

    attempt = 0
    
    # ONLEM 2: Arka arkaya ayni item gelme sayaci
    prev_item_text = ""
    consecutive_same_count = 0
    
    # ONLEM 3: Kopyalama basarisizsa (veya bos okursa) bir sonraki tur tiklamayi atla
    skip_click = False

    while running and (safety_limit == 0 or attempt < safety_limit):
        
        # 1. MANUEL STOP KONTROLU
        if keyboard.is_pressed(hotkey_stop):
            log("Stop key pressed (detected in loop).")
            running = False 
            root.after(0, stop)
            return

        if not is_poe_active():
            log("PoE not active - pausing...")
            running = False
            root.after(0, stop)
            return
        
        attempt += 1
        limit_display = "∞" if safety_limit == 0 else str(safety_limit)
        
        # 2. CLICK (Eger skip_click aktifse bu adimi atla)
        if not running: break
        
        if not skip_click:
            log(f"--- Attempt {attempt}/{limit_display} ---")
            try:
                pyautogui.click()
            except Exception as e:
                log(f"Click error: {e}")
        else:
            log(f"--- Retry Read (Attempt {attempt}) ---")
            log("Skipping click to retry reading...")
            # Flag'i false yap, eger okuma basarili olursa bir sonraki tur tiklasin
            skip_click = False

        # 3. CLIPBOARD OKUMA
        if not running: break
        item_text = read_clipboard_after_copy()
        
        # --- STUCK / AYNI ITEM KONTROLU ---
        # Eger okunan metin bos degilse ve bir oncekiyle birebir ayniysa:
        if item_text and item_text == prev_item_text and item_text.strip() != "":
            consecutive_same_count += 1
            if consecutive_same_count >= 3:
                log("!!! SAME ITEM DETECTED 3 TIMES (Stuck/Mouse moved?) - STOPPING !!!")
                running = False
                root.after(0, stop)
                return
        else:
            # Farkli bir metin geldiyse (veya bos degilse) sayaci sifirla
            if item_text.strip() != "":
                consecutive_same_count = 0
                prev_item_text = item_text
        # ----------------------------------
        
        if keyboard.is_pressed(hotkey_stop):
            running = False
            root.after(0, stop)
            return

        # 4. ITEM ANALIZI
        status = analyze_item(item_text)

        if status == 'FOUND':
            log("===== MATCH FOUND - STOPPING =====")
            running = False
            root.after(0, lambda: stop(from_found=True))
            return
        elif status == 'NO_IMPLICIT':
            log("!!! Mouse not over item or invalid item. STOPPING. !!!")
            running = False
            root.after(0, stop)
            return
        elif status == 'EMPTY':
            # ONLEM 3 DEVREYE GIRIYOR:
            # Bos okuduysa: Ya mouse item ustunde degil, ya da Ctrl+C o an calismadi.
            # Bir sonraki tur tiklama yapma, sadece okumayi tekrar dene.
            log("Read failed (Empty). Retrying read next loop without clicking...")
            skip_click = True
            
            consecutive_same_count += 1
            if consecutive_same_count >= 3:
                log("!!! READ EMPTY 3 TIMES (Mouse moved away?) - STOPPING !!!")
                running = False
                root.after(0, stop)
                return
        
        # 'CONTINUE' durumunda dongu devam eder (sleep -> basa don)
        time.sleep(0.12)

    running = False
    root.after(0, stop)

# ---------------- START / STOP -----------------
def start():
    global running
    if running:
        return
    
    if not is_poe_active():
        log("ERROR: Path of Exile is not active! Cannot start.")
        return
    
    # --- SAFETY PRE-CHECK ---
    log("Scanning item before starting loop...")
    
    # 1. Panoya kopyala
    item_text = read_clipboard_after_copy()
    
    # 2. Analiz et
    status = analyze_item(item_text)
    
    if status == 'FOUND':
        log(">>> SAFETY STOP: Item ALREADY MATCHES the filter! Not starting.")
        # Kullaniciya gorsel uyari (Turuncu FOUND yazisi)
        root.after(0, lambda: status_label.config(text="● FOUND", fg="#ffaa00", bg="#1a1a1a"))
        return # Donguyu baslatmadan cik
        
    elif status == 'NO_IMPLICIT':
        log(">>> SAFETY STOP: No implicit found (Mouse not over item?). Not starting.")
        return # Donguyu baslatmadan cik
        
    elif status == 'EMPTY':
        log(">>> SAFETY STOP: Could not read item data. Not starting.")
        return
    
    # Eger 'CONTINUE' donduyse item uygun degildir, yani baslayabiliriz.
    log("Item check passed (No match). STARTING LOOP.")
    
    running = True
    
    def _update_ui():
        status_label.config(text="● RUNNING", fg="#00ff88", bg="#1a1a1a")
    root.after(0, _update_ui)
    
    hold_shift_once()
    threading.Thread(target=auto_loop, daemon=True).start()

def stop(from_found=False):
    global running
    running = False 
    log("Stopping...")
    
    def _update_ui():
        if from_found:
            status_label.config(text="● FOUND", fg="#ffaa00", bg="#1a1a1a")
        else:
            status_label.config(text="● STOPPED", fg="#ff4444", bg="#1a1a1a")
            
    root.after(0, _update_ui)
    release_shift_once()

# ---------------- GUI -----------------
load_config()

root = tk.Tk()
root.title("PoE Orb Tool")
root.geometry("600x570")
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

# --- GLOBAL FOCUS CLICK HANDLER ---
def on_global_click(event):
    widget = event.widget
    if isinstance(widget, (ttk.Entry, tk.Text, tk.Listbox, ttk.Button, tk.Button, tk.Scrollbar, ttk.Scrollbar)):
        return
    root.focus()
    try:
        filters_list.selection_clear(0, tk.END)
    except:
        pass

root.bind("<Button-1>", on_global_click)

# Status & Controls
status_frame = ttk.LabelFrame(root, text="Control Panel", padding=10)
status_frame.pack(fill="x", padx=10, pady=10)

control_row = ttk.Frame(status_frame)
control_row.pack(fill="x")

status_label = tk.Label(control_row, text="● STOPPED", font=("Arial", 14, "bold"), 
                        fg="#ff4444", bg="#1a1a1a", padx=15, pady=6, relief="sunken")
status_label.grid(row=0, column=0, sticky="w", padx=(0, 20))

ttk.Label(control_row, text="Limit:", font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="e", padx=5)
limit_var = tk.StringVar(value=str(safety_limit))
entry_limit = ttk.Entry(control_row, textvariable=limit_var, width=8, font=("Consolas", 11))
entry_limit.grid(row=0, column=2, padx=5)
ttk.Button(control_row, text="Save", command=lambda: update_limit(), width=8).grid(row=0, column=3, padx=5)

# Settings
frame_settings = ttk.LabelFrame(root, text="Settings", padding=8)
frame_settings.pack(fill="x", padx=10, pady=8)

settings_row = ttk.Frame(frame_settings)
settings_row.pack(fill="x", padx=5, pady=5)

ttk.Label(settings_row, text="Hotkeys:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))
ttk.Label(settings_row, text="Start:", font=("Arial", 9)).grid(row=0, column=1, sticky="e", padx=5)
start_key_btn = ttk.Button(settings_row, text=hotkey_start.upper(), width=10)
start_key_btn.grid(row=0, column=2, padx=5)
ttk.Label(settings_row, text="Stop:", font=("Arial", 9)).grid(row=0, column=3, sticky="e", padx=5)
stop_key_btn = ttk.Button(settings_row, text=hotkey_stop.upper(), width=10)
stop_key_btn.grid(row=0, column=4, padx=5)

listening_key = {"active": False, "type": None, "hook": None}

def update_limit():
    global safety_limit
    try:
        new_val = int(limit_var.get())
        safety_limit = new_val
        save_config()
        log(f"Safety limit updated to: {safety_limit} (0 = unlimited)")
    except:
        log("ERROR: Invalid safety limit value!")
        limit_var.set(str(safety_limit))

def listen_for_key(key_type):
    if listening_key["active"]:
        return
    
    listening_key["active"] = True
    listening_key["type"] = key_type
    
    original_key = hotkey_start if key_type == "start" else hotkey_stop
    
    if key_type == "start":
        start_key_btn.config(text="Press key...", state="disabled")
    else:
        stop_key_btn.config(text="Press key...", state="disabled")
    
    def on_key_event(e):
        if not listening_key["active"]:
            return
        
        global hotkey_start, hotkey_stop
        key_name = e.name
        
        if key_name == original_key:
            listening_key["active"] = False
            if listening_key["hook"]:
                keyboard.unhook(listening_key["hook"])
            
            if listening_key["type"] == "start":
                start_key_btn.config(text=original_key.upper(), state="normal")
            else:
                stop_key_btn.config(text=original_key.upper(), state="normal")
            return
        
        try:
            keyboard.remove_hotkey(hotkey_start)
        except:
            pass
        try:
            keyboard.remove_hotkey(hotkey_stop)
        except:
            pass
        
        if listening_key["type"] == "start":
            hotkey_start = key_name.lower()
            start_key_btn.config(text=key_name.upper(), state="normal")
        else:
            hotkey_stop = key_name.lower()
            stop_key_btn.config(text=key_name.upper(), state="normal")
        
        try:
            keyboard.add_hotkey(hotkey_start, start, suppress=True)
            keyboard.add_hotkey(hotkey_stop, stop, suppress=True)
        except:
            pass
        
        save_config()
        listening_key["active"] = False
        if listening_key["hook"]:
            keyboard.unhook(listening_key["hook"])
    
    listening_key["hook"] = keyboard.on_press(on_key_event, suppress=False)

start_key_btn.config(command=lambda: listen_for_key("start"))
stop_key_btn.config(command=lambda: listen_for_key("stop"))

# FILTERS
frame_filters = ttk.LabelFrame(root, text="Filters", padding=8)
frame_filters.pack(fill="x", padx=10, pady=8)

filters_container = ttk.Frame(frame_filters)
filters_container.pack(fill="both", padx=5, pady=5)

filters_scrollbar = ttk.Scrollbar(filters_container, orient="vertical")
filters_list = tk.Listbox(filters_container, height=5, font=("Consolas", 9), bg="#1a1a1a", 
                         fg="#00ff88", 
                         selectbackground="#4a4a4a", 
                         selectforeground="#ffffff", 
                         yscrollcommand=filters_scrollbar.set)
filters_scrollbar.config(command=filters_list.yview)

filters_list.pack(side="left", fill="both", expand=True)
filters_scrollbar.pack(side="right", fill="y")

for f in filters:
    filters_list.insert(tk.END, f"{f.get('value','')} → {f.get('name','')}")

def on_right_click(event):
    sel = filters_list.curselection()
    if not sel:
        index = filters_list.nearest(event.y)
        filters_list.selection_clear(0, tk.END)
        filters_list.selection_set(index)
        filters_list.activate(index)
        sel = (index,)
    
    if sel:
        idx = sel[0]
        f = filters[idx]
        value_var.set(f.get('value', ''))
        name_var.set(f.get('name', ''))
        filters.pop(idx)
        filters_list.delete(idx)
        save_config()

filters_list.bind("<Button-3>", on_right_click)

filter_input_frame = ttk.Frame(frame_filters)
filter_input_frame.pack(fill="x", padx=5, pady=5)

ttk.Label(filter_input_frame, text="Value:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=2)
value_var = tk.StringVar()
entry_value = ttk.Entry(filter_input_frame, textvariable=value_var, width=6, font=("Consolas", 10))
entry_value.grid(row=0, column=1, padx=2)

ttk.Label(filter_input_frame, text="Name:", font=("Arial", 9)).grid(row=0, column=2, sticky="w", padx=2)
name_var = tk.StringVar()
entry_name = ttk.Entry(filter_input_frame, textvariable=name_var, font=("Consolas", 9))
entry_name.grid(row=0, column=3, sticky="ew", padx=2)

filter_input_frame.columnconfigure(3, weight=1)

def add_filter():
    name = name_var.get().strip()
    value = value_var.get().strip()
    if not name or not value:
        return
    f = {"name": name, "value": value}
    filters.append(f)
    filters_list.insert(tk.END, f"{value} → {name}")
    save_config()
    name_var.set("")
    value_var.set("")
    entry_value.focus()

def del_filter():
    sel = filters_list.curselection()
    if not sel:
        return
    idx = sel[0]
    filters.pop(idx)
    filters_list.delete(idx)
    save_config()

btn_frame = ttk.Frame(frame_filters)
btn_frame.pack(fill="x", padx=5, pady=2)
ttk.Button(btn_frame, text="Add", command=add_filter).pack(side="left", padx=2)
ttk.Button(btn_frame, text="Delete", command=del_filter).pack(side="left", padx=2)

entry_name.bind("<Return>", lambda e: add_filter())
entry_value.bind("<Return>", lambda e: entry_name.focus())

# LOG
frame_log = ttk.LabelFrame(root, text="Log", padding=5)
frame_log.pack(fill="both", expand=True, padx=10, pady=8)

log_container = ttk.Frame(frame_log)
log_container.pack(fill="both", expand=True, padx=5, pady=5)

log_scrollbar = ttk.Scrollbar(log_container, orient="vertical")
log_box = tk.Text(log_container, height=12, wrap="word", font=("Consolas", 9), 
                 bg="#1a1a1a", fg="#00ff88", insertbackground="#00d4ff",
                 yscrollcommand=log_scrollbar.set)
log_scrollbar.config(command=log_box.yview)

def on_log_right_click(event):
    log_box.delete("1.0", tk.END)

log_box.bind("<Button-3>", on_log_right_click)

log_box.pack(side="left", fill="both", expand=True)
log_scrollbar.pack(side="right", fill="y")

try:
    keyboard.add_hotkey(hotkey_start, start, suppress=True)
    keyboard.add_hotkey(hotkey_stop, stop, suppress=True)
    log(f"Hotkeys registered: {hotkey_start.upper()} (Start) / {hotkey_stop.upper()} (Stop)")
except Exception as e:
    log(f"Hotkey registration error: {e}")

root.mainloop()