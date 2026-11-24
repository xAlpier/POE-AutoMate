/* PoE AutoMate v2.0 — Responsive Web & Mobile Companion Client */
(() => {
  "use strict";

  const SAMPLE_ITEM = `Item Class: Utility Flasks
Rarity: Magic
Alchemist's Quicksilver Flask of the Cheetah
--------
Quality: +20% (augmented)
Lasts 6.00 Seconds
Consumes 30 of 60 Charges on use
Currently has 60 Charges
40% increased Movement Speed
--------
Requirements:
Level: 58
--------
Item Level: 85
--------
Used when Charges reach full (enchant)
--------
25% increased effect
30% reduced Duration
14% increased Movement Speed during Effect
--------
Right click to drink. Can only hold charges while in belt.`;

  const state = {
    config: null,
    engine: null,
    translations: {},
    categories: [],
    urls: {},
    logs: [],
    desktopTab: "workspace",
    mobileTab: "filters",
    searchTimer: null,
    settingsTimer: null,
    sse: null,
  };

  const $ = (id) => document.getElementById(id);

  function t(key, ...args) {
    const lang = (state.config && state.config.language) || "TR";
    const dict = state.translations[lang] || state.translations.TR || {};
    let str = dict[key] || key;
    args.forEach((arg) => {
      str = str.replace("{}", String(arg));
    });
    return str;
  }

  let toastTimer = null;
  function showToast(msg) {
    const el = $("toast");
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 2200);
  }

  async function api(url, method = "GET", body = null) {
    const opts = { method, headers: {} };
    if (body !== null) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const resp = await fetch(url, opts);
    const data = await resp.json().catch(() => ({ ok: false, error: resp.statusText }));
    if (!resp.ok || data.ok === false) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }
    return data;
  }

  function applyTheme(theme) {
    const mode = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", mode);
    $("btnTheme").textContent = mode === "light" ? "☀️" : "🌙";
    $("setTheme").value = mode;
  }

  function applyTranslations() {
    if (!state.config) return;
    $("btnStart").textContent = "▶ " + t("btn_start");
    $("btnStop").textContent = "■ " + t("btn_stop");
    $("modeAttrBtn").textContent = t("attribute");
    $("modeColorBtn").textContent = t("color");
    $("lblMaxTries").textContent = t("max_tries");
    $("hdrActiveFilters").textContent = t("active_filters").split("(")[0].trim();
    $("lblLogic").textContent = t("filter_logic");
    $("lblScope").textContent = t("mod_scope");

    const logicSel = $("logicSelect");
    logicSel.options[0].textContent = t("logic_or");
    logicSel.options[1].textContent = t("logic_and");

    const scopeSel = $("scopeSelect");
    scopeSel.options[0].textContent = t("scope_explicit");
    scopeSel.options[1].textContent = t("scope_implicit");
    scopeSel.options[2].textContent = t("scope_all");

    $("lblFilterValue").textContent = t("value_min");
    $("lblFilterName").textContent = t("modifier_name");
    $("btnAddFilter").textContent = "+ " + t("add_filter");
    $("btnClearFilters").textContent = t("clear_all");

    $("hdrColorFilters").textContent = t("color_filters");
    $("lblColorR").textContent = t("red");
    $("lblColorG").textContent = t("green");
    $("lblColorB").textContent = t("blue");
    $("lblColorW").textContent = t("white");
    $("lblWhiteWildcard").textContent = t("white_wildcard");

    $("hdrLibrary").textContent = t("database_library");
    $("hdrLogs").textContent = t("system_log");
    $("btnClearLogs").textContent = t("clear_log");
    $("hdrTester").textContent = t("web_tester_title");
    $("descTester").textContent = t("web_tester_desc");
    $("btnRunTest").textContent = "🧪 " + t("web_tester_btn");
    $("btnSampleItem").textContent = t("web_tester_sample");

    $("hdrSettings").textContent = t("settings");
    $("grpGeneral").textContent = t("grp_general");
    $("lblSetTopmost").textContent = t("lbl_always_on_top");
    $("lblSetSound").textContent = t("lbl_sound_enabled");
    $("lblSetTheme").textContent = t("lbl_theme");
    $("grpTiming").textContent = t("grp_timing");
    $("lblSetClickDelay").textContent = t("lbl_click_delay");
    $("lblSetClipDelay").textContent = t("lbl_clipboard_delay");
    $("lblLocalUrl").textContent = t("lbl_web_url");
    $("lblMobileUrl").textContent = t("lbl_mobile_url");

    $("mnavFilters").textContent = t("web_tab_filters");
    $("mnavLibrary").textContent = t("web_tab_library");
    $("mnavLogs").textContent = t("web_tab_logs");
    $("mnavTester").textContent = t("web_tab_tester");
    $("mnavSettings").textContent = t("web_tab_settings");

    $("dtabWorkspace").textContent = "🎛️ " + t("attr_filters_library");
    $("dtabLogsLabel").textContent = t("system_log");
    $("dtabTester").textContent = "🧪 " + t("web_tab_tester");
    $("dtabSettings").textContent = "⚙️ " + t("settings");
  }

  function renderEngineState() {
    if (!state.engine) return;
    const st = state.engine;
    const badge = $("statusBadge");
    badge.className = "status-pill";
    if (st.status === "RUNNING") {
      badge.textContent = t("status_running");
      badge.classList.add("status-running");
    } else if (st.status === "FOUND") {
      badge.textContent = t("status_found");
      badge.classList.add("status-found");
    } else {
      badge.textContent = t("status_stopped");
      badge.classList.add("status-stopped");
    }

    const lim = st.safety_limit === 0 ? "∞" : String(st.safety_limit);
    $("statAttempts").textContent = `${st.attempts} / ${lim}`;
    $("statSpeed").textContent = `${Number(st.rolls_per_sec || 0).toFixed(1)}/s`;

    const poeEl = $("poeBadge");
    poeEl.textContent = st.poe_active ? t("web_poe_status_active") : t("web_poe_status_inactive");
    poeEl.classList.toggle("active", Boolean(st.poe_active));

    $("btnStart").disabled = Boolean(st.running);
    $("btnStop").disabled = !st.running;
  }

  function renderConfig() {
    const cfg = state.config;
    if (!cfg) return;

    applyTheme(cfg.theme);
    $("langSelect").value = cfg.language || "TR";
    applyTranslations();

    const isAttr = cfg.search_mode !== "color";
    $("modeAttrBtn").classList.toggle("active", isAttr);
    $("modeColorBtn").classList.toggle("active", !isAttr);
    $("attrModeBox").classList.toggle("hidden", !isAttr);
    $("colorModeBox").classList.toggle("hidden", isAttr);

    if (document.activeElement !== $("maxTriesInput")) {
      $("maxTriesInput").value = cfg.safety_limit;
    }
    $("logicSelect").value = cfg.filter_logic || "OR";
    $("scopeSelect").value = cfg.mod_scope || "explicit";

    const colors = cfg.color_targets || { R: 0, G: 0, B: 0, W: 0 };
    ["R", "G", "B", "W"].forEach((k) => {
      const inp = $("color" + k);
      if (document.activeElement !== inp) {
        inp.value = colors[k] || 0;
      }
    });
    const totalReq = (colors.R || 0) + (colors.G || 0) + (colors.B || 0) + (colors.W || 0);
    $("socketTotalBadge").textContent = t("total_sockets_req", totalReq);
    $("whiteWildcardChk").checked = Boolean(cfg.white_as_wildcard);

    $("setTopmost").checked = Boolean(cfg.always_on_top);
    $("setSound").checked = Boolean(cfg.sound_enabled);
    if (document.activeElement !== $("setClickDelay")) {
      $("setClickDelay").value = cfg.click_delay;
    }
    if (document.activeElement !== $("setClipboardDelay")) {
      $("setClipboardDelay").value = cfg.clipboard_delay;
    }
    $("txtHotkeys").textContent = `${(cfg.hotkey_start || "f2").toUpperCase()} / ${(cfg.hotkey_stop || "f3").toUpperCase()}`;

    renderFiltersList();
    renderEngineState();
  }

  function renderFiltersList() {
    const container = $("filtersList");
    const filters = (state.config && state.config.filters) || [];
    container.textContent = "";

    if (!filters.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = t("web_no_filters_hint");
      container.appendChild(empty);
      return;
    }

    filters.forEach((f, idx) => {
      const row = document.createElement("div");
      row.className = "filter-item" + (f.active === false ? " passive" : "");

      const chk = document.createElement("input");
      chk.type = "checkbox";
      chk.className = "filter-toggle";
      chk.checked = f.active !== false;
      chk.addEventListener("change", async () => {
        try {
          const res = await api(`/api/filters/${idx}/toggle`, "POST");
          state.config = res.config;
          renderFiltersList();
        } catch (err) {
          showToast(err.message);
        }
      });

      const body = document.createElement("div");
      body.className = "filter-body";
      body.addEventListener("click", () => {
        $("filterNameInput").value = f.name || "";
        $("filterValueInput").value = f.value || "";
        $("filterValueInput").focus();
        showToast("Düzenlemek için forma yüklendi");
      });

      const valBadge = document.createElement("span");
      valBadge.className = "filter-val-badge";
      valBadge.textContent = f.value ? `≥ ${f.value}` : "ANY";

      const nameSpan = document.createElement("span");
      nameSpan.className = "filter-name";
      nameSpan.textContent = f.name || "";

      body.appendChild(valBadge);
      body.appendChild(nameSpan);

      const actions = document.createElement("div");
      actions.className = "filter-actions";

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "icon-btn";
      delBtn.title = t("delete_selected");
      delBtn.textContent = "🗑️";
      delBtn.addEventListener("click", async () => {
        try {
          const res = await api(`/api/filters/${idx}`, "DELETE");
          state.config = res.config;
          renderFiltersList();
        } catch (err) {
          showToast(err.message);
        }
      });

      actions.appendChild(delBtn);
      row.appendChild(chk);
      row.appendChild(body);
      row.appendChild(actions);
      container.appendChild(row);
    });
  }

  function renderCategories() {
    const sel = $("categorySelect");
    sel.textContent = "";
    state.categories.forEach((cat) => {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.textContent = cat === "All Categories" ? t("all_categories") : cat;
      sel.appendChild(opt);
    });
    const last = (state.config && state.config.last_category) || state.categories[0] || "Item (General)";
    if (state.categories.includes(last)) {
      sel.value = last;
    }
  }

  async function fetchLibrary() {
    const category = $("categorySelect").value || "Item (General)";
    const q = $("libSearchInput").value || "";
    try {
      const res = await api(
        `/api/library?category=${encodeURIComponent(category)}&q=${encodeURIComponent(q)}&limit=250`
      );
      $("libCountBadge").textContent = t("results_count", res.total);
      const list = $("libraryList");
      list.textContent = "";

      if (!res.items.length) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "—";
        list.appendChild(empty);
        return;
      }

      const frag = document.createDocumentFragment();
      res.items.forEach((modText) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "lib-row";

        const txt = document.createElement("span");
        txt.textContent = modText;

        const tag = document.createElement("span");
        tag.className = "lib-add-tag";
        tag.textContent = "+ Seç";

        btn.appendChild(txt);
        btn.appendChild(tag);
        btn.addEventListener("click", () => {
          $("filterNameInput").value = modText;
          $("filterValueInput").value = "";
          if (state.config && state.config.search_mode !== "attribute") {
            pushSettings({ search_mode: "attribute" });
          }
          if (window.innerWidth < 900) {
            switchMobileTab("filters");
          }
          $("filterValueInput").focus();
          showToast(modText);
        });
        frag.appendChild(btn);
      });
      list.appendChild(frag);
    } catch (err) {
      showToast(err.message);
    }
  }

  function appendLogElement(entry) {
    const box = $("logContainer");
    const line = document.createElement("div");
    line.className = `log-line log-level-${entry.level || "info"}`;

    const ts = document.createElement("span");
    ts.className = "log-ts";
    ts.textContent = `[${entry.ts || "--:--:--"}]`;

    line.appendChild(ts);
    line.appendChild(document.createTextNode(entry.text || ""));
    box.appendChild(line);

    while (box.childElementCount > 400) {
      box.removeChild(box.firstElementChild);
    }
    $("logCountBadge").textContent = String(box.childElementCount);

    if ($("autoScrollChk").checked) {
      box.scrollTop = box.scrollHeight;
    }
  }

  function renderAllLogs(entries) {
    const box = $("logContainer");
    box.textContent = "";
    const frag = document.createDocumentFragment();
    entries.forEach((entry) => {
      const line = document.createElement("div");
      line.className = `log-line log-level-${entry.level || "info"}`;
      const ts = document.createElement("span");
      ts.className = "log-ts";
      ts.textContent = `[${entry.ts || "--:--:--"}]`;
      line.appendChild(ts);
      line.appendChild(document.createTextNode(entry.text || ""));
      frag.appendChild(line);
    });
    box.appendChild(frag);
    $("logCountBadge").textContent = String(box.childElementCount);
    box.scrollTop = box.scrollHeight;
  }

  async function pushSettings(patch) {
    try {
      const res = await api("/api/settings", "POST", patch);
      state.config = res.config;
      renderConfig();
    } catch (err) {
      showToast(err.message);
    }
  }

  function pushSettingsDebounced(patch) {
    clearTimeout(state.settingsTimer);
    state.settingsTimer = setTimeout(() => pushSettings(patch), 200);
  }

  function switchDesktopTab(tab) {
    state.desktopTab = tab;
    document.querySelectorAll(".desktop-tabs .tab-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.tab === tab);
    });
    const main = document.querySelector(".main-content");
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active-desktop-panel"));

    if (tab === "workspace") {
      main.classList.add("view-workspace");
      main.classList.remove("view-single");
    } else {
      main.classList.remove("view-workspace");
      main.classList.add("view-single");
      const map = { logs: "panelLogs", tester: "panelTester", settings: "panelSettings" };
      const target = $(map[tab]);
      if (target) target.classList.add("active-desktop-panel");
    }
  }

  function switchMobileTab(tab) {
    state.mobileTab = tab;
    document.querySelectorAll(".mnav-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.mtab === tab);
    });
    document.querySelectorAll(".panel").forEach((p) => {
      p.classList.toggle("active-mobile-panel", p.dataset.panel === tab);
    });
  }

  async function runItemTest() {
    const raw = $("testerInput").value;
    const out = $("testerResult");
    if (!raw.trim()) {
      out.classList.add("hidden");
      return;
    }
    try {
      const res = await api("/api/test-item", "POST", { text: raw });
      const r = res.result;
      out.classList.remove("hidden");
      out.textContent = "";

      const banner = document.createElement("div");
      banner.className = "tester-banner " + (r.matched ? "ok" : ["INVALID_ITEM", "UNMODIFIABLE", "IMPOSSIBLE_SOCKETS"].includes(r.status) ? "err" : "miss");
      banner.textContent = `${r.status}${r.summary ? " — " + r.summary : ""}`;
      out.appendChild(banner);

      const item = r.item || {};
      const meta = document.createElement("div");
      meta.className = "parsed-meta";
      [
        item.rarity && `Rarity: ${item.rarity}`,
        item.item_class && `Class: ${item.item_class}`,
        item.item_level != null && `iLvl: ${item.item_level}`,
        item.sockets_raw && `Sockets: ${item.sockets_raw}`,
        item.is_corrupted && "CORRUPTED",
        item.is_mirrored && "MIRRORED",
      ]
        .filter(Boolean)
        .forEach((txt) => {
          const span = document.createElement("span");
          span.className = "meta-tag";
          span.textContent = txt;
          meta.appendChild(span);
        });
      out.appendChild(meta);

      const logWrap = document.createElement("div");
      logWrap.className = "log-box";
      logWrap.style.height = "auto";
      logWrap.style.maxHeight = "220px";
      (r.logs || []).forEach((l) => {
        const line = document.createElement("div");
        line.className = `log-line log-level-${l.level}`;
        line.textContent = l.text;
        logWrap.appendChild(line);
      });
      out.appendChild(logWrap);
    } catch (err) {
      showToast(err.message);
    }
  }

  function connectSSE() {
    if (state.sse) {
      try { state.sse.close(); } catch (_) {}
    }
    const es = new EventSource("/api/events");
    state.sse = es;

    es.onopen = () => {
      $("connDot").className = "dot dot-ok";
      $("connText").textContent = t("web_connected");
    };

    es.onerror = () => {
      $("connDot").className = "dot dot-warn";
      $("connText").textContent = t("web_reconnecting");
    };

    es.addEventListener("init", (ev) => {
      try {
        const d = JSON.parse(ev.data);
        if (d.config) state.config = d.config;
        if (d.state) state.engine = d.state;
        renderConfig();
      } catch (_) {}
    });

    es.addEventListener("state", (ev) => {
      try {
        state.engine = JSON.parse(ev.data);
        renderEngineState();
      } catch (_) {}
    });

    es.addEventListener("config", (ev) => {
      try {
        state.config = JSON.parse(ev.data);
        renderConfig();
      } catch (_) {}
    });

    es.addEventListener("log", (ev) => {
      try {
        appendLogElement(JSON.parse(ev.data));
      } catch (_) {}
    });

    es.addEventListener("logs_cleared", () => {
      $("logContainer").textContent = "";
      $("logCountBadge").textContent = "0";
    });
  }

  function bindEvents() {
    $("btnStart").addEventListener("click", () => api("/api/control/start", "POST").catch((e) => showToast(e.message)));
    $("btnStop").addEventListener("click", () => api("/api/control/stop", "POST").catch((e) => showToast(e.message)));

    $("btnTheme").addEventListener("click", () => {
      const next = (state.config && state.config.theme) === "light" ? "dark" : "light";
      pushSettings({ theme: next });
    });

    $("langSelect").addEventListener("change", (e) => {
      pushSettings({ language: e.target.value }).then(() => {
        renderCategories();
      });
    });

    $("modeAttrBtn").addEventListener("click", () => pushSettings({ search_mode: "attribute" }));
    $("modeColorBtn").addEventListener("click", () => pushSettings({ search_mode: "color" }));

    $("maxTriesInput").addEventListener("input", (e) => {
      const v = Math.max(0, parseInt(e.target.value || "0", 10) || 0);
      pushSettingsDebounced({ safety_limit: v });
    });

    $("logicSelect").addEventListener("change", (e) => pushSettings({ filter_logic: e.target.value }));
    $("scopeSelect").addEventListener("change", (e) => pushSettings({ mod_scope: e.target.value }));

    $("addFilterForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = $("filterNameInput").value.trim();
      const value = $("filterValueInput").value.trim();
      if (!name) return;
      try {
        const res = await api("/api/filters", "POST", { name, value, active: true });
        state.config = res.config;
        $("filterNameInput").value = "";
        $("filterValueInput").value = "";
        renderFiltersList();
        showToast("+ " + name);
      } catch (err) {
        showToast(err.message);
      }
    });

    $("btnClearFilters").addEventListener("click", async () => {
      try {
        const res = await api("/api/filters", "DELETE");
        state.config = res.config;
        renderFiltersList();
      } catch (err) {
        showToast(err.message);
      }
    });

    // Socket color steppers & inputs
    document.querySelectorAll(".step-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.dataset.color;
        const delta = parseInt(btn.dataset.delta, 10);
        const inp = $("color" + key);
        const next = Math.max(0, Math.min(6, (parseInt(inp.value, 10) || 0) + delta));
        inp.value = next;
        pushSettings({ color_targets: { [key]: next } });
      });
    });
    ["R", "G", "B", "W"].forEach((k) => {
      $("color" + k).addEventListener("input", (e) => {
        const next = Math.max(0, Math.min(6, parseInt(e.target.value || "0", 10) || 0));
        pushSettingsDebounced({ color_targets: { [k]: next } });
      });
    });

    $("whiteWildcardChk").addEventListener("change", (e) => {
      pushSettings({ white_as_wildcard: e.target.checked });
    });

    $("categorySelect").addEventListener("change", (e) => {
      pushSettings({ last_category: e.target.value });
      fetchLibrary();
    });

    $("libSearchInput").addEventListener("input", () => {
      clearTimeout(state.searchTimer);
      state.searchTimer = setTimeout(fetchLibrary, 120);
    });

    $("btnClearLogs").addEventListener("click", () => {
      api("/api/logs/clear", "POST").catch((e) => showToast(e.message));
    });

    $("btnSampleItem").addEventListener("click", () => {
      $("testerInput").value = SAMPLE_ITEM;
      runItemTest();
    });
    $("btnRunTest").addEventListener("click", runItemTest);
    $("btnClearTest").addEventListener("click", () => {
      $("testerInput").value = "";
      $("testerResult").classList.add("hidden");
    });

    $("setTopmost").addEventListener("change", (e) => pushSettings({ always_on_top: e.target.checked }));
    $("setSound").addEventListener("change", (e) => pushSettings({ sound_enabled: e.target.checked }));
    $("setTheme").addEventListener("change", (e) => pushSettings({ theme: e.target.value }));
    $("setClickDelay").addEventListener("input", (e) => {
      const v = parseFloat(e.target.value);
      if (!isNaN(v)) pushSettingsDebounced({ click_delay: v });
    });
    $("setClipboardDelay").addEventListener("input", (e) => {
      const v = parseFloat(e.target.value);
      if (!isNaN(v)) pushSettingsDebounced({ clipboard_delay: v });
    });

    document.querySelectorAll(".desktop-tabs .tab-btn").forEach((b) => {
      b.addEventListener("click", () => switchDesktopTab(b.dataset.tab));
    });
    document.querySelectorAll(".mnav-btn").forEach((b) => {
      b.addEventListener("click", () => switchMobileTab(b.dataset.mtab));
    });
  }

  async function init() {
    bindEvents();
    switchDesktopTab("workspace");
    switchMobileTab("filters");

    try {
      const data = await api("/api/state");
      state.translations = data.translations || {};
      state.categories = data.categories || [];
      state.config = data.config;
      state.engine = data.state;
      state.urls = data.urls || {};

      $("appVersion").textContent = "v" + (data.version || "2.0");
      $("txtLocalUrl").textContent = state.urls.local || location.origin;
      $("txtMobileUrl").textContent = state.urls.mobile || "LAN Kapalı (Ayarlardan açılabilir)";

      renderCategories();
      renderConfig();
      renderAllLogs(data.logs || []);
      await fetchLibrary();
      connectSSE();
    } catch (err) {
      $("connDot").className = "dot dot-err";
      $("connText").textContent = err.message;
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
