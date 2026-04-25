"""
MedLens AI — drug_food_warnings.py
Automatic drug-food interaction surface layer.
Uses indian_drug_index.json for lookups.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from rapidfuzz import fuzz

from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger("FOOD_WARN")

# ── DB loader ─────────────────────────────────────────────────────────────────

_drug_index: List[Dict] = []

def _load_db():
    global _drug_index
    if not _drug_index:
        path = os.path.join(os.path.dirname(settings.INTERACTION_DB_PATH), "indian_drug_index.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                _drug_index = data
            else:
                _drug_index = data.get("drugs", [])
            logger.info(f"[FOOD_WARNINGS] Loaded {len(_drug_index)} drugs from index")

_load_db()

def _fuzzy_find_drug(name: str) -> dict | None:
    normalized = name.lower().strip()
    for drug in _drug_index:
        all_names = (
            [drug["brand"].lower(), drug["generic"].lower()] +
            [a.lower() for a in drug.get("aliases", [])] +
            [b.lower() for b in drug.get("indian_brands", [])]
        )
        scores = [fuzz.token_sort_ratio(normalized, n) for n in all_names]
        if max(scores) >= 75:
            return drug
    return None

def get_food_warnings(drug_names: list[str]) -> list[dict]:
    """
    For each drug name, fuzzy-match against indian_drug_index.json.
    Return all food_interactions[] entries from matched drugs.
    """
    _load_db()
    
    warnings = []
    for drug_name in drug_names:
        matched_drug = _fuzzy_find_drug(drug_name)  # returns drug dict or None
        if matched_drug:
            food_interactions = matched_drug.get("food_interactions", [])
            if food_interactions:
                for fi in food_interactions:
                    warnings.append({
                        "drug_name": matched_drug["brand"],
                        "generic_name": matched_drug["generic"],
                        "food_item": fi["food_item"],
                        "interaction_type": fi["interaction_type"],
                        "severity": fi["severity"],
                        "recommendation": fi["recommendation"]
                    })
            else:
                # No specific food interactions in DB for this drug
                warnings.append({
                    "drug_name": matched_drug["brand"],
                    "generic_name": matched_drug["generic"],
                    "food_item": "None known",
                    "interaction_type": "unknown",
                    "severity": "SAFE",
                    "recommendation": f"No specific food interactions recorded for {matched_drug['brand']}."
                })
        else:
            # Drug not in index — return generic safe message
            warnings.append({
                "drug_name": drug_name,
                "generic_name": drug_name,
                "food_item": "No data available",
                "interaction_type": "unknown",
                "severity": "UNKNOWN",
                "recommendation": "Consult pharmacist for food interactions with this medication"
            })
            logger.warning(f"[FOOD_WARNINGS] Drug not in index: {drug_name}")
    
    logger.info(f"[FOOD_WARNINGS] {len(warnings)} warnings for {len(drug_names)} drugs")
    return warnings

