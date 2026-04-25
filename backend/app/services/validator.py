"""
MedLens AI — validator.py
Pydantic v2 validation layer + review-trigger logic.

Hard failures (wrong types)  → raise ValidationError
Soft failures (MISSING fields) → collected in ReviewFields

After validation:
  • % missing fields across all medications > 30%  → trigger Groq fallback
  • % LOW confidence medications            > 30%  → trigger Groq fallback
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Tuple

from pydantic import ValidationError

from app.core.config import settings
from app.schemas.prescription import (
    ConfidenceLevel,
    Medication,
    Prescription,
)
from app.utils.helpers import get_logger

logger = get_logger("VALIDATOR")

MISSING = "MISSING"

_MEDICATION_FIELDS = [
    "DrugName", "DoseValue", "DoseUnit",
    "Frequency", "Duration", "Route", "AdminInstructions",
]

_HEADER_FIELDS = [
    "PatientName", "Age", "Sex", "Date", "Diagnosis", "PrescriberName",
]


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ── Medication validation ─────────────────────────────────────────────────────

def validate_medication(raw: Dict[str, Any]) -> Tuple[Medication, List[str]]:
    """
    Validate a raw medication dict.

    Returns:
        (Medication instance, list of soft-failure field names)
    """
    soft_failures: List[str] = []

    # Hard-validate via Pydantic
    try:
        med = Medication(**raw)
    except ValidationError as exc:
        logger.error(f"[{_ts()}] [VALIDATOR] Hard validation error: {exc}")
        raise

    # Collect soft failures
    for field in _MEDICATION_FIELDS:
        if getattr(med, field, MISSING) == MISSING:
            soft_failures.append(field)

    if soft_failures:
        logger.debug(
            f"[{_ts()}] [VALIDATOR] Medication '{med.DrugName}' missing: {soft_failures}"
        )

    return med, soft_failures


# ── Prescription validation ───────────────────────────────────────────────────

def validate_prescription(raw: Dict[str, Any]) -> Prescription:
    """
    Validate the full prescription dict and compute review flags.

    Args:
        raw: dict with PatientName, Age, Sex, Date, Diagnosis,
             PrescriberName, Medications (list of dicts)

    Returns:
        Validated Prescription with ReviewRequired and ReviewFields populated.
    """
    logger.info(f"[{_ts()}] [VALIDATOR] Validating prescription")

    raw_meds: List[Dict] = raw.pop("Medications", [])
    validated_meds: List[Medication] = []
    all_review_fields: List[str] = []

    # ── Validate header ────────────────────────────────────────────────────────
    header_missing = [
        f for f in _HEADER_FIELDS
        if not raw.get(f) or raw.get(f) == MISSING
    ]
    all_review_fields.extend([f"header.{f}" for f in header_missing])

    # ── Validate each medication ──────────────────────────────────────────────
    total_fields = 0
    missing_count = 0

    for i, raw_med in enumerate(raw_meds):
        try:
            med, soft_fails = validate_medication(raw_med)
        except ValidationError:
            # Skip uncorrectable medication entries
            logger.error(f"[{_ts()}] [VALIDATOR] Medication {i+1} failed hard validation — skipped")
            continue

        validated_meds.append(med)
        total_fields += len(_MEDICATION_FIELDS)
        missing_count += len(soft_fails)

        for f in soft_fails:
            all_review_fields.append(f"medications[{i}].{f}")

    # ── Compute missing field percentage ──────────────────────────────────────
    if total_fields > 0:
        missing_pct = missing_count / total_fields
    else:
        missing_pct = 0.0

    # ── Count LOW confidence medications ─────────────────────────────────────
    low_conf_count = sum(1 for m in validated_meds if m.ConfidenceLevel == ConfidenceLevel.LOW)
    low_conf_pct = low_conf_count / len(validated_meds) if validated_meds else 0.0

    # ── Decide review / fallback ──────────────────────────────────────────────
    review_required = (
        missing_pct > settings.MISSING_FIELD_TRIGGER_PCT
        or low_conf_pct > settings.LOW_CONFIDENCE_MED_TRIGGER_PCT
    )

    if len(validated_meds) == 0:
        logger.warning(f"[{_ts()}] [VALIDATOR] 0 medications extracted — forcing ReviewRequired=True")
        review_required = True
        all_review_fields.append("ALL_MEDICATIONS_MISSING")

    if review_required:
        logger.warning(
            f"[{_ts()}] [VALIDATOR] Review triggered: "
            f"missing_pct={missing_pct:.0%}, low_conf_pct={low_conf_pct:.0%}"
        )
    else:
        logger.info(
            f"[{_ts()}] [VALIDATOR] Validation passed — "
            f"missing_pct={missing_pct:.0%}, low_conf_pct={low_conf_pct:.0%}"
        )

    # ── Build Prescription ────────────────────────────────────────────────────
    raw["Medications"] = [m.model_dump() for m in validated_meds]
    raw["ReviewRequired"] = review_required
    raw["ReviewFields"] = all_review_fields

    try:
        prescription = Prescription(**raw)
    except ValidationError as exc:
        logger.error(f"[{_ts()}] [VALIDATOR] Prescription-level validation error: {exc}")
        raise

    logger.info(
        f"[{_ts()}] [VALIDATOR] Prescription validated: "
        f"{len(validated_meds)} meds, ReviewRequired={review_required}"
    )
    return prescription
