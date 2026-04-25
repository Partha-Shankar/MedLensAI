import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def preprocess_image(image_pil: Image.Image) -> tuple[np.ndarray, Image.Image]:
    """
    Lightweight preprocessing before Gemini Vision.
    Gemini handles OCR — we just need a clean readable image.
    Steps: grayscale → deskew (angle clamped) → sharpen → back to RGB PIL
    """
    logger.info("[PREPROCESS] Starting lightweight preprocessing")

    img_array = np.array(image_pil.convert("RGB"))
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Detect and apply deskew with angle clamped to [-15, +15]
    angle = _detect_angle(gray)
    clamped = max(-15.0, min(15.0, angle))
    logger.info(f"[PREPROCESS] Deskew angle detected: {angle:.1f}° → clamped to {clamped:.1f}°")

    if abs(clamped) > 0.5:
        gray = _rotate_image(gray, clamped)

    # Mild unsharp mask — helps on blurry phone photos
    blurred = cv2.GaussianBlur(gray, (0, 0), 3)
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)

    # Return as RGB PIL (Gemini expects colour image)
    result_rgb = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)
    result_pil = Image.fromarray(result_rgb)

    # Enforce minimum resolution for Gemini Vision
    MIN_DIMENSION = 1000
    w, h = result_pil.size
    longest = max(w, h)
    if longest < MIN_DIMENSION:
        scale = MIN_DIMENSION / longest
        new_w, new_h = int(w * scale), int(h * scale)
        result_pil = result_pil.resize((new_w, new_h), Image.LANCZOS)
        result_rgb = np.array(result_pil)
        logger.info(f"[PREPROCESS] Upscaled from {(w, h)} to {(new_w, new_h)} — was below {MIN_DIMENSION}px")

    logger.info(f"[PREPROCESS] Complete — output size: {result_pil.size}")
    return result_rgb, result_pil


def _detect_angle(gray: np.ndarray) -> float:
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180,
        threshold=80, minLineLength=100, maxLineGap=10
    )
    if lines is None:
        return 0.0
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 != x1:
            angles.append(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
    return float(np.median(angles)) if angles else 0.0


def _rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(
        img, M, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE
    )
