import os
import logging
from openai import OpenAI
from app.config import OPENAI_API_KEY, IS_API_KEY_VALID

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=OPENAI_API_KEY if IS_API_KEY_VALID else "dummy_key")

CLINICAL_MOCK_TRANSCRIPTS = [
    "The patient is a 55-year-old male with a history of Stage 2 Hypertension. He's been checking his blood pressure at home and it's running around 145 over 92. He complains of mild headaches but denies any chest pain, shortness of breath, or palpitations. He is currently on no medications. We will start him on Lisinopril 10 mg daily and check a BMP in two weeks.",
    "A 34-year-old female presents with acute shortness of breath and expiratory wheezing that started last night. She has a history of childhood asthma and has been using an albuterol inhaler three times a day for the past week. She denies fever, chills, or productive cough. On exam, diffuse expiratory wheezes are present. We will start a daily low-dose ICS-formoterol inhaler and follow up in two weeks.",
    "The patient is a 62-year-old female coming in for a follow-up on her Type 2 Diabetes. Her latest home glucose readings have been averaging 160. She is currently taking Metformin 500 mg twice a day. She denies any polyuria, polydipsia, or blurred vision, but she is scheduled for an outpatient CT scan with iodinated contrast dye next Tuesday. We discussed withholding Metformin for 48 hours post-contrast and checking a basic metabolic panel to monitor renal function.",
    "A 28-year-old male presents with acute onset watery diarrhea and moderate vomiting for the last 24 hours. He denies bloody stools or high fevers. He reports feeling lightheaded. On exam, mucous membranes are slightly dry. We will initiate oral rehydration therapy with ORS and prescribe Ondansetron 4 mg as needed for nausea. Loperamide was advised against."
]

def transcribe_audio_file(file_path: str) -> tuple:
    """Sends audio to OpenAI Whisper API, falls back to mock transcript if key has no quota."""
    if not IS_API_KEY_VALID:
        logger.info("No valid OpenAI API Key. Returning fallback clinical simulation transcript.")
        return CLINICAL_MOCK_TRANSCRIPTS[0], True
        
    try:
        with open(file_path, "rb") as audio_file:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        logger.info("Audio transcribed successfully via OpenAI Whisper API.")
        return response.text, False
    except Exception as e:
        logger.warning(f"OpenAI Whisper transcription failed ({e}). Using simulated clinical audio fallback.")
        # Return fallback based on hash of filepath to ensure consistency
        idx = hash(file_path) % len(CLINICAL_MOCK_TRANSCRIPTS)
        return CLINICAL_MOCK_TRANSCRIPTS[idx], True


