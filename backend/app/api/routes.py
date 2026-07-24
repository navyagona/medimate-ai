import os
import shutil
import tempfile
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.models.schemas import SoapGenerationResponse, SaveNoteRequest
from app.services.transcription import transcribe_audio_file
from app.services.soap_generator import generate_soap_note_draft
from app.services.db import get_saved_notes, save_patient_note, get_eval_results_db, save_eval_results_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Transcribes an uploaded audio file using Whisper with offline fallback."""
    # Write to a temporary file
    temp_dir = tempfile.gettempdir()
    suffix = os.path.splitext(audio.filename)[1] or ".wav"
    temp_path = os.path.join(temp_dir, f"upload_{os.urandom(8).hex()}{suffix}")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
        transcript_text = transcribe_audio_file(temp_path)
        logger.info(f"Successfully processed audio upload ({audio.filename})")
        return {"text": transcript_text}
    except Exception as e:
        logger.error(f"Error during audio upload transcription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Transcription service failure.")
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_err:
                logger.warning(f"Could not remove temporary file {temp_path}: {cleanup_err}")

@router.post("/generate-soap", response_model=SoapGenerationResponse)
async def generate_soap(payload: dict):
    """Generates structured SOAP Note, ICD-10 suggestions, and drug check warnings."""
    transcript = payload.get("transcript")
    force_offline = payload.get("forceOffline", False)
    
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is required.")
        
    try:
        result = await generate_soap_note_draft(transcript, force_offline)
        logger.info(f"SOAP note draft generated successfully (acuity: {result.get('acuityLevel')})")
        return result
    except Exception as e:
        logger.error(f"Error during SOAP generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save-note")
def save_note(note: SaveNoteRequest):
    """Saves a doctor-approved patient note draft."""
    try:
        saved = save_patient_note(note.model_dump())
        logger.info(f"Patient note saved (ID: {saved.get('id')})")
        return {"success": True, "note": saved}
    except Exception as e:
        logger.error(f"Failed to save patient record: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save patient record: {e}")

@router.get("/notes")
def get_notes():
    """Retrieves list of all saved approved notes."""
    try:
        notes = get_saved_notes()
        logger.info(f"Retrieved {len(notes)} saved notes")
        return notes
    except Exception as e:
        logger.error(f"Failed to retrieve notes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-eval")
async def run_evaluation_endpoint():
    """Triggers the evaluation script and computes metrics on 50 samples."""
    try:
        logger.info("Triggering clinical evaluation pipeline run...")
        from eval.evaluate import run_eval_pipeline
        results = await run_eval_pipeline()
        logger.info(f"Evaluation pipeline completed with overall score: {results.get('metrics', {}).get('overall_compliance')}%")
        return results
    except Exception as e:
        logger.error(f"Error running evaluations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute evaluation: {e}")

@router.get("/eval-results")
def get_evaluation_results():
    """Retrieves cached results of the last evaluation run."""
    results = get_eval_results_db()
    if not results:
        logger.info("Requested evaluation results, but none are cached yet")
        return {"error": "No evaluations have been run yet. Trigger it from the dashboard."}
    return results

