import base64
import json
import logging
import re
import time
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize client once at module load
client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"

PRESCRIPTION_EXTRACTION_PROMPT = """
You are a medical prescription OCR and extraction system specialized in
handwritten Indian prescriptions.

Extract ALL information from this prescription image and return ONLY a JSON
object. No explanation. No markdown fences. No preamble. Just the raw JSON.

Return this exact structure:

{
  "patient_name": "",
  "age": "",
  "sex": "",
  "date": "",
  "doctor_name": "",
  "registration_number": "",
  "clinic_name": "",
  "chief_complaints": [],
  "medications": [
    {
      "raw_text": "",
      "drug_name": "",
      "dose_value": "",
      "dose_unit": "",
      "frequency": "",
      "duration": "",
      "route": "",
      "admin_instructions": ""
    }
  ]
}

Rules you must follow:
1. raw_text = copy the exact handwritten text for that drug line, even if misspelled
2. drug_name = your best interpretation of the drug name (may differ from raw_text)
3. dose_value = numeric value only e.g. "650" not "650mg"
4. dose_unit = unit only e.g. "mg", "ml", "mcg"
5. frequency = standard notation: OD, BD, TDS, QID, HS, SOS, PRN, BBF, AF
   - "once daily" → "OD"
   - "twice daily" → "BD"
   - "three times daily" → "TDS"
   - "at night" / "at bedtime" → "HS"
   - "every 6-8 hours if fever" → "Q6-8H PRN fever"
   - "1-0-1" → "BD (morning + night)"
   - "1-1-1" → "TDS"
   - "0-0-1" → "HS"
6. duration = e.g. "3 days", "2 weeks", "1 month"
7. admin_instructions = e.g. "after food", "before breakfast", "empty stomach",
   "maximum 3 tablets/day"
8. route = "oral" for tablets/capsules/syrups unless specified otherwise.
   If not written and it is a tablet, default to "oral"
9. If any field is genuinely absent use empty string ""
   NEVER use null, None, or omit any key
10. Extract ALL medications — do not skip any even if handwriting is unclear
11. chief_complaints = list of strings, one per complaint
12. For Indian brand names keep the brand name as drug_name
"""


def pil_to_jpeg_bytes(image: Image.Image, max_size: int = 1600) -> bytes:
    """Resize if needed and return JPEG bytes."""
    w, h = image.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        image = image.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        logger.info(f"[GEMINI_VISION] Resized image to {image.size}")

    if image.mode != "RGB":
        image = image.convert("RGB")

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()


def extract_prescription_from_image(image_pil: Image.Image) -> dict:
    """
    Primary OCR function. Sends image to Gemini 2.5 Flash and returns
    structured prescription dict.

    On any failure returns safe empty dict with parse_error=True
    so groq_fallback can handle missing fields.
    """
    start = time.time()
    logger.info(f"[GEMINI_VISION] Starting extraction — model: {MODEL_NAME}")

    try:
        image_bytes = pil_to_jpeg_bytes(image_pil)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                ),
                PRESCRIPTION_EXTRACTION_PROMPT
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8192,
            )
        )

        raw_output = response.text.strip()
        elapsed = time.time() - start
        logger.info(f"[GEMINI_VISION] API response received in {elapsed:.2f}s")

        # Detect truncated response — a valid JSON object must end with }
        stripped = raw_output.strip().rstrip('`').strip()
        if not stripped.endswith('}'):
            logger.error(
                f"[GEMINI_VISION] Response appears TRUNCATED — "
                f"last 80 chars: ...{stripped[-80:]}"
            )
            # Attempt to close the JSON by finding the last complete medication entry
            # and closing all open brackets
            stripped = _attempt_json_recovery(stripped)

        result = _clean_and_parse_json(stripped)
        result = _ensure_structure(result)

        meds = result.get("medications", [])
        logger.info(f"[GEMINI_VISION] Extraction complete — {len(meds)} medications found")
        for i, med in enumerate(meds):
            logger.info(
                f"[GEMINI_VISION] Med {i+1}: "
                f"raw=\"{med.get('raw_text', '')}\" "
                f"drug=\"{med.get('drug_name', '')}\" "
                f"dose=\"{med.get('dose_value', '')}{med.get('dose_unit', '')}\" "
                f"freq=\"{med.get('frequency', '')}\""
            )

        return result

    except (json.JSONDecodeError, ValueError) as e:
        elapsed = time.time() - start
        logger.error(f"[GEMINI_VISION] JSON parse failed after {elapsed:.2f}s: {e}")
        logger.error(f"[GEMINI_VISION] Problematic output: {raw_output[:500]}")
        return _empty_result(raw_text=raw_output)

    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"[GEMINI_VISION] API call failed after {elapsed:.2f}s: {e}")
        return _empty_result(raw_text=str(e))


def _clean_and_parse_json(raw: str) -> dict:
    """
    Multi-strategy JSON parser. Tries progressively more aggressive fixes.
    """
    # Strategy 1: direct parse
    try:
        data = json.loads(raw)
        logger.info("[GEMINI_VISION] JSON parsed successfully via strategy 1")
        return data
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip markdown fences
    clean = raw.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1] if len(parts) > 1 else clean
        if clean.lower().startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    try:
        data = json.loads(clean)
        logger.info("[GEMINI_VISION] JSON parsed successfully via strategy 2")
        return data
    except json.JSONDecodeError:
        pass

    # Strategy 3: extract first { ... } block
    match = re.search(r'\{.*\}', clean, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            logger.info("[GEMINI_VISION] JSON parsed successfully via strategy 3")
            return data
        except json.JSONDecodeError:
            pass

    # Strategy 4: fix trailing commas before } or ]
    fixed = re.sub(r',\s*([}\]])', r'\1', clean)
    try:
        data = json.loads(fixed)
        logger.info("[GEMINI_VISION] JSON parsed successfully via strategy 4")
        return data
    except json.JSONDecodeError:
        pass

    # Strategy 5: fix trailing commas + remove // comments
    fixed2 = re.sub(r'//[^\n]*', '', fixed)          # strip // comments
    fixed2 = re.sub(r',\s*([}\]])', r'\1', fixed2)   # trailing commas again
    try:
        data = json.loads(fixed2)
        logger.info("[GEMINI_VISION] JSON parsed successfully via strategy 5")
        return data
    except json.JSONDecodeError as final_err:
        raise final_err  # let caller handle


def _attempt_json_recovery(partial: str) -> str:
    """
    When JSON is truncated mid-response, try to close it gracefully
    so at least the medications already parsed are not lost.
    """
    # Remove the last incomplete line (likely cut off mid-value)
    lines = partial.rsplit('\n', 1)
    if len(lines) > 1:
        partial = lines[0].rstrip().rstrip(',')

    # Count unclosed braces and brackets
    open_braces = partial.count('{') - partial.count('}')
    open_brackets = partial.count('[') - partial.count(']')

    # Close in reverse order
    for _ in range(open_brackets):
        partial += '\n  ]'
    for _ in range(open_braces):
        partial += '\n}'

    logger.warning(
        f"[GEMINI_VISION] Recovery attempted — "
        f"closed {open_brackets} brackets, {open_braces} braces"
    )
    return partial


def _empty_result(raw_text: str = "") -> dict:
    return {
        "parse_error": True,
        "raw_text": raw_text,
        "patient_name": "", "age": "", "sex": "", "date": "",
        "doctor_name": "", "registration_number": "", "clinic_name": "",
        "chief_complaints": [], "medications": []
    }


def _ensure_structure(result: dict) -> dict:
    """Ensure all required keys exist with correct types. Never raises."""
    top_defaults = {
        "patient_name": "", "age": "", "sex": "", "date": "",
        "doctor_name": "", "registration_number": "", "clinic_name": "",
        "chief_complaints": [], "medications": []
    }
    for key, default in top_defaults.items():
        if key not in result or result[key] is None:
            logger.warning(f"[GEMINI_VISION] Missing key in response: {key} — using default")
            result[key] = default

    med_defaults = {
        "raw_text": "", "drug_name": "", "dose_value": "",
        "dose_unit": "", "frequency": "", "duration": "",
        "route": "oral", "admin_instructions": ""
    }
    for med in result.get("medications", []):
        for key, default in med_defaults.items():
            if key not in med or med[key] is None:
                med[key] = default

    return result
