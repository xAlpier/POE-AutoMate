"""Cached Path of Exile modifier library loader with fast multi-token search."""

from __future__ import annotations

import os
import threading
from typing import Dict, List, Optional, Tuple

from .config import DATA_DIR

ALL_CATEGORIES_KEY = "All Categories"

ITEM_DATABASE_MAP: Dict[str, List[str]] = {
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
    "Optional/General": ["0ptional.txt"],
}


class LibraryManager:
    """Loads, caches, and searches modifier database text files efficiently."""

    def __init__(self, data_dir: str = DATA_DIR) -> None:
        self._data_dir = data_dir
        self._lock = threading.RLock()
        self._cache: Dict[str, List[Tuple[str, str]]] = {}

    def get_categories(self) -> List[str]:
        return list(ITEM_DATABASE_MAP.keys()) + [ALL_CATEGORIES_KEY]

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def _load_files(self, filenames: List[str]) -> List[Tuple[str, str]]:
        if not os.path.isdir(self._data_dir):
            return []
        combined = set()
        for filename in filenames:
            filepath = os.path.join(self._data_dir, filename)
            if not os.path.isfile(filepath):
                continue
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        clean = line.strip()
                        if clean and not clean.startswith("//"):
                            combined.add(clean)
            except Exception as exc:
                print(f"[Library] Error reading {filename}: {exc}")
        ordered = sorted(combined, key=str.lower)
        return [(item, item.lower()) for item in ordered]

    def _get_indexed(self, category: str) -> List[Tuple[str, str]]:
        with self._lock:
            cached = self._cache.get(category)
            if cached is not None:
                return cached

        if category == ALL_CATEGORIES_KEY:
            all_files = []
            for file_list in ITEM_DATABASE_MAP.values():
                all_files.extend(file_list)
            indexed = self._load_files(list(dict.fromkeys(all_files)))
        else:
            files = ITEM_DATABASE_MAP.get(category, [])
            indexed = self._load_files(files)

        with self._lock:
            self._cache[category] = indexed
        return indexed

    def get_items(self, category: str) -> List[str]:
        return [orig for orig, _ in self._get_indexed(category)]

    def search(
        self,
        category: str,
        query: str = "",
        limit: Optional[int] = None,
    ) -> Tuple[List[str], int]:
        """Search category with multi-word case-insensitive token matching.

        Returns (matching_items_slice, total_match_count).
        """
        indexed = self._get_indexed(category)
        tokens = [tok for tok in query.strip().lower().split() if tok]

        if not tokens:
            total = len(indexed)
            if limit is not None and limit > 0:
                return [orig for orig, _ in indexed[:limit]], total
            return [orig for orig, _ in indexed], total

        if len(tokens) == 1:
            tok = tokens[0]
            matches = [orig for orig, low in indexed if tok in low]
        else:
            matches = [orig for orig, low in indexed if all(tok in low for tok in tokens)]

        total = len(matches)
        if limit is not None and limit > 0:
            return matches[:limit], total
        return matches, total
