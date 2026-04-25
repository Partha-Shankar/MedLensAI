"""
MedLens AI — dosage_parser.py
Extract structured dosage fields from a medicine text line.

Two parallel extraction layers:
  1. Regex layer   — pattern-based, fast, handles Indian notation
  2. NLP layer     — scispaCy + medspaCy NER

Conflict resolution: regex wins when both produce a value.
Missing values → "MISSING" (never None / null).

Extracted fields:
  DrugName, DoseValue, DoseUnit, Frequency, Duration, Route, AdminInstructions
"""
from __future__ import annotations

import re
import datetime
from typing import Dict, Optional

from app.utils.helpers import get_logger

logger = get_logger("DOSAGE_PARSER")

MISSING = "MISSING"


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ═══════════════════════════════════════════════════════════════════════════════
#  REGEX LAYER
# ═══════════════════════════════════════════════════════════════════════════════

# ── Drug name prefix ──────────────────────────────────────────────────────────
_PREFIX_RE = re.compile(
    r"^(?P<route_prefix>Tab|Cap|Inj|Syr|Drops?|Oint|Gel|Susp|Syp|Cream|Lotion|Sachet|Patch|Inhaler)\s+",
    re.IGNORECASE,
)

_DRUG_NAME_RE = re.compile(
    r"^(?:Tab|Cap|Inj|Syr|Drops?|Oint|Gel|Susp|Syp|Cream|Lotion|Sachet|Patch|Inhaler)?\s*"
    r"(?P<drug>[A-Za-z][A-Za-z0-9\-\+\s]{1,40}?)"
    r"(?=\s+\d|\s+\(|\s*$|\s+[A-Z]{2,4}\b)",
    re.IGNORECASE,
)

# ── Dose value + unit ─────────────────────────────────────────────────────────
_DOSE_RE = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|µg|g|ml|mL|IU|units?|%)",
    re.IGNORECASE,
)

# ── Route of administration ───────────────────────────────────────────────────
_ROUTE_RE = re.compile(
    r"\b(?P<route>oral|IV|IM|SC|topical|inhalation|sublingual|intrathecal|intravitreal|transdermal|rectal)\b",
    re.IGNORECASE,
)
_ROUTE_FROM_PREFIX = {
    "tab": "oral", "cap": "oral", "syr": "oral", "syp": "oral",
    "susp": "oral", "drops": "topical", "oint": "topical",
    "gel": "topical", "cream": "topical", "lotion": "topical",
    "inj": "parenteral", "patch": "transdermal", "inhaler": "inhalation",
    "sachet": "oral",
}

# ── Frequency ─────────────────────────────────────────────────────────────────
# Indian notation first (1-0-1 etc.), then named tokens
_INDIAN_FREQ_RE = re.compile(
    r"\b(?P<indian>\d[-–]\d[-–]\d)\b"
)
_FREQ_TOKEN_RE = re.compile(
    r"\b(?P<freq>OD|BD|TDS|QID|HS|SOS|PRN|BBF|AF|"
    r"once daily|twice daily|thrice daily|four times daily|"
    r"once weekly|weekly|twice weekly|alternate days?|"
    r"at night|at bedtime|morning and night|1\s+tablet\s+at\s+night)\b",
    re.IGNORECASE,
)

_PRN_FREQ_RE = re.compile(
    r"\b(?:if|when)\s+(?P<condition>fever|pain|needed|required|necessary)\b",
    re.IGNORECASE,
)

_HOURLY_FREQ_RE = re.compile(
    r"\bevery\s+(?P<h1>\d+)(?:[-–](?P<h2>\d+))?\s+hours?\b",
    re.IGNORECASE,
)

_INDIAN_FREQ_MAP = {
    "1-0-0": "morning only",
    "0-0-1": "night only",
    "1-0-1": "morning + night",
    "1-1-0": "morning + afternoon",
    "1-1-1": "thrice daily (morning + afternoon + night)",
    "0-1-1": "afternoon + night",
    "0-1-0": "afternoon only",
}

_DURATION_RE = re.compile(
    r"(?:x|for|×)\s*(?P<duration>\d+\s*(?:days?|weeks?|months?|years?))",
    re.IGNORECASE,
)

_MAX_DOSE_RE = re.compile(
    r"\bmaximum\s+(?P<max_tabs>\d+)\s+tablets?/day\b",
    re.IGNORECASE,
)

# ── Admin instructions ────────────────────────────────────────────────────────
_ADMIN_RE = re.compile(
    r"\b(?P<admin>"
    r"1\s+tablet\s+after\s+food|after\s+food|before\s+food|with\s+food|empty\s+stomach|"
    r"before\s+breakfast|with\s+milk|with\s+water|at\s+bedtime|on\s+waking|"
    r"weekly|once\s+weekly|every\s+\d+\s+(?:hours?|days?)|"
    r"taper|tapering\s+schedule|as\s+directed|as\s+needed"
    r")\b",
    re.IGNORECASE,
)


def _regex_parse(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {
        "DrugName": MISSING,
        "DoseValue": MISSING,
        "DoseUnit": MISSING,
        "Frequency": MISSING,
        "Duration": MISSING,
        "Route": MISSING,
        "AdminInstructions": MISSING,
    }

    # Route from prefix
    prefix_m = _PREFIX_RE.match(text)
    if prefix_m:
        prefix = prefix_m.group("route_prefix").lower()
        result["Route"] = _ROUTE_FROM_PREFIX.get(prefix, MISSING)

    # Drug name
    drug_m = _DRUG_NAME_RE.match(text)
    if drug_m:
        result["DrugName"] = drug_m.group("drug").strip().title()

    # Dose
    dose_m = _DOSE_RE.search(text)
    if dose_m:
        result["DoseValue"] = dose_m.group("value")
        result["DoseUnit"] = dose_m.group("unit").lower()

    # Route override from text body
    route_m = _ROUTE_RE.search(text)
    if route_m:
        result["Route"] = route_m.group("route").lower()

    # Frequency — Indian notation first
    indian_m = _INDIAN_FREQ_RE.search(text)
    hourly_m = _HOURLY_FREQ_RE.search(text)
    prn_m = _PRN_FREQ_RE.search(text)
    
    freq_str = ""
    
    if indian_m:
        raw = indian_m.group("indian").replace("–", "-")
        mapped = _INDIAN_FREQ_MAP.get(raw, raw)
        freq_str = mapped
        logger.info(f"[{_ts()}] [DOSAGE_PARSER] Frequency \"{raw}\" → {mapped}")
    elif hourly_m:
        h1 = hourly_m.group("h1")
        h2 = hourly_m.group("h2")
        if h2:
            freq_str = f"Q{h1}-{h2}H"
            logger.info(f"[{_ts()}] [DOSAGE_PARSER] Frequency \"every {h1}-{h2} hours\" → {freq_str}")
        else:
            freq_str = f"Q{h1}H"
            logger.info(f"[{_ts()}] [DOSAGE_PARSER] Frequency \"every {h1} hours\" → {freq_str}")
    else:
        freq_m = _FREQ_TOKEN_RE.search(text)
        if freq_m:
            raw_freq = freq_m.group("freq").lower()
            if "night" in raw_freq:
                freq_str = "HS"
            else:
                freq_str = freq_m.group("freq").upper()

    if prn_m:
        cond = prn_m.group("condition").lower()
        suffix = f"PRN {cond}"
        if freq_str:
            freq_str = f"{freq_str} {suffix}"
        else:
            freq_str = suffix
        logger.info(f"[{_ts()}] [DOSAGE_PARSER] PRN condition → {suffix}")

    if freq_str:
        result["Frequency"] = freq_str

    # Duration
    dur_m = _DURATION_RE.search(text)
    if dur_m:
        result["Duration"] = dur_m.group("duration").strip()

    # Admin instructions
    admin_insts = []
    
    admin_m = _ADMIN_RE.search(text)
    if admin_m:
        raw_admin = admin_m.group("admin").lower()
        if "after food" in raw_admin:
            admin_insts.append("after food")
        elif "before breakfast" in raw_admin:
            admin_insts.append("before breakfast / AC")
        else:
            admin_insts.append(raw_admin)
            
    max_m = _MAX_DOSE_RE.search(text)
    if max_m:
        max_tabs = max_m.group("max_tabs")
        admin_insts.append(f"max {max_tabs} tabs/day")
        
    if admin_insts:
        result["AdminInstructions"] = " ".join(admin_insts)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  NLP LAYER (scispaCy + medspaCy)
# ═══════════════════════════════════════════════════════════════════════════════

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        import medspacy
        _nlp = spacy.load("en_core_sci_sm")
        _nlp.add_pipe("medspacy_context")
        logger.info(f"[{_ts()}] [DOSAGE_PARSER] scispaCy + medspaCy loaded")
    except Exception as exc:
        logger.warning(f"[{_ts()}] [DOSAGE_PARSER] NLP load failed ({exc}) — regex-only mode")
        _nlp = None
    return _nlp


def _nlp_parse(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {k: MISSING for k in [
        "DrugName", "DoseValue", "DoseUnit",
        "Frequency", "Duration", "Route", "AdminInstructions",
    ]}
    nlp = _get_nlp()
    if nlp is None:
        return result

    try:
        doc = nlp(text)
        for ent in doc.ents:
            label = ent.label_.upper()
            val = ent.text.strip()
            if label in ("CHEMICAL", "DRUG", "MEDICATION") and result["DrugName"] == MISSING:
                result["DrugName"] = val.title()
            elif label in ("DOSAGE",) and result["DoseValue"] == MISSING:
                dose_m = _DOSE_RE.search(val)
                if dose_m:
                    result["DoseValue"] = dose_m.group("value")
                    result["DoseUnit"] = dose_m.group("unit").lower()
            elif label in ("FREQUENCY",) and result["Frequency"] == MISSING:
                result["Frequency"] = val
            elif label in ("DURATION",) and result["Duration"] == MISSING:
                result["Duration"] = val
            elif label in ("ROUTE",) and result["Route"] == MISSING:
                result["Route"] = val.lower()
    except Exception as exc:
        logger.warning(f"[{_ts()}] [DOSAGE_PARSER] NLP parse error: {exc}")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  MERGE: regex wins on conflict
# ═══════════════════════════════════════════════════════════════════════════════

def _merge(regex_result: Dict, nlp_result: Dict) -> Dict:
    merged = {}
    for key in regex_result:
        r_val = regex_result[key]
        n_val = nlp_result.get(key, MISSING)
        # Prefer regex; fall back to NLP; final fallback is MISSING
        if r_val != MISSING:
            merged[key] = r_val
        elif n_val != MISSING:
            merged[key] = n_val
        else:
            merged[key] = MISSING
    return merged


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def parse_dosage(text: str) -> Dict[str, str]:
    """
    Parse a single medicine text line into structured fields.

    Args:
        text: raw OCR text of one prescription line

    Returns:
        dict with keys: DrugName, DoseValue, DoseUnit, Frequency,
                        Duration, Route, AdminInstructions
        All missing values are the string "MISSING".
    """
    logger.info(f"[{_ts()}] [DOSAGE_PARSER] Parsing: \"{text}\"")

    regex_result = _regex_parse(text)
    nlp_result   = _nlp_parse(text)
    merged       = _merge(regex_result, nlp_result)

    missing_fields = [k for k, v in merged.items() if v == MISSING]
    if missing_fields:
        logger.debug(
            f"[{_ts()}] [DOSAGE_PARSER] Missing fields after parse: {missing_fields}"
        )

    return merged
