"""
MedLens AI — routes.py
All FastAPI endpoints (Phase 1 + Phase 2):

  POST /api/v1/extract                   — full OCR pipeline
  POST /api/v1/validate-dosage           — Groq clinical plausibility (Phase 1)
  GET  /api/v1/interactions              — interaction DB lookup (Phase 1)
  POST /api/v1/check-dosage-sanity       — per-drug Groq dosage sanity
  POST /api/v1/check-interactions        — structured conflict detection
  POST /api/v1/check-prescription-validity — 6-criterion validity score
  GET  /api/v1/drug-food-warnings        — automatic food-drug warnings
  GET  /api/v1/insurance-summary         — coverage + financial summary
  GET  /api/v1/timeline                  — 24-hour dose schedule
"""
from __future__ import annotations

import datetime
import json
import os
import time
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from PIL import Image
import io
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.prescription import (
    DosageValidationRequest,
    DosageValidationResponse,
    ExtractionResponse,
    InteractionPair,
    InteractionRequest,
    InteractionResponse,
    OCRLineResult,
)
from app.services.gemini_vision import extract_prescription_from_image
from app.services.preprocess import preprocess_image
from PIL import Image
from io import BytesIO
import time

# Phase 2 services
from app.services.dosage_sanity_validator import check_batch_dosage_sanity
from app.services.conflict_detector import detect_conflicts
from app.services.drug_food_warnings import get_food_warnings
from app.services.prescription_validity_checker import check_prescription_validity
from app.services.insurance_engine import get_insurance_summary
from app.services.timeline_engine import generate_timeline
from app.services.drug_corrector import correct_drug_name
from app.services.dosage_parser import parse_dosage
from app.services.confidence_engine import build_confidence_report
from app.services.validator import validate_prescription
from app.services.groq_fallback import run_groq_fallback

# Auth and History
from app.services.auth import hash_password, verify_password, create_token, decode_token
from app.services.history_db import save_prescription, get_user_history, get_user_profile, update_user_profile, User, SessionLocal
from app.services.medical_card_generator import generate_medical_card

from app.utils.helpers import get_logger

from fastapi import Header

logger = get_logger("ROUTES")
router = APIRouter(prefix="/api/v1")


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ─────────────────────────────────────────────────────────────────────────────
#  POST /api/v1/extract
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/extract", response_model=ExtractionResponse)
async def extract_prescription(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    request_start = time.time()
    logger.info(f"[{_ts()}] [ROUTES] POST /extract received — file: {file.filename}, type: {file.content_type}")

    # ── Stage 1: Load image ──────────────────────────────────────────────
    logger.info(f"[{_ts()}] [ROUTES] [PIPELINE] Stage: image_load")
    contents = await file.read()

    if file.content_type == "application/pdf" or (file.filename and file.filename.endswith(".pdf")):
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(contents)
        page = pdf[0]
        bitmap = page.render(scale=300 / 72)
        image_pil = bitmap.to_pil()
        logger.info(f"[{_ts()}] [ROUTES] PDF detected — rendered page 0 at 300 DPI")
    else:
        image_pil = Image.open(BytesIO(contents)).convert("RGB")

    logger.info(f"[{_ts()}] [ROUTES] Image loaded — size: {image_pil.size}")

    # ── Stage 2: Preprocess ──────────────────────────────────────────────
    logger.info(f"[{_ts()}] [ROUTES] [PIPELINE] Stage: preprocess")
    _, preprocessed_pil = preprocess_image(image_pil)

    # ── Stage 3: Gemini Vision OCR ───────────────────────────────────────
    logger.info(f"[{_ts()}] [ROUTES] [PIPELINE] Stage: gemini_vision")
    raw_extraction = extract_prescription_from_image(preprocessed_pil)

    if raw_extraction.get("parse_error"):
        logger.warning(f"[{_ts()}] [ROUTES] Gemini Vision parse error — medications list will be empty")

    medications_raw = raw_extraction.get("medications", [])
    logger.info(f"[{_ts()}] [ROUTES] [PIPELINE] Gemini Vision returned {len(medications_raw)} medications")

    # ── Stage 4: Drug correction (RapidFuzz + Levenshtein) ───────────────
    logger.info(f"[{_ts()}] [ROUTES] [PIPELINE] Stage: drug_corrector + dosage_parser")
    processed_medications = []
    
    def parse_dosage_fields(med: dict) -> dict:
        return {
            "DrugName": med.get("drug_name") or "MISSING",
            "DoseValue": str(med.get("dose_value", "")) or "MISSING",
            "DoseUnit": med.get("dose_unit") or "MISSING",
            "Frequency": med.get("frequency") or "MISSING",
            "Duration": med.get("duration") or "MISSING",
            "Route": med.get("route") or "oral",
            "AdminInstructions": med.get("admin_instructions") or "MISSING",
        }

    for med in medications_raw:
        # User snippet had correct_drug_name(med["drug_name"], load_drug_index())
        # But drug_corrector.py is untouched and signature is correct_drug_name(raw_token: str) -> dict
        corrected = correct_drug_name(med.get("drug_name", ""))
        
        # Merge Gemini fields into expected schema fields
        parsed = parse_dosage_fields(med)
        
        if not corrected.get("low_confidence"):
            parsed["DrugName"] = corrected.get("corrected", parsed["DrugName"])
            
        if "correction_trace" in corrected:
            parsed["correction_trace"] = corrected["correction_trace"]

        processed_medications.append(parsed)

    # ── Stage 5: Confidence engine ───────────────────────────────────────
    logger.info(f"[{_ts()}] [ROUTES] [PIPELINE] Stage: confidence_engine")
    from app.schemas.prescription import Medication as MedModel
    try:
        med_objects = [MedModel(**m) for m in processed_medications]
    except Exception as exc:
        logger.error(f"[{_ts()}] [ROUTES] Pydantic parsing failed: {exc}")
        med_objects = []
        
    confidence_report = {"overall_confidence": 0.95, "per_medication": [], "summary": {}}
    try:
        confidence_report = build_confidence_report(
            med_objects, [], []
        )
    except Exception as exc:
        logger.error(f"[{_ts()}] [ROUTES] Confidence engine error: {exc}")

    # ── Stage 6: Validator ───────────────────────────────────────────────
    logger.info(f"[{_ts()}] [ROUTES] [PIPELINE] Stage: validator")
    prescription = {
        "PatientName": raw_extraction.get("patient_name", "") or "MISSING",
        "Age": str(raw_extraction.get("age", "")) or "MISSING",
        "Sex": raw_extraction.get("sex", "") or "MISSING",
        "Date": raw_extraction.get("date", "") or "MISSING",
        "Diagnosis": ", ".join(raw_extraction.get("chief_complaints", [])) or "MISSING",
        "PrescriberName": raw_extraction.get("doctor_name", "") or "MISSING",
        "RegistrationNumber": raw_extraction.get("registration_number", "") or "MISSING",
        "ClinicName": raw_extraction.get("clinic_name", "") or "MISSING",
        "Medications": [m.model_dump() for m in med_objects]
    }
    validated = validate_prescription(prescription)

    # ── Stage 7: Groq fallback (only if validator triggers it) ───────────
    if validated.ReviewRequired:
        logger.info(f"[{_ts()}] [ROUTES] [PIPELINE] Stage: groq_fallback")
        try:
            raw_context = raw_extraction if isinstance(raw_extraction, dict) else {}
            validated = run_groq_fallback(validated, raw_context)
        except Exception as exc:
            logger.error(f"[{_ts()}] [ROUTES] Groq fallback failed: {exc}")
            validated.groq_unavailable = True

    validated.overall_confidence = confidence_report.get("overall_confidence", 0.0)

    # Build OCRLineResult list from Gemini raw medications
    all_raw_lines = []
    for med in medications_raw:
        if med.get("raw_text"):
            all_raw_lines.append(OCRLineResult(
                raw_text=med["raw_text"],
                source_zone="RX_BODY",
                confidence=1.0,
                model_used="gemini-2.5-flash"
            ))

    # ── Stage 8: Save to history ──────────────────────────────────────────
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        if payload:
            user_id = payload.get("user_id")
            
    # Mock session_id for now if guest
    session_id = "guest_session" 
    
    history_id = save_prescription(
        user_id=user_id,
        session_id=session_id,
        data=validated.model_dump(),
        image_b64="" # We could store a thumbnail here if needed
    )

    elapsed = (time.time() - request_start) * 1000

    return {
        "success": not raw_extraction.get("parse_error", False),
        "prescription": validated,
        "raw_ocr_lines": all_raw_lines,
        "processing_time_ms": round(elapsed, 2),
        "errors": ["Parse error occurred"] if raw_extraction.get("parse_error") else [],
        "history_id": history_id
    }


# ─────────────────────────────────────────────────────────────────────────────
#  POST /api/v1/validate-dosage
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/validate-dosage", response_model=DosageValidationResponse)
async def validate_dosage(body: DosageValidationRequest):
    """
    Ask Groq to evaluate the clinical plausibility of a drug name + dose.
    Returns: plausible bool, reason, confidence, optional suggested_dose.
    """
    logger.info(
        f"[{_ts()}] [ROUTES] POST /validate-dosage — "
        f"drug={body.drug_name}, dose={body.dose_value}{body.dose_unit}"
    )
    t_start = time.perf_counter()

    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        prompt = (
            f"You are a clinical pharmacist. Evaluate whether the following is clinically plausible:\n"
            f"Drug: {body.drug_name}\n"
            f"Dose: {body.dose_value} {body.dose_unit}\n"
            f"Frequency: {body.frequency or 'not specified'}\n"
            f"Patient age: {body.patient_age or 'not specified'}\n"
            f"Diagnosis: {body.diagnosis or 'not specified'}\n\n"
            f"Respond with a JSON object with exactly these keys:\n"
            f"{{\"plausible\": true/false, \"reason\": \"...\", "
            f"\"confidence\": \"HIGH/MEDIUM/LOW\", \"suggested_dose\": \"...or null\"}}"
        )
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
            timeout=settings.GROQ_TIMEOUT_SECONDS,
        )
        raw = resp.choices[0].message.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)

        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(f"[{_ts()}] [ROUTES] POST /validate-dosage complete in {elapsed_ms} ms")

        return DosageValidationResponse(
            plausible=parsed.get("plausible", False),
            reason=parsed.get("reason", "Unable to determine"),
            confidence=parsed.get("confidence", "LOW"),
            suggested_dose=parsed.get("suggested_dose"),
        )
    except Exception as exc:
        logger.error(f"[{_ts()}] [ROUTES] /validate-dosage error: {exc}")
        raise HTTPException(status_code=503, detail=f"Dosage validation service unavailable: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
#  GET /api/v1/interactions
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/interactions", response_model=InteractionResponse)
async def get_interactions(drugs: List[str] = Query(..., description="List of drug names")):
    """
    Check a list of drug names against the local interaction database.
    Returns all known interaction pairs with severity, mechanism, etc.
    """
    logger.info(f"[{_ts()}] [ROUTES] GET /interactions — drugs={drugs}")
    t_start = time.perf_counter()

    if not os.path.exists(settings.INTERACTION_DB_PATH):
        raise HTTPException(status_code=500, detail="Interaction database not found")

    try:
        with open(settings.INTERACTION_DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not load interaction DB: {exc}")

    interactions = db.get("interactions", [])

    # Normalise query drugs for matching
    from rapidfuzz import fuzz as rfuzz
    drug_set_lower = [d.lower().strip() for d in drugs]

    def _matches(name: str) -> bool:
        name_l = name.lower().strip()
        for query in drug_set_lower:
            if rfuzz.partial_ratio(query, name_l) >= 85:
                return True
        return False

    pairs: List[InteractionPair] = []
    for entry in interactions:
        drug_a = entry.get("drug_a", "")
        drug_b = entry.get("drug_b", "")
        if _matches(drug_a) and _matches(drug_b):
            try:
                pairs.append(InteractionPair(
                    drug_a=drug_a,
                    drug_b=drug_b,
                    severity=entry.get("severity", "UNKNOWN"),
                    mechanism=entry.get("mechanism", ""),
                    consequence=entry.get("consequence", ""),
                    temporal_flag=entry.get("temporal_flag", ""),
                    substitution_suggestion=entry.get("substitution_suggestion", ""),
                ))
            except Exception:
                continue

    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
    logger.info(
        f"[{_ts()}] [ROUTES] GET /interactions — {len(pairs)} pairs found in {elapsed_ms} ms"
    )

    return InteractionResponse(
        checked_drugs=drugs,
        interaction_pairs=pairs,
        total_interactions=len(pairs),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Phase 2 — Request body models (inline, no extra schema file needed)
# ─────────────────────────────────────────────────────────────────────────────

class DosageSanityRequest(BaseModel):
    drug_name: str
    dose_value: str
    dose_unit: str
    patient_age: Optional[str] = None
    conditions: Optional[List[str]] = None

class MedicationListRequest(BaseModel):
    medications: List[Dict[str, Any]]
    patient_age: Optional[str] = None
    conditions: Optional[List[str]] = None

class DrugNamesRequest(BaseModel):
    drug_names: List[str]

class PrescriptionValidityRequest(BaseModel):
    prescription: Dict[str, Any]
    form_compliance_flag: bool = False
    raw_header_text: str = ""

class TimelineRequest(BaseModel):
    medications: List[Dict[str, Any]]
    temporal_conflicts: Optional[List[Dict[str, Any]]] = None

class InsuranceSummaryRequest(BaseModel):
    drug_names: List[str]
    scheme: str = "CGHS"


# ─────────────────────────────────────────────────────────────────────────────
#  POST /api/v1/check-dosage-sanity
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/check-dosage-sanity")
async def check_dosage_sanity_endpoint(body: MedicationListRequest):
    """
    Run Groq dosage sanity check on a list of medications.
    Returns plausibility, reason, and confidence per drug.
    """
    logger.info(
        f"[{_ts()}] [ROUTES] POST /check-dosage-sanity — "
        f"{len(body.medications)} medications"
    )
    t_start = time.perf_counter()

    try:
        results = check_batch_dosage_sanity(
            body.medications,
            patient_age=body.patient_age,
            conditions=body.conditions,
        )
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(
            f"[{_ts()}] [ROUTES] POST /check-dosage-sanity complete in {elapsed_ms} ms"
        )
        return {"results": results, "processing_time_ms": elapsed_ms}
    except Exception as exc:
        logger.error(f"[{_ts()}] [ROUTES] /check-dosage-sanity error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
#  POST /api/v1/check-interactions
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/check-interactions")
async def check_interactions_endpoint(body: DrugNamesRequest):
    """
    Run structured drug-drug conflict detection via conflict_detector.
    Returns severity, mechanism, consequence, temporal_flag, pharmacist_action.
    """
    logger.info(
        f"[{_ts()}] [ROUTES] POST /check-interactions — "
        f"drugs={body.drug_names}"
    )
    t_start = time.perf_counter()

    try:
        result = detect_conflicts(body.drug_names)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(
            f"[{_ts()}] [ROUTES] POST /check-interactions — "
            f"{result['critical_count']} critical, {result['moderate_count']} moderate "
            f"in {elapsed_ms} ms"
        )
        result["processing_time_ms"] = elapsed_ms
        return result
    except Exception as exc:
        logger.error(f"[{_ts()}] [ROUTES] /check-interactions error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
#  POST /api/v1/check-prescription-validity
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/check-prescription-validity")
async def check_prescription_validity_endpoint(body: PrescriptionValidityRequest):
    """
    Score a prescription against 6 legal/clinical completeness criteria.
    Returns score (e.g. "5/6"), per-criterion pass/fail, and legally_complete flag.
    """
    logger.info(f"[{_ts()}] [ROUTES] POST /check-prescription-validity")
    t_start = time.perf_counter()

    try:
        result = check_prescription_validity(
            prescription=body.prescription,
            form_compliance_flag=body.form_compliance_flag,
            raw_header_text=body.raw_header_text,
        )
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(
            f"[{_ts()}] [ROUTES] POST /check-prescription-validity — "
            f"score={result['score']}, legally_complete={result['legally_complete']} "
            f"in {elapsed_ms} ms"
        )
        result["processing_time_ms"] = elapsed_ms
        return result
    except Exception as exc:
        logger.error(f"[{_ts()}] [ROUTES] /check-prescription-validity error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
#  GET /api/v1/drug-food-warnings
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/drug-food-warnings")
async def drug_food_warnings_endpoint(
    drugs: List[str] = Query(..., description="List of drug names"),
):
    """
    Return automatic food-drug interaction warnings for a list of drug names.
    Warnings are surfaced without the patient needing to ask.
    """
    logger.info(f"[{_ts()}] [ROUTES] GET /drug-food-warnings — drugs={drugs}")
    t_start = time.perf_counter()

    try:
        warnings = get_food_warnings(drugs)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(
            f"[{_ts()}] [ROUTES] GET /drug-food-warnings — "
            f"{len(warnings)} warnings in {elapsed_ms} ms"
        )
        return {
            "drug_names": drugs,
            "warnings": warnings,
            "total_warnings": len(warnings),
            "processing_time_ms": elapsed_ms,
        }
    except Exception as exc:
        logger.error(f"[{_ts()}] [ROUTES] /drug-food-warnings error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
#  GET /api/v1/insurance-summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/insurance-summary")
async def insurance_summary_endpoint(
    drugs: List[str] = Query(..., description="List of drug names"),
    scheme: str = Query("CGHS", description="Insurance scheme: PMJAY | CGHS | ESI"),
):
    """
    Return insurance coverage and financial summary for a list of drugs.
    Covers PMJAY, CGHS, and ESI schemes with brand vs generic pricing.
    """
    logger.info(
        f"[{_ts()}] [ROUTES] GET /insurance-summary — drugs={drugs}, scheme={scheme}"
    )
    t_start = time.perf_counter()

    try:
        result = get_insurance_summary(drugs, scheme=scheme)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(
            f"[{_ts()}] [ROUTES] GET /insurance-summary — "
            f"OOP=₹{result['financial_summary']['final_out_of_pocket_inr']} "
            f"in {elapsed_ms} ms"
        )
        result["processing_time_ms"] = elapsed_ms
        return result
    except Exception as exc:
        logger.error(f"[{_ts()}] [ROUTES] /insurance-summary error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
#  GET /api/v1/timeline
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/timeline")
async def timeline_endpoint(
    drugs: List[str] = Query(..., description="Drug names"),
    frequencies: List[str] = Query(..., description="Frequency tokens, one per drug"),
    doses: Optional[List[str]] = Query(None, description="Dose strings, one per drug"),
):
    """
    Generate a 24-hour medication timeline.
    Pass parallel lists: drugs[], frequencies[], doses[] (optional).
    """
    logger.info(
        f"[{_ts()}] [ROUTES] GET /timeline — {len(drugs)} drugs"
    )
    t_start = time.perf_counter()

    if len(drugs) != len(frequencies):
        raise HTTPException(
            status_code=400,
            detail="drugs and frequencies lists must have the same length",
        )

    medications = []
    for i, drug in enumerate(drugs):
        dose_str = doses[i] if doses and i < len(doses) else ""
        # Split dose into value+unit
        import re as _re
        dm = _re.match(r"([\d.]+)\s*([a-zA-Z%]+)?", dose_str or "")
        medications.append({
            "DrugName": drug,
            "Frequency": frequencies[i],
            "DoseValue": dm.group(1) if dm else "",
            "DoseUnit": dm.group(2) if dm and dm.group(2) else "",
        })

    try:
        result = generate_timeline(medications)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(
            f"[{_ts()}] [ROUTES] GET /timeline — "
            f"{result['total_doses_per_day']} doses/day in {elapsed_ms} ms"
        )
        result["processing_time_ms"] = elapsed_ms
        return result
    except Exception as exc:
        logger.error(f"[{_ts()}] [ROUTES] /timeline error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
# ─────────────────────────────────────────────────────────────────────────────
#  Auth Endpoints
# ─────────────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/auth/signup")
async def signup(body: SignupRequest):
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == body.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        new_user = User(
            email=body.email,
            password_hash=hash_password(body.password),
            name=body.name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        token = create_token(new_user.id, new_user.email)
        return {
            "token": token,
            "user": {"id": new_user.id, "email": new_user.email, "name": new_user.name}
        }
    finally:
        db.close()

@router.post("/auth/login")
async def login(body: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == body.email).first()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = create_token(user.id, user.email)
        return {
            "token": token,
            "user": {"id": user.id, "email": user.email, "name": user.name}
        }
    finally:
        db.close()

@router.get("/auth/me")
async def get_me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "email": user.email, "name": user.name}
    finally:
        db.close()

@router.get("/history")
async def get_history(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    history = get_user_history(payload["user_id"])
    return history

class ProfileUpdateRequest(BaseModel):
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    current_meds: Optional[str] = None
    emergency_contact: Optional[str] = None

@router.get("/profile")
async def get_profile(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    profile = get_user_profile(payload["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/profile")
async def update_profile_route(body: ProfileUpdateRequest, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    profile = update_user_profile(payload["user_id"], body.model_dump(exclude_unset=True))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.get("/public/medical-card/{user_id}")
async def get_medical_card_route(user_id: int):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    history = get_user_history(user_id)
    card_data = generate_medical_card(profile, history)
    
    return {
        "success": True,
        "user_id": user_id,
        "medical_card": card_data
    }
