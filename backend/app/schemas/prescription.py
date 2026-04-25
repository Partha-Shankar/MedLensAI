"""
MedLens AI — Pydantic v2 Schemas
Defines Medication and Prescription output models with strict validation.
"""
from __future__ import annotations
from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, field_validator, model_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FieldSource(str, Enum):
    OCR = "ocr"
    GROQ_FALLBACK = "groq_fallback"
    REGEX = "regex"
    NLP = "nlp"


# ── Sub-models ────────────────────────────────────────────────────────────────

class CorrectionTrace(BaseModel):
    raw_ocr_text: str
    matched_drug: str
    method: str  # "exact" | "rapidfuzz_local" | "rxnorm_api" | "groq_fallback"
    rapidfuzz_score: float
    levenshtein_distance: int
    candidate_shortlist: list[dict]
    correction_applied: bool

class OCRLineResult(BaseModel):
    """Raw OCR output for a single text line."""
    raw_text: str
    source_zone: str
    confidence: float
    model_used: str
    agreement_flag: bool = True
    bounding_box: Optional[List[int]] = None  # [x, y, w, h]


class FieldValue(BaseModel):
    """Wrapper that carries a value alongside its provenance."""
    value: str
    source: FieldSource = FieldSource.OCR
    confidence: float = 1.0


# ── Core prescription models ──────────────────────────────────────────────────

class Medication(BaseModel):
    DrugName: str = "MISSING"
    DoseValue: str = "MISSING"
    DoseUnit: str = "MISSING"
    Frequency: str = "MISSING"
    Duration: str = "MISSING"
    Route: str = "MISSING"
    AdminInstructions: str = "MISSING"
    ConfidenceLevel: ConfidenceLevel = ConfidenceLevel.LOW
    correction_trace: Optional[CorrectionTrace] = None

    # Provenance metadata (optional, won't break serialisation if absent)
    DrugName_source: Optional[str] = None
    DoseValue_source: Optional[str] = None
    DoseUnit_source: Optional[str] = None
    Frequency_source: Optional[str] = None
    Duration_source: Optional[str] = None
    Route_source: Optional[str] = None
    AdminInstructions_source: Optional[str] = None

    # Per-field confidence scores
    field_scores: Optional[dict] = None

    @field_validator(
        "DrugName", "DoseValue", "DoseUnit", "Frequency",
        "Duration", "Route", "AdminInstructions",
        mode="before"
    )
    @classmethod
    def coerce_none_to_missing(cls, v: Any) -> str:
        """Guarantee no field ever holds None or empty string."""
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return "MISSING"
        return str(v)

    @property
    def missing_fields(self) -> List[str]:
        fields = ["DrugName", "DoseValue", "DoseUnit", "Frequency",
                  "Duration", "Route", "AdminInstructions"]
        return [f for f in fields if getattr(self, f) == "MISSING"]

    @property
    def is_complete(self) -> bool:
        return len(self.missing_fields) == 0


class Prescription(BaseModel):
    PatientName: str = "MISSING"
    Age: str = "MISSING"
    Sex: str = "MISSING"
    Date: str = "MISSING"
    Diagnosis: str = "MISSING"
    PrescriberName: str = "MISSING"
    Medications: List[Medication] = []

    # Review flags
    ReviewRequired: bool = False
    ReviewFields: List[str] = []

    # Groq fallback metadata
    groq_unavailable: bool = False
    groq_fields_filled: List[str] = []

    # Overall pipeline confidence
    overall_confidence: float = 0.0
    pipeline_version: str = "1.0.0"

    @field_validator(
        "PatientName", "Age", "Sex", "Date", "Diagnosis", "PrescriberName",
        mode="before"
    )
    @classmethod
    def coerce_none_to_missing(cls, v: Any) -> str:
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return "MISSING"
        return str(v)

    @property
    def header_missing_fields(self) -> List[str]:
        fields = ["PatientName", "Age", "Sex", "Date", "Diagnosis", "PrescriberName"]
        return [f for f in fields if getattr(self, f) == "MISSING"]

    @property
    def low_confidence_med_count(self) -> int:
        return sum(1 for m in self.Medications if m.ConfidenceLevel == ConfidenceLevel.LOW)


# ── API request/response wrappers ─────────────────────────────────────────────

class ExtractionResponse(BaseModel):
    success: bool
    prescription: Optional[Prescription] = None
    raw_ocr_lines: List[OCRLineResult] = []
    processing_time_ms: float = 0.0
    errors: List[str] = []
    history_id: Optional[int] = None


class DosageValidationRequest(BaseModel):
    drug_name: str
    dose_value: str
    dose_unit: str
    frequency: Optional[str] = None
    patient_age: Optional[str] = None
    diagnosis: Optional[str] = None


class DosageValidationResponse(BaseModel):
    plausible: bool
    reason: str
    confidence: str
    suggested_dose: Optional[str] = None


class InteractionRequest(BaseModel):
    drug_names: List[str]


class InteractionPair(BaseModel):
    drug_a: str
    drug_b: str
    severity: str           # MAJOR / MODERATE / MINOR
    mechanism: str
    consequence: str
    temporal_flag: str      # e.g. "Avoid concurrent use"
    substitution_suggestion: str


class InteractionResponse(BaseModel):
    checked_drugs: List[str]
    interaction_pairs: List[InteractionPair]
    total_interactions: int
