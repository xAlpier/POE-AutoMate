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
                hotkey_start = data.get("hotkey_start", "F2")
                hotkey_stop = data.get("hotkey_stop", "F3")
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

# ---------------- SHIFT CONTROL -----------------
def hold_shift_once():
    """Use pyautogui to hold shift once (keyDown)."""
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
    log_box.insert(tk.END, text + "\n")
    log_box.see(tk.END)

# ---------------- READ CLIPBOARD -----------------
def read_clipboard_after_copy():
    """
    Sends Ctrl+C, waits briefly, returns clipboard text.
    """
    try:
        pyautogui.hotkey('ctrl', 'c')
    except Exception:
        # fallback to keyboard if pyautogui.hotkey fails
        keyboard.send('ctrl+c')
    time.sleep(0.06)  # small wait for clipboard to populate
    try:
        return pyperclip.paste() or ""
    except Exception:
        return ""

# ---------------- MATCHING LOGIC -----------------
def filter_matches_item(filt, item_text):
    """
    filt: dict with keys 'name' and 'value'
    item_text: full item text (string)
    Returns (True, reason) if matched, else (False, None)
    Behavior:
      - If filt['value'] looks numeric (digits, maybe trailing %), treat as threshold:
          search for a number immediately before the filt['name'] phrase.
          e.g. +1 to Level of all Spell Skill Gems  -> pattern finds 1 and compares >= threshold
                25% to Fire Damage over Time Multiplier -> handles % as well
      - Otherwise treat filt['value'] as substring to search case-insensitive.
    """
    name = (filt.get("name") or "").strip()
    val = (filt.get("value") or "").strip()

    if not val:
        return False, None

    # Normalize item_text
    txt = item_text

    # Check numeric-threshold form: allow forms like "25", "25%", "+25", "-1"
    m_num = re.match(r'^([+-]?\d+)%?$', val)
    if m_num and name:
        # threshold number
        thresh = int(m_num.group(1))
        # build pattern: number (with optional + or - and optional %) followed by optional whitespace and the name phrase
        # e.g. r'([+-]?\d+)%?\s*(to Level of all Spell Skill Gems)'
        pat = re.compile(r'([+-]?\d+)%?\s*' + re.escape(name), re.IGNORECASE)
        found = pat.findall(txt)
        if found:
            # found is list of captured numbers (strings)
            for numstr in found:
                try:
                    val_num = int(numstr)
                except:
                    continue
                if val_num >= thresh:
                    reason = f"threshold match: {val_num} >= {thresh} for phrase '{name}'"
                    return True, reason
            return False, None
        else:
            return False, None

    # else: plain substring match on value
    if val.lower() in txt.lower():
        reason = f"substring match '{val}'"
        return True, reason

    return False, None

# ---------------- AUTO LOOP -----------------
def auto_loop():
    global running, safety_limit

    attempt = 0
    while running and attempt < safety_limit:
        attempt += 1
        log(f"--- Attempt {attempt}/{safety_limit} ---")

        # 1) Click (shift is held by keyDown)
        try:
            pyautogui.click()  # left click at current cursor
        except Exception as e:
            log(f"Click error: {e}")

        # 2) Read clipboard (Ctrl+C)
        item_text = read_clipboard_after_copy()
        cleaned = item_text.strip()
        if not cleaned:
            log("Clipboard empty or couldn't read. Continuing...")
        else:
            # pretty-print clipboard in log (line by line)
            log("---- ITEM ----")
            lines = cleaned.splitlines()

            # implicit satırını bul
            implicit_index = None
            for i, line in enumerate(lines):
                if "(implicit)" in line:
                    implicit_index = i
                    break

            # implicit bulunduysa sadece altındaki özellikleri yaz
            if implicit_index is not None:
                for line in lines[implicit_index+1:]:
                    # Boş çizgi gibi ayırıcıları atla
                    if line.strip() == "" or "--------" in line:
                        continue
                    log(line)
            else:
                # implicit yoksa hiçbir şey yazma
                log("(No implicit found)")

            log("--------------")


            # Filter check
            matched = False
            for f in filters:
                ok, reason = filter_matches_item(f, cleaned)
                if ok:
                    log(f"Matched filter: {f.get('name','?')} -> {f.get('value')}; reason: {reason}")
                    log("===== MATCH FOUND - STOPPING =====")
                    # stop and release shift
                    root.after(0, stop)
                    matched = True
                    break
            if matched:
                return

        time.sleep(0.12)

    # reached limit or running turned false
    root.after(0, stop)

# ---------------- START / STOP -----------------
def start():
    global running
    if running:
        return
    log("Starting...")
    running = True
    led.config(bg="green")
    # hold shift once
    hold_shift_once()
    # start worker thread
    threading.Thread(target=auto_loop, daemon=True).start()

def stop():
    global running
    if not running:
        return
    running = False
    log("Stopping...")
    led.config(bg="red")
    # release shift
    release_shift_once()

# ---------------- GUI -----------------
load_config()

root = tk.Tk()
root.title("PoE Orb Tool")
root.geometry("640x700")
root.attributes("-topmost", True)

style = ttk.Style()
style.theme_use("clam")

# LED Indicator
led = tk.Label(root, text="", width=2, height=1, bg="red")
led.place(x=10, y=10)

# Safety limit
frame_limit = ttk.LabelFrame(root, text="Safety Limit")
frame_limit.pack(fill="x", padx=10, pady=8)

limit_var = tk.StringVar(value=str(safety_limit))
entry_limit = ttk.Entry(frame_limit, textvariable=limit_var, width=10)
entry_limit.pack(side="left", padx=5)

def update_limit():
    global safety_limit
    try:
        safety_limit = int(limit_var.get())
        save_config()
        messagebox.showinfo("OK", "Updated.")
    except:
        messagebox.showerror("ERR", "Invalid number")

ttk.Button(frame_limit, text="Update", command=update_limit).pack(side="left", padx=5)

# HOTKEYS
frame_key = ttk.LabelFrame(root, text="Hotkeys")
frame_key.pack(fill="x", padx=10, pady=8)

start_var = tk.StringVar(value=hotkey_start)
stop_var = tk.StringVar(value=hotkey_stop)

ttk.Label(frame_key, text="Start Key:").pack(anchor="w", padx=5)
entry_start = ttk.Entry(frame_key, textvariable=start_var)
entry_start.pack(fill="x", padx=5)

ttk.Label(frame_key, text="Stop Key:").pack(anchor="w", padx=5)
entry_stop = ttk.Entry(frame_key, textvariable=stop_var)
entry_stop.pack(fill="x", padx=5)

def update_keys():
    global hotkey_start, hotkey_stop
    try:
        try:
            keyboard.remove_hotkey(hotkey_start)
        except Exception:
            pass
        try:
            keyboard.remove_hotkey(hotkey_stop)
        except Exception:
            pass

        hotkey_start = start_var.get().strip() or "F2"
        hotkey_stop = stop_var.get().strip() or "F3"
        keyboard.add_hotkey(hotkey_start, start)
        keyboard.add_hotkey(hotkey_stop, stop)
        save_config()
        messagebox.showinfo("OK", "Keys updated.")
    except Exception as e:
        messagebox.showerror("ERR", f"Failed to update keys: {e}")

ttk.Button(frame_key, text="Save Hotkeys", command=update_keys).pack(pady=5)

# FILTERS
frame_filters = ttk.LabelFrame(root, text="Filters")
frame_filters.pack(fill="x", padx=10, pady=8)

filters_list = tk.Listbox(frame_filters, height=6)
filters_list.pack(fill="both", padx=5, pady=5)

for f in filters:
    filters_list.insert(tk.END, f"{f.get('name','')} → {f.get('value','')}")

name_var = tk.StringVar()
value_var = tk.StringVar()

ttk.Label(frame_filters, text="Name:").pack(anchor="w", padx=5)
entry_name = ttk.Entry(frame_filters, textvariable=name_var)
entry_name.pack(fill="x", padx=5)

ttk.Label(frame_filters, text="Value (substring to search or numeric threshold):").pack(anchor="w", padx=5)
entry_value = ttk.Entry(frame_filters, textvariable=value_var)
entry_value.pack(fill="x", padx=5)

def add_filter():
    name = name_var.get().strip()
    value = value_var.get().strip()
    if not name or not value:
        return
    f = {"name": name, "value": value}
    filters.append(f)
    filters_list.insert(tk.END, f"{name} → {value}")
    save_config()
    name_var.set("")
    value_var.set("")

def del_filter():
    sel = filters_list.curselection()
    if not sel:
        return
    idx = sel[0]
    filters.pop(idx)
    filters_list.delete(idx)
    save_config()

ttk.Button(frame_filters, text="Add Filter", command=add_filter).pack(side="left", padx=5, pady=4)
ttk.Button(frame_filters, text="Delete Selected", command=del_filter).pack(side="left", padx=5, pady=4)

# LOG
frame_log = ttk.LabelFrame(root, text="Log")
frame_log.pack(fill="both", expand=True, padx=10, pady=8)

log_box = tk.Text(frame_log, height=18, wrap="word")
log_box.pack(fill="both", expand=True, padx=5, pady=5)

# Controls
frame_ctrl = ttk.LabelFrame(root, text="Controls")
frame_ctrl.pack(fill="x", padx=10, pady=8)

ttk.Button(frame_ctrl, text="Start", command=start).pack(side="left", padx=10, pady=8)
ttk.Button(frame_ctrl, text="Stop", command=stop).pack(side="left", padx=10, pady=8)

# Register initial hotkeys
try:
    keyboard.add_hotkey(hotkey_start, start)
    keyboard.add_hotkey(hotkey_stop, stop)
except Exception:
    pass

root.mainloop()
