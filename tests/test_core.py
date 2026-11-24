"""Unit tests for config, library, Path of Exile item parser, and matching engine."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from poe_automate.config import ConfigManager, sanitize_config
from poe_automate.library import ALL_CATEGORIES_KEY, LibraryManager
from poe_automate.parser import check_color_match, evaluate_item, filter_matches_item, parse_item_text


SAMPLE_FLASK = """Item Class: Utility Flasks
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
Right click to drink. Can only hold charges while in belt."""


SAMPLE_MULTI_IMPLICIT_ARMOUR = """Item Class: Body Armours
Rarity: Rare
Doom Shell
Vaal Regalia
--------
Quality: +20% (augmented)
Energy Shield: 612 (augmented)
--------
Requirements:
Level: 68
Int: 194
--------
Sockets: B-B-G-R-B-W
--------
Item Level: 86
--------
+15% to Fire Resistance (implicit)
12% increased Action Speed (implicit)
--------
+112 to maximum Life
+44% to Cold Resistance
0.4% of Physical Attack Damage Leeched as Life
Adds 12 to 28 Lightning Damage to Attacks
+38% to Fire Damage over Time Multiplier (fractured)
--------
Searing Exarch Item
Eater of Worlds Item"""


SAMPLE_CORRUPTED_ITEM = """Item Class: Rings
Rarity: Rare
Bramble Loop
Ruby Ring
--------
Item Level: 82
--------
+28% to Fire Resistance (implicit)
--------
+78 to maximum Life
--------
Corrupted"""


SAMPLE_MAGIC_OPEN_SUFFIX = """Item Class: Utility Flasks
Rarity: Magic
Alchemist's Quicksilver Flask
--------
Item Level: 85
--------
25% increased effect"""


class TestConfigManager(unittest.TestCase):
    def test_backward_compatible_load_and_atomic_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = os.path.join(tmp, "config.json")
            legacy = {
                "filters": [{"name": "to maximum Life", "value": "80"}],  # missing 'active'
                "safety_limit": 25,
                "hotkey_start": "F2",
                "hotkey_stop": "F3",
                "search_mode": "color",
                "color_targets": {"R": 3, "G": 2, "B": 1},  # missing 'W'
                "language": "TR",
            }
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(legacy, f)

            cm = ConfigManager(cfg_path)
            snap = cm.snapshot()
            self.assertEqual(snap["filters"][0]["active"], True)
            self.assertEqual(snap["color_targets"]["W"], 0)
            self.assertEqual(snap["hotkey_start"], "f2")
            self.assertEqual(snap["filter_logic"], "OR")
            self.assertEqual(snap["mod_scope"], "explicit")

            cm.add_filter("Instant Recovery", "")
            self.assertEqual(len(cm.get("filters")), 2)
            cm.toggle_filter(1)
            self.assertFalse(cm.get("filters")[1]["active"])
            cm.delete_filter(0)
            self.assertEqual(len(cm.get("filters")), 1)

            # Reload from disk to verify atomic persistence
            cm2 = ConfigManager(cfg_path)
            self.assertEqual(len(cm2.get("filters")), 1)
            self.assertEqual(cm2.get("filters")[0]["name"], "Instant Recovery")

    def test_sanitize_clamps_invalid_values(self) -> None:
        s = sanitize_config(
            {
                "safety_limit": -50,
                "hotkey_start": "f5",
                "hotkey_stop": "f5",
                "click_delay": 0.001,
                "clipboard_delay": 9.9,
                "color_targets": {"R": 99, "G": -3},
                "filter_logic": "INVALID",
                "mod_scope": "NOPE",
            }
        )
        self.assertEqual(s["safety_limit"], 0)
        self.assertNotEqual(s["hotkey_start"], s["hotkey_stop"])
        self.assertEqual(s["click_delay"], 0.05)
        self.assertEqual(s["clipboard_delay"], 0.5)
        self.assertEqual(s["color_targets"]["R"], 6)
        self.assertEqual(s["color_targets"]["G"], 0)
        self.assertEqual(s["filter_logic"], "OR")
        self.assertEqual(s["mod_scope"], "explicit")


class TestLibraryManager(unittest.TestCase):
    def test_load_cache_and_multi_token_search(self) -> None:
        lib = LibraryManager()
        cats = lib.get_categories()
        self.assertIn("Flask", cats)
        self.assertIn(ALL_CATEGORIES_KEY, cats)

        flask_items = lib.get_items("Flask")
        self.assertGreater(len(flask_items), 80)
        self.assertIn("25% increased effect", flask_items)
        self.assertNotIn("66 % increased Amount Recovered", flask_items)

        # Multi-token search
        matches, total = lib.search("Item (General)", "fire resistance")
        self.assertGreater(total, 0)
        self.assertTrue(any("Fire Resistance" in m for m in matches))

        # All categories search with limit
        all_items, all_total = lib.search(ALL_CATEGORIES_KEY, "movement speed", limit=15)
        self.assertLessEqual(len(all_items), 15)
        self.assertGreaterEqual(all_total, len(all_items))


class TestParserAndMatcher(unittest.TestCase):
    def test_parse_multi_implicit_armour(self) -> None:
        parsed = parse_item_text(SAMPLE_MULTI_IMPLICIT_ARMOUR)
        self.assertTrue(parsed.is_valid_poe_item)
        self.assertEqual(parsed.item_class, "Body Armours")
        self.assertEqual(parsed.rarity, "Rare")
        self.assertEqual(parsed.item_level, 86)
        self.assertEqual(len(parsed.implicits), 2)
        self.assertEqual(len(parsed.explicits), 5)
        self.assertEqual(parsed.socket_counts["B"], 3)
        self.assertEqual(parsed.socket_counts["G"], 1)
        self.assertEqual(parsed.socket_counts["R"], 1)
        self.assertEqual(parsed.socket_counts["W"], 1)
        self.assertEqual(parsed.socket_counts["total"], 6)
        self.assertEqual(parsed.socket_counts["max_links"], 6)

    def test_explicit_scope_does_not_false_match_second_implicit(self) -> None:
        parsed = parse_item_text(SAMPLE_MULTI_IMPLICIT_ARMOUR)
        filt = {"name": "#% increased Action Speed", "value": "10", "active": True}

        ok_exp, _ = filter_matches_item(filt, parsed, mod_scope="explicit")
        self.assertFalse(ok_exp)

        ok_imp, _ = filter_matches_item(filt, parsed, mod_scope="implicit")
        self.assertTrue(ok_imp)

        ok_all, _ = filter_matches_item(filt, parsed, mod_scope="all")
        self.assertTrue(ok_all)

    def test_decimal_and_multi_value_and_fractured_and_boolean_mods(self) -> None:
        parsed = parse_item_text(SAMPLE_MULTI_IMPLICIT_ARMOUR)

        # Decimal threshold
        ok_dec, _ = filter_matches_item(
            {"name": "#% of Physical Attack Damage Leeched as Life", "value": "0.3"}, parsed
        )
        self.assertTrue(ok_dec)
        ok_dec_high, _ = filter_matches_item(
            {"name": "#% of Physical Attack Damage Leeched as Life", "value": "0.5"}, parsed
        )
        self.assertFalse(ok_dec_high)

        # Multi-value # to #
        ok_multi, _ = filter_matches_item(
            {"name": "Adds # to # Lightning Damage to Attacks", "value": "10, 25"}, parsed
        )
        self.assertTrue(ok_multi)
        ok_multi_fail, _ = filter_matches_item(
            {"name": "Adds # to # Lightning Damage to Attacks", "value": "10, 35"}, parsed
        )
        self.assertFalse(ok_multi_fail)

        # Fractured mod line matching (strips trailing "(fractured)")
        ok_frac, _ = filter_matches_item(
            {"name": "+#% to Fire Damage over Time Multiplier", "value": "37"}, parsed
        )
        self.assertTrue(ok_frac)

        # Property mod from 0ptional.txt
        ok_prop, _ = filter_matches_item({"name": "Energy Shield: # (augmented)", "value": "600"}, parsed)
        self.assertTrue(ok_prop)

        # Boolean / empty-value enchant match
        flask = parse_item_text(SAMPLE_FLASK)
        ok_bool, _ = filter_matches_item(
            {"name": "Used when Charges reach full", "value": ""}, flask, mod_scope="implicit"
        )
        self.assertTrue(ok_bool)

        # Open suffix heuristic on Magic item
        magic_open = parse_item_text(SAMPLE_MAGIC_OPEN_SUFFIX)
        ok_open, _ = filter_matches_item({"name": "~Open suffix~", "value": ""}, magic_open)
        self.assertTrue(ok_open)

    def test_and_vs_or_logic_and_corrupted_guard(self) -> None:
        cfg_and = sanitize_config(
            {
                "search_mode": "attribute",
                "filter_logic": "AND",
                "filters": [
                    {"name": "25% increased effect", "value": "", "active": True},
                    {"name": "#% increased Movement Speed during Effect", "value": "14", "active": True},
                ],
            }
        )
        res_ok = evaluate_item(SAMPLE_FLASK, cfg_and)
        self.assertEqual(res_ok.status, "FOUND")

        cfg_and_miss = sanitize_config(
            {
                "search_mode": "attribute",
                "filter_logic": "AND",
                "filters": [
                    {"name": "25% increased effect", "value": "", "active": True},
                    {"name": "#% increased Movement Speed during Effect", "value": "20", "active": True},
                ],
            }
        )
        res_miss = evaluate_item(SAMPLE_FLASK, cfg_and_miss)
        self.assertEqual(res_miss.status, "CONTINUE")

        # Corrupted item blocked before rolling
        res_cor = evaluate_item(SAMPLE_CORRUPTED_ITEM, cfg_and)
        self.assertEqual(res_cor.status, "UNMODIFIABLE")

    def test_socket_colors_wildcard_and_impossible_guard(self) -> None:
        parsed = parse_item_text(SAMPLE_MULTI_IMPLICIT_ARMOUR)  # B:3, G:1, R:1, W:1 (total 6)

        # Needs 4 Blue -> 3 Blue + 1 White wildcard matches!
        res_wild = check_color_match(parsed, {"R": 1, "G": 1, "B": 4, "W": 0}, white_as_wildcard=True)
        self.assertEqual(res_wild.status, "FOUND")

        # Without wildcard -> fails
        res_strict = check_color_match(parsed, {"R": 1, "G": 1, "B": 4, "W": 0}, white_as_wildcard=False)
        self.assertEqual(res_strict.status, "CONTINUE")

        # Impossible total socket count (requires 7 on a 6-socket item)
        res_imp = check_color_match(parsed, {"R": 3, "G": 2, "B": 2, "W": 0}, white_as_wildcard=True)
        self.assertEqual(res_imp.status, "IMPOSSIBLE")


if __name__ == "__main__":
    unittest.main()
