"""
MedLens AI — dosage_sanity_validator.py
Local dosage plausibility check against dosage_rules_database.json.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from rapidfuzz import fuzz

from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger("DOSAGE_SANITY")

# ── DB loader ─────────────────────────────────────────────────────────────────

_dosage_rules: List[Dict] = []

def _load_db():
    global _dosage_rules
    if not _dosage_rules:
        path = os.path.join(os.path.dirname(settings.INTERACTION_DB_PATH), "dosage_rules_database.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                _dosage_rules = data
            else:
                _dosage_rules = data.get("rules", [])
            logger.info(f"[DOSAGE_SANITY] Loaded {len(_dosage_rules)} rules from database")

_load_db()

def _find_dosage_rule(name: str) -> dict | None:
    normalized = name.lower().strip()
    for rule in _dosage_rules:
        all_names = (
            [rule["drug_name"].lower(), rule.get("generic", "").lower()] +
            [a.lower() for a in rule.get("aliases", [])]
        )
        scores = [fuzz.token_sort_ratio(normalized, n) for n in all_names if n]
        if scores and max(scores) >= 80:
            return rule
    return None

def validate_dosage(drug_name: str, dose_value: str, dose_unit: str, 
                    patient_age: str, conditions: list[str]) -> dict:
    """
    Local dosage validation against dosage_rules_database.json.
    No external API call.
    """
    _load_db()
    
    # Fuzzy find drug in rules
    rule = _find_dosage_rule(drug_name)
    
    if not rule:
        logger.warning(f"[DOSAGE_SANITY] No rule found for: {drug_name}")
        return {
            "plausibility": "unverified",
            "reason": f"No dosage data found for {drug_name} in local database",
            "confidence": 0.0,
            "source": "local_db_miss"
        }
    
    # Parse dose value
    try:
        # Extract numeric part
        numeric_part = ''.join(filter(lambda c: c.isdigit() or c == '.', str(dose_value)))
        dose_float = float(numeric_part) if numeric_part else 0.0
    except Exception:
        return {
            "plausibility": "unverified",
            "reason": "Could not parse dose value",
            "confidence": 0.0,
            "source": "parse_error"
        }
    
    # Determine adult vs pediatric
    age_int = 0
    try:
        age_int_str = ''.join(filter(str.isdigit, str(patient_age)))
        age_int = int(age_int_str) if age_int_str else 0
    except Exception:
        pass
    
    if 0 < age_int < 12 and "pediatric_dose" in rule:
        pd = rule["pediatric_dose"]
        max_single = pd.get("max_single_dose_mg", rule["adult_dose"]["max_single_dose_mg"])
        typical = rule["adult_dose"]["typical_dose_mg"] * 0.5
    else:
        max_single = rule["adult_dose"]["max_single_dose_mg"]
        typical = rule["adult_dose"]["typical_dose_mg"]
    
    dangerous_threshold = max_single * rule.get("dangerous_dose_multiplier", 2.0)
    
    if dose_float > dangerous_threshold:
        result = "dangerous"
        reason = f"{drug_name} {dose_float}{dose_unit} exceeds safe limit. Max single dose: {max_single}{dose_unit}."
        confidence = 0.95
    elif dose_float > max_single:
        result = "implausible"
        reason = f"{drug_name} {dose_float}{dose_unit} is above typical max of {max_single}{dose_unit}."
        confidence = 0.85
    elif 0 < dose_float < (typical * 0.1):
        result = "implausible"
        reason = f"{drug_name} {dose_float}{dose_unit} appears very low. Typical dose: {typical}{dose_unit}."
        confidence = 0.75
    else:
        result = "plausible"
        reason = f"{drug_name} {dose_float}{dose_unit} is within normal range (typical: {typical}{dose_unit}, max: {max_single}{dose_unit})."
        confidence = 0.90
    
    # Special checks
    if conditions and "Kidney Disease" in conditions and rule.get("renal_caution"):
        reason += f" ⚠️ Renal caution: {rule.get('renal_adjustment', 'monitor renal function')}."
    if conditions and "Pregnancy" in conditions and not rule.get("pregnancy_safe", True):
        result = "dangerous"
        reason += f" ⚠️ NOT safe in pregnancy."
    
    logger.info(f"[DOSAGE_SANITY] {drug_name} {dose_float}{dose_unit} → {result} (confidence {confidence})")
    return {
        "plausibility": result,
        "reason": reason,
        "confidence": confidence,
        "source": "local_rules_db",
        "rule_used": rule["drug_name"]
    }

def check_batch_dosage_sanity(
    medications: List[Dict[str, Any]],
    patient_age: Optional[str] = None,
    conditions: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Run dosage sanity on a list of medication dicts.
    Each dict must have: DrugName, DoseValue, DoseUnit.
    """
    results = []
    for med in medications:
        res = validate_dosage(
            drug_name=med.get("DrugName", "MISSING"),
            dose_value=med.get("DoseValue", "0"),
            dose_unit=med.get("DoseUnit", "mg"),
            patient_age=patient_age or "0",
            conditions=conditions or [],
        )
        res["drug_name"] = med.get("DrugName", "MISSING")
        results.append(res)
    return results

