"""Thread-safe Path of Exile automation engine with guaranteed key cleanup and live events."""

from __future__ import annotations

import atexit
import collections
import threading
import time
from datetime import datetime
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

from .config import ConfigManager
from .i18n import get_text
from .parser import EvaluationResult, evaluate_item

try:
    import keyboard  # type: ignore
except Exception:  # pragma: no cover
    keyboard = None

try:
    import pyautogui  # type: ignore

    pyautogui.PAUSE = 0
except Exception:  # pragma: no cover
    pyautogui = None

try:
    import pyperclip  # type: ignore
except Exception:  # pragma: no cover
    pyperclip = None

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None

try:
    import win32gui  # type: ignore
    import win32process  # type: ignore
except Exception:  # pragma: no cover
    win32gui = None
    win32process = None

try:
    import winsound  # type: ignore
except Exception:  # pragma: no cover
    winsound = None

EventCallback = Callable[[Dict[str, Any]], None]


class AutomationEngine:
    """Controls item scanning, rolling loop, hotkeys, sounds, logs, and live state sync."""

    MAX_LOG_ENTRIES = 500

    def __init__(self, config: ConfigManager) -> None:
        self.config = config
        self._lock = threading.RLock()
        self._sound_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker: Optional[threading.Thread] = None

        self._status: str = "STOPPED"  # STOPPED | RUNNING | FOUND
        self._starting: bool = False
        self._shift_held: bool = False
        self._listening_hotkey: bool = False
        self._registered_hotkeys: List[str] = []

        self._attempts: int = 0
        self._started_at: float = 0.0
        self._last_elapsed: float = 0.0
        self._last_match_summary: str = ""

        self._log_seq: int = 0
        self._logs: Deque[Dict[str, Any]] = collections.deque(maxlen=self.MAX_LOG_ENTRIES)
        self._subscribers: List[EventCallback] = []

        # Short-TTL cache for PID -> process name to avoid repeated handle opens
        self._proc_cache: Dict[int, Tuple[str, float]] = {}

        self.config.add_listener(self._on_config_changed)
        atexit.register(self.shutdown)

    # ---------------- EVENT PUB/SUB -----------------
    def subscribe(self, callback: EventCallback) -> None:
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback: EventCallback) -> None:
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def _emit(self, event_type: str, data: Any) -> None:
        with self._lock:
            subs = list(self._subscribers)
        payload = {"type": event_type, "data": data}
        for cb in subs:
            try:
                cb(payload)
            except Exception:
                pass

    def _on_config_changed(self, cfg_snapshot: Dict[str, Any]) -> None:
        self._emit("config", cfg_snapshot)

    # ---------------- LOGGING -----------------
    def log(self, text: str, level: str = "info") -> Dict[str, Any]:
        ts = datetime.now().strftime("%H:%M:%S")
        with self._lock:
            self._log_seq += 1
            entry = {
                "id": self._log_seq,
                "ts": ts,
                "level": level,
                "text": str(text),
            }
            self._logs.append(entry)
        self._emit("log", entry)
        return entry

    def get_logs(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._logs)
        if limit > 0:
            return items[-limit:]
        return items

    def clear_logs(self) -> None:
        with self._lock:
            self._logs.clear()
        self._emit("logs_cleared", {})

    # ---------------- STATE / STATS -----------------
    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._status == "RUNNING" or self._starting

    def set_listening_hotkey(self, active: bool) -> None:
        with self._lock:
            self._listening_hotkey = bool(active)

    def is_listening_hotkey(self) -> bool:
        with self._lock:
            return self._listening_hotkey

    def get_state(self) -> Dict[str, Any]:
        cfg = self.config.snapshot()
        with self._lock:
            status = self._status
            attempts = self._attempts
            if status == "RUNNING" and self._started_at > 0:
                elapsed = max(0.0, time.monotonic() - self._started_at)
            else:
                elapsed = self._last_elapsed
            rolls_per_sec = (attempts / elapsed) if elapsed > 0.25 and attempts > 0 else 0.0
            last_match = self._last_match_summary

        return {
            "status": status,
            "running": status == "RUNNING",
            "attempts": attempts,
            "safety_limit": cfg.get("safety_limit", 40),
            "elapsed_seconds": round(elapsed, 1),
            "rolls_per_sec": round(rolls_per_sec, 2),
            "last_match_summary": last_match,
            "poe_active": self.is_poe_active(),
        }

    def _broadcast_state(self) -> None:
        self._emit("state", self.get_state())

    # ---------------- PROCESS CHECK -----------------
    def is_poe_active(self) -> bool:
        if win32gui is None or win32process is None:
            return False
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid and psutil is not None:
                now = time.monotonic()
                cached = self._proc_cache.get(pid)
                if cached and (now - cached[1]) < 5.0:
                    proc_name = cached[0]
                else:
                    try:
                        proc_name = psutil.Process(pid).name().lower()
                        self._proc_cache[pid] = (proc_name, now)
                        if len(self._proc_cache) > 64:
                            self._proc_cache.clear()
                    except Exception:
                        proc_name = ""
                if proc_name:
                    return "pathofexile" in proc_name

            # Fallback for elevated (Admin) PoE windows where psutil gets AccessDenied
            title = win32gui.GetWindowText(hwnd) or ""
            return "path of exile" in title.lower()
        except Exception:
            return False

    # ---------------- SOUND (NON-BLOCKING) -----------------
    def play_sound(self, sound_type: str) -> None:
        if not self.config.get("sound_enabled", True):
            return
        if winsound is None:
            return

        def _play() -> None:
            with self._sound_lock:
                try:
                    if sound_type == "success":
                        winsound.Beep(1568, 130)
                        winsound.Beep(2093, 170)
                    elif sound_type == "error":
                        winsound.Beep(260, 280)
                except Exception:
                    pass

        threading.Thread(target=_play, daemon=True).start()

    # ---------------- INPUT / CLIPBOARD -----------------
    def _hold_shift(self) -> None:
        if pyautogui is None:
            return
        try:
            pyautogui.keyDown("shift")
            with self._lock:
                self._shift_held = True
        except Exception:
            pass

    def _release_shift(self) -> None:
        with self._lock:
            was_held = self._shift_held
            self._shift_held = False
        if not was_held or pyautogui is None:
            return
        try:
            pyautogui.keyUp("shift")
        except Exception:
            pass

    def _perform_click(self) -> None:
        if pyautogui is None:
            return
        try:
            pyautogui.click()
        except Exception as exc:
            self.log(f"Click error: {exc}", level="error")

    def read_clipboard_after_copy(self, delay: Optional[float] = None) -> str:
        if delay is None:
            delay = float(self.config.get("clipboard_delay", 0.06))
        if pyperclip is not None:
            try:
                pyperclip.copy("")
            except Exception:
                pass

        copied = False
        if pyautogui is not None:
            try:
                pyautogui.hotkey("ctrl", "c")
                copied = True
            except Exception:
                copied = False
        if not copied and keyboard is not None:
            try:
                keyboard.send("ctrl+c")
            except Exception:
                pass

        # Interruptible wait so Stop responds instantaneously
        self._stop_event.wait(max(0.03, delay))

        if pyperclip is not None:
            try:
                return pyperclip.paste() or ""
            except Exception:
                return ""
        return ""

    # ---------------- HOTKEYS -----------------
    def unregister_hotkeys(self) -> None:
        if keyboard is None:
            return
        with self._lock:
            keys = list(self._registered_hotkeys)
            self._registered_hotkeys.clear()
        for key in keys:
            try:
                keyboard.remove_hotkey(key)
            except Exception:
                pass

    def register_hotkeys(self, log_result: bool = True) -> bool:
        if keyboard is None:
            return False
        self.unregister_hotkeys()
        cfg = self.config.snapshot()
        hk_start = cfg["hotkey_start"]
        hk_stop = cfg["hotkey_stop"]
        lang = cfg["language"]
        try:
            keyboard.add_hotkey(hk_start, self.start_async, suppress=True)
            keyboard.add_hotkey(hk_stop, self.stop, suppress=True)
            with self._lock:
                self._registered_hotkeys = [hk_start, hk_stop]
            if log_result:
                self.log(get_text(lang, "log_hotkeys_reg", hk_start.upper(), hk_stop.upper()), level="system")
            return True
        except Exception as exc:
            if log_result:
                self.log(get_text(lang, "log_hotkey_reg_err", exc), level="error")
            return False

    # ---------------- TESTER (OFFLINE / WEB SIMULATOR) -----------------
    def test_item(self, raw_text: str) -> EvaluationResult:
        cfg = self.config.snapshot()
        return evaluate_item(raw_text, cfg, check_modifiable=True)

    # ---------------- START / STOP / LOOP -----------------
    def start_async(self) -> None:
        """Non-blocking entry point safe to invoke directly from global keyboard hooks."""
        threading.Thread(target=self.start, daemon=True, name="poe-start").start()

    def start(self) -> bool:
        with self._lock:
            if self._listening_hotkey or self._starting or self._status == "RUNNING":
                return False
            self._starting = True

        cfg = self.config.snapshot()
        lang = cfg["language"]

        try:
            if not self.is_poe_active():
                self.log(get_text(lang, "log_poe_not_active_start"), level="error")
                self.play_sound("error")
                return False

            # Quick config validation before scanning
            if cfg["search_mode"] == "attribute":
                active_filters = [f for f in cfg.get("filters", []) if f.get("active", True)]
                if not active_filters:
                    self.log(get_text(lang, "log_no_active_filters"), level="warning")
                    self.play_sound("error")
                    return False
            else:
                ct = cfg.get("color_targets", {})
                if sum(int(ct.get(c, 0)) for c in ("R", "G", "B", "W")) <= 0:
                    self.log(get_text(lang, "log_no_color_req"), level="warning")
                    self.play_sound("error")
                    return False

            self._stop_event.clear()
            self.log(get_text(lang, "log_scanning"), level="info")
            item_text = self.read_clipboard_after_copy(cfg.get("clipboard_delay", 0.06))
            eval_res = evaluate_item(item_text, cfg, check_modifiable=True)

            for lvl, msg in eval_res.log_entries:
                self.log(msg, level=lvl)

            if eval_res.status == "FOUND":
                self.log(get_text(lang, "log_already_match"), level="success")
                self.play_sound("success")
                with self._lock:
                    self._status = "FOUND"
                    self._last_match_summary = eval_res.summary
                self._broadcast_state()
                return False

            if eval_res.status == "EMPTY":
                self.log(get_text(lang, "log_read_fail"), level="error")
                self.play_sound("error")
                return False

            if eval_res.status in (
                "INVALID_ITEM",
                "UNMODIFIABLE",
                "NO_FILTERS",
                "NO_COLOR_REQ",
                "NO_SOCKET",
                "IMPOSSIBLE_SOCKETS",
            ):
                self.play_sound("error")
                return False

            self.log(get_text(lang, "log_start_loop"), level="system")
            with self._lock:
                self._status = "RUNNING"
                self._attempts = 0
                self._started_at = time.monotonic()
                self._last_elapsed = 0.0
                self._last_match_summary = ""
                worker = threading.Thread(
                    target=self._auto_loop,
                    args=(item_text,),
                    daemon=True,
                    name="poe-auto-loop",
                )
                self._worker = worker
            self._broadcast_state()
            worker.start()
            return True
        finally:
            with self._lock:
                self._starting = False

    def stop(self, from_found: bool = False, silent: bool = False) -> None:
        with self._lock:
            if self._listening_hotkey and not from_found:
                return
            was_running = self._status == "RUNNING" or self._starting
            if not was_running and not from_found:
                return
            self._stop_event.set()
            if self._started_at > 0:
                self._last_elapsed = max(0.0, time.monotonic() - self._started_at)
            self._status = "FOUND" if from_found else "STOPPED"

        self._release_shift()
        if not silent:
            lang = self.config.get("language", "TR")
            self.log(get_text(lang, "log_stopping"), level="system")
        self._broadcast_state()

    def _is_stop_key_pressed(self, hotkey_stop: str) -> bool:
        if keyboard is None:
            return False
        try:
            return bool(keyboard.is_pressed(hotkey_stop))
        except Exception:
            return False

    def _auto_loop(self, initial_item_text: str = "") -> None:
        attempt = 0
        prev_item_text = initial_item_text.strip()
        consecutive_same_count = 0
        consecutive_empty_count = 0
        skip_click = False
        stopped_from_found = False

        self._hold_shift()
        try:
            while not self._stop_event.is_set():
                cfg = self.config.snapshot()
                lang = cfg["language"]
                safety_limit = int(cfg["safety_limit"])
                hotkey_stop = cfg["hotkey_stop"]
                click_delay = float(cfg["click_delay"])
                clipboard_delay = float(cfg["clipboard_delay"])

                if safety_limit > 0 and attempt >= safety_limit:
                    self.log(get_text(lang, "log_limit_reached", safety_limit), level="warning")
                    break

                if self._is_stop_key_pressed(hotkey_stop):
                    self.log(get_text(lang, "log_stop_key_loop"), level="warning")
                    break

                if not self.is_poe_active():
                    self.log(get_text(lang, "log_poe_active"), level="warning")
                    break

                limit_display = "∞" if safety_limit == 0 else str(safety_limit)

                if not skip_click:
                    attempt += 1
                    with self._lock:
                        self._attempts = attempt
                    self._broadcast_state()
                    self.log(get_text(lang, "log_attempt", attempt, limit_display), level="dim")
                    self._perform_click()
                else:
                    self.log(get_text(lang, "log_retry_click", attempt), level="warning")
                    skip_click = False

                if self._stop_event.is_set():
                    break

                item_text = self.read_clipboard_after_copy(clipboard_delay)
                cleaned_text = item_text.strip()

                if self._stop_event.is_set() or self._is_stop_key_pressed(hotkey_stop):
                    self.log(get_text(lang, "log_stop_key_read"), level="warning")
                    break

                if not cleaned_text:
                    consecutive_empty_count += 1
                    self.log(get_text(lang, "log_read_retry"), level="warning")
                    skip_click = True
                    if consecutive_empty_count >= 3:
                        self.log(get_text(lang, "log_read_empty_3"), level="error")
                        self.play_sound("error")
                        break
                    self._stop_event.wait(click_delay)
                    continue

                consecutive_empty_count = 0

                if cleaned_text == prev_item_text:
                    consecutive_same_count += 1
                    if consecutive_same_count >= 3:
                        self.log(get_text(lang, "log_same_item"), level="error")
                        self.play_sound("error")
                        break
                else:
                    consecutive_same_count = 0
                    prev_item_text = cleaned_text

                eval_res = evaluate_item(cleaned_text, cfg, check_modifiable=True)
                for lvl, msg in eval_res.log_entries:
                    self.log(msg, level=lvl)

                if eval_res.status == "FOUND":
                    self.log(get_text(lang, "log_match_found"), level="success")
                    with self._lock:
                        self._last_match_summary = eval_res.summary
                    self.play_sound("success")
                    stopped_from_found = True
                    break

                if eval_res.status in (
                    "INVALID_ITEM",
                    "UNMODIFIABLE",
                    "NO_FILTERS",
                    "NO_COLOR_REQ",
                    "NO_SOCKET",
                    "IMPOSSIBLE_SOCKETS",
                ):
                    self.play_sound("error")
                    break

                self._stop_event.wait(click_delay)
        except Exception as exc:
            self.log(f"Loop error: {exc}", level="error")
            self.play_sound("error")
        finally:
            self._release_shift()
            self.stop(from_found=stopped_from_found, silent=False)

    def shutdown(self) -> None:
        self._stop_event.set()
        self._release_shift()
        self.unregister_hotkeys()
        self.config.save()
