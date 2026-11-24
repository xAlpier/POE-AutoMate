"""Responsive, thread-safe Tkinter Desktop GUI synchronized with the Web & Mobile UI."""

from __future__ import annotations

import ctypes
import queue
import sys
import tkinter as tk
from tkinter import ttk
import webbrowser
from typing import Any, Dict, List, Optional

from . import __version__
from .automation import AutomationEngine
from .config import ConfigManager
from .i18n import get_text
from .library import ALL_CATEGORIES_KEY, LibraryManager
from .web_server import WebCompanionServer

try:
    import keyboard  # type: ignore
except Exception:  # pragma: no cover
    keyboard = None


PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#1e222a",
        "surface": "#252a34",
        "input_bg": "#151820",
        "input_fg": "#e8eef7",
        "fg": "#e8eef7",
        "muted": "#93a2b8",
        "accent": "#38bdf8",
        "list_bg": "#161a22",
        "list_sel": "#334155",
        "log_bg": "#101319",
        "status_bg": "#12151c",
        "active_fg": "#4ade80",
        "passive_fg": "#64748b",
    },
    "light": {
        "bg": "#f1f5f9",
        "surface": "#ffffff",
        "input_bg": "#ffffff",
        "input_fg": "#0f172a",
        "fg": "#0f172a",
        "muted": "#475569",
        "accent": "#0284c7",
        "list_bg": "#ffffff",
        "list_sel": "#bae6fd",
        "log_bg": "#0f172a",
        "status_bg": "#e2e8f0",
        "active_fg": "#15803d",
        "passive_fg": "#94a3b8",
    },
}


def _enable_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class AutoMateGUI:
    """Main desktop application window for PoE AutoMate."""

    MAX_LOG_LINES = 600
    NORMAL_GEOMETRY = "980x740"
    MINIMAL_GEOMETRY = "520x320"

    def __init__(
        self,
        config: ConfigManager,
        library: LibraryManager,
        engine: AutomationEngine,
        web_server: Optional[WebCompanionServer] = None,
    ) -> None:
        self.config = config
        self.library = library
        self.engine = engine
        self.web_server = web_server

        _enable_windows_dpi_awareness()

        self.root = tk.Tk()
        self.root.title(f"PoE AutoMate v{__version__}")
        self.root.geometry(self.NORMAL_GEOMETRY)
        self.root.minsize(760, 560)

        self._event_queue: queue.Queue[Dict[str, Any]] = queue.Queue(maxsize=1000)
        self._syncing_ui: bool = False
        self._current_theme: str = ""
        self._is_minimal_mode: bool = False
        self._limit_log_timer: Optional[str] = None
        self._search_timer: Optional[str] = None
        self._poll_job: Optional[str] = None
        self._last_logged_limit: int = int(self.config.get("safety_limit", 40))

        self._settings_win: Optional[tk.Toplevel] = None
        self._listening: Dict[str, Any] = {"active": False, "type": None, "hook": None, "btn": None}

        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self._build_ui()
        self._apply_theme(self.config.get("theme", "dark"))
        self._sync_from_config(self.config.snapshot())
        self._load_initial_category()

        # Subscribe to engine events (logs, state, config changes from Web UI)
        self.engine.subscribe(self._enqueue_event)

        # Replay any startup logs already recorded (e.g. web server URL)
        for entry in self.engine.get_logs(100):
            self._append_log_lines([entry])

        # Register hotkeys & welcome log
        cfg = self.config.snapshot()
        self.engine.register_hotkeys(log_result=False)
        self.engine.log(
            get_text(cfg["language"], "log_welcome", cfg["hotkey_start"].upper(), cfg["hotkey_stop"].upper()),
            level="system",
        )

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_event_drain()

    # ---------------- HELPER: I18N -----------------
    def _lang(self) -> str:
        return str(self.config.get("language", "TR")).upper()

    def _t(self, key: str, *args: Any) -> str:
        return get_text(self._lang(), key, *args)

    # ---------------- EVENT QUEUE (THREAD-SAFE) -----------------
    def _enqueue_event(self, event: Dict[str, Any]) -> None:
        try:
            self._event_queue.put_nowait(event)
        except queue.Full:
            try:
                self._event_queue.get_nowait()
                self._event_queue.put_nowait(event)
            except Exception:
                pass

    def _schedule_event_drain(self) -> None:
        self._poll_job = self.root.after(50, self._drain_events)

    def _drain_events(self) -> None:
        log_batch: List[Dict[str, Any]] = []
        latest_state: Optional[Dict[str, Any]] = None
        latest_config: Optional[Dict[str, Any]] = None
        clear_logs = False

        for _ in range(150):
            try:
                ev = self._event_queue.get_nowait()
            except queue.Empty:
                break
            ev_type = ev.get("type")
            if ev_type == "log":
                log_batch.append(ev["data"])
            elif ev_type == "logs_cleared":
                log_batch.clear()
                clear_logs = True
            elif ev_type == "state":
                latest_state = ev["data"]
            elif ev_type == "config":
                latest_config = ev["data"]

        if clear_logs:
            self._clear_log_widget()
        if log_batch:
            self._append_log_lines(log_batch)
        if latest_config is not None:
            self._sync_from_config(latest_config)
        if latest_state is not None:
            self._apply_engine_state(latest_state)

        self._schedule_event_drain()

    # ---------------- THEME -----------------
    def _apply_theme(self, theme_name: str) -> None:
        p = PALETTES.get(theme_name, PALETTES["dark"])
        self.root.configure(bg=p["bg"])

        self.style.configure("TFrame", background=p["bg"])
        self.style.configure("TLabelframe", background=p["bg"], foreground=p["fg"])
        self.style.configure("TLabelframe.Label", background=p["bg"], foreground=p["accent"], font=("Segoe UI", 9, "bold"))
        self.style.configure("TLabel", background=p["bg"], foreground=p["fg"], font=("Segoe UI", 9))
        self.style.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"], font=("Segoe UI", 8))
        self.style.configure("TButton", padding=(8, 4), font=("Segoe UI", 9))
        self.style.configure("TCheckbutton", background=p["bg"], foreground=p["fg"], font=("Segoe UI", 9))
        self.style.map("TCheckbutton", background=[("active", p["bg"])], foreground=[("active", p["fg"])])
        self.style.configure("Custom.TRadiobutton", background=p["bg"], foreground=p["fg"], font=("Segoe UI", 9))
        self.style.map("Custom.TRadiobutton", background=[("active", p["bg"])], foreground=[("active", p["fg"])])

        self.status_label.configure(bg=p["status_bg"])
        self.stats_label.configure(bg=p["bg"], fg=p["muted"])
        self.lib_listbox.configure(bg=p["list_bg"], fg=p["fg"], selectbackground=p["list_sel"], selectforeground=p["fg"])
        self.filters_list.configure(bg=p["list_bg"], selectbackground=p["list_sel"])
        self.log_box.configure(bg=p["log_bg"])

        for entry in (self.entry_limit, self.entry_value, self.entry_name):
            entry.configure(bg=p["input_bg"], fg=p["input_fg"], insertbackground=p["input_fg"])

        for lbl in self.color_labels.values():
            lbl.configure(bg=p["bg"])

        self._refresh_filters_ui()

    # ---------------- UI CONSTRUCTION -----------------
    def _build_ui(self) -> None:
        self.root.bind("<Button-1>", self._on_global_click)

        vcmd_num = (self.root.register(lambda P: P.isdigit() or P == ""), "%P")
        vcmd_val = (
            self.root.register(lambda P: all(c.isdigit() or c in ",.- " for c in P)),
            "%P",
        )
        vcmd_single = (self.root.register(lambda P: P == "" or (P.isdigit() and len(P) <= 1 and int(P) <= 6)), "%P")

        # --- TOP CONTROL PANEL ---
        self.status_frame = ttk.LabelFrame(self.root, text="Control Panel", padding=8)
        self.status_frame.pack(fill="x", padx=10, pady=(8, 4))

        self.control_row = ttk.Frame(self.status_frame)
        self.control_row.pack(fill="x")

        status_col = ttk.Frame(self.control_row)
        status_col.pack(side="left", padx=(0, 12))

        self.status_label = tk.Label(
            status_col,
            text="● DURDU",
            font=("Segoe UI", 12, "bold"),
            fg="#ef4444",
            bg="#12151c",
            padx=12,
            pady=4,
            relief="sunken",
        )
        self.status_label.pack(side="top", anchor="w")

        self.stats_label = tk.Label(
            status_col,
            text="0 / 40",
            font=("Consolas", 8),
            fg="#93a2b8",
            bg="#1e222a",
        )
        self.stats_label.pack(side="top", anchor="w", pady=(2, 0))

        # Collapsible middle controls (hidden in Minimal Mode)
        self.collapsible_controls = ttk.Frame(self.control_row)
        self.collapsible_controls.pack(side="left", fill="x", expand=True, padx=(0, 6))

        grp_limit = ttk.Frame(self.collapsible_controls)
        grp_limit.pack(side="left")
        self.lbl_max_tries = ttk.Label(grp_limit, text="Max Tries:")
        self.lbl_max_tries.pack(side="left", padx=(0, 4))

        self.limit_var = tk.StringVar(value=str(self.config.get("safety_limit", 40)))
        self.limit_var.trace_add("write", self._on_limit_change)
        self.entry_limit = tk.Entry(
            grp_limit,
            textvariable=self.limit_var,
            width=6,
            font=("Consolas", 10, "bold"),
            justify="center",
            validate="key",
            validatecommand=vcmd_num,
        )
        self.entry_limit.bind("<FocusOut>", lambda e: self.limit_var.set("0") if self.limit_var.get() == "" else None)
        self.entry_limit.bind("<FocusIn>", lambda e: e.widget.after(10, lambda: e.widget.select_range(0, tk.END)))
        self.entry_limit.pack(side="left")

        ttk.Separator(self.collapsible_controls, orient="vertical").pack(side="left", fill="y", padx=10, pady=2)

        grp_mode = ttk.Frame(self.collapsible_controls)
        grp_mode.pack(side="left")
        self.lbl_mode = ttk.Label(grp_mode, text="Mode:")
        self.lbl_mode.pack(side="left", padx=(0, 4))
        self.mode_var = tk.StringVar(value=self.config.get("search_mode", "attribute"))
        self.rb_attr = ttk.Radiobutton(
            grp_mode, text="Modifiers", variable=self.mode_var, value="attribute",
            command=self._on_mode_radio, style="Custom.TRadiobutton"
        )
        self.rb_attr.pack(side="left", padx=2)
        self.rb_color = ttk.Radiobutton(
            grp_mode, text="Socket Colors", variable=self.mode_var, value="color",
            command=self._on_mode_radio, style="Custom.TRadiobutton"
        )
        self.rb_color.pack(side="left", padx=2)

        # Right-side action buttons
        self.btn_minimal = ttk.Button(
            self.control_row, text="Minimal Mod", command=self.toggle_minimal_mode, width=12, takefocus=False
        )
        self.btn_minimal.pack(side="right", padx=(4, 0))

        self.btn_settings = ttk.Button(
            self.control_row, text="⚙ Ayarlar", command=self.open_settings_window, width=10, takefocus=False
        )
        self.btn_settings.pack(side="right", padx=4)

        self.btn_web = ttk.Button(
            self.control_row, text="🌐 Web", command=self._open_web_browser, width=8, takefocus=False
        )
        self.btn_web.pack(side="right", padx=4)

        self.lang_frame = ttk.Frame(self.control_row)
        self.lang_frame.pack(side="right", padx=4)
        self.lbl_lang = ttk.Label(self.lang_frame, text="Dil:")
        self.lbl_lang.pack(side="left", padx=(0, 3))
        self.lang_var = tk.StringVar(value=self._lang())
        self.lang_combo = ttk.Combobox(
            self.lang_frame, textvariable=self.lang_var, state="readonly", values=["TR", "EN"], width=4
        )
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_lang_selected)
        self.lang_combo.pack(side="left")

        # --- MAIN CONTENT (FILTERS / COLORS) ---
        self.frame_filters = ttk.LabelFrame(self.root, text="Mod Filters & Library", padding=6)
        self.frame_filters.pack(fill="both", expand=True, padx=10, pady=4)

        # 1. Attribute & Library container
        self.frame_attr_contents = ttk.Frame(self.frame_filters)

        # Left column: Library
        self.library_frame = ttk.LabelFrame(self.frame_attr_contents, text="Database / Library", padding=6)
        self.library_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        lib_top = ttk.Frame(self.library_frame)
        lib_top.pack(fill="x", pady=(0, 4))
        self.lbl_type = ttk.Label(lib_top, text="Type:")
        self.lbl_type.pack(side="left")
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            lib_top, textvariable=self.category_var, state="readonly", values=self.library.get_categories()
        )
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_selected)
        self.category_combo.pack(side="left", fill="x", expand=True, padx=6)

        self.lbl_lib_count = ttk.Label(lib_top, text="0", style="Muted.TLabel")
        self.lbl_lib_count.pack(side="right")

        lib_list_wrap = ttk.Frame(self.library_frame)
        lib_list_wrap.pack(fill="both", expand=True, pady=(0, 4))
        lib_sb = ttk.Scrollbar(lib_list_wrap, orient="vertical")
        self.lib_listbox = tk.Listbox(
            lib_list_wrap, font=("Consolas", 9), activestyle="none", yscrollcommand=lib_sb.set
        )
        lib_sb.config(command=self.lib_listbox.yview)
        self.lib_listbox.pack(side="left", fill="both", expand=True)
        lib_sb.pack(side="right", fill="y")
        self.lib_listbox.bind("<Double-Button-1>", self._on_lib_double_click)

        self.lbl_search = ttk.Label(self.library_frame, text="Search in Library:")
        self.lbl_search.pack(anchor="w")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_typed)
        self.search_entry = ttk.Entry(self.library_frame, textvariable=self.search_var)
        self.search_entry.pack(fill="x", pady=(2, 0))

        # Right column: Active Filters
        self.active_filter_frame = ttk.LabelFrame(self.frame_attr_contents, text="Active Filters", padding=6)
        self.active_filter_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Logic & Scope bar
        af_opts = ttk.Frame(self.active_filter_frame)
        af_opts.pack(fill="x", pady=(0, 4))

        self.lbl_logic = ttk.Label(af_opts, text="Match:")
        self.lbl_logic.pack(side="left", padx=(0, 4))
        self.logic_var = tk.StringVar(value=self.config.get("filter_logic", "OR"))
        self.logic_combo = ttk.Combobox(
            af_opts, textvariable=self.logic_var, state="readonly", values=["OR", "AND"], width=6
        )
        self.logic_combo.bind("<<ComboboxSelected>>", self._on_logic_or_scope_changed)
        self.logic_combo.pack(side="left", padx=(0, 10))

        self.lbl_scope = ttk.Label(af_opts, text="Scope:")
        self.lbl_scope.pack(side="left", padx=(0, 4))
        self.scope_var = tk.StringVar(value=self.config.get("mod_scope", "explicit"))
        self.scope_combo = ttk.Combobox(
            af_opts, textvariable=self.scope_var, state="readonly", values=["explicit", "implicit", "all"], width=10
        )
        self.scope_combo.bind("<<ComboboxSelected>>", self._on_logic_or_scope_changed)
        self.scope_combo.pack(side="left")

        af_list_wrap = ttk.Frame(self.active_filter_frame)
        af_list_wrap.pack(fill="both", expand=True)
        af_sb = ttk.Scrollbar(af_list_wrap, orient="vertical")
        self.filters_list = tk.Listbox(
            af_list_wrap, font=("Consolas", 9), activestyle="none", yscrollcommand=af_sb.set
        )
        af_sb.config(command=self.filters_list.yview)
        self.filters_list.pack(side="left", fill="both", expand=True)
        af_sb.pack(side="right", fill="y")
        self.filters_list.bind("<Double-Button-1>", self._on_filter_toggle)
        self.filters_list.bind("<Button-3>", self._on_filter_right_click)

        # Edit controls
        edit_frame = ttk.Frame(self.active_filter_frame)
        edit_frame.pack(fill="x", pady=(6, 4))

        hdr_row = ttk.Frame(edit_frame)
        hdr_row.pack(fill="x")
        self.lbl_header_value = ttk.Label(hdr_row, text="Value (Min)", width=15)
        self.lbl_header_value.pack(side="left")
        self.lbl_header_name = ttk.Label(hdr_row, text="Modifier Name")
        self.lbl_header_name.pack(side="left", padx=6)

        inp_row = ttk.Frame(edit_frame)
        inp_row.pack(fill="x", pady=(2, 0))
        self.value_var = tk.StringVar()
        self.entry_value = tk.Entry(
            inp_row,
            textvariable=self.value_var,
            width=14,
            font=("Consolas", 10, "bold"),
            justify="center",
            validate="key",
            validatecommand=vcmd_val,
        )
        self.entry_value.pack(side="left")
        self.entry_value.bind("<Button-3>", lambda e: e.widget.delete(0, tk.END))
        self.entry_value.bind("<Return>", self._add_filter)

        self.name_var = tk.StringVar()
        self.entry_name = tk.Entry(inp_row, textvariable=self.name_var, font=("Consolas", 10))
        self.entry_name.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.entry_name.bind("<Button-3>", lambda e: e.widget.delete(0, tk.END))
        self.entry_name.bind("<Return>", lambda e: self.entry_value.focus())

        btn_row = ttk.Frame(self.active_filter_frame)
        btn_row.pack(fill="x", pady=(2, 0))
        self.btn_add = ttk.Button(btn_row, text="Add Filter", command=self._add_filter, takefocus=False)
        self.btn_add.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.btn_del = ttk.Button(btn_row, text="Delete Selected", command=self._del_filter, takefocus=False)
        self.btn_del.pack(side="left", fill="x", expand=True, padx=(3, 0))

        # 2. Socket Color container
        self.frame_color_contents = ttk.Frame(self.frame_filters)
        color_row = ttk.Frame(self.frame_color_contents)
        color_row.pack(anchor="center", pady=(6, 8))

        self.color_labels: Dict[str, tk.Label] = {}
        self.color_entries: Dict[str, tk.Entry] = {}

        color_specs = [
            ("R", "#991b1b", "#f87171"),
            ("G", "#166534", "#4ade80"),
            ("B", "#1e40af", "#60a5fa"),
            ("W", "#475569", "#f8fafc"),
        ]
        for key, bg_hex, fg_hex in color_specs:
            box = ttk.Frame(color_row)
            box.pack(side="left", padx=10)
            lbl = tk.Label(box, text=key, fg=fg_hex, bg="#1e222a", font=("Segoe UI", 11, "bold"))
            lbl.pack(side="left")
            self.color_labels[key] = lbl

            ent = tk.Entry(
                box,
                width=2,
                font=("Consolas", 14, "bold"),
                bg=bg_hex,
                fg="white",
                insertbackground="white",
                justify="center",
                validate="key",
                validatecommand=vcmd_single,
            )
            ent.pack(side="left", padx=5)
            ent.bind("<KeyPress>", self._on_color_keypress_overwrite)
            ent.bind("<KeyRelease>", lambda ev, k=key: self._on_color_release(k))
            self.color_entries[key] = ent

        color_extra = ttk.Frame(self.frame_color_contents)
        color_extra.pack(anchor="center", pady=(0, 4))
        self.white_wildcard_var = tk.BooleanVar(value=bool(self.config.get("white_as_wildcard", True)))
        self.chk_white_wildcard = ttk.Checkbutton(
            color_extra,
            text="White wildcard",
            variable=self.white_wildcard_var,
            command=self._on_white_wildcard_toggle,
        )
        self.chk_white_wildcard.pack(side="left", padx=(0, 14))
        self.lbl_total_sockets = ttk.Label(color_extra, text="Total: 0", style="Muted.TLabel")
        self.lbl_total_sockets.pack(side="left")

        # --- SYSTEM LOG AREA ---
        self.frame_log = ttk.LabelFrame(self.root, text="System Log", padding=6)
        self.frame_log.pack(fill="x", padx=10, pady=(4, 10))

        log_top = ttk.Frame(self.frame_log)
        log_top.pack(fill="x", pady=(0, 3))
        self.lbl_web_status = ttk.Label(log_top, text="", style="Muted.TLabel")
        self.lbl_web_status.pack(side="left")
        self.btn_clear_log = ttk.Button(
            log_top, text="Temizle", command=self.engine.clear_logs, width=9, takefocus=False
        )
        self.btn_clear_log.pack(side="right")

        log_wrap = ttk.Frame(self.frame_log)
        log_wrap.pack(fill="both", expand=True)
        log_sb = ttk.Scrollbar(log_wrap, orient="vertical")
        self.log_box = tk.Text(
            log_wrap,
            height=11,
            font=("Consolas", 8),
            bg="#101319",
            fg="#cbd5e1",
            state="disabled",
            wrap="word",
            yscrollcommand=log_sb.set,
        )
        log_sb.config(command=self.log_box.yview)
        self.log_box.pack(side="left", fill="both", expand=True)
        log_sb.pack(side="right", fill="y")
        self.log_box.bind("<Button-3>", lambda e: self.engine.clear_logs())

        # Color tags for structured logs
        self.log_box.tag_configure("ts", foreground="#64748b")
        self.log_box.tag_configure("info", foreground="#e2e8f0")
        self.log_box.tag_configure("success", foreground="#4ade80", font=("Consolas", 8, "bold"))
        self.log_box.tag_configure("error", foreground="#f87171", font=("Consolas", 8, "bold"))
        self.log_box.tag_configure("warning", foreground="#fbbf24")
        self.log_box.tag_configure("system", foreground="#38bdf8")
        self.log_box.tag_configure("mod", foreground="#c4b5fd")
        self.log_box.tag_configure("dim", foreground="#94a3b8")

    # ---------------- LOG WIDGET HELPERS -----------------
    def _clear_log_widget(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.configure(state="disabled")

    def _append_log_lines(self, entries: List[Dict[str, Any]]) -> None:
        if not entries:
            return
        self.log_box.configure(state="normal")
        for entry in entries:
            ts = entry.get("ts", "")
            lvl = entry.get("level", "info")
            txt = entry.get("text", "")
            if ts:
                self.log_box.insert(tk.END, f"[{ts}] ", "ts")
            self.log_box.insert(tk.END, txt + "\n", lvl)

        # Keep bounded line count to prevent unbounded memory/UI slowdown
        total_lines = int(self.log_box.index("end-1c").split(".")[0])
        if total_lines > self.MAX_LOG_LINES:
            excess = total_lines - self.MAX_LOG_LINES
            self.log_box.delete("1.0", f"{excess + 1}.0")

        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")

    # ---------------- CONFIG & STATE SYNC -----------------
    def _sync_from_config(self, cfg: Dict[str, Any]) -> None:
        self._syncing_ui = True
        try:
            self.root.attributes("-topmost", bool(cfg.get("always_on_top", True)))
            if self._settings_win is not None and self._settings_win.winfo_exists():
                self._settings_win.attributes("-topmost", bool(cfg.get("always_on_top", True)))

            if self.root.focus_get() != self.entry_limit:
                self.limit_var.set(str(cfg.get("safety_limit", 40)))

            self.mode_var.set(cfg.get("search_mode", "attribute"))
            self.lang_var.set(cfg.get("language", "TR"))
            self.logic_var.set(cfg.get("filter_logic", "OR"))
            self.scope_var.set(cfg.get("mod_scope", "explicit"))
            self.white_wildcard_var.set(bool(cfg.get("white_as_wildcard", True)))

            ct = cfg.get("color_targets", {"R": 0, "G": 0, "B": 0, "W": 0})
            for k, ent in self.color_entries.items():
                if self.root.focus_get() != ent:
                    ent.delete(0, tk.END)
                    ent.insert(0, str(ct.get(k, 0)))

            new_theme = cfg.get("theme", "dark")
            if new_theme != self._current_theme:
                self._current_theme = new_theme
                self._apply_theme(new_theme)
            self._update_mode_layout()
            self._update_ui_language()
            self._refresh_filters_ui()
            self._update_web_status_label()
        finally:
            self._syncing_ui = False

    def _apply_engine_state(self, st: Dict[str, Any]) -> None:
        status = st.get("status", "STOPPED")
        if status == "RUNNING":
            self.status_label.configure(text=self._t("status_running"), fg="#4ade80")
        elif status == "FOUND":
            self.status_label.configure(text=self._t("status_found"), fg="#fbbf24")
        else:
            self.status_label.configure(text=self._t("status_stopped"), fg="#ef4444")

        lim = "∞" if st.get("safety_limit", 0) == 0 else str(st.get("safety_limit", 0))
        att = st.get("attempts", 0)
        rps = st.get("rolls_per_sec", 0.0)
        stats_str = f"{self._t('stats_attempts', att, lim)}"
        if rps > 0:
            stats_str += f"  ({self._t('stats_speed', rps)})"
        self.stats_label.configure(text=stats_str)

    def _update_web_status_label(self) -> None:
        if self.web_server and self.web_server.is_running:
            urls = self.web_server.get_urls()
            txt = f"🌐 {urls['local']}"
            if urls.get("mobile"):
                txt += f"  |  📱 {urls['mobile']}"
            self.lbl_web_status.configure(text=txt)
        else:
            self.lbl_web_status.configure(text="")

    def _update_mode_layout(self) -> None:
        if self._is_minimal_mode:
            return
        mode = self.config.get("search_mode", "attribute")
        if mode == "attribute":
            self.frame_filters.configure(text=self._t("attr_filters_library"))
            self.frame_color_contents.pack_forget()
            self.frame_attr_contents.pack(fill="both", expand=True)
            self.frame_filters.pack_configure(fill="both", expand=True)
            self.frame_log.pack_configure(fill="x", expand=False)
        else:
            self.frame_filters.configure(text=self._t("color_filters"))
            self.frame_attr_contents.pack_forget()
            self.frame_color_contents.pack(fill="x", pady=8)
            self.frame_filters.pack_configure(fill="x", expand=False)
            self.frame_log.pack_configure(fill="both", expand=True)

    def _update_ui_language(self) -> None:
        self.root.title(self._t("app_title"))
        self.status_frame.configure(text=self._t("control_panel"))
        self.lbl_max_tries.configure(text=self._t("max_tries"))
        self.lbl_mode.configure(text=self._t("mode"))
        self.rb_attr.configure(text=self._t("attribute"))
        self.rb_color.configure(text=self._t("color"))
        self.btn_settings.configure(text=self._t("btn_settings"))
        self.btn_web.configure(text=self._t("btn_web"))
        self.btn_minimal.configure(text=self._t("btn_normal" if self._is_minimal_mode else "btn_minimal"))
        self.lbl_lang.configure(text=self._t("lang"))

        if self.config.get("search_mode", "attribute") == "attribute":
            self.frame_filters.configure(text=self._t("attr_filters_library"))
        else:
            self.frame_filters.configure(text=self._t("color_filters"))

        self.library_frame.configure(text=self._t("database_library"))
        self.lbl_type.configure(text=self._t("type"))
        self.lbl_search.configure(text=self._t("search_lib"))
        self.active_filter_frame.configure(text=self._t("active_filters"))
        self.lbl_logic.configure(text=self._t("filter_logic"))
        self.lbl_scope.configure(text=self._t("mod_scope"))
        self.lbl_header_value.configure(text=self._t("value_min"))
        self.lbl_header_name.configure(text=self._t("modifier_name"))
        self.btn_add.configure(text=self._t("add_filter"))
        self.btn_del.configure(text=self._t("delete_selected"))

        self.frame_log.configure(text=self._t("system_log"))
        self.btn_clear_log.configure(text=self._t("clear_log"))

        self.color_labels["R"].configure(text=self._t("red"))
        self.color_labels["G"].configure(text=self._t("green"))
        self.color_labels["B"].configure(text=self._t("blue"))
        self.color_labels["W"].configure(text=self._t("white"))
        self.chk_white_wildcard.configure(text=self._t("white_wildcard"))

        ct = self.config.get("color_targets", {})
        total_req = sum(int(ct.get(k, 0)) for k in ("R", "G", "B", "W"))
        self.lbl_total_sockets.configure(text=self._t("total_sockets_req", total_req))

        self._apply_engine_state(self.engine.get_state())

    # ---------------- LIBRARY & FILTERS -----------------
    def _load_initial_category(self) -> None:
        cats = self.library.get_categories()
        last = self.config.get("last_category", "")
        if last in cats:
            self.category_var.set(last)
        elif cats:
            self.category_var.set(cats[0])
        self._populate_library_list()

    def _populate_library_list(self) -> None:
        cat = self.category_var.get() or ALL_CATEGORIES_KEY
        query = self.search_var.get()
        items, total = self.library.search(cat, query)
        self.lib_listbox.delete(0, tk.END)
        if items:
            # Batch single Tcl call — drastically faster than inserting item by item
            self.lib_listbox.insert(tk.END, *items)
        self.lbl_lib_count.configure(text=self._t("results_count", total))

    def _on_category_selected(self, event: Any) -> None:
        cat = self.category_var.get()
        self.config.update({"last_category": cat}, immediate_save=True)
        self.search_var.set("")
        self._populate_library_list()
        if event is not None:
            event.widget.selection_clear()
        self.root.focus()

    def _on_search_typed(self, *args: Any) -> None:
        if self._search_timer is not None:
            self.root.after_cancel(self._search_timer)
        self._search_timer = self.root.after(90, self._populate_library_list)

    def _on_lib_double_click(self, event: Any) -> None:
        sel = self.lib_listbox.curselection()
        if not sel:
            return
        text = self.lib_listbox.get(sel[0])
        self.name_var.set(text)
        self.value_var.set("")
        self.entry_value.focus()

    def _refresh_filters_ui(self) -> None:
        filters = self.config.get("filters", [])
        p = PALETTES.get(self.config.get("theme", "dark"), PALETTES["dark"])
        self.filters_list.delete(0, tk.END)
        p_tag = self._t("passive_tag")

        for i, f in enumerate(filters):
            val = f.get("value", "")
            val_disp = val if val else "ANY"
            display = f"{val_disp} → {f.get('name', '')}"
            if f.get("active", True):
                self.filters_list.insert(tk.END, display)
                self.filters_list.itemconfigure(i, fg=p["active_fg"])
            else:
                self.filters_list.insert(tk.END, f"{p_tag} {display}")
                self.filters_list.itemconfigure(i, fg=p["passive_fg"])

    def _add_filter(self, event: Any = None) -> None:
        name = self.name_var.get().strip()
        value = self.value_var.get().strip()
        if not name:
            return
        self.config.add_filter(name=name, value=value, active=True)
        self.name_var.set("")
        self.value_var.set("")
        self.entry_value.focus()

    def _del_filter(self) -> None:
        sel = self.filters_list.curselection()
        if not sel:
            return
        self.config.delete_filter(sel[0])

    def _on_filter_toggle(self, event: Any) -> None:
        sel = self.filters_list.curselection()
        if not sel:
            return
        toggled = self.config.toggle_filter(sel[0])
        if toggled:
            st = self._t("status_active" if toggled["active"] else "status_passive")
            self.engine.log(self._t("log_filter_toggled", toggled["name"], st), level="info")

    def _on_filter_right_click(self, event: Any) -> None:
        idx = self.filters_list.nearest(event.y)
        filters = self.config.get("filters", [])
        if idx < 0 or idx >= len(filters):
            return
        f = filters[idx]
        self.name_var.set(f.get("name", ""))
        self.value_var.set(f.get("value", ""))
        self.config.delete_filter(idx)
        self.entry_value.focus()

    # ---------------- CONTROL HANDLERS -----------------
    def _on_limit_change(self, *args: Any) -> None:
        if self._syncing_ui:
            return
        val = self.limit_var.get()
        num = int(val) if val.isdigit() else 0
        self.config.update({"safety_limit": num}, immediate_save=False)

        if self._limit_log_timer is not None:
            self.root.after_cancel(self._limit_log_timer)
        self._limit_log_timer = self.root.after(750, self._log_limit_change)

    def _log_limit_change(self) -> None:
        self._limit_log_timer = None
        current_val = int(self.config.get("safety_limit", 0))
        if current_val != self._last_logged_limit:
            if current_val == 0:
                self.engine.log(self._t("log_limit_unlimited"), level="info")
            else:
                self.engine.log(self._t("log_limit_set", current_val), level="info")
            self._last_logged_limit = current_val

    def _on_mode_radio(self) -> None:
        if self._syncing_ui:
            return
        self.config.update({"search_mode": self.mode_var.get()}, immediate_save=True)

    def _on_lang_selected(self, event: Any) -> None:
        self.config.update({"language": self.lang_var.get()}, immediate_save=True)
        if event is not None:
            event.widget.selection_clear()
        self.root.focus()

    def _on_logic_or_scope_changed(self, event: Any) -> None:
        if self._syncing_ui:
            return
        self.config.update(
            {"filter_logic": self.logic_var.get(), "mod_scope": self.scope_var.get()},
            immediate_save=True,
        )
        if event is not None:
            event.widget.selection_clear()
        self.root.focus()

    def _on_color_keypress_overwrite(self, event: Any) -> None:
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab"):
            return
        if event.char.isdigit() and int(event.char) <= 6:
            event.widget.delete(0, tk.END)

    def _on_color_release(self, key: str) -> None:
        ent = self.color_entries[key]
        raw = "".join(c for c in ent.get() if c.isdigit())
        val = int(raw[-1]) if raw else 0
        val = max(0, min(6, val))
        if str(val) != ent.get():
            ent.delete(0, tk.END)
            ent.insert(0, str(val))
        self.config.update({"color_targets": {key: val}}, immediate_save=False)

    def _on_white_wildcard_toggle(self) -> None:
        if self._syncing_ui:
            return
        self.config.update({"white_as_wildcard": bool(self.white_wildcard_var.get())}, immediate_save=True)

    # ---------------- MINIMAL MODE -----------------
    def toggle_minimal_mode(self) -> None:
        self._is_minimal_mode = not self._is_minimal_mode
        if self._is_minimal_mode:
            self.collapsible_controls.pack_forget()
            self.lang_frame.pack_forget()
            self.frame_filters.pack_forget()
            self.frame_log.pack_configure(fill="both", expand=True)
            self.root.minsize(420, 240)
            self.root.geometry(self.MINIMAL_GEOMETRY)
            self.btn_minimal.configure(text=self._t("btn_normal"))
        else:
            self.collapsible_controls.pack(side="left", fill="x", expand=True, padx=(0, 6))
            for w in (self.btn_minimal, self.btn_settings, self.btn_web, self.lang_frame):
                w.pack_forget()
            self.btn_minimal.pack(side="right", padx=(4, 0))
            self.btn_settings.pack(side="right", padx=4)
            self.btn_web.pack(side="right", padx=4)
            self.lang_frame.pack(side="right", padx=4)

            self.frame_filters.pack(fill="both", expand=True, padx=10, pady=4, before=self.frame_log)
            self.root.minsize(760, 560)
            self.root.geometry(self.NORMAL_GEOMETRY)
            self.btn_minimal.configure(text=self._t("btn_minimal"))
            self._update_mode_layout()

    # ---------------- WEB BROWSER LAUNCH -----------------
    def _open_web_browser(self) -> None:
        if self.web_server is None:
            return
        if not self.web_server.is_running:
            self.config.update({"web_enabled": True}, immediate_save=True)
            self.web_server.start()
            self._update_web_status_label()
        urls = self.web_server.get_urls()
        if urls.get("running"):
            webbrowser.open(urls["local"])

    # ---------------- HOTKEY LISTENING (BUG-FREE) -----------------
    def _cancel_hotkey_listen(self, log_cancel: bool = True) -> None:
        if not self._listening["active"]:
            return
        k_type = self._listening["type"]
        btn = self._listening["btn"]
        hook = self._listening["hook"]

        self._listening = {"active": False, "type": None, "hook": None, "btn": None}
        self.engine.set_listening_hotkey(False)

        if hook is not None and keyboard is not None:
            try:
                keyboard.unhook(hook)
            except Exception:
                pass

        original = self.config.get("hotkey_start" if k_type == "start" else "hotkey_stop", "f2")
        if btn is not None:
            try:
                if btn.winfo_exists():
                    btn.configure(text=str(original).upper())
            except Exception:
                pass

        if log_cancel:
            self.engine.log(self._t("log_hotkey_cancel"), level="info")

    def _listen_for_key(self, k_type: str, btn_widget: ttk.Button) -> None:
        if keyboard is None or self._listening["active"]:
            return
        self._listening = {"active": True, "type": k_type, "hook": None, "btn": btn_widget}
        self.engine.set_listening_hotkey(True)
        btn_widget.configure(text="...")

        def on_press(e: Any) -> None:
            if not self._listening["active"] or e.event_type != "down":
                return
            key_name = str(e.name).lower()

            if key_name == "esc":
                self.root.after(0, lambda: self._cancel_hotkey_listen(log_cancel=True))
                return

            cfg = self.config.snapshot()
            other_key = cfg["hotkey_stop"] if k_type == "start" else cfg["hotkey_start"]
            other_action = "Stop" if k_type == "start" else "Start"
            if key_name == other_key:
                self.engine.log(self._t("log_hotkey_error", key_name.upper(), other_action), level="error")
                return

            def _apply() -> None:
                self._cancel_hotkey_listen(log_cancel=False)
                field = "hotkey_start" if k_type == "start" else "hotkey_stop"
                self.config.update({field: key_name}, immediate_save=True)
                self.engine.register_hotkeys(log_result=True)
                try:
                    if btn_widget.winfo_exists():
                        btn_widget.configure(text=key_name.upper())
                except Exception:
                    pass

            self.root.after(0, _apply)

        self._listening["hook"] = keyboard.on_press(on_press, suppress=False)

    def _on_global_click(self, event: Any) -> None:
        if self._listening["active"]:
            self._cancel_hotkey_listen(log_cancel=True)
            return
        w = event.widget
        if not isinstance(w, (ttk.Entry, tk.Entry, tk.Text, tk.Listbox, ttk.Button, tk.Button, ttk.Combobox)):
            self.root.focus()
            try:
                self.filters_list.selection_clear(0, tk.END)
            except Exception:
                pass

    # ---------------- SETTINGS MODAL -----------------
    def open_settings_window(self) -> None:
        if self._listening["active"]:
            return
        if self._settings_win is not None and self._settings_win.winfo_exists():
            self._settings_win.lift()
            self._settings_win.focus_force()
            return

        cfg = self.config.snapshot()
        p = PALETTES.get(cfg.get("theme", "dark"), PALETTES["dark"])

        sw = tk.Toplevel(self.root)
        self._settings_win = sw
        sw.title(self._t("win_settings_title"))
        sw.resizable(False, False)
        sw.configure(bg=p["bg"])

        # Clamp geometry to visible screen bounds (fixes off-screen modal in Minimal Mode)
        w, h = 420, 520
        cx = self.root.winfo_x() + self.root.winfo_width() // 2 - w // 2
        cy = self.root.winfo_y() + self.root.winfo_height() // 2 - h // 2
        max_x = max(0, sw.winfo_screenwidth() - w - 20)
        max_y = max(0, sw.winfo_screenheight() - h - 60)
        x = max(10, min(cx, max_x))
        y = max(10, min(cy, max_y))
        sw.geometry(f"{w}x{h}+{x}+{y}")

        sw.transient(self.root)
        sw.attributes("-topmost", bool(cfg.get("always_on_top", True)))
        sw.grab_set()
        sw.focus_force()

        def close_settings() -> None:
            self._cancel_hotkey_listen(log_cancel=False)
            self._settings_win = None
            sw.destroy()

        sw.protocol("WM_DELETE_WINDOW", close_settings)

        # General Group
        frm_gen = ttk.LabelFrame(sw, text=self._t("grp_general"), padding=8)
        frm_gen.pack(fill="x", padx=12, pady=(10, 6))

        var_top = tk.BooleanVar(value=bool(cfg["always_on_top"]))
        ttk.Checkbutton(
            frm_gen,
            text=self._t("lbl_always_on_top"),
            variable=var_top,
            command=lambda: self.config.update({"always_on_top": bool(var_top.get())}, immediate_save=True),
        ).pack(anchor="w", pady=2)

        var_sound = tk.BooleanVar(value=bool(cfg["sound_enabled"]))
        ttk.Checkbutton(
            frm_gen,
            text=self._t("lbl_sound_enabled"),
            variable=var_sound,
            command=lambda: self.config.update({"sound_enabled": bool(var_sound.get())}, immediate_save=True),
        ).pack(anchor="w", pady=2)

        row_theme = ttk.Frame(frm_gen)
        row_theme.pack(fill="x", pady=(4, 0))
        ttk.Label(row_theme, text=self._t("lbl_theme")).pack(side="left")
        var_theme = tk.StringVar(value=cfg.get("theme", "dark"))
        cmb_theme = ttk.Combobox(row_theme, textvariable=var_theme, state="readonly", values=["dark", "light"], width=10)
        cmb_theme.bind("<<ComboboxSelected>>", lambda e: self.config.update({"theme": var_theme.get()}, immediate_save=True))
        cmb_theme.pack(side="right")

        # Performance / Timing Group
        frm_time = ttk.LabelFrame(sw, text=self._t("grp_timing"), padding=8)
        frm_time.pack(fill="x", padx=12, pady=6)

        row_cd = ttk.Frame(frm_time)
        row_cd.pack(fill="x", pady=2)
        ttk.Label(row_cd, text=self._t("lbl_click_delay")).pack(side="left")
        var_cd = tk.StringVar(value=str(cfg["click_delay"]))
        sp_cd = ttk.Spinbox(
            row_cd, from_=0.05, to=2.0, increment=0.01, textvariable=var_cd, width=8,
            command=lambda: self.config.update({"click_delay": var_cd.get()}, immediate_save=True),
        )
        sp_cd.bind("<FocusOut>", lambda e: self.config.update({"click_delay": var_cd.get()}, immediate_save=True))
        sp_cd.pack(side="right")

        row_clip = ttk.Frame(frm_time)
        row_clip.pack(fill="x", pady=2)
        ttk.Label(row_clip, text=self._t("lbl_clipboard_delay")).pack(side="left")
        var_clip = tk.StringVar(value=str(cfg["clipboard_delay"]))
        sp_clip = ttk.Spinbox(
            row_clip, from_=0.03, to=0.5, increment=0.01, textvariable=var_clip, width=8,
            command=lambda: self.config.update({"clipboard_delay": var_clip.get()}, immediate_save=True),
        )
        sp_clip.bind("<FocusOut>", lambda e: self.config.update({"clipboard_delay": var_clip.get()}, immediate_save=True))
        sp_clip.pack(side="right")

        # Web & Mobile Group
        frm_web = ttk.LabelFrame(sw, text=self._t("grp_web"), padding=8)
        frm_web.pack(fill="x", padx=12, pady=6)

        var_web = tk.BooleanVar(value=bool(cfg.get("web_enabled", True)))
        var_lan = tk.BooleanVar(value=bool(cfg.get("web_allow_lan", False)))
        lbl_urls = ttk.Label(frm_web, text="", style="Muted.TLabel")

        def refresh_web_info() -> None:
            if self.web_server and self.web_server.is_running:
                u = self.web_server.get_urls()
                lines = [f"{self._t('lbl_web_url')} {u['local']}"]
                if u.get("mobile"):
                    lines.append(f"{self._t('lbl_mobile_url')} {u['mobile']}")
                lbl_urls.configure(text="\n".join(lines))
            else:
                lbl_urls.configure(text="Web UI: Kapalı / Off")
            self._update_web_status_label()

        def on_web_toggle() -> None:
            enabled = bool(var_web.get())
            lan = bool(var_lan.get())
            self.config.update({"web_enabled": enabled, "web_allow_lan": lan}, immediate_save=True)
            if self.web_server is not None:
                if enabled:
                    self.web_server.restart(allow_lan=lan)
                else:
                    self.web_server.stop()
            refresh_web_info()

        ttk.Checkbutton(frm_web, text=self._t("lbl_web_enabled"), variable=var_web, command=on_web_toggle).pack(anchor="w", pady=2)
        ttk.Checkbutton(frm_web, text=self._t("lbl_web_lan"), variable=var_lan, command=on_web_toggle).pack(anchor="w", pady=2)
        lbl_urls.pack(anchor="w", pady=(4, 4))
        ttk.Button(frm_web, text=self._t("lbl_open_browser"), command=self._open_web_browser, takefocus=False).pack(anchor="w")
        refresh_web_info()

        # Hotkeys Group
        frm_keys = ttk.LabelFrame(sw, text=self._t("grp_hotkeys"), padding=8)
        frm_keys.pack(fill="x", padx=12, pady=6)
        ttk.Label(frm_keys, text=self._t("lbl_keys_info"), style="Muted.TLabel").pack(anchor="w", pady=(0, 6))

        row_start = ttk.Frame(frm_keys)
        row_start.pack(fill="x", pady=2)
        ttk.Label(row_start, text=self._t("start"), width=12).pack(side="left")
        btn_start_set = ttk.Button(row_start, text=cfg["hotkey_start"].upper(), width=10, takefocus=False)
        btn_start_set.configure(command=lambda: self._listen_for_key("start", btn_start_set))
        btn_start_set.pack(side="right")

        row_stop = ttk.Frame(frm_keys)
        row_stop.pack(fill="x", pady=2)
        ttk.Label(row_stop, text=self._t("stop"), width=12).pack(side="left")
        btn_stop_set = ttk.Button(row_stop, text=cfg["hotkey_stop"].upper(), width=10, takefocus=False)
        btn_stop_set.configure(command=lambda: self._listen_for_key("stop", btn_stop_set))
        btn_stop_set.pack(side="right")

        ttk.Button(sw, text=self._t("btn_save_close"), command=close_settings, takefocus=False).pack(pady=(6, 10))

    # ---------------- LIFECYCLE -----------------
    def _on_close(self) -> None:
        self._cancel_hotkey_listen(log_cancel=False)
        if self._poll_job is not None:
            try:
                self.root.after_cancel(self._poll_job)
            except Exception:
                pass
        self.engine.unsubscribe(self._enqueue_event)
        self.engine.shutdown()
        if self.web_server is not None:
            self.web_server.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
