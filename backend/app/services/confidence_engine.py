"""
MedLens AI — confidence_engine.py
Compute final per-medication and overall prescription confidence scores.

Per-medication rules:
  HIGH   → TrOCR conf > 0.80  AND  drug correction score > 2  AND  no MISSING fields
  MEDIUM → any ONE of those fails
  LOW    → two or more fail

Overall prescription confidence:
  Weighted average over all medication confidence levels.
"""
from __future__ import annotations

import datetime
from typing import Dict, List, Any

from app.schemas.prescription import ConfidenceLevel, Medication, Prescription
from app.utils.helpers import get_logger

logger = get_logger("CONFIDENCE_ENGINE")

MISSING = "MISSING"

_MEDICATION_FIELDS = [
    "DrugName", "DoseValue", "DoseUnit",
    "Frequency", "Duration", "Route", "AdminInstructions",
]

_LEVEL_WEIGHTS = {
    ConfidenceLevel.HIGH:   1.0,
    ConfidenceLevel.MEDIUM: 0.6,
    ConfidenceLevel.LOW:    0.2,
}


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ── Per-medication confidence ─────────────────────────────────────────────────

def compute_medication_confidence(
    med: Medication,
    trocr_confidence: float = 0.0,
    drug_correction_score: int = 0,
) -> ConfidenceLevel:
    """
    Apply 3-criterion rule to set medication confidence level.

    Criteria:
      A) TrOCR confidence  > 0.80
      B) Drug correction score > 2
      C) No MISSING fields

    HIGH   → all three pass
    MEDIUM → exactly one fails
    LOW    → two or more fail
    """
    missing_fields = [f for f in _MEDICATION_FIELDS if getattr(med, f, MISSING) == MISSING]

    crit_a = trocr_confidence > 0.80
    crit_b = drug_correction_score > 2
    crit_c = len(missing_fields) == 0

    failures = sum([not crit_a, not crit_b, not crit_c])

    if failures == 0:
        level = ConfidenceLevel.HIGH
    elif failures == 1:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW

    logger.info(
        f"[{_ts()}] [CONFIDENCE_ENGINE] '{med.DrugName}': "
        f"trocr={trocr_confidence:.2f}({'✓' if crit_a else '✗'}) "
        f"drug_score={drug_correction_score}({'✓' if crit_b else '✗'}) "
        f"missing={missing_fields}({'✓' if crit_c else '✗'}) "
        f"→ {level.value}"
    )
    return level


# ── Per-field scores ──────────────────────────────────────────────────────────

def compute_field_scores(med: Medication, trocr_confidence: float) -> Dict[str, float]:
    """Return a per-field confidence score dict for the medication."""
    scores: Dict[str, float] = {}
    for field in _MEDICATION_FIELDS:
        val = getattr(med, field, MISSING)
        if val == MISSING:
            scores[field] = 0.0
        else:
            # Base score from TrOCR; penalise short/generic values
            base = trocr_confidence
            if len(str(val)) < 2:
                base *= 0.5
            scores[field] = round(base, 4)
    return scores


# ── Overall prescription confidence ──────────────────────────────────────────

def compute_overall_confidence(medications: List[Medication]) -> float:
    """
    Weighted average confidence across all medications.

    Returns a [0, 1] float.
    """
    if not medications:
        return 0.0

    total_weight = sum(
        _LEVEL_WEIGHTS.get(m.ConfidenceLevel, 0.2)
        for m in medications
    )
    overall = total_weight / len(medications)
    return round(overall, 4)


# ── Full confidence report ────────────────────────────────────────────────────

def build_confidence_report(
    medications: List[Medication],
    trocr_line_results: List[Dict[str, Any]],
    drug_correction_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute and attach confidence to each medication in-place.

    Args:
        medications           : list of Medication objects (will be mutated)
        trocr_line_results    : list of dicts from trocr_engine, one per med line
        drug_correction_results: list of dicts from drug_corrector, one per med

    Returns:
        confidence report dict:
        {
          overall_confidence: float,
          per_medication: [{drug_name, level, field_scores}, ...],
          summary: {HIGH, MEDIUM, LOW counts},
        }
    """
    logger.info(
        f"[{_ts()}] [CONFIDENCE_ENGINE] Computing confidence for {len(medications)} medications"
    )

    per_med_reports = []

    for i, med in enumerate(medications):
        trocr_conf = (
            trocr_line_results[i].get("confidence", 0.0)
            if i < len(trocr_line_results)
            else 0.0
        )
        drug_score = (
            drug_correction_results[i].get("score", 0)
            if i < len(drug_correction_results)
            else 0
        )

        level = compute_medication_confidence(med, trocr_conf, drug_score)
        field_scores = compute_field_scores(med, trocr_conf)

        # Mutate medication confidence level
        med.ConfidenceLevel = level
        med.field_scores = field_scores

        per_med_reports.append({
            "drug_name": med.DrugName,
            "level": level.value,
            "trocr_confidence": trocr_conf,
            "drug_correction_score": drug_score,
            "field_scores": field_scores,
        })

    overall = compute_overall_confidence(medications)

    counts = {
        "HIGH":   sum(1 for m in medications if m.ConfidenceLevel == ConfidenceLevel.HIGH),
        "MEDIUM": sum(1 for m in medications if m.ConfidenceLevel == ConfidenceLevel.MEDIUM),
        "LOW":    sum(1 for m in medications if m.ConfidenceLevel == ConfidenceLevel.LOW),
    }

    logger.info(
        f"[{_ts()}] [CONFIDENCE_ENGINE] Overall={overall:.2f} | "
        f"HIGH={counts['HIGH']} MEDIUM={counts['MEDIUM']} LOW={counts['LOW']}"
    )

    return {
        "overall_confidence": overall,
        "per_medication": per_med_reports,
        "summary": counts,
    }
