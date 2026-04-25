"""
MedLens AI — timeline_engine.py
Generate a 24-hour medication schedule timeline from frequency tokens.

Frequency → scheduled dose times:
  OD       → 08:00
  BD       → 08:00, 20:00
  TDS      → 08:00, 14:00, 20:00
  QID      → 08:00, 12:00, 16:00, 20:00
  HS       → 22:00
  BBF      → 07:30
  AC       → 07:30, 13:30, 19:30  (30 min before each meal)
  AF/PC    → 08:30, 14:30, 20:30  (30 min after each meal)
  SOS/PRN  → as needed (no fixed schedule)
  WEEKLY   → 08:00 (day 1 marker only)
  Indian notation 1-0-1 → 08:00, 20:00
  Indian notation 1-1-1 → 08:00, 14:00, 20:00

Also computes conflict_windows for temporal drug-drug conflicts.
"""
from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Optional, Tuple

from app.utils.helpers import get_logger

logger = get_logger("TIMELINE")


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ── Frequency → times map ──────────────────────────────────────────────────────

_FREQ_TIMES: Dict[str, List[str]] = {
    # Standard tokens
    "OD":           ["08:00"],
    "ONCE DAILY":   ["08:00"],
    "BD":           ["08:00", "20:00"],
    "TWICE DAILY":  ["08:00", "20:00"],
    "TDS":          ["08:00", "14:00", "20:00"],
    "THRICE DAILY": ["08:00", "14:00", "20:00"],
    "QID":          ["08:00", "12:00", "16:00", "20:00"],
    "FOUR TIMES DAILY": ["08:00", "12:00", "16:00", "20:00"],
    "HS":           ["22:00"],
    "AT NIGHT":     ["22:00"],
    "AT BEDTIME":   ["22:00"],
    "BBF":          ["07:30"],
    "AC":           ["07:30", "13:30", "19:30"],
    "BEFORE FOOD":  ["07:30", "13:30", "19:30"],
    "AF":           ["08:30", "14:30", "20:30"],
    "AFTER FOOD":   ["08:30", "14:30", "20:30"],
    "SOS":          [],  # as needed
    "PRN":          [],
    "WEEKLY":       ["08:00"],
    "ONCE WEEKLY":  ["08:00"],
    # Indian notation
    "1-0-0":        ["08:00"],
    "0-0-1":        ["22:00"],
    "1-0-1":        ["08:00", "20:00"],
    "0-1-0":        ["14:00"],
    "1-1-0":        ["08:00", "14:00"],
    "0-1-1":        ["14:00", "20:00"],
    "1-1-1":        ["08:00", "14:00", "20:00"],
    # Descriptive expansions from dosage_parser
    "MORNING ONLY":               ["08:00"],
    "NIGHT ONLY":                 ["22:00"],
    "MORNING + NIGHT":            ["08:00", "20:00"],
    "MORNING + AFTERNOON":        ["08:00", "14:00"],
    "AFTERNOON + NIGHT":          ["14:00", "20:00"],
    "AFTERNOON ONLY":             ["14:00"],
    "THRICE DAILY (MORNING + AFTERNOON + NIGHT)": ["08:00", "14:00", "20:00"],
}

# ── Time utility ───────────────────────────────────────────────────────────────

def _time_to_minutes(t: str) -> int:
    """Convert 'HH:MM' to minutes since midnight."""
    h, m = map(int, t.split(":"))
    return h * 60 + m


def _minutes_to_time(minutes: int) -> str:
    h = (minutes % 1440) // 60
    m = (minutes % 1440) % 60
    return f"{h:02d}:{m:02d}"


# ── Frequency resolver ────────────────────────────────────────────────────────

_INDIAN_RE = re.compile(r"^(\d)[-–](\d)[-–](\d)$")


def _resolve_frequency(freq_token: str) -> Tuple[List[str], bool]:
    """
    Map a frequency token to a list of scheduled times.

    Returns:
        (times_list, is_as_needed)
    """
    upper = freq_token.upper().strip()

    # Direct lookup
    if upper in _FREQ_TIMES:
        times = _FREQ_TIMES[upper]
        return times, len(times) == 0

    # Indian notation e.g. "1-0-1"
    m = _INDIAN_RE.match(upper)
    if m:
        morning, afternoon, night = m.groups()
        times = []
        if morning != "0":
            times.append("08:00")
        if afternoon != "0":
            times.append("14:00")
        if night != "0":
            times.append("20:00")
        return times, False

    # Partial match for aliases
    for key, times in _FREQ_TIMES.items():
        if key in upper or upper in key:
            return times, len(times) == 0

    # Default: once daily
    logger.debug(f"[{_ts()}] [TIMELINE] Unknown frequency '{freq_token}' — defaulting to OD")
    return ["08:00"], False


# ── Timeline entry builder ────────────────────────────────────────────────────

def _build_entries(med: Dict[str, Any]) -> List[Dict[str, Any]]:
    drug_name = med.get("DrugName", "Unknown")
    freq_token = med.get("Frequency", "OD")
    dose_value = med.get("DoseValue", "")
    dose_unit = med.get("DoseUnit", "")
    dose_str = f"{dose_value} {dose_unit}".strip() if dose_value else "as prescribed"

    times, as_needed = _resolve_frequency(freq_token)

    if as_needed:
        return [{
            "drug_name": drug_name,
            "time_24h": "SOS",
            "dose": dose_str,
            "frequency_token": freq_token,
            "as_needed": True,
        }]

    return [
        {
            "drug_name": drug_name,
            "time_24h": t,
            "dose": dose_str,
            "frequency_token": freq_token,
            "as_needed": False,
        }
        for t in times
    ]


# ── Conflict window detection ─────────────────────────────────────────────────

def _compute_conflict_windows(
    timeline: List[Dict[str, Any]],
    temporal_conflicts: List[Dict[str, Any]],
    overlap_minutes: int = 60,
) -> List[Dict[str, Any]]:
    """
    For each temporal conflict pair, find timeline slots where both drugs
    are scheduled within `overlap_minutes` of each other.
    """
    windows: List[Dict[str, Any]] = []

    # Build drug → times index
    drug_times: Dict[str, List[int]] = {}
    for entry in timeline:
        dn = entry["drug_name"].lower()
        t = entry.get("time_24h", "")
        if t and t != "SOS":
            drug_times.setdefault(dn, []).append(_time_to_minutes(t))

    from rapidfuzz import fuzz as rfuzz

    for conflict in temporal_conflicts:
        if not conflict.get("temporal_flag"):
            continue

        a = conflict.get("drug_a", "").lower()
        b = conflict.get("drug_b", "").lower()

        # Fuzzy match drug names to timeline keys
        a_key = next((k for k in drug_times if rfuzz.partial_ratio(a, k) >= 82), None)
        b_key = next((k for k in drug_times if rfuzz.partial_ratio(b, k) >= 82), None)

        if not a_key or not b_key:
            continue

        for t_a in drug_times.get(a_key, []):
            for t_b in drug_times.get(b_key, []):
                if abs(t_a - t_b) <= overlap_minutes:
                    start = min(t_a, t_b)
                    end = max(t_a, t_b) + 30  # add 30-min buffer
                    windows.append({
                        "start_time": _minutes_to_time(start),
                        "end_time": _minutes_to_time(end),
                        "drug_a": conflict["drug_a"],
                        "drug_b": conflict["drug_b"],
                        "conflict_type": conflict.get("severity", "MODERATE"),
                        "time_separation_required": conflict.get("time_separation", ""),
                    })

    return windows


# ── Public API ────────────────────────────────────────────────────────────────

def generate_timeline(
    medications: List[Dict[str, Any]],
    temporal_conflicts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Generate a 24-hour timeline for a prescription.

    Args:
        medications       : list of medication dicts (DrugName, Frequency, DoseValue, DoseUnit)
        temporal_conflicts: list of conflict dicts from conflict_detector (optional)

    Returns:
        {
          timeline: sorted list of {drug_name, time_24h, dose, frequency_token, as_needed},
          as_needed_drugs: list of drug names with SOS/PRN scheduling,
          conflict_windows: list of overlap windows,
          total_doses_per_day: int,
        }
    """
    logger.info(f"[{_ts()}] [TIMELINE] Generating timeline for {len(medications)} medications")

    all_entries: List[Dict[str, Any]] = []
    as_needed: List[str] = []

    for med in medications:
        entries = _build_entries(med)
        for e in entries:
            if e.get("as_needed"):
                as_needed.append(e["drug_name"])
            else:
                all_entries.append(e)

    # Sort by time
    all_entries.sort(key=lambda e: _time_to_minutes(e["time_24h"]) if e["time_24h"] != "SOS" else 9999)

    conflict_windows: List[Dict[str, Any]] = []
    if temporal_conflicts:
        conflict_windows = _compute_conflict_windows(all_entries, temporal_conflicts)

    logger.info(
        f"[{_ts()}] [TIMELINE] {len(all_entries)} scheduled entries, "
        f"{len(as_needed)} SOS drugs, {len(conflict_windows)} conflict windows"
    )

    return {
        "timeline": all_entries,
        "as_needed_drugs": as_needed,
        "conflict_windows": conflict_windows,
        "total_doses_per_day": len(all_entries),
    }
