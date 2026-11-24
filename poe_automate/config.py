"""Thread-safe configuration persistence with atomic writes and validation."""

from __future__ import annotations

import copy
import json
import os
import threading
from typing import Any, Callable, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
WEB_DIR = os.path.join(BASE_DIR, "web")

VALID_MODES = ("attribute", "color")
VALID_FILTER_LOGICS = ("OR", "AND")
VALID_MOD_SCOPES = ("explicit", "implicit", "all")
VALID_LANGUAGES = ("TR", "EN")
VALID_THEMES = ("dark", "light")

DEFAULT_CONFIG: Dict[str, Any] = {
    "filters": [],
    "filter_logic": "OR",
    "mod_scope": "explicit",
    "safety_limit": 40,
    "hotkey_start": "f2",
    "hotkey_stop": "f3",
    "search_mode": "attribute",
    "color_targets": {"R": 0, "G": 0, "B": 0, "W": 0},
    "white_as_wildcard": True,
    "last_category": "Item (General)",
    "language": "TR",
    "always_on_top": True,
    "sound_enabled": True,
    "click_delay": 0.12,
    "clipboard_delay": 0.06,
    "web_enabled": True,
    "web_port": 8765,
    "web_allow_lan": False,
    "theme": "dark",
}


def _clamp_int(val: Any, low: int, high: int, default: int) -> int:
    try:
        num = int(val)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, num))


def _clamp_float(val: Any, low: float, high: float, default: float) -> float:
    try:
        num = float(val)
    except (TypeError, ValueError):
        return default
    return round(max(low, min(high, num)), 3)


def sanitize_filter(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name", "")).strip()
    value = str(raw.get("value", "")).strip()
    if not name:
        return None
    active = bool(raw.get("active", True))
    return {"name": name, "value": value, "active": active}


def sanitize_config(raw: Any) -> Dict[str, Any]:
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if not isinstance(raw, dict):
        return cfg

    raw_filters = raw.get("filters", [])
    if isinstance(raw_filters, list):
        clean_filters: List[Dict[str, Any]] = []
        for item in raw_filters:
            sf = sanitize_filter(item)
            if sf is not None:
                clean_filters.append(sf)
        cfg["filters"] = clean_filters

    logic = str(raw.get("filter_logic", cfg["filter_logic"])).upper()
    cfg["filter_logic"] = logic if logic in VALID_FILTER_LOGICS else "OR"

    scope = str(raw.get("mod_scope", cfg["mod_scope"])).lower()
    cfg["mod_scope"] = scope if scope in VALID_MOD_SCOPES else "explicit"

    cfg["safety_limit"] = _clamp_int(raw.get("safety_limit", 40), 0, 100000, 40)

    hk_start = str(raw.get("hotkey_start", "f2")).strip().lower() or "f2"
    hk_stop = str(raw.get("hotkey_stop", "f3")).strip().lower() or "f3"
    if hk_start == hk_stop:
        hk_stop = "f3" if hk_start != "f3" else "f4"
    cfg["hotkey_start"] = hk_start
    cfg["hotkey_stop"] = hk_stop

    mode = str(raw.get("search_mode", "attribute")).lower()
    cfg["search_mode"] = mode if mode in VALID_MODES else "attribute"

    raw_colors = raw.get("color_targets", {})
    if isinstance(raw_colors, dict):
        cfg["color_targets"] = {
            "R": _clamp_int(raw_colors.get("R", 0), 0, 6, 0),
            "G": _clamp_int(raw_colors.get("G", 0), 0, 6, 0),
            "B": _clamp_int(raw_colors.get("B", 0), 0, 6, 0),
            "W": _clamp_int(raw_colors.get("W", 0), 0, 6, 0),
        }

    cfg["white_as_wildcard"] = bool(raw.get("white_as_wildcard", True))
    cfg["last_category"] = str(raw.get("last_category", cfg["last_category"])).strip()

    lang = str(raw.get("language", "TR")).upper()
    cfg["language"] = lang if lang in VALID_LANGUAGES else "TR"

    cfg["always_on_top"] = bool(raw.get("always_on_top", True))
    cfg["sound_enabled"] = bool(raw.get("sound_enabled", True))
    cfg["click_delay"] = _clamp_float(raw.get("click_delay", 0.12), 0.05, 2.0, 0.12)
    cfg["clipboard_delay"] = _clamp_float(raw.get("clipboard_delay", 0.06), 0.03, 0.5, 0.06)
    cfg["web_enabled"] = bool(raw.get("web_enabled", True))
    cfg["web_port"] = _clamp_int(raw.get("web_port", 8765), 1024, 65535, 8765)
    cfg["web_allow_lan"] = bool(raw.get("web_allow_lan", False))

    theme = str(raw.get("theme", "dark")).lower()
    cfg["theme"] = theme if theme in VALID_THEMES else "dark"
    return cfg


class ConfigManager:
    """Thread-safe configuration store with atomic disk persistence and observers."""

    def __init__(self, config_path: str = CONFIG_FILE) -> None:
        self._path = config_path
        self._lock = threading.RLock()
        self._data: Dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._save_timer: Optional[threading.Timer] = None
        self.load()

    @property
    def path(self) -> str:
        return self._path

    def load(self) -> Dict[str, Any]:
        with self._lock:
            if os.path.exists(self._path):
                try:
                    with open(self._path, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    self._data = sanitize_config(raw)
                except Exception as exc:
                    print(f"[Config] Load error ({self._path}): {exc}")
                    self._data = copy.deepcopy(DEFAULT_CONFIG)
            else:
                self._data = copy.deepcopy(DEFAULT_CONFIG)
            return copy.deepcopy(self._data)

    def save(self) -> bool:
        with self._lock:
            if self._save_timer is not None:
                self._save_timer.cancel()
                self._save_timer = None
            snapshot = copy.deepcopy(self._data)
        return self._write_atomic(snapshot)

    def save_debounced(self, delay: float = 0.25) -> None:
        with self._lock:
            if self._save_timer is not None:
                self._save_timer.cancel()
            timer = threading.Timer(delay, self.save)
            timer.daemon = True
            self._save_timer = timer
            timer.start()

    def _write_atomic(self, snapshot: Dict[str, Any]) -> bool:
        tmp_path = f"{self._path}.tmp.{threading.get_ident()}"
        try:
            parent = os.path.dirname(self._path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self._path)
            return True
        except Exception as exc:
            print(f"[Config] Save error ({self._path}): {exc}")
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            return False

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            val = self._data.get(key, default)
            return copy.deepcopy(val)

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def _notify(self) -> None:
        with self._lock:
            snap = copy.deepcopy(self._data)
            listeners = list(self._listeners)
        for cb in listeners:
            try:
                cb(snap)
            except Exception as exc:
                print(f"[Config] Listener error: {exc}")

    def update(self, patch: Dict[str, Any], immediate_save: bool = True) -> Dict[str, Any]:
        with self._lock:
            merged = copy.deepcopy(self._data)
            for key, value in patch.items():
                if key == "color_targets" and isinstance(value, dict):
                    merged_colors = dict(merged.get("color_targets", {}))
                    merged_colors.update(value)
                    merged["color_targets"] = merged_colors
                elif key in DEFAULT_CONFIG:
                    merged[key] = value
            self._data = sanitize_config(merged)
            snap = copy.deepcopy(self._data)

        if immediate_save:
            self.save()
        else:
            self.save_debounced()
        self._notify()
        return snap

    def add_filter(self, name: str, value: str = "", active: bool = True) -> Optional[Dict[str, Any]]:
        clean = sanitize_filter({"name": name, "value": value, "active": active})
        if clean is None:
            return None
        with self._lock:
            self._data["filters"].append(clean)
        self.save()
        self._notify()
        return copy.deepcopy(clean)

    def update_filter(self, index: int, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            filters = self._data["filters"]
            if index < 0 or index >= len(filters):
                return None
            merged = dict(filters[index])
            merged.update(patch)
            clean = sanitize_filter(merged)
            if clean is None:
                return None
            filters[index] = clean
            result = copy.deepcopy(clean)
        self.save()
        self._notify()
        return result

    def toggle_filter(self, index: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            filters = self._data["filters"]
            if index < 0 or index >= len(filters):
                return None
            filters[index]["active"] = not bool(filters[index].get("active", True))
            result = copy.deepcopy(filters[index])
        self.save()
        self._notify()
        return result

    def delete_filter(self, index: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            filters = self._data["filters"]
            if index < 0 or index >= len(filters):
                return None
            removed = filters.pop(index)
        self.save()
        self._notify()
        return copy.deepcopy(removed)

    def clear_filters(self) -> None:
        with self._lock:
            self._data["filters"] = []
        self.save()
        self._notify()
