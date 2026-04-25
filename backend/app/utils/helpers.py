"""
MedLens AI — Shared Helpers / Utilities
"""
from __future__ import annotations
import time
import datetime
import logging
from typing import Any


# ── Structured console logger ─────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger


# ── Timing decorator ──────────────────────────────────────────────────────────

class Timer:
    """Context manager that measures elapsed ms."""

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000

    @property
    def elapsed(self) -> float:
        return round(self.elapsed_ms, 2)


# ── Image helpers ─────────────────────────────────────────────────────────────

def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def pct_crop(img_h: int, img_w: int, top_pct: float, bot_pct: float):
    """Return (y1, y2) pixel coords from percentage thresholds."""
    y1 = int(img_h * top_pct)
    y2 = int(img_h * bot_pct)
    return y1, y2


# ── String utilities ──────────────────────────────────────────────────────────

OCR_CORRUPTION_MAP: dict[str, str] = {
    "0": "O",
    "1": "l",
    "rn": "m",
    "|": "I",
}


def apply_ocr_corrections(token: str) -> str:
    """Fix common single-char OCR corruption patterns."""
    for wrong, right in OCR_CORRUPTION_MAP.items():
        token = token.replace(wrong, right)
    return token


def normalise_drug_token(token: str) -> str:
    """Strip non-alpha chars and title-case for fuzzy matching."""
    import re
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", token).strip()
    return cleaned.title()


# ── Date helper ───────────────────────────────────────────────────────────────

def utc_now_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"
