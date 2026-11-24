"""Path of Exile item clipboard parser and modifier/socket matching engine."""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .i18n import get_text

_SEPARATOR_RE = re.compile(r"^-{4,}$")
_NUMBER_RE = re.compile(r"([+-]?\d+(?:\.\d+)?)")
_SOCKET_CHAR_RE = re.compile(r"[RGBWA]")
_TAG_SUFFIX_RE = re.compile(r"\s*\((implicit|enchant|fractured|crafted|scourge)\)\s*$", re.IGNORECASE)
_ADVANCED_MOD_HEADER_RE = re.compile(r"^\{.*\}$")

_PROPERTY_PREFIXES = (
    "quality:",
    "armour:",
    "evasion rating:",
    "energy shield:",
    "ward:",
    "physical damage:",
    "elemental damage:",
    "chaos damage:",
    "critical strike chance:",
    "attacks per second:",
    "weapon range:",
    "chance to block:",
    "item quantity:",
    "item rarity:",
    "monster pack size:",
    "map tier:",
)

_NON_MOD_LINE_PREFIXES = (
    "right click to ",
    "place into an allocated ",
    "travel to this map ",
    "hold ctrl ",
    "note:",
    "talisman tier:",
    "can have up to ",
    "cannot use this item",
    "heist target:",
    "area level:",
    "requires ",
)

_NON_MOD_EXACT_LINES = {
    "corrupted",
    "mirrored",
    "split",
    "unidentified",
    "synthesised item",
    "fractured item",
    "shaper item",
    "elder item",
    "crusader item",
    "redeemer item",
    "hunter item",
    "warlord item",
    "searing exarch item",
    "eater of worlds item",
    "relic",
    "foil unique",
}


def _format_num(val: float) -> str:
    if val == int(val):
        return str(int(val))
    return f"{val:g}"


@functools.lru_cache(maxsize=512)
def _compile_hash_pattern(template: str) -> re.Pattern[str]:
    parts = template.split("#")
    escaped_parts = [re.escape(p) for p in parts]
    pattern_str = r"([+-]?\d+(?:\.\d+)?)".join(escaped_parts)
    return re.compile(pattern_str, re.IGNORECASE)


def _strip_mod_tag(line: str) -> str:
    return _TAG_SUFFIX_RE.sub("", line).strip()


def _is_non_mod_line(line: str) -> bool:
    low = line.strip().lower()
    if not low:
        return True
    if low in _NON_MOD_EXACT_LINES:
        return True
    if any(low.startswith(prefix) for prefix in _NON_MOD_LINE_PREFIXES):
        return True
    return False


@dataclass
class ParsedItem:
    raw_text: str = ""
    item_class: str = ""
    rarity: str = ""
    name: str = ""
    item_level: Optional[int] = None
    sockets_raw: str = ""
    socket_counts: Dict[str, int] = field(
        default_factory=lambda: {"R": 0, "G": 0, "B": 0, "W": 0, "A": 0, "total": 0, "max_links": 0}
    )
    properties: List[str] = field(default_factory=list)
    enchants: List[str] = field(default_factory=list)
    implicits: List[str] = field(default_factory=list)
    explicits: List[str] = field(default_factory=list)
    prefix_count: Optional[int] = None
    suffix_count: Optional[int] = None
    is_corrupted: bool = False
    is_mirrored: bool = False
    is_unidentified: bool = False
    is_split: bool = False
    is_valid_poe_item: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_class": self.item_class,
            "rarity": self.rarity,
            "name": self.name,
            "item_level": self.item_level,
            "sockets_raw": self.sockets_raw,
            "socket_counts": dict(self.socket_counts),
            "properties": list(self.properties),
            "enchants": list(self.enchants),
            "implicits": list(self.implicits),
            "explicits": list(self.explicits),
            "is_corrupted": self.is_corrupted,
            "is_mirrored": self.is_mirrored,
            "is_unidentified": self.is_unidentified,
            "is_valid_poe_item": self.is_valid_poe_item,
        }


def parse_sockets(sockets_str: str) -> Dict[str, int]:
    counts = {"R": 0, "G": 0, "B": 0, "W": 0, "A": 0, "total": 0, "max_links": 0}
    cleaned = sockets_str.strip().upper()
    if not cleaned:
        return counts

    groups = cleaned.split()
    max_links = 0
    for grp in groups:
        chars = _SOCKET_CHAR_RE.findall(grp)
        if len(chars) > max_links:
            max_links = len(chars)
        for ch in chars:
            counts[ch] += 1
            counts["total"] += 1
    counts["max_links"] = max_links
    return counts


def parse_item_text(raw_text: str) -> ParsedItem:
    """Parse raw Path of Exile clipboard text into structured sections."""
    item = ParsedItem(raw_text=raw_text or "")
    cleaned = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return item

    sections: List[List[str]] = []
    current: List[str] = []
    for raw_line in cleaned.split("\n"):
        line = raw_line.strip()
        if _SEPARATOR_RE.match(line):
            if current:
                sections.append(current)
                current = []
        elif line:
            current.append(line)
    if current:
        sections.append(current)

    if not sections:
        return item

    # Header section
    header = sections[0]
    name_parts: List[str] = []
    for line in header:
        low = line.lower()
        if low.startswith("item class:"):
            item.item_class = line.split(":", 1)[1].strip()
            item.is_valid_poe_item = True
        elif low.startswith("rarity:"):
            item.rarity = line.split(":", 1)[1].strip()
            item.is_valid_poe_item = True
        else:
            name_parts.append(line)
    item.name = " — ".join(name_parts) if name_parts else ""

    # Track advanced copy prefix/suffix counts if present
    adv_prefixes = 0
    adv_suffixes = 0
    saw_advanced = False

    after_ilvl = False
    for sec in sections[1:]:
        sec_low = [l.lower() for l in sec]

        # Global flags can appear in any section
        for l_low in sec_low:
            if l_low == "corrupted":
                item.is_corrupted = True
            elif l_low == "mirrored":
                item.is_mirrored = True
            elif l_low == "unidentified":
                item.is_unidentified = True
            elif l_low == "split":
                item.is_split = True

        # Requirements section
        if sec_low[0].startswith("requirements:"):
            continue

        # Sockets section
        socket_found = False
        for line in sec:
            if line.lower().startswith("sockets:"):
                item.sockets_raw = line.split(":", 1)[1].strip()
                item.socket_counts = parse_sockets(item.sockets_raw)
                item.is_valid_poe_item = True
                socket_found = True
        if socket_found and len(sec) == 1:
            continue

        # Item Level section
        ilvl_found = False
        for line in sec:
            if line.lower().startswith("item level:"):
                m = re.search(r"\d+", line)
                if m:
                    item.item_level = int(m.group(0))
                item.is_valid_poe_item = True
                after_ilvl = True
                ilvl_found = True
        if ilvl_found and len(sec) == 1:
            continue

        # Before Item Level -> properties / base stats
        if not after_ilvl:
            for line in sec:
                if line.lower().startswith("sockets:") or line.lower().startswith("item level:"):
                    continue
                if line.lower().endswith("(enchant)"):
                    item.enchants.append(line)
                elif line.lower().endswith("(implicit)"):
                    item.implicits.append(line)
                elif not _is_non_mod_line(line):
                    item.properties.append(line)
            continue

        # After Item Level -> enchants, implicits, explicits, or trailing notes/flags
        # Skip sections where every line is a non-mod flag/hint
        if all(_is_non_mod_line(l) for l in sec):
            continue

        # Skip Unique flavor text section (if rarity is Unique and we already parsed explicits)
        if item.rarity.lower() == "unique" and item.explicits and not any(
            l.lower().endswith(("(implicit)", "(enchant)", "(fractured)", "(crafted)")) for l in sec
        ):
            # Flavor text normally follows explicit mods on Uniques
            continue

        for line in sec:
            low = line.lower()
            if _ADVANCED_MOD_HEADER_RE.match(line):
                saw_advanced = True
                if "prefix modifier" in low:
                    adv_prefixes += 1
                elif "suffix modifier" in low:
                    adv_suffixes += 1
                continue
            if _is_non_mod_line(line):
                continue
            if low.endswith("(enchant)"):
                item.enchants.append(line)
            elif low.endswith("(implicit)"):
                item.implicits.append(line)
            else:
                item.explicits.append(line)

    if saw_advanced:
        item.prefix_count = adv_prefixes
        item.suffix_count = adv_suffixes

    return item


def _check_open_affix(kind: str, parsed: ParsedItem) -> Tuple[bool, Optional[str]]:
    """Evaluate ~Open prefix~ or ~Open suffix~ filters."""
    rarity = parsed.rarity.lower()
    if rarity == "normal":
        return True, f"~Open {kind}~"

    if parsed.prefix_count is not None and parsed.suffix_count is not None:
        max_slots = 1 if rarity == "magic" else (2 if "jewel" in parsed.item_class.lower() else 3)
        current = parsed.prefix_count if kind == "prefix" else parsed.suffix_count
        if current < max_slots:
            return True, f"~Open {kind}~ ({current}/{max_slots})"
        return False, None

    # Heuristic for Magic items without Ctrl+Alt+C:
    # A Magic item with " of " in its name has a suffix; otherwise no suffix.
    if rarity == "magic":
        has_suffix = " of " in parsed.name.lower()
        # Magic items have at most 1 prefix and 1 suffix (max 2 mods, though hybrid mods can span 2 lines)
        if kind == "suffix":
            return (not has_suffix), ("~Open suffix~" if not has_suffix else None)
        if kind == "prefix":
            # If it has 0 explicits or only a suffix (starts with base name + " of ")
            if not parsed.explicits:
                return True, "~Open prefix~"
            # If no suffix and only 1 mod -> prefix is occupied; if has suffix and only 1 mod line -> prefix is open
            if has_suffix and len(parsed.explicits) == 1:
                return True, "~Open prefix~"
    return False, None


def _candidate_lines_for_filter(
    filt_name: str, parsed: ParsedItem, mod_scope: str = "explicit"
) -> List[str]:
    low_name = filt_name.lower()
    is_property_filter = any(low_name.startswith(pref) for pref in _PROPERTY_PREFIXES)
    if is_property_filter:
        return list(parsed.properties)

    scope = mod_scope.lower()
    if scope == "implicit":
        return list(parsed.implicits) + list(parsed.enchants)
    if scope == "all":
        return list(parsed.explicits) + list(parsed.implicits) + list(parsed.enchants) + list(parsed.properties)
    # Default: explicit only (prevents multi-implicit false positives)
    return list(parsed.explicits)


def filter_matches_item(
    filt: Dict[str, Any],
    item_or_text: Any,
    mod_scope: str = "explicit",
    language: str = "TR",
) -> Tuple[bool, Any]:
    """Check whether a single modifier filter matches the item.

    Accepts either a ParsedItem or a raw text string (for backward compatibility).
    """
    name = str(filt.get("name") or "").strip()
    val_str = str(filt.get("value") or "").strip()
    if not name:
        return False, None

    if isinstance(item_or_text, ParsedItem):
        parsed = item_or_text
        lines = _candidate_lines_for_filter(name, parsed, mod_scope=mod_scope)
    else:
        parsed = None
        lines = [l.strip() for l in str(item_or_text).splitlines() if l.strip()]

    # Special pseudo-mods from 0ptional.txt
    low_name = name.lower()
    if parsed is not None:
        if low_name == "~open prefix~":
            return _check_open_affix("prefix", parsed)
        if low_name == "~open suffix~":
            return _check_open_affix("suffix", parsed)

    # Case 1: Empty value -> boolean / presence / fixed-value mod match
    if not val_str:
        if "#" in name:
            pattern = _compile_hash_pattern(name)
            for raw_line in lines:
                clean_line = _strip_mod_tag(raw_line)
                if pattern.search(clean_line):
                    return True, (name, raw_line)
            return False, None
        for raw_line in lines:
            clean_line = _strip_mod_tag(raw_line)
            if low_name in clean_line.lower():
                return True, (name, raw_line)
        return False, None

    # Parse numeric target values (supports int, float, negative, comma-separated)
    target_values: Optional[List[float]] = None
    try:
        parts = [x.strip() for x in val_str.split(",") if x.strip()]
        if parts:
            target_values = [float(x) for x in parts]
    except ValueError:
        target_values = None

    # Non-numeric value string fallback: substring match
    if not target_values:
        joined = "\n".join(lines).lower()
        if val_str.lower() in joined and low_name in joined:
            return True, get_text(language, "log_substring_match", val_str)
        return False, None

    # Case 2: Placeholder template with '#' (supports single & multi-value, ints & floats)
    if "#" in name:
        pattern = _compile_hash_pattern(name)
        for raw_line in lines:
            clean_line = _strip_mod_tag(raw_line)
            match = pattern.search(clean_line)
            if not match:
                continue
            found_groups = match.groups()
            check_count = min(len(found_groups), len(target_values))
            if check_count == 0:
                continue

            all_met = True
            for i in range(check_count):
                try:
                    f_val = float(found_groups[i])
                    t_val = target_values[i]
                    if f_val < t_val:
                        all_met = False
                        break
                except ValueError:
                    all_met = False
                    break

            if all_met:
                display_name = name
                for i in range(check_count):
                    display_name = display_name.replace("#", _format_num(target_values[i]), 1)
                return True, (display_name, raw_line)
        return False, None

    # Case 3: Plain modifier text + numeric threshold (supports float & int)
    thresh = target_values[0]
    for raw_line in lines:
        clean_line = _strip_mod_tag(raw_line)
        if low_name in clean_line.lower():
            nums = _NUMBER_RE.findall(clean_line)
            if not nums:
                # If user put 0 for a mod that has no numbers, treat as presence match
                if thresh == 0:
                    return True, (name, raw_line)
                continue
            for numstr in nums:
                try:
                    val_num = float(numstr)
                except ValueError:
                    continue
                if val_num >= thresh:
                    reason = get_text(
                        language, "log_thresh_match", _format_num(val_num), _format_num(thresh), name
                    )
                    return True, reason
    return False, None


@dataclass
class ColorMatchResult:
    status: str  # 'FOUND', 'CONTINUE', 'NO_SOCKET', 'NO_REQ', 'IMPOSSIBLE'
    matched: bool
    found: Dict[str, int]
    required: Dict[str, int]
    total_sockets: int
    total_required: int
    message: str = ""


def check_color_match(
    parsed: ParsedItem,
    color_targets: Dict[str, int],
    white_as_wildcard: bool = True,
    language: str = "TR",
) -> ColorMatchResult:
    req_r = int(color_targets.get("R", 0))
    req_g = int(color_targets.get("G", 0))
    req_b = int(color_targets.get("B", 0))
    req_w = int(color_targets.get("W", 0))
    req = {"R": req_r, "G": req_g, "B": req_b, "W": req_w}
    total_req = req_r + req_g + req_b + req_w

    counts = parsed.socket_counts
    total_sockets = counts.get("total", 0)

    if not parsed.sockets_raw or total_sockets == 0:
        return ColorMatchResult(
            status="NO_SOCKET",
            matched=False,
            found=dict(counts),
            required=req,
            total_sockets=0,
            total_required=total_req,
            message=get_text(language, "log_no_socket"),
        )

    if total_req == 0:
        return ColorMatchResult(
            status="NO_REQ",
            matched=False,
            found=dict(counts),
            required=req,
            total_sockets=total_sockets,
            total_required=0,
            message=get_text(language, "log_no_req"),
        )

    if total_req > total_sockets:
        return ColorMatchResult(
            status="IMPOSSIBLE",
            matched=False,
            found=dict(counts),
            required=req,
            total_sockets=total_sockets,
            total_required=total_req,
            message=get_text(language, "log_impossible_sockets", total_sockets, total_req),
        )

    c_r, c_g, c_b, c_w = counts["R"], counts["G"], counts["B"], counts["W"]
    if c_w < req_w:
        return ColorMatchResult(
            status="CONTINUE",
            matched=False,
            found=dict(counts),
            required=req,
            total_sockets=total_sockets,
            total_required=total_req,
        )

    extra_w = c_w - req_w
    deficit = max(0, req_r - c_r) + max(0, req_g - c_g) + max(0, req_b - c_b)
    matched = (deficit <= extra_w) if white_as_wildcard else (deficit == 0)

    if matched:
        return ColorMatchResult(
            status="FOUND",
            matched=True,
            found=dict(counts),
            required=req,
            total_sockets=total_sockets,
            total_required=total_req,
            message=get_text(language, "log_socket_match_detail", c_r, c_g, c_b, c_w, total_sockets),
        )

    return ColorMatchResult(
        status="CONTINUE",
        matched=False,
        found=dict(counts),
        required=req,
        total_sockets=total_sockets,
        total_required=total_req,
    )


@dataclass
class EvaluationResult:
    status: str
    # Status values:
    # 'EMPTY', 'INVALID_ITEM', 'UNMODIFIABLE', 'NO_FILTERS',
    # 'NO_SOCKET', 'NO_COLOR_REQ', 'IMPOSSIBLE_SOCKETS', 'FOUND', 'CONTINUE'
    parsed: ParsedItem
    matched_filters: List[Dict[str, Any]] = field(default_factory=list)
    log_entries: List[Tuple[str, str]] = field(default_factory=list)  # (level, message)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "matched": self.status == "FOUND",
            "summary": self.summary,
            "item": self.parsed.to_dict(),
            "matched_filters": list(self.matched_filters),
            "logs": [{"level": lvl, "text": msg} for lvl, msg in self.log_entries],
        }


def evaluate_item(
    raw_text: str,
    config: Dict[str, Any],
    check_modifiable: bool = True,
) -> EvaluationResult:
    """Evaluate a copied Path of Exile item against the current configuration."""
    lang = str(config.get("language", "TR")).upper()
    cleaned = (raw_text or "").strip()
    if not cleaned:
        return EvaluationResult(status="EMPTY", parsed=ParsedItem())

    parsed = parse_item_text(cleaned)
    logs: List[Tuple[str, str]] = [("dim", get_text(lang, "log_checking"))]

    if not parsed.is_valid_poe_item:
        logs.append(("error", get_text(lang, "log_invalid_item")))
        return EvaluationResult(
            status="INVALID_ITEM",
            parsed=parsed,
            log_entries=logs,
            summary=get_text(lang, "log_invalid_item"),
        )

    if check_modifiable and (parsed.is_corrupted or parsed.is_mirrored or parsed.is_unidentified):
        msg = get_text(lang, "log_corrupted_item")
        logs.append(("error", msg))
        return EvaluationResult(status="UNMODIFIABLE", parsed=parsed, log_entries=logs, summary=msg)

    mode = str(config.get("search_mode", "attribute")).lower()

    if mode == "color":
        res = check_color_match(
            parsed,
            config.get("color_targets", {}),
            white_as_wildcard=bool(config.get("white_as_wildcard", True)),
            language=lang,
        )
        if res.status == "FOUND":
            msg = get_text(lang, "log_color_match", res.message)
            logs.append(("success", msg))
            return EvaluationResult(status="FOUND", parsed=parsed, log_entries=logs, summary=msg)
        if res.status == "IMPOSSIBLE":
            logs.append(("error", res.message))
            return EvaluationResult(
                status="IMPOSSIBLE_SOCKETS", parsed=parsed, log_entries=logs, summary=res.message
            )
        if res.status == "NO_REQ":
            msg = get_text(lang, "log_no_color_req")
            logs.append(("warning", msg))
            return EvaluationResult(status="NO_COLOR_REQ", parsed=parsed, log_entries=logs, summary=msg)
        if res.status == "NO_SOCKET":
            logs.append(("warning", res.message))
            return EvaluationResult(status="NO_SOCKET", parsed=parsed, log_entries=logs, summary=res.message)

        logs.append(("info", get_text(lang, "log_color_fail")))
        logs.append(("mod", get_text(lang, "log_saw", f"Sockets: {parsed.sockets_raw}")))
        return EvaluationResult(
            status="CONTINUE",
            parsed=parsed,
            log_entries=logs,
            summary=f"Sockets: {parsed.sockets_raw}",
        )

    # Attribute / Modifier mode
    all_filters = config.get("filters", [])
    active_filters = [f for f in all_filters if f.get("active", True)]
    if not active_filters:
        msg = get_text(lang, "log_no_active_filters")
        logs.append(("warning", msg))
        return EvaluationResult(status="NO_FILTERS", parsed=parsed, log_entries=logs, summary=msg)

    mod_scope = str(config.get("mod_scope", "explicit")).lower()
    filter_logic = str(config.get("filter_logic", "OR")).upper()

    # Log visible mods according to scope
    if mod_scope == "implicit":
        visible_mods = parsed.implicits + parsed.enchants
    elif mod_scope == "all":
        visible_mods = parsed.enchants + parsed.implicits + parsed.explicits
    else:
        visible_mods = parsed.explicits

    for mod_line in visible_mods:
        logs.append(("mod", mod_line))

    matched_list: List[Dict[str, Any]] = []
    for f in active_filters:
        ok, result = filter_matches_item(f, parsed, mod_scope=mod_scope, language=lang)
        if ok:
            if isinstance(result, tuple):
                req_text, found_text = result
                detail = get_text(lang, "log_match_simplified", req_text, found_text)
            else:
                detail = get_text(lang, "log_matched", f.get("name", "?"), f.get("value", ""), result)
            matched_list.append({"filter": f, "detail": detail})

            if filter_logic == "OR":
                logs.append(("success", detail))
                return EvaluationResult(
                    status="FOUND",
                    parsed=parsed,
                    matched_filters=matched_list,
                    log_entries=logs,
                    summary=detail,
                )

    if filter_logic == "AND":
        if len(matched_list) == len(active_filters):
            for m in matched_list:
                logs.append(("success", m["detail"]))
            summary = get_text(lang, "log_and_matched", len(active_filters))
            logs.append(("success", summary))
            return EvaluationResult(
                status="FOUND",
                parsed=parsed,
                matched_filters=matched_list,
                log_entries=logs,
                summary=summary,
            )
        elif matched_list:
            logs.append(("info", get_text(lang, "log_and_partial", len(matched_list), len(active_filters))))

    return EvaluationResult(status="CONTINUE", parsed=parsed, matched_filters=matched_list, log_entries=logs)
