"""
MedLens AI — drug_corrector.py
Triple-source drug name correction pipeline.

For every DRUG_CANDIDATE token, three lookups run concurrently via asyncio:
  1. RxNorm spelling suggestions API  (score +3 for rank-1 hit)
  2. RapidFuzz against local indian_drug_index.json (score +2 if ≥ 80)
  3. RxNorm approximate match endpoint (score +1 for any hit)

Candidate with highest combined score wins.
If all scores == 0, token is marked LOW_CONFIDENCE → review queue.

Also corrects common OCR corruptions before lookup:
  rn → m,  l → 1 (reversed),  0 → O, | → I
"""
from __future__ import annotations

import asyncio
import datetime
import json
import os
import re
from typing import Dict, List, Optional, Tuple

import requests
from rapidfuzz import process as fuzz_process, fuzz
from rapidfuzz.distance import Levenshtein

from app.core.config import settings
from app.utils.helpers import get_logger, apply_ocr_corrections, normalise_drug_token

logger = get_logger("DRUG_CORRECTOR")

# ── Drug index (loaded once) ───────────────────────────────────────────────────

_drug_index: List[str] = []


def _load_drug_index() -> List[str]:
    global _drug_index
    if _drug_index:
        return _drug_index
    path = settings.DRUG_INDEX_PATH
    if not os.path.exists(path):
        logger.warning(f"[DRUG_CORRECTOR] Drug index not found at {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    drugs_list = data if isinstance(data, list) else data.get("drugs", [])
    
    entries: List[str] = []
    for drug in drugs_list:
        if isinstance(drug, dict):
            entries.append(drug.get("brand", ""))
            entries.append(drug.get("generic", ""))
    _drug_index = [e for e in entries if e]
    logger.info(f"[DRUG_CORRECTOR] Loaded {len(_drug_index)} drug name entries")
    return _drug_index


_load_drug_index()


# ── Timestamp ─────────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ── OCR pre-correction ────────────────────────────────────────────────────────

_OCR_PATTERNS: List[Tuple[str, str]] = [
    (r"\brn\b", "m"),
    (r"(?<=[a-zA-Z])1(?=[a-zA-Z])", "l"),
    (r"(?<=[a-zA-Z])0(?=[a-zA-Z])", "O"),
    (r"\|", "I"),
]


def _pre_correct(token: str) -> str:
    for pattern, replacement in _OCR_PATTERNS:
        token = re.sub(pattern, replacement, token)
    return apply_ocr_corrections(token)


# ── Lookup 1: RxNorm spelling suggestions ─────────────────────────────────────

def _rxnorm_spelling(token: str) -> Tuple[Optional[str], int]:
    """Returns (best_suggestion, score).  score=3 if rank-1, 0 if none."""
    url = "https://rxnav.nlm.nih.gov/REST/spellingsuggestions.json"
    try:
        resp = requests.get(url, params={"name": token}, timeout=4)
        if resp.status_code != 200:
            return None, 0
        data = resp.json()
        suggestions = (
            data.get("suggestionGroup", {})
                .get("suggestionList", {})
                .get("suggestion", [])
        )
        if suggestions:
            return suggestions[0], 3
    except Exception as exc:
        logger.debug(f"[{_ts()}] [DRUG_CORRECTOR] RxNorm spelling error: {exc}")
    return None, 0


# ── Lookup 2: RapidFuzz local index ──────────────────────────────────────────

def _rapidfuzz_lookup(token: str) -> Tuple[Optional[str], int]:
    """Returns (best_match, score).  score=2 if similarity ≥ 80, else 0."""
    index = _load_drug_index()
    if not index:
        return None, 0
    result = fuzz_process.extractOne(
        token, index,
        scorer=fuzz.WRatio,
        score_cutoff=settings.RAPIDFUZZ_DRUG_THRESHOLD,
    )
    if result:
        match, similarity, _ = result
        logger.info(
            f"[{_ts()}] [DRUG_CORRECTOR] \"{token}\" → \"{match}\" via RapidFuzz score {int(similarity)}"
        )
        return match, 2
    return None, 0


# ── Lookup 3: RxNorm approximate match ────────────────────────────────────────

def _rxnorm_approx(token: str) -> Tuple[Optional[str], int]:
    """Returns (best_match, score).  score=1 if any hit, 0 if none."""
    url = "https://rxnav.nlm.nih.gov/REST/approximateTerm.json"
    try:
        resp = requests.get(url, params={"term": token, "maxEntries": 1}, timeout=4)
        if resp.status_code != 200:
            return None, 0
        data = resp.json()
        candidates = (
            data.get("approximateGroup", {})
                .get("candidate", [])
        )
        if candidates:
            name = candidates[0].get("name", None)
            if name:
                return name, 1
    except Exception as exc:
        logger.debug(f"[{_ts()}] [DRUG_CORRECTOR] RxNorm approx error: {exc}")
    return None, 0


# ── Async runner ──────────────────────────────────────────────────────────────

async def _correct_token_async(token: str) -> Dict:
    """Run all three lookups concurrently."""
    loop = asyncio.get_event_loop()

    spelling_fut = loop.run_in_executor(None, _rxnorm_spelling, token)
    fuzzy_fut    = loop.run_in_executor(None, _rapidfuzz_lookup, token)
    approx_fut   = loop.run_in_executor(None, _rxnorm_approx, token)

    (spell_name, spell_score), (fuzz_name, fuzz_score), (approx_name, approx_score) = (
        await asyncio.gather(spelling_fut, fuzzy_fut, approx_fut)
    )

    # Build candidate table
    candidates = []
    if spell_name:
        candidates.append((spell_name, spell_score, "rxnorm_api"))
    if fuzz_name:
        candidates.append((fuzz_name, fuzz_score, "rapidfuzz_local"))
    if approx_name:
        candidates.append((approx_name, approx_score, "rxnorm_api"))

    if not candidates:
        logger.warning(
            f"[{_ts()}] [DRUG_CORRECTOR] \"{token}\" — no match found (LOW_CONFIDENCE)"
        )
        return {
            "original": token,
            "corrected": token,
            "source": "none",
            "score": 0,
            "low_confidence": True,
            "correction_trace": {
                "raw_ocr_text": token,
                "matched_drug": token,
                "method": "exact",
                "rapidfuzz_score": 0.0,
                "levenshtein_distance": 0,
                "candidate_shortlist": [],
                "correction_applied": False
            }
        }

    # Pick highest-scoring candidate
    best = max(candidates, key=lambda c: c[1])
    corrected, score, source = best
    
    correction_applied = token.lower() != corrected.lower()
    
    # Calculate RapidFuzz and Levenshtein explicitly against the chosen corrected name
    rf_score = fuzz.WRatio(token, corrected)
    lev_dist = Levenshtein.distance(token.lower(), corrected.lower())
    
    index = _load_drug_index()
    shortlist_cands = fuzz_process.extract(token, index, scorer=fuzz.WRatio, limit=3) if index else []
    
    shortlist = [
        {
            "name": c[0],
            "rapidfuzz_score": round(c[1], 1),
            "levenshtein_distance": Levenshtein.distance(token.lower(), c[0].lower())
        }
        for c in shortlist_cands
    ]
    
    logger.info(
        f"[{_ts()}] [DRUG_CORRECTOR] \"{token}\" → \"{corrected}\" | "
        f"RapidFuzz={rf_score:.0f} | Levenshtein={lev_dist} | "
        f"method={source}"
    )
    if shortlist:
        logger.info(
            f"[{_ts()}] [DRUG_CORRECTOR] Shortlist: " +
            " | ".join([f"{c['name']}({c['rapidfuzz_score']:.0f},d={c['levenshtein_distance']})" for c in shortlist])
        )
    
    if not correction_applied:
        logger.info(f"[{_ts()}] [DRUG_CORRECTOR] \"{token}\" — exact match, no correction needed | distance=0")

    return {
        "original": token,
        "corrected": corrected,
        "source": source,
        "score": score,
        "low_confidence": False,
        "correction_trace": {
            "raw_ocr_text": token,
            "matched_drug": corrected,
            "method": source,
            "rapidfuzz_score": round(rf_score, 1),
            "levenshtein_distance": lev_dist,
            "candidate_shortlist": shortlist,
            "correction_applied": correction_applied
        }
    }


# ── Public API ────────────────────────────────────────────────────────────────

def correct_drug_name(raw_token: str) -> Dict:
    """
    Synchronous wrapper — corrects a single drug token.
    Runs OCR pre-correction then async triple lookup.
    """
    pre = _pre_correct(raw_token)
    normalised = normalise_drug_token(pre)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Inside async context (FastAPI request handler)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _correct_token_async(normalised))
                return future.result(timeout=10)
        else:
            return loop.run_until_complete(_correct_token_async(normalised))
    except Exception as exc:
        logger.error(f"[{_ts()}] [DRUG_CORRECTOR] Correction failed for '{raw_token}': {exc}")
        return {
            "original": raw_token,
            "corrected": raw_token,
            "source": "error",
            "score": 0,
            "low_confidence": True,
        }


async def correct_drug_names_batch(tokens: List[str]) -> List[Dict]:
    """Correct a list of drug tokens concurrently."""
    pre_corrected = [normalise_drug_token(_pre_correct(t)) for t in tokens]
    tasks = [_correct_token_async(t) for t in pre_corrected]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for token, res in zip(tokens, results):
        if isinstance(res, Exception):
            output.append({
                "original": token,
                "corrected": token,
                "source": "error",
                "score": 0,
                "low_confidence": True,
            })
        else:
            output.append(res)
    return output
