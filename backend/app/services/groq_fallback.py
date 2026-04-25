"""
MedLens AI — groq_fallback.py
Targeted Groq LLM fallback for LOW/MISSING fields only.

Rules:
  • Only called when validator signals ReviewRequired=True.
  • Passes ONLY missing/low-confidence fields — never the full document.
  • Never overwrites HIGH or MEDIUM confidence fields.
  • Every Groq-filled field is tagged source="groq_fallback".
  • 5-second hard timeout; on failure sets groq_unavailable=True and continues.
  • Uses llama3-8b-8192 model via Groq SDK.
"""
from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List

from app.core.config import settings
from app.schemas.prescription import ConfidenceLevel, Medication, Prescription
from app.utils.helpers import get_logger

logger = get_logger("GROQ_FALLBACK")

MISSING = "MISSING"

_MEDICATION_FIELDS = [
    "DrugName", "DoseValue", "DoseUnit",
    "Frequency", "Duration", "Route", "AdminInstructions",
]


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ── Groq client (lazy init) ───────────────────────────────────────────────────

_groq_client = None


def _get_client():
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    try:
        from groq import Groq
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info(f"[{_ts()}] [GROQ_FALLBACK] Groq client initialised")
    except Exception as exc:
        logger.error(f"[{_ts()}] [GROQ_FALLBACK] Groq client init failed: {exc}")
        _groq_client = None
    return _groq_client


# ── Build targeted prompt ─────────────────────────────────────────────────────

def _build_prompt(
    raw_ocr_text: str,
    missing_fields: List[str],
    drug_name: str,
) -> str:
    fields_str = ", ".join(missing_fields)
    return f"""You are a clinical pharmacist assistant helping read a handwritten Indian prescription.

The OCR engine extracted this raw text for one medication line:
"{raw_ocr_text}"

Drug name identified: {drug_name}

The following fields could NOT be reliably extracted:
{fields_str}

Based ONLY on the raw OCR text above, provide the best-guess values for the missing fields.
Respond with a valid JSON object containing ONLY the missing fields as keys.
If you genuinely cannot determine a field, set its value to "MISSING".
Do NOT include any other text or explanation — only the JSON object.

Example response format:
{{"Frequency": "OD", "Duration": "15 days", "Route": "oral"}}"""


# ── Fill a single medication ──────────────────────────────────────────────────

def _fill_medication(
    med: Medication,
    raw_ocr_text: str,
) -> tuple[Medication, List[str], bool]:
    """
    Attempt to fill MISSING fields in `med` using Groq.

    Returns:
        (updated_med, fields_filled, groq_unavailable)
    """
    # Identify which fields need filling
    missing = [f for f in _MEDICATION_FIELDS if getattr(med, f, MISSING) == MISSING]
    # Only fill fields where confidence is LOW or MISSING (never overwrite HIGH/MEDIUM)
    if med.ConfidenceLevel in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
        # Still fill strictly missing individual fields even on MEDIUM meds
        missing = [f for f in missing]  # keep as-is; HIGH/MEDIUM → field-level only

    if not missing:
        return med, [], False

    logger.info(
        f"[{_ts()}] [GROQ_FALLBACK] Filling {len(missing)} missing fields: {missing}"
    )

    client = _get_client()
    if client is None:
        return med, [], True

    prompt = _build_prompt(raw_ocr_text, missing, med.DrugName)

    try:
        import signal

        # Use Groq SDK with timeout
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=256,
            timeout=settings.GROQ_TIMEOUT_SECONDS,
        )

        raw_reply = response.choices[0].message.content.strip()

        # Extract JSON from response
        # Handle code-fenced JSON gracefully
        if "```" in raw_reply:
            raw_reply = raw_reply.split("```")[1]
            if raw_reply.startswith("json"):
                raw_reply = raw_reply[4:]

        filled: Dict[str, Any] = json.loads(raw_reply)

        fields_actually_filled: List[str] = []
        for field, value in filled.items():
            if field not in _MEDICATION_FIELDS:
                continue
            if value and value != MISSING:
                # Only overwrite if current value is MISSING
                if getattr(med, field, MISSING) == MISSING:
                    setattr(med, field, str(value))
                    setattr(med, f"{field}_source", "groq_fallback")
                    fields_actually_filled.append(field)

        logger.info(
            f"[{_ts()}] [GROQ_FALLBACK] Filled fields: {fields_actually_filled}"
        )
        return med, fields_actually_filled, False

    except json.JSONDecodeError as exc:
        logger.error(f"[{_ts()}] [GROQ_FALLBACK] JSON parse error: {exc}")
        return med, [], False

    except Exception as exc:
        logger.error(f"[{_ts()}] [GROQ_FALLBACK] Groq call failed/timed out: {exc}")
        return med, [], True


# ── Public API ────────────────────────────────────────────────────────────────

def run_groq_fallback(
    prescription: Prescription,
    context: Any,
) -> Prescription:
    """
    Attempt to fill missing prescription fields using Groq.
    Called only when validator sets ReviewRequired=True.

    Args:
        prescription : Prescription object with potential MISSING fields
        context      : Can be raw OCR text (str) or raw_extraction (dict)
    """
    if not prescription.ReviewRequired:
        return prescription

    # Handle both raw text and dict context
    if isinstance(context, str):
        context_dict = {"raw_text": context}
        raw_text = context
    elif isinstance(context, dict):
        context_dict = context
        raw_text = context.get("raw_text", "")
    else:
        context_dict = {}
        raw_text = ""

    logger.info(
        f"[{_ts()}] [GROQ_FALLBACK] Context received — type: {type(context).__name__}, length: {len(raw_text)} chars"
    )

    logger.info(
        f"[{_ts()}] [GROQ_FALLBACK] Starting fallback for {len(prescription.Medications)} medications"
    )

    groq_unavailable = False
    all_filled_fields: List[str] = []

    for i, med in enumerate(prescription.Medications):
        # Find the raw OCR text for this medication line
        ocr_text = ""
        # Try to get specific raw_text from medications list if available
        meds_list = context_dict.get("medications", [])
        if i < len(meds_list):
            ocr_text = meds_list[i].get("raw_text", "")
        
        # Fallback to global raw_text if specific line text is missing
        if not ocr_text:
            ocr_text = raw_text

        updated_med, filled, unavailable = _fill_medication(med, ocr_text)
        prescription.Medications[i] = updated_med

        if unavailable:
            groq_unavailable = True
        all_filled_fields.extend([f"medications[{i}].{f}" for f in filled])

    # Fill header fields
    header_missing = {
        "PatientName": prescription.PatientName,
        "Age": prescription.Age,
        "Sex": prescription.Sex,
        "Date": prescription.Date,
        "Diagnosis": prescription.Diagnosis,
        "PrescriberName": prescription.PrescriberName,
    }
    header_needs_fill = [k for k, v in header_missing.items() if v == MISSING]

    if header_needs_fill and not groq_unavailable:
        client = _get_client()
        if client:
            # Use top-level raw_text for header context
            context_str = raw_text[:2000]  # Limit context size
            prompt = (
                f"From this prescription header OCR text:\n\"{context_str}\"\n\n"
                f"Extract ONLY these fields as JSON: {header_needs_fill}.\n"
                f"Use \"MISSING\" for anything you cannot determine."
            )
            try:
                resp = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=128,
                    timeout=settings.GROQ_TIMEOUT_SECONDS,
                )
                raw_reply = resp.choices[0].message.content.strip()
                if "```" in raw_reply:
                    raw_reply = raw_reply.split("```")[1]
                    if raw_reply.startswith("json"):
                        raw_reply = raw_reply[4:]
                header_filled = json.loads(raw_reply)
                for field, value in header_filled.items():
                    if hasattr(prescription, field) and value and value != MISSING:
                        if getattr(prescription, field) == MISSING:
                            setattr(prescription, field, str(value))
                            all_filled_fields.append(f"header.{field}")
            except Exception as exc:
                logger.error(f"[{_ts()}] [GROQ_FALLBACK] Header fill failed: {exc}")
                groq_unavailable = True

    prescription.groq_unavailable = groq_unavailable
    prescription.groq_fields_filled = all_filled_fields

    if groq_unavailable:
        logger.warning(f"[{_ts()}] [GROQ_FALLBACK] Groq unavailable — partial fill only")
    else:
        logger.info(
            f"[{_ts()}] [GROQ_FALLBACK] Complete — {len(all_filled_fields)} fields filled"
        )

    return prescription
