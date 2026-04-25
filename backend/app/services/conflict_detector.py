"""
MedLens AI — conflict_detector.py
Drug-drug interaction detection from local interaction_database.json.
Uses fuzzy matching and brand-to-generic resolution.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from rapidfuzz import fuzz, process

from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger("CONFLICT")

def _normalize(name: str) -> str:
    return name.lower().strip()

# ── DB loaders ─────────────────────────────────────────────────────────────────

_interaction_db: List[Dict] = []
_drug_index: List[Dict] = []

def _load_dbs():
    global _interaction_db, _drug_index
    
    # Load interactions
    if not _interaction_db:
        path = settings.INTERACTION_DB_PATH
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                _interaction_db = data
            else:
                _interaction_db = data.get("interactions", [])
            logger.info(f"[CONFLICT] Loaded {len(_interaction_db)} interactions")
            
    # Load drug index
    if not _drug_index:
        path = os.path.join(os.path.dirname(settings.INTERACTION_DB_PATH), "indian_drug_index.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                _drug_index = data
            else:
                _drug_index = data.get("drugs", [])
            logger.info(f"[CONFLICT] Loaded {len(_drug_index)} drugs from index")

_load_dbs()

def resolve_generic(brand_name: str) -> str:
    """Look up brand in drug index, return generic if found, else return original"""
    normalized = _normalize(brand_name)
    for drug in _drug_index:
        all_names = [_normalize(drug["brand"])] + [_normalize(a) for a in drug.get("aliases", [])]
        # Also check generic name itself
        all_names.append(_normalize(drug["generic"]))
        if any(fuzz.token_sort_ratio(normalized, n) >= 85 for n in all_names):
            return drug["generic"]
    return brand_name

def find_interactions(drug_names: list[str]) -> list[dict]:
    """
    For every pair in drug_names, fuzzy-match against both drug_a and drug_b
    in interaction_database. Match threshold: 80.
    """
    _load_dbs()
    
    results = []
    # Resolve all drug names to generic first
    resolved_names = [resolve_generic(d) for d in drug_names]
    drug_names_normalized = [_normalize(d) for d in resolved_names]
    
    for interaction in _interaction_db:
        a = _normalize(interaction["drug_a"])
        b = _normalize(interaction["drug_b"])
        
        # Check if any drug in the prescription fuzzy-matches drug_a
        match_a = process.extractOne(a, drug_names_normalized, scorer=fuzz.token_sort_ratio)
        match_b = process.extractOne(b, drug_names_normalized, scorer=fuzz.token_sort_ratio)
        
        if match_a and match_b and match_a[1] >= 80 and match_b[1] >= 80:
            # Avoid matching the same drug to both a and b unless they are different instances in the list
            # and the interaction allows it. But usually it's between two different drugs.
            idx_a = drug_names_normalized.index(match_a[0])
            idx_b = drug_names_normalized.index(match_b[0])
            
            if idx_a != idx_b:
                results.append({
                    **interaction,
                    "matched_drug_a": drug_names[idx_a],
                    "matched_drug_b": drug_names[idx_b],
                    "match_score_a": match_a[1],
                    "match_score_b": match_b[1]
                })
                logger.info(f"[CONFLICT] {interaction['severity']}: {interaction['drug_a']} + {interaction['drug_b']}")
    
    return results

def detect_conflicts(drug_names: List[str]) -> Dict[str, Any]:
    """
    Wrapper to maintain compatibility with existing routes.
    """
    interactions = find_interactions(drug_names)
    
    critical = sum(1 for c in interactions if c.get("severity", "").upper() in ("MAJOR", "CRITICAL"))
    moderate = sum(1 for c in interactions if c.get("severity", "").upper() == "MODERATE")
    minor    = sum(1 for c in interactions if c.get("severity", "").upper() == "MINOR")
    
    logger.info(f"[CONFLICT] Checked {len(drug_names)} drug pairs — {len(interactions)} interactions found")
    
    return {
        "checked_drugs": drug_names,
        "conflicts": interactions,
        "critical_count": critical,
        "moderate_count": moderate,
        "minor_count": minor,
        "has_critical": critical > 0,
    }

