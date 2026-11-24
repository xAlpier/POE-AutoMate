"""POE AutoMate v2.0 — Main Entry Point (Desktop GUI + Responsive Web & Mobile Companion)."""

from __future__ import annotations

import argparse
import signal
import sys
import time
import webbrowser

from poe_automate import __version__
from poe_automate.automation import AutomationEngine
from poe_automate.config import ConfigManager
from poe_automate.library import LibraryManager
from poe_automate.web_server import WebCompanionServer


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="POE-AutoMate",
        description="Path of Exile automated item rolling, filtering, and Web/Mobile companion.",
    )
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Run only the Web & Mobile Companion server without the desktop Tkinter window.",
    )
    parser.add_argument(
        "--no-web",
        action="store_true",
        help="Launch desktop GUI without starting the local Web & Mobile server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Override the Web & Mobile server port (default from config.json, 8765).",
    )
    parser.add_argument(
        "--lan",
        action="store_true",
        help="Allow access from other devices on the same local Wi-Fi/LAN (binds 0.0.0.0).",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the Web UI in your default web browser on startup.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"PoE AutoMate {__version__}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    config = ConfigManager()
    library = LibraryManager()
    engine = AutomationEngine(config)
    web_server = WebCompanionServer(config, engine, library)

    port = args.port if args.port is not None else config.get("web_port", 8765)
    allow_lan = True if args.lan else bool(config.get("web_allow_lan", False))

    if args.web_only:
        engine.register_hotkeys(log_result=True)
        started = web_server.start(port=port, allow_lan=allow_lan)
        if not started:
            print(f"[PoE AutoMate] Failed to start web server on port {port}.", file=sys.stderr)
            engine.shutdown()
            return 1

        urls = web_server.get_urls()
        print(f"PoE AutoMate v{__version__} (Web & Mobile Mode)")
        print(f"  Local URL : {urls['local']}")
        if urls.get("mobile"):
            print(f"  Mobile URL: {urls['mobile']}")
        else:
            print("  Tip: Add --lan to enable access from mobile devices on the same Wi-Fi.")
        print("Press Ctrl+C to stop.")

        if args.open_browser:
            webbrowser.open(urls["local"])

        stop_flag = False

        def _handle_sig(_sig: int, _frame: object) -> None:
            nonlocal stop_flag
            stop_flag = True

        signal.signal(signal.SIGINT, _handle_sig)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _handle_sig)

        try:
            while not stop_flag:
                time.sleep(0.3)
        except KeyboardInterrupt:
            pass
        finally:
            web_server.stop()
            engine.shutdown()
        return 0

    # Desktop GUI mode (with optional built-in Web & Mobile Companion)
    if not args.no_web and config.get("web_enabled", True):
        web_server.start(port=port, allow_lan=allow_lan)
        if args.open_browser and web_server.is_running:
            webbrowser.open(web_server.get_urls()["local"])

    from poe_automate.gui import AutoMateGUI

    app = AutoMateGUI(config=config, library=library, engine=engine, web_server=web_server)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
