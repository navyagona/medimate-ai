import io
import pytest

def test_api_generate_soap_success(client):
    """Integration Test: POST /api/generate-soap with transcript payload."""
    payload = {
        "transcript": "62-year-old female for follow-up of Type 2 Diabetes taking Metformin 500mg.",
        "forceOffline": True
    }
    response = client.post("/api/generate-soap", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "soapNote" in data
    assert "icd10" in data
    assert "acuityLevel" in data

def test_api_generate_soap_missing_transcript(client):
    """Integration Test: POST /api/generate-soap without transcript returns 400 error."""
    response = client.post("/api/generate-soap", json={})
    assert response.status_code == 400
    assert "Transcript is required" in response.json()["detail"]

def test_api_save_and_retrieve_notes_flow(client):
    """Integration Test: POST /api/save-note followed by GET /api/notes."""
    sample_note = {
        "id": "test_note_integration_123",
        "patientName": "John Doe",
        "transcript": "55yo male hypertension checkup",
        "soapNote": {
            "subjective": "Headache reported.",
            "objective": "BP 142/90.",
            "assessment": "Stage 1 Hypertension, suspected.",
            "plan": "Lisinopril 10mg daily."
        },
        "icd10": [{"code": "I10", "description": "Essential hypertension", "confidence": 0.95}],
        "tests": ["BMP", "ECG"],
        "drugInteractions": [],
        "acuityLevel": "Moderate",
        "isOutsideScope": False,
        "safetyRefusals": [],
        "status": "Approved"
    }
    
    # 1. Save note
    save_resp = client.post("/api/save-note", json=sample_note)
    assert save_resp.status_code == 200
    save_data = save_resp.json()
    assert save_data["success"] is True
    assert save_data["note"]["id"] == "test_note_integration_123"

    
    # 2. Retrieve notes list
    get_resp = client.get("/api/notes")
    assert get_resp.status_code == 200
    notes_list = get_resp.json()
    assert isinstance(notes_list, list)
    assert any(n.get("id") == "test_note_integration_123" for n in notes_list)

def test_api_get_eval_results(client):
    """Integration Test: GET /api/eval-results returns valid JSON response."""
    response = client.get("/api/eval-results")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)

def test_api_transcribe_audio_upload(client):
    """Integration Test: POST /api/transcribe with simulated audio file upload."""
    fake_wav_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    files = {"audio": ("test_clinical_recording.wav", io.BytesIO(fake_wav_bytes), "audio/wav")}
    response = client.post("/api/transcribe", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert len(data["text"]) > 0
