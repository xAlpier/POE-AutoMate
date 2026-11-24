"""Zero-dependency local HTTP & SSE server powering the Web & Mobile Companion UI."""

from __future__ import annotations

import json
import mimetypes
import os
import queue
import socket
import threading
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Set

from . import __version__
from .automation import AutomationEngine
from .config import ConfigManager, WEB_DIR
from .i18n import TRANSLATIONS, get_text
from .library import LibraryManager

MAX_BODY_BYTES = 262_144  # 256 KB


def get_local_ip() -> str:
    """Discover the primary local LAN IPv4 address without sending network traffic."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass
    try:
        hostname_ip = socket.gethostbyname(socket.gethostname())
        if hostname_ip and not hostname_ip.startswith("127."):
            return hostname_ip
    except Exception:
        pass
    return "127.0.0.1"


class _CompanionHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_cls: type[BaseHTTPRequestHandler],
        companion: "WebCompanionServer",
    ) -> None:
        self.companion = companion
        super().__init__(server_address, handler_cls)


class _CompanionRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        # Silence noisy default stderr access logs
        return

    @property
    def companion(self) -> "WebCompanionServer":
        return self.server.companion  # type: ignore[attr-defined]

    def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message: str, status: int = HTTPStatus.BAD_REQUEST) -> None:
        self._send_json({"ok": False, "error": message}, status=status)

    def _read_json_body(self) -> Optional[Dict[str, Any]]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_error_json("Invalid Content-Length", HTTPStatus.BAD_REQUEST)
            return None
        if length < 0 or length > MAX_BODY_BYTES:
            self._send_error_json("Payload too large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return None
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_error_json("Invalid JSON body", HTTPStatus.BAD_REQUEST)
            return None
        if not isinstance(data, dict):
            self._send_error_json("JSON body must be an object", HTTPStatus.BAD_REQUEST)
            return None
        return data

    def _serve_static(self, rel_path: str) -> None:
        if rel_path in ("", "/"):
            rel_path = "index.html"
        rel_path = rel_path.lstrip("/")
        web_root = os.path.abspath(self.companion.web_dir)
        target = os.path.abspath(os.path.join(web_root, rel_path))
        try:
            if os.path.commonpath([web_root, target]) != web_root:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN)
            return

        if not os.path.isfile(target):
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        mime, _ = mimetypes.guess_type(target)
        if not mime:
            if target.endswith(".js"):
                mime = "application/javascript"
            elif target.endswith(".css"):
                mime = "text/css"
            elif target.endswith(".svg"):
                mime = "image/svg+xml"
            elif target.endswith(".json"):
                mime = "application/json"
            else:
                mime = "application/octet-stream"
        if mime.startswith("text/") or mime in ("application/javascript", "application/json", "image/svg+xml"):
            content_type = f"{mime}; charset=utf-8"
        else:
            content_type = mime

        try:
            with open(target, "rb") as f:
                data = f.read()
        except OSError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _handle_sse(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        client_q = self.companion.register_sse_client()
        try:
            # Initial state snapshot
            init_payload = json.dumps(
                {
                    "state": self.companion.engine.get_state(),
                    "config": self.companion.config.snapshot(),
                },
                ensure_ascii=False,
            )
            self.wfile.write(f"event: init\ndata: {init_payload}\n\n".encode("utf-8"))
            self.wfile.flush()

            while self.companion.is_running:
                try:
                    event = client_q.get(timeout=15.0)
                except queue.Empty:
                    # Heartbeat keeps mobile/proxy connections alive
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    continue

                if event is None:
                    break

                ev_type = event.get("type", "message")
                ev_data = json.dumps(event.get("data", {}), ensure_ascii=False)
                chunk = f"event: {ev_type}\ndata: {ev_data}\n\n".encode("utf-8")
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            self.companion.unregister_sse_client(client_q)

    # ---------------- HTTP VERBS -----------------
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/api/events":
            self._handle_sse()
            return

        if path == "/api/state":
            self._send_json(
                {
                    "ok": True,
                    "version": __version__,
                    "state": self.companion.engine.get_state(),
                    "config": self.companion.config.snapshot(),
                    "logs": self.companion.engine.get_logs(250),
                    "categories": self.companion.library.get_categories(),
                    "urls": self.companion.get_urls(),
                    "translations": TRANSLATIONS,
                }
            )
            return

        if path == "/api/library":
            category = (qs.get("category") or [self.companion.config.get("last_category", "Item (General)")])[0]
            query_str = (qs.get("q") or [""])[0]
            try:
                limit = int((qs.get("limit") or ["250"])[0])
            except ValueError:
                limit = 250
            limit = max(10, min(1500, limit))
            items, total = self.companion.library.search(category, query_str, limit=limit)
            self._send_json(
                {
                    "ok": True,
                    "category": category,
                    "query": query_str,
                    "total": total,
                    "items": items,
                }
            )
            return

        if path == "/api/health":
            self._send_json({"ok": True, "version": __version__})
            return

        self._serve_static(path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/control/start":
            self.companion.engine.start_async()
            self._send_json({"ok": True, "state": self.companion.engine.get_state()})
            return

        if path == "/api/control/stop":
            self.companion.engine.stop()
            self._send_json({"ok": True, "state": self.companion.engine.get_state()})
            return

        if path == "/api/logs/clear":
            self.companion.engine.clear_logs()
            self._send_json({"ok": True})
            return

        if path == "/api/filters":
            body = self._read_json_body()
            if body is None:
                return
            name = str(body.get("name", "")).strip()
            value = str(body.get("value", "")).strip()
            active = bool(body.get("active", True))
            added = self.companion.config.add_filter(name=name, value=value, active=active)
            if added is None:
                self._send_error_json("Modifier name cannot be empty", HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"ok": True, "filter": added, "config": self.companion.config.snapshot()}, HTTPStatus.CREATED)
            return

        if path.startswith("/api/filters/") and path.endswith("/toggle"):
            parts = path.strip("/").split("/")
            if len(parts) == 4:
                try:
                    idx = int(parts[2])
                except ValueError:
                    self._send_error_json("Invalid filter index", HTTPStatus.BAD_REQUEST)
                    return
                toggled = self.companion.config.toggle_filter(idx)
                if toggled is None:
                    self._send_error_json("Filter not found", HTTPStatus.NOT_FOUND)
                    return
                lang = self.companion.config.get("language", "TR")
                st = get_text(lang, "status_active" if toggled["active"] else "status_passive")
                self.companion.engine.log(get_text(lang, "log_filter_toggled", toggled["name"], st), level="info")
                self._send_json({"ok": True, "filter": toggled, "config": self.companion.config.snapshot()})
                return

        if path == "/api/settings":
            body = self._read_json_body()
            if body is None:
                return
            # Prevent changing hotkeys into duplicates from web unless valid
            updated = self.companion.config.update(body, immediate_save=True)
            self._send_json({"ok": True, "config": updated})
            return

        if path == "/api/test-item":
            body = self._read_json_body()
            if body is None:
                return
            raw_text = str(body.get("text", ""))
            result = self.companion.engine.test_item(raw_text)
            self._send_json({"ok": True, "result": result.to_dict()})
            return

        self._send_error_json("Endpoint not found", HTTPStatus.NOT_FOUND)

    def do_PUT(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/filters/"):
            parts = path.strip("/").split("/")
            if len(parts) == 3:
                try:
                    idx = int(parts[2])
                except ValueError:
                    self._send_error_json("Invalid filter index", HTTPStatus.BAD_REQUEST)
                    return
                body = self._read_json_body()
                if body is None:
                    return
                updated = self.companion.config.update_filter(idx, body)
                if updated is None:
                    self._send_error_json("Filter not found or invalid", HTTPStatus.NOT_FOUND)
                    return
                self._send_json({"ok": True, "filter": updated, "config": self.companion.config.snapshot()})
                return

        self._send_error_json("Endpoint not found", HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/filters":
            self.companion.config.clear_filters()
            self._send_json({"ok": True, "config": self.companion.config.snapshot()})
            return

        if path.startswith("/api/filters/"):
            parts = path.strip("/").split("/")
            if len(parts) == 3:
                try:
                    idx = int(parts[2])
                except ValueError:
                    self._send_error_json("Invalid filter index", HTTPStatus.BAD_REQUEST)
                    return
                removed = self.companion.config.delete_filter(idx)
                if removed is None:
                    self._send_error_json("Filter not found", HTTPStatus.NOT_FOUND)
                    return
                self._send_json({"ok": True, "removed": removed, "config": self.companion.config.snapshot()})
                return

        self._send_error_json("Endpoint not found", HTTPStatus.NOT_FOUND)


class WebCompanionServer:
    """Manages lifecycle and SSE pub/sub for the local Web & Mobile dashboard."""

    def __init__(
        self,
        config: ConfigManager,
        engine: AutomationEngine,
        library: LibraryManager,
        web_dir: str = WEB_DIR,
    ) -> None:
        self.config = config
        self.engine = engine
        self.library = library
        self.web_dir = web_dir

        self._lock = threading.RLock()
        self._httpd: Optional[_CompanionHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._sse_clients: Set[queue.Queue[Optional[Dict[str, Any]]]] = set()
        self._bound_host: str = "127.0.0.1"
        self._bound_port: int = 8765
        self._running: bool = False

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def port(self) -> int:
        with self._lock:
            return self._bound_port

    def get_urls(self) -> Dict[str, Any]:
        with self._lock:
            host = self._bound_host
            port = self._bound_port
            running = self._running
        local_url = f"http://127.0.0.1:{port}"
        lan_ip = get_local_ip()
        allow_lan = host == "0.0.0.0"
        mobile_url = f"http://{lan_ip}:{port}" if allow_lan and lan_ip != "127.0.0.1" else None
        return {
            "running": running,
            "local": local_url,
            "mobile": mobile_url,
            "allow_lan": allow_lan,
            "port": port,
        }

    def register_sse_client(self) -> queue.Queue[Optional[Dict[str, Any]]]:
        q: queue.Queue[Optional[Dict[str, Any]]] = queue.Queue(maxsize=250)
        with self._lock:
            self._sse_clients.add(q)
        return q

    def unregister_sse_client(self, q: queue.Queue[Optional[Dict[str, Any]]]) -> None:
        with self._lock:
            self._sse_clients.discard(q)

    def _on_engine_event(self, event: Dict[str, Any]) -> None:
        with self._lock:
            clients = list(self._sse_clients)
        for q in clients:
            try:
                q.put_nowait(event)
            except queue.Full:
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    pass

    def start(self, port: Optional[int] = None, allow_lan: Optional[bool] = None) -> bool:
        with self._lock:
            if self._running:
                return True
            cfg = self.config.snapshot()
            use_port = int(port if port is not None else cfg.get("web_port", 8765))
            use_lan = bool(allow_lan if allow_lan is not None else cfg.get("web_allow_lan", False))
            host = "0.0.0.0" if use_lan else "127.0.0.1"

            try:
                httpd = _CompanionHTTPServer((host, use_port), _CompanionRequestHandler, self)
            except OSError as exc:
                lang = cfg.get("language", "TR")
                self.engine.log(get_text(lang, "log_web_error", exc), level="warning")
                return False

            self._httpd = httpd
            self._bound_host = host
            self._bound_port = httpd.server_address[1]
            self._running = True
            self.engine.subscribe(self._on_engine_event)

            t = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.4}, daemon=True, name="poe-web")
            self._thread = t
            t.start()

        urls = self.get_urls()
        lang = self.config.get("language", "TR")
        self.engine.log(get_text(lang, "log_web_started", urls["local"]), level="system")
        if urls["mobile"]:
            self.engine.log(get_text(lang, "log_web_mobile_hint", urls["mobile"]), level="system")
        return True

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._running = False
            httpd = self._httpd
            self._httpd = None
            clients = list(self._sse_clients)
            self._sse_clients.clear()

        self.engine.unsubscribe(self._on_engine_event)
        for q in clients:
            try:
                q.put_nowait(None)
            except Exception:
                pass
        if httpd is not None:
            try:
                httpd.shutdown()
                httpd.server_close()
            except Exception:
                pass

    def restart(self, port: Optional[int] = None, allow_lan: Optional[bool] = None) -> bool:
        self.stop()
        return self.start(port=port, allow_lan=allow_lan)
