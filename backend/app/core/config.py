"""
MedLens AI — Application Configuration
Centralises all environment variables and runtime settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "MedLens AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── API Keys ─────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ── Model paths / names ───────────────────────────────────────────────────
    TROCR_MODEL_NAME: str = "microsoft/trocr-large-handwritten"
    PADDLE_LANG: str = "en"

    # ── Thresholds ────────────────────────────────────────────────────────────
    TROCR_HIGH_CONFIDENCE: float = 0.75
    TROCR_LOW_CONFIDENCE: float = 0.60
    RAPIDFUZZ_DRUG_THRESHOLD: int = 80
    MEDICINE_LINE_SCORE_THRESHOLD: float = 1.0
    MISSING_FIELD_TRIGGER_PCT: float = 0.30
    LOW_CONFIDENCE_MED_TRIGGER_PCT: float = 0.30
    GROQ_TIMEOUT_SECONDS: int = 5

    # ── Layout zone thresholds (% of image height) ────────────────────────────
    HEADER_TOP_PCT: float = 0.0
    HEADER_BOTTOM_PCT: float = 0.20
    PATIENT_TOP_PCT: float = 0.20
    PATIENT_BOTTOM_PCT: float = 0.40
    RX_TOP_PCT: float = 0.40
    RX_BOTTOM_PCT: float = 0.80
    FOOTER_TOP_PCT: float = 0.80
    FOOTER_BOTTOM_PCT: float = 1.00

    # ── Data file paths ───────────────────────────────────────────────────────
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DRUG_INDEX_PATH: str = os.path.join(BASE_DIR, "data", "indian_drug_index.json")
    INTERACTION_DB_PATH: str = os.path.join(BASE_DIR, "data", "interaction_database.json")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
