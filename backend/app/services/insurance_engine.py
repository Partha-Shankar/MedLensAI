"""
MedLens AI — insurance_engine.py
Insurance coverage lookup for Indian healthcare schemes (PMJAY, CGHS,
corporate plans, ESI) with generic substitution and financial summary.

Returns per-drug:
  coverage_status, generic_alternative, brand_price_inr,
  generic_price_inr, price_differential_inr, substitution_note

Returns financial summary:
  total_prescription_cost_inr, insurer_covered_amount_inr,
  savings_via_generics_inr, final_out_of_pocket_inr
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from rapidfuzz import fuzz as rfuzz

from app.utils.helpers import get_logger

logger = get_logger("INSURANCE")


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ── Coverage database ─────────────────────────────────────────────────────────
# Keyed by lowercase generic name.
# coverage: "covered" | "prior_auth_required" | "not_covered"
# schemes: list of schemes covering this drug

_COVERAGE_DB: Dict[str, Dict[str, Any]] = {
    "metformin": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS", "ESI"],
        "brand_price_inr": 35,
        "generic_price_inr": 8,
        "generic_alternative": "Metformin 500mg (Generic)",
        "substitution_note": (
            "Generic metformin is bioequivalent. "
            "Available at Jan Aushadhi outlets at ₹8/strip."
        ),
    },
    "atorvastatin": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS"],
        "brand_price_inr": 120,
        "generic_price_inr": 22,
        "generic_alternative": "Atorvastatin 10mg (Generic)",
        "substitution_note": "Generic atorvastatin available at Jan Aushadhi at ₹22/strip.",
    },
    "rosuvastatin": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 150,
        "generic_price_inr": 30,
        "generic_alternative": "Rosuvastatin 10mg (Generic)",
        "substitution_note": "CGHS reimbursement at generic rate only.",
    },
    "amlodipine": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS", "ESI"],
        "brand_price_inr": 60,
        "generic_price_inr": 10,
        "generic_alternative": "Amlodipine 5mg (Generic)",
        "substitution_note": "Widely available generic — significant savings.",
    },
    "ramipril": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 85,
        "generic_price_inr": 18,
        "generic_alternative": "Ramipril 5mg (Generic)",
        "substitution_note": "Generic available at government hospitals.",
    },
    "telmisartan": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 110,
        "generic_price_inr": 20,
        "generic_alternative": "Telmisartan 40mg (Generic)",
        "substitution_note": "Jan Aushadhi generic at ₹20/strip.",
    },
    "losartan": {
        "coverage_status": "covered",
        "schemes": ["CGHS", "ESI"],
        "brand_price_inr": 90,
        "generic_price_inr": 16,
        "generic_alternative": "Losartan 50mg (Generic)",
        "substitution_note": "Generic widely available.",
    },
    "metoprolol": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS", "ESI"],
        "brand_price_inr": 75,
        "generic_price_inr": 14,
        "generic_alternative": "Metoprolol 50mg (Generic)",
        "substitution_note": "Jan Aushadhi generic available.",
    },
    "aspirin": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS", "ESI"],
        "brand_price_inr": 15,
        "generic_price_inr": 5,
        "generic_alternative": "Aspirin 75mg (Generic)",
        "substitution_note": "Very low cost generic available everywhere.",
    },
    "clopidogrel": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS"],
        "brand_price_inr": 180,
        "generic_price_inr": 35,
        "generic_alternative": "Clopidogrel 75mg (Generic)",
        "substitution_note": "Significant savings via generic. Jan Aushadhi price ₹35/strip.",
    },
    "warfarin": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 45,
        "generic_price_inr": 20,
        "generic_alternative": "Warfarin 5mg (Generic)",
        "substitution_note": "Generic available; INR monitoring remains essential.",
    },
    "paracetamol": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS", "ESI"],
        "brand_price_inr": 25,
        "generic_price_inr": 5,
        "generic_alternative": "Paracetamol 500mg (Generic)",
        "substitution_note": "Jan Aushadhi generic at ₹5/strip.",
    },
    "ibuprofen": {
        "coverage_status": "covered",
        "schemes": ["CGHS", "ESI"],
        "brand_price_inr": 30,
        "generic_price_inr": 8,
        "generic_alternative": "Ibuprofen 400mg (Generic)",
        "substitution_note": "Generic widely available.",
    },
    "omeprazole": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS", "ESI"],
        "brand_price_inr": 55,
        "generic_price_inr": 10,
        "generic_alternative": "Omeprazole 20mg (Generic)",
        "substitution_note": "Jan Aushadhi at ₹10/strip.",
    },
    "pantoprazole": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 60,
        "generic_price_inr": 12,
        "generic_alternative": "Pantoprazole 40mg (Generic)",
        "substitution_note": "Generic available at government pharmacies.",
    },
    "methotrexate": {
        "coverage_status": "prior_auth_required",
        "schemes": ["PMJAY"],
        "brand_price_inr": 95,
        "generic_price_inr": 40,
        "generic_alternative": "Methotrexate 2.5mg (Generic)",
        "substitution_note": (
            "Prior authorisation required under PMJAY. "
            "Generic available at cancer centres and Jan Aushadhi."
        ),
    },
    "hydroxychloroquine": {
        "coverage_status": "covered",
        "schemes": ["CGHS", "ESI"],
        "brand_price_inr": 120,
        "generic_price_inr": 45,
        "generic_alternative": "Hydroxychloroquine 200mg (Generic)",
        "substitution_note": "Generic HCQ available; widely used for RA and lupus.",
    },
    "prednisolone": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS", "ESI"],
        "brand_price_inr": 40,
        "generic_price_inr": 8,
        "generic_alternative": "Prednisolone 5mg (Generic)",
        "substitution_note": "Very low-cost generic.",
    },
    "azithromycin": {
        "coverage_status": "covered",
        "schemes": ["CGHS", "ESI"],
        "brand_price_inr": 90,
        "generic_price_inr": 25,
        "generic_alternative": "Azithromycin 500mg (Generic)",
        "substitution_note": "Jan Aushadhi price ₹25/strip.",
    },
    "amoxicillin": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS", "ESI"],
        "brand_price_inr": 50,
        "generic_price_inr": 12,
        "generic_alternative": "Amoxicillin 500mg (Generic)",
        "substitution_note": "Generic available everywhere.",
    },
    "levothyroxine": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 55,
        "generic_price_inr": 15,
        "generic_alternative": "Levothyroxine 50mcg (Generic)",
        "substitution_note": (
            "Generic available; bioequivalence is critical for thyroid replacement — "
            "check TSH after switching."
        ),
    },
    "insulin glargine": {
        "coverage_status": "prior_auth_required",
        "schemes": ["PMJAY"],
        "brand_price_inr": 1200,
        "generic_price_inr": 650,
        "generic_alternative": "Basalog (Biosimilar Insulin Glargine)",
        "substitution_note": (
            "Basalog biosimilar available at ₹650/vial. "
            "Prior auth required under PMJAY; covered under state diabetes schemes."
        ),
    },
    "adalimumab": {
        "coverage_status": "prior_auth_required",
        "schemes": ["PMJAY"],
        "brand_price_inr": 45000,
        "generic_price_inr": 18000,
        "generic_alternative": "Exemptia or Adfrar (Biosimilar Adalimumab)",
        "substitution_note": (
            "Biosimilar adalimumab (Exemptia) available at ₹18,000/vial. "
            "PMJAY prior auth required; significant out-of-pocket savings."
        ),
    },
    "pregabalin": {
        "coverage_status": "prior_auth_required",
        "schemes": ["CGHS"],
        "brand_price_inr": 320,
        "generic_price_inr": 95,
        "generic_alternative": "Pregabalin 75mg (Generic)",
        "substitution_note": "Schedule H — prior auth under CGHS. Jan Aushadhi at ₹95/strip.",
    },
    "gabapentin": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 150,
        "generic_price_inr": 45,
        "generic_alternative": "Gabapentin 300mg (Generic)",
        "substitution_note": "Generic available.",
    },
    "dapagliflozin": {
        "coverage_status": "not_covered",
        "schemes": [],
        "brand_price_inr": 850,
        "generic_price_inr": 0,
        "generic_alternative": None,
        "substitution_note": (
            "Not currently covered under PMJAY/CGHS. "
            "Consider metformin + glimepiride as a covered alternative for T2DM."
        ),
    },
    "empagliflozin": {
        "coverage_status": "not_covered",
        "schemes": [],
        "brand_price_inr": 920,
        "generic_price_inr": 0,
        "generic_alternative": None,
        "substitution_note": (
            "Not covered under major public schemes. "
            "Glipizide + metformin combination is a covered alternative."
        ),
    },
    "colchicine": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 65,
        "generic_price_inr": 18,
        "generic_alternative": "Colchicine 0.5mg (Generic)",
        "substitution_note": "Generic available; used for gout flares.",
    },
    "allopurinol": {
        "coverage_status": "covered",
        "schemes": ["CGHS", "ESI"],
        "brand_price_inr": 45,
        "generic_price_inr": 10,
        "generic_alternative": "Allopurinol 100mg (Generic)",
        "substitution_note": "Jan Aushadhi price ₹10/strip.",
    },
    "furosemide": {
        "coverage_status": "covered",
        "schemes": ["PMJAY", "CGHS", "ESI"],
        "brand_price_inr": 30,
        "generic_price_inr": 6,
        "generic_alternative": "Furosemide 40mg (Generic)",
        "substitution_note": "Widely available inexpensive generic.",
    },
    "spironolactone": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 75,
        "generic_price_inr": 20,
        "generic_alternative": "Spironolactone 25mg (Generic)",
        "substitution_note": "Generic available at CGHS dispensaries.",
    },
    "escitalopram": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 95,
        "generic_price_inr": 25,
        "generic_alternative": "Escitalopram 10mg (Generic)",
        "substitution_note": "Generic available.",
    },
    "sertraline": {
        "coverage_status": "covered",
        "schemes": ["CGHS"],
        "brand_price_inr": 85,
        "generic_price_inr": 22,
        "generic_alternative": "Sertraline 50mg (Generic)",
        "substitution_note": "Jan Aushadhi generic at ₹22/strip.",
    },
}

# Drug name → canonical key aliases
_BRAND_ALIASES: Dict[str, str] = {
    "glycomet": "metformin", "glucophage": "metformin",
    "lipitor": "atorvastatin", "atorlip": "atorvastatin",
    "crestor": "rosuvastatin", "rozavel": "rosuvastatin",
    "amlong": "amlodipine", "stamlo": "amlodipine",
    "cardace": "ramipril", "hopace": "ramipril",
    "telma": "telmisartan", "telvas": "telmisartan",
    "losar": "losartan", "repace": "losartan",
    "betaloc": "metoprolol",
    "ecosprin": "aspirin",
    "plavix": "clopidogrel", "deplatt": "clopidogrel",
    "warf": "warfarin",
    "crocin": "paracetamol", "dolo": "paracetamol", "calpol": "paracetamol",
    "brufen": "ibuprofen",
    "omez": "omeprazole",
    "pan": "pantoprazole", "pantocid": "pantoprazole",
    "folitrax": "methotrexate", "biotrexate": "methotrexate",
    "hcqs": "hydroxychloroquine", "plaquenil": "hydroxychloroquine",
    "wysolone": "prednisolone", "omnacortil": "prednisolone",
    "azithral": "azithromycin",
    "thyronorm": "levothyroxine", "eltroxin": "levothyroxine",
    "lantus": "insulin glargine", "basalog": "insulin glargine",
    "humira": "adalimumab",
    "lyrica": "pregabalin", "pregalin": "pregabalin",
    "gabantin": "gabapentin",
    "forxiga": "dapagliflozin",
    "jardiance": "empagliflozin",
    "colchicum": "colchicine",
    "zyloric": "allopurinol",
    "lasix": "furosemide", "frusemide": "furosemide",
    "aldactone": "spironolactone",
    "nexito": "escitalopram",
    "sertima": "sertraline",
}


def _resolve_key(drug_name: str) -> str:
    lower = drug_name.lower().strip()
    if lower in _COVERAGE_DB:
        return lower
    if lower in _BRAND_ALIASES:
        return _BRAND_ALIASES[lower]
    # Fuzzy fallback
    best_score, best_key = 0, None
    for key in list(_COVERAGE_DB.keys()) + list(_BRAND_ALIASES.keys()):
        score = rfuzz.partial_ratio(lower, key)
        if score > best_score:
            best_score, best_key = score, key
    if best_score >= 88 and best_key:
        return _BRAND_ALIASES.get(best_key, best_key)
    return ""


def get_insurance_summary(
    drug_names: List[str],
    scheme: str = "CGHS",
) -> Dict[str, Any]:
    """
    Compute insurance coverage and financial summary for a list of drugs.

    Args:
        drug_names : list of resolved drug name strings
        scheme     : insurance scheme name (default: "CGHS")

    Returns:
        {
          drugs: [{drug_name, coverage_status, ...}, ...],
          financial_summary: {...},
        }
    """
    drug_results: List[Dict[str, Any]] = []
    total_brand = 0
    total_generic = 0
    total_covered = 0

    for drug in drug_names:
        if not drug or drug == "MISSING":
            continue
        key = _resolve_key(drug)
        if not key or key not in _COVERAGE_DB:
            drug_results.append({
                "drug_name": drug,
                "coverage_status": "not_covered",
                "schemes": [],
                "brand_price_inr": 0,
                "generic_price_inr": 0,
                "price_differential_inr": 0,
                "generic_alternative": None,
                "substitution_note": "No coverage data available for this drug.",
            })
            continue

        entry = _COVERAGE_DB[key]
        brand_p = entry.get("brand_price_inr", 0)
        generic_p = entry.get("generic_price_inr", 0)
        differential = brand_p - generic_p

        total_brand += brand_p
        total_generic += generic_p

        if entry.get("coverage_status") == "covered" and scheme in entry.get("schemes", []):
            total_covered += generic_p

        drug_results.append({
            "drug_name": drug,
            "coverage_status": entry.get("coverage_status", "not_covered"),
            "schemes": entry.get("schemes", []),
            "brand_price_inr": brand_p,
            "generic_price_inr": generic_p,
            "price_differential_inr": differential,
            "generic_alternative": entry.get("generic_alternative"),
            "substitution_note": entry.get("substitution_note", ""),
        })

        logger.info(
            f"[{_ts()}] [INSURANCE] {drug} → {entry.get('coverage_status')} "
            f"(brand ₹{brand_p}, generic ₹{generic_p})"
        )

    savings = total_brand - total_generic
    out_of_pocket = total_brand - total_covered

    financial_summary = {
        "total_prescription_cost_inr": total_brand,
        "insurer_covered_amount_inr": total_covered,
        "savings_via_generics_inr": savings,
        "final_out_of_pocket_inr": max(0, out_of_pocket),
        "scheme_used": scheme,
    }

    logger.info(
        f"[{_ts()}] [INSURANCE] Summary: brand=₹{total_brand}, "
        f"covered=₹{total_covered}, savings=₹{savings}, oop=₹{out_of_pocket}"
    )

    return {
        "drugs": drug_results,
        "financial_summary": financial_summary,
    }
