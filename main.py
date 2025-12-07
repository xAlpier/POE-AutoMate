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
# Config variables
filters = []
safety_limit = 40
hotkey_start = "F2"
hotkey_stop = "F3"
search_mode = "attribute" # 'attribute' or 'color'
color_targets = {"R": 0, "G": 0, "B": 0}

# ---------------- CONFIG LOAD / SAVE -----------------
def load_config():
    global filters, safety_limit, hotkey_start, hotkey_stop, search_mode, color_targets
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                filters[:] = data.get("filters", [])
                safety_limit = data.get("safety_limit", 40)
                hotkey_start = data.get("hotkey_start", "f2").lower()
                hotkey_stop = data.get("hotkey_stop", "f3").lower()
                search_mode = data.get("search_mode", "attribute")
                color_targets = data.get("color_targets", {"R": 0, "G": 0, "B": 0})
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
                "color_targets": color_targets
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
        try:
            log_box.insert(tk.END, text + "\n")
            log_box.see(tk.END)
        except:
            pass
    if root:
        root.after(0, _log)

# ---------------- READ CLIPBOARD -----------------
def read_clipboard_after_copy():
    try:
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

# ---------------- MATCHING LOGIC (ATTRIBUTE) -----------------
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

# ---------------- MATCHING LOGIC (COLOR) -----------------
def check_color_match(item_text):
    # Sockets satirini bul
    # Ornek: "Sockets: R-B-B-R-B-G"
    socket_line = None
    lines = item_text.splitlines()
    for line in lines:
        if line.strip().startswith("Sockets:"):
            socket_line = line.strip()
            break
    
    if not socket_line:
        return False, "No Sockets line found"

    # Soket harflerini say
    # Sadece R, G, B harflerine bakalim.
    
    # "Sockets: " kismini atalim
    sockets_str = socket_line.replace("Sockets:", "").strip()
    
    count_r = sockets_str.count('R')
    count_g = sockets_str.count('G')
    count_b = sockets_str.count('B')

    req_r = color_targets.get("R", 0)
    req_g = color_targets.get("G", 0)
    req_b = color_targets.get("B", 0)

    # Kosul: Itemdeki sayi >= Istenen sayi
    # Eger req_X = 0 ise, count_X >= 0 her zaman dogrudur (Yani o rengi yok sayar/onemsemez)
    if count_r >= req_r and count_g >= req_g and count_b >= req_b:
        # Hepsi 0 ise (filtre yoksa) eslesme sayma
        if req_r == 0 and req_g == 0 and req_b == 0:
             return False, "No color requirements set"
             
        reason = f"Sockets matched: Found(R:{count_r}, G:{count_g}, B:{count_b}) >= Req(R:{req_r}, G:{req_g}, B:{req_b})"
        return True, reason

    return False, None

# ---------------- ITEM ANALYSIS -----------------
def analyze_item(item_text):
    cleaned = item_text.strip()
    if not cleaned:
        return 'EMPTY'

    log("---- CHECKING ITEM ----")
    
    if search_mode == "color":
        # --- COLOR SEARCH MODE ---
        ok, reason = check_color_match(cleaned)
        if ok:
            log(f"COLOR MATCH: {reason}")
            log("-----------------------")
            return 'FOUND'
        else:
            log("Color check failed or no match.")
            # Log socket line for debug
            for line in cleaned.splitlines():
                if "Sockets:" in line:
                    log(f"Saw: {line.strip()}")
            log("-----------------------")
            return 'CONTINUE' # Match olmadigi surece devam

    else:
        # --- ATTRIBUTE SEARCH MODE (Legacy) ---
        lines = cleaned.splitlines()
        start_index = None
        
        # 1. Oncelik: (implicit) aramasi
        for i, line in enumerate(lines):
            if "(implicit)" in line:
                start_index = i + 1
                break
                
        # 2. Eger implicit yoksa: Item Level aramasi
        if start_index is None:
            for i, line in enumerate(lines):
                if "Item Level:" in line:
                    start_index = i + 1
                    break

        if start_index is not None:
            # Bulunan noktadan sonrasini analiz et
            for line in lines[start_index:]:
                if line.strip() == "" or "--------" in line:
                    continue
                log(line)
            
            # Filtre kontrolu
            search_text = "\n".join(lines[start_index:])
            if search_text.strip():
                for f in filters:
                    ok, reason = filter_matches_item(f, search_text)
                    if ok:
                        log(f"Matched filter: {f.get('name','?')} -> {f.get('value')}; reason: {reason}")
                        log("-----------------------")
                        return 'FOUND'
        else:
            log("(No implicit or Item Level found)")
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
            skip_click = False

        if not running: break
        item_text = read_clipboard_after_copy()
        
        if item_text and item_text == prev_item_text and item_text.strip() != "":
            consecutive_same_count += 1
            if consecutive_same_count >= 3:
                log("!!! SAME ITEM DETECTED 3 TIMES (Stuck/Mouse moved?) - STOPPING !!!")
                running = False
                root.after(0, stop)
                return
        else:
            if item_text.strip() != "":
                consecutive_same_count = 0
                prev_item_text = item_text
        
        if keyboard.is_pressed(hotkey_stop):
            running = False
            root.after(0, stop)
            return

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
            log("Read failed (Empty). Retrying read next loop without clicking...")
            skip_click = True
            
            consecutive_same_count += 1
            if consecutive_same_count >= 3:
                log("!!! READ EMPTY 3 TIMES (Mouse moved away?) - STOPPING !!!")
                running = False
                root.after(0, stop)
                return
        
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
    
    log("Scanning item before starting loop...")
    item_text = read_clipboard_after_copy()
    status = analyze_item(item_text)
    
    if status == 'FOUND':
        log(">>> SAFETY STOP: Item ALREADY MATCHES the filter! Not starting.")
        root.after(0, lambda: status_label.config(text="● FOUND", fg="#ffaa00", bg="#1a1a1a"))
        return
        
    elif status == 'NO_IMPLICIT':
        log(">>> SAFETY STOP: No implicit found (Mouse not over item?). Not starting.")
        return
        
    elif status == 'EMPTY':
        log(">>> SAFETY STOP: Could not read item data. Not starting.")
        return
    
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
root.title("PoE AutoMate")
root.geometry("600x600")
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

# --- RADIO BUTTON STYLE FIX ---
# Focus ring'i kaldir
style.layout('Custom.TRadiobutton', [
    ('Radiobutton.padding', {'sticky': 'nswe', 'children': [
        ('Radiobutton.indicator', {'side': 'left', 'sticky': ''}),
        ('Radiobutton.label', {'side': 'left', 'sticky': ''})
    ]})
])

# indicatorforeground: Nokta (secim) rengi -> Beyaz (#ffffff)
# indicatorbackground: Yuvarlak ic arka plan rengi -> Koyu (#2b2b2b)
style.configure("Custom.TRadiobutton", 
    background="#2b2b2b", 
    foreground="#ffffff", 
    font=("Arial", 9),
    indicatorbackground="#2b2b2b", 
    indicatorforeground="#ffffff" 
)

# Haritalamada selected oldugunda noktayi beyaz yap
style.map("Custom.TRadiobutton",
    background=[('active', '#2b2b2b'), ('!disabled', '#2b2b2b')],
    foreground=[('active', '#ffffff'), ('!disabled', '#ffffff')],
    indicatorbackground=[('active', '#2b2b2b'), ('!disabled', '#2b2b2b')], # Arkaplan hep koyu
    indicatorforeground=[('selected', '#ffffff'), ('pressed', '#ffffff'), ('active', '#ffffff')] # Nokta beyaz
)

# --- VALIDATION ---
def validate_number_input(P):
    if P == "": return True
    return P.isdigit()

vcmd = (root.register(validate_number_input), '%P')

# --- GLOBAL FOCUS CLICK HANDLER ---
def on_global_click(event):
    widget = event.widget
    if isinstance(widget, (ttk.Entry, tk.Entry, tk.Text, tk.Listbox, ttk.Button, tk.Button, tk.Scrollbar, ttk.Scrollbar, ttk.Radiobutton)):
        return
    root.focus()
    try:
        filters_list.selection_clear(0, tk.END)
    except:
        pass

root.bind("<Button-1>", on_global_click)

# ---------------- CONTROL PANEL -----------------
status_frame = ttk.LabelFrame(root, text="Control Panel", padding=10)
status_frame.pack(fill="x", padx=10, pady=10)

control_row = ttk.Frame(status_frame)
control_row.pack(fill="x")

status_label = tk.Label(control_row, text="● STOPPED", font=("Arial", 14, "bold"), 
                        fg="#ff4444", bg="#1a1a1a", padx=15, pady=6, relief="sunken")
status_label.pack(side="left", padx=(0, 20))

hotkey_frame = ttk.Frame(control_row)
hotkey_frame.pack(side="right")

ttk.Label(hotkey_frame, text="Start:", font=("Arial", 9)).pack(side="left", padx=5)
start_key_btn = ttk.Button(hotkey_frame, text=hotkey_start.upper(), width=8)
start_key_btn.pack(side="left", padx=5)

ttk.Label(hotkey_frame, text="Stop:", font=("Arial", 9)).pack(side="left", padx=5)
stop_key_btn = ttk.Button(hotkey_frame, text=hotkey_stop.upper(), width=8)
stop_key_btn.pack(side="left", padx=5)

# ---------------- SETTINGS -----------------
frame_settings = ttk.LabelFrame(root, text="Settings", padding=8)
frame_settings.pack(fill="x", padx=10, pady=8)

settings_row = ttk.Frame(frame_settings)
settings_row.pack(fill="x", padx=5, pady=5)

# Limit
ttk.Label(settings_row, text="Attempt Limit (0 = Unlimited):", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 10))

limit_var = tk.StringVar(value=str(safety_limit))

def on_limit_change(*args):
    global safety_limit
    val = limit_var.get()
    if val.isdigit():
        safety_limit = int(val)
        save_config()
    elif val == "":
        safety_limit = 0
        save_config()

def on_limit_focus_out(event):
    if limit_var.get() == "":
        limit_var.set("0")

limit_var.trace_add("write", on_limit_change)

# STYLE UPDATE: Tk.Entry kullanildi ki stil color inputlara benzesin
entry_limit = tk.Entry(settings_row, textvariable=limit_var, width=6, 
                       font=("Consolas", 12, "bold"), # Benzer font
                       justify="center",             # Ortali
                       bg="white", fg="black")       # Beyaz arkaplan, siyah yazi
# Validation manuel event ile yapilabilir veya vcmd Entry ile de calisir ama tk.Entry icin config gerekir
entry_limit.config(validate="key", validatecommand=vcmd)

entry_limit.pack(side="left", padx=5)
entry_limit.bind("<FocusOut>", on_limit_focus_out)

# --- MODE SELECTION ---
ttk.Label(settings_row, text="| Mode:", font=("Arial", 10, "bold")).pack(side="left", padx=(20, 5))

mode_var = tk.StringVar(value=search_mode)

def update_ui_for_mode():
    global search_mode
    search_mode = mode_var.get()
    save_config()
    
    if search_mode == "attribute":
        frame_filters.config(text="Attribute Filters")
        frame_color_contents.pack_forget()
        frame_attr_contents.pack(fill="both", expand=True)
    else:
        frame_filters.config(text="Color Filters")
        frame_attr_contents.pack_forget()
        frame_color_contents.pack(fill="x", pady=10)

def on_mode_change():
    update_ui_for_mode()

rb_attr = ttk.Radiobutton(settings_row, text="Attribute", variable=mode_var, value="attribute", 
                          command=on_mode_change, style="Custom.TRadiobutton")
rb_attr.pack(side="left", padx=5)

rb_color = ttk.Radiobutton(settings_row, text="Color", variable=mode_var, value="color", 
                           command=on_mode_change, style="Custom.TRadiobutton")
rb_color.pack(side="left", padx=5)

# ---------------- FILTERS CONTAINER -----------------
frame_filters = ttk.LabelFrame(root, text="Attribute Filters", padding=8)
frame_filters.pack(fill="x", padx=10, pady=8)

# --- 1. ATTRIBUTE FILTER UI ---
frame_attr_contents = ttk.Frame(frame_filters)

attr_list_frame = ttk.Frame(frame_attr_contents)
attr_list_frame.pack(fill="both", padx=5, pady=5)

filters_scrollbar = ttk.Scrollbar(attr_list_frame, orient="vertical")
filters_list = tk.Listbox(attr_list_frame, height=5, font=("Consolas", 9), bg="#1a1a1a", 
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

# Attribute Inputs
filter_input_frame = ttk.Frame(frame_attr_contents)
filter_input_frame.pack(fill="x", padx=5, pady=5)

ttk.Label(filter_input_frame, text="Value:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=2)
value_var = tk.StringVar()

# STYLE UPDATE: Value inputu da benzetildi
entry_value = tk.Entry(filter_input_frame, textvariable=value_var, width=6, 
                       font=("Consolas", 12, "bold"), 
                       justify="center",
                       bg="white", fg="black")
entry_value.config(validate="key", validatecommand=vcmd)
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

btn_frame = ttk.Frame(frame_attr_contents)
btn_frame.pack(fill="x", padx=5, pady=2)
ttk.Button(btn_frame, text="Add", command=add_filter).pack(side="left", padx=2)
ttk.Button(btn_frame, text="Delete", command=del_filter).pack(side="left", padx=2)

entry_name.bind("<Return>", lambda e: add_filter())
entry_value.bind("<Return>", lambda e: entry_name.focus())


# --- 2. COLOR FILTER UI ---
frame_color_contents = ttk.Frame(frame_filters)

color_input_frame = ttk.Frame(frame_color_contents)
color_input_frame.pack(anchor="center")

def on_color_keypress(event):
    # Overwrite behavior: Rakam basildiginda mevcut icerigi sil
    if event.char and event.char.isdigit():
        event.widget.delete(0, tk.END)
    # Harf girisini engellemek icin break
    elif event.char and not event.char.isdigit() and event.keysym not in ("BackSpace", "Delete", "Left", "Right"):
        return "break"

def on_color_keyrelease(event, key):
    widget = event.widget
    val = widget.get()
    
    digits = "".join([c for c in val if c.isdigit()])
    
    if len(digits) > 1:
        digits = digits[-1]
        
    if val != digits:
        widget.delete(0, tk.END)
        widget.insert(0, digits)
        val = digits
    
    save_val = int(val) if val else 0
    color_targets[key] = save_val
    save_config()

def on_color_focus_out(event):
    widget = event.widget
    if widget.get() == "":
        widget.insert(0, "0")

# Red Input
lbl_r = tk.Label(color_input_frame, text="Red:", bg="#2b2b2b", fg="#ff5555", font=("Arial", 10, "bold"))
lbl_r.pack(side="left", padx=(0,5))

entry_r = tk.Entry(color_input_frame, width=3, font=("Consolas", 14, "bold"),
                   bg="#550000", fg="white", insertbackground="white", justify="center")
entry_r.insert(0, str(color_targets.get("R", 0)))
entry_r.pack(side="left", padx=(0, 20))
entry_r.bind("<KeyPress>", on_color_keypress)
entry_r.bind("<KeyRelease>", lambda e: on_color_keyrelease(e, "R"))
entry_r.bind("<FocusOut>", on_color_focus_out)

# Green Input
lbl_g = tk.Label(color_input_frame, text="Green:", bg="#2b2b2b", fg="#55ff55", font=("Arial", 10, "bold"))
lbl_g.pack(side="left", padx=(0,5))

entry_g = tk.Entry(color_input_frame, width=3, font=("Consolas", 14, "bold"),
                   bg="#004400", fg="white", insertbackground="white", justify="center")
entry_g.insert(0, str(color_targets.get("G", 0)))
entry_g.pack(side="left", padx=(0, 20))
entry_g.bind("<KeyPress>", on_color_keypress)
entry_g.bind("<KeyRelease>", lambda e: on_color_keyrelease(e, "G"))
entry_g.bind("<FocusOut>", on_color_focus_out)

# Blue Input
lbl_b = tk.Label(color_input_frame, text="Blue:", bg="#2b2b2b", fg="#5555ff", font=("Arial", 10, "bold"))
lbl_b.pack(side="left", padx=(0,5))

entry_b = tk.Entry(color_input_frame, width=3, font=("Consolas", 14, "bold"),
                   bg="#000055", fg="white", insertbackground="white", justify="center")
entry_b.insert(0, str(color_targets.get("B", 0)))
entry_b.pack(side="left", padx=(0, 0))
entry_b.bind("<KeyPress>", on_color_keypress)
entry_b.bind("<KeyRelease>", lambda e: on_color_keyrelease(e, "B"))
entry_b.bind("<FocusOut>", on_color_focus_out)


# ---------------- LOG -----------------
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

# ---------------- HOTKEYS -----------------
listening_key = {"active": False, "type": None, "hook": None}

def listen_for_key(key_type):
    if listening_key["active"]:
        return
    
    listening_key["active"] = True
    listening_key["type"] = key_type
    
    original_key = hotkey_start if key_type == "start" else hotkey_stop
    
    if key_type == "start":
        start_key_btn.config(text="...", state="disabled")
    else:
        stop_key_btn.config(text="...", state="disabled")
    
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

try:
    keyboard.add_hotkey(hotkey_start, start, suppress=True)
    keyboard.add_hotkey(hotkey_stop, stop, suppress=True)
    log(f"Hotkeys registered: {hotkey_start.upper()} (Start) / {hotkey_stop.upper()} (Stop)")
except Exception as e:
    log(f"Hotkey registration error: {e}")

update_ui_for_mode()

root.mainloop()