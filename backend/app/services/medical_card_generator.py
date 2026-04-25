import logging
from google import genai
from google.genai import types
from app.core.config import settings
import json

logger = logging.getLogger(__name__)

# Initialize client once at module load
client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

def generate_medical_card(profile_data: dict, history_data: list) -> dict:
    prompt = f"""
You are an expert medical AI assistant. Your task is to generate an Emergency Medical Card for a patient.
You are given the patient's self-reported profile data and their recent prescription history.

Profile Data:
{json.dumps(profile_data, indent=2)}

Prescription History (recent first):
{json.dumps(history_data[:10], indent=2)}

Extract and structure this information into a critical, easy-to-read emergency medical summary.
Return ONLY a JSON object with this exact structure:
{{
  "patient_name": "...",
  "blood_group": "...",
  "emergency_contact": "...",
  "known_allergies": [...],
  "chronic_conditions": [...],
  "current_medications": [
    {{
      "drug_name": "...",
      "dosage": "...",
      "frequency": "..."
    }}
  ],
  "recent_medical_history_summary": "A 2-3 sentence summary of recent treatments based on history",
  "critical_warnings": ["...any severe interactions or high-risk drugs..."]
}}
No explanation, no markdown fences. Just raw JSON.
"""
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2048,
            )
        )
        
        raw_output = response.text.strip()
        if raw_output.startswith("```"):
            parts = raw_output.split("```")
            raw_output = parts[1] if len(parts) > 1 else raw_output
            if raw_output.lower().startswith("json"):
                raw_output = raw_output[4:]
        
        return json.loads(raw_output.strip())
    except Exception as e:
        logger.error(f"[MEDICAL_CARD] Failed to generate medical card: {e}")
        # fallback
        return {
            "patient_name": profile_data.get("name", "Unknown"),
            "blood_group": profile_data.get("blood_group", "Unknown"),
            "emergency_contact": profile_data.get("emergency_contact", "None"),
            "known_allergies": [profile_data.get("allergies", "")] if profile_data.get("allergies") else [],
            "chronic_conditions": [profile_data.get("conditions", "")] if profile_data.get("conditions") else [],
            "current_medications": [],
            "recent_medical_history_summary": "Generation failed.",
            "critical_warnings": []
        }
