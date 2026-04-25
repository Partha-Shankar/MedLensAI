"""
MedLens AI — prescription_validity_checker.py
Score a prescription against six legal/clinical completeness criteria
before conflict analysis runs.

Criteria:
  1. Patient name present and non-empty
  2. Doctor MCI registration number present (regex: MCI-XXXXXX or digits 5-8 long)
  3. Prescription date present and within last 30 days
  4. Dosage + frequency specified for every drug (no MISSING values)
  5. Drug legibility confidence ≥ 0.6 for all medications
  6. If any controlled substance present, form_compliance_flag must be set

Output:
  {
    score:           "5/6",
    legally_complete: bool,
    criteria:        [{name, passed, detail}, ...],
    warnings:        [str],
  }
"""
from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Optional

from app.utils.helpers import get_logger

logger = get_logger("VALIDITY")

MISSING = "MISSING"

# ── Controlled substances (Schedule H / H1 / X in India) ─────────────────────

CONTROLLED_SUBSTANCES = {
    # Schedule X
    "alprazolam", "clonazepam", "diazepam", "lorazepam", "nitrazepam",
    "phenobarbitone", "phenobarbital", "buprenorphine", "morphine",
    "codeine", "tramadol", "fentanyl", "pethidine", "methadone",
    "zolpidem", "zopiclone",
    # Schedule H1
    "cefixime", "ciprofloxacin", "levofloxacin", "azithromycin",
    "clarithromycin", "amoxicillin", "metronidazole",
    # High-risk rheumatology
    "methotrexate", "leflunomide", "azathioprine", "cyclosporine",
}

# ── MCI number regex ──────────────────────────────────────────────────────────
# Accepts: MCI-123456, MCI/123456, or bare 5–8 digit registration numbers

_MCI_RE = re.compile(
    r"\b(MCI[-/]?\d{5,8}|\d{5,8})\b",
    re.IGNORECASE,
)

# ── Date parsing helpers ──────────────────────────────────────────────────────

_DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
    "%Y-%m-%d", "%d %b %Y", "%d %B %Y",
]


def _parse_date(date_str: str) -> Optional[datetime.date]:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ── Criteria evaluators ───────────────────────────────────────────────────────

def _crit_patient_name(prescription: Dict) -> Dict:
    name = prescription.get("PatientName", MISSING)
    passed = bool(name and name != MISSING and len(name.strip()) >= 2)
    return {
        "name": "Patient name present",
        "passed": passed,
        "detail": f"PatientName='{name}'" if passed else "PatientName is missing or empty",
    }


def _crit_mci_number(prescription: Dict) -> Dict:
    prescriber = prescription.get("PrescriberName", "")
    raw_text = prescription.get("_raw_header_text", "")
    combined = f"{prescriber} {raw_text}"
    match = _MCI_RE.search(combined)
    passed = bool(match)
    return {
        "name": "Doctor MCI registration number present",
        "passed": passed,
        "detail": (
            f"MCI number found: {match.group()}" if passed
            else "MCI registration number not found in prescriber field"
        ),
    }


def _crit_date_valid(prescription: Dict) -> Dict:
    date_str = prescription.get("Date", MISSING)
    if date_str == MISSING or not date_str:
        return {
            "name": "Prescription date within last 30 days",
            "passed": False,
            "detail": "Date field is missing",
        }
    parsed = _parse_date(date_str)
    if parsed is None:
        return {
            "name": "Prescription date within last 30 days",
            "passed": False,
            "detail": f"Could not parse date: '{date_str}'",
        }
    today = datetime.date.today()
    age_days = (today - parsed).days
    passed = 0 <= age_days <= 30
    return {
        "name": "Prescription date within last 30 days",
        "passed": passed,
        "detail": (
            f"Date {parsed} is {age_days} days old" if not passed
            else f"Date {parsed} is valid ({age_days} days ago)"
        ),
    }


def _crit_dosage_complete(prescription: Dict) -> Dict:
    meds = prescription.get("Medications", [])
    incomplete = []
    for med in meds:
        drug = med.get("DrugName", MISSING)
        dose = med.get("DoseValue", MISSING)
        freq = med.get("Frequency", MISSING)
        if dose == MISSING or freq == MISSING:
            incomplete.append(drug)
    passed = len(incomplete) == 0
    return {
        "name": "Dosage and frequency specified for all drugs",
        "passed": passed,
        "detail": (
            "All medications have dose and frequency"
            if passed
            else f"Missing dose/frequency for: {incomplete}"
        ),
    }


def _crit_legibility(prescription: Dict, threshold: float = 0.6) -> Dict:
    meds = prescription.get("Medications", [])
    low_conf = []
    for med in meds:
        scores = med.get("field_scores") or {}
        # Use average field score as proxy for legibility
        vals = [v for v in scores.values() if isinstance(v, (int, float))]
        avg = sum(vals) / len(vals) if vals else 0.5
        conf_level = med.get("ConfidenceLevel", "LOW")
        effective_conf = avg if vals else (0.8 if conf_level == "HIGH" else 0.5 if conf_level == "MEDIUM" else 0.3)
        if effective_conf < threshold:
            low_conf.append(med.get("DrugName", MISSING))
    passed = len(low_conf) == 0
    return {
        "name": f"Drug legibility confidence ≥ {threshold} for all medications",
        "passed": passed,
        "detail": (
            "All medications meet legibility threshold"
            if passed
            else f"Low legibility for: {low_conf}"
        ),
    }


def _crit_controlled_substance(
    prescription: Dict,
    form_compliance_flag: bool = False,
) -> Dict:
    meds = prescription.get("Medications", [])
    controlled_found = []
    for med in meds:
        drug_lower = med.get("DrugName", "").lower().strip()
        if any(cs in drug_lower for cs in CONTROLLED_SUBSTANCES):
            controlled_found.append(med.get("DrugName", ""))

    if not controlled_found:
        return {
            "name": "Controlled substance form compliance",
            "passed": True,
            "detail": "No controlled substances in prescription",
        }

    passed = form_compliance_flag
    return {
        "name": "Controlled substance form compliance",
        "passed": passed,
        "detail": (
            f"Controlled substances present: {controlled_found}. "
            + ("Form compliance verified." if passed else "Form compliance NOT set — Schedule H/X form required.")
        ),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def check_prescription_validity(
    prescription: Dict[str, Any],
    form_compliance_flag: bool = False,
    raw_header_text: str = "",
) -> Dict[str, Any]:
    """
    Run all six validity criteria and return a scored report.

    Args:
        prescription         : prescription dict (from validator output)
        form_compliance_flag : True if prescriber submitted Schedule H form
        raw_header_text      : raw OCR text from header zone (for MCI search)

    Returns:
        {score, legally_complete, criteria, warnings}
    """
    # Inject raw header text for MCI search
    prescription["_raw_header_text"] = raw_header_text

    criteria_results = [
        _crit_patient_name(prescription),
        _crit_mci_number(prescription),
        _crit_date_valid(prescription),
        _crit_dosage_complete(prescription),
        _crit_legibility(prescription),
        _crit_controlled_substance(prescription, form_compliance_flag),
    ]

    passed_count = sum(1 for c in criteria_results if c["passed"])
    total = len(criteria_results)
    score = f"{passed_count}/{total}"
    legally_complete = passed_count == total

    warnings = [c["detail"] for c in criteria_results if not c["passed"]]

    logger.info(
        f"[{_ts()}] [VALIDITY] Score {score} — "
        + (", ".join(w for w in warnings) or "all criteria passed")
    )

    return {
        "score": score,
        "passed_count": passed_count,
        "total_criteria": total,
        "legally_complete": legally_complete,
        "criteria": criteria_results,
        "warnings": warnings,
    }
