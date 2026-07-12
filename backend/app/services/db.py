import os
import json
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
NOTES_PATH = os.path.join(BASE_DIR, "backend", "data", "saved_notes.json")
EVALS_PATH = os.path.join(BASE_DIR, "backend", "data", "eval_results.json")

def ensure_file_exists(file_path: str, default_data=None):
    if default_data is None:
        default_data = []
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2)

def get_saved_notes() -> list:
    ensure_file_exists(NOTES_PATH, [])
    try:
        with open(NOTES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_patient_note(note_data: dict) -> dict:
    ensure_file_exists(NOTES_PATH, [])
    notes = get_saved_notes()
    
    if not note_data.get("id"):
        note_data["id"] = "note_" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=9))
        
    # Check if duplicate and update, or append
    index = -1
    for i, n in enumerate(notes):
        if n.get("id") == note_data["id"]:
            index = i
            break
            
    if index != -1:
        notes[index] = {**notes[index], **note_data}
    else:
        notes.append(note_data)
        
    with open(NOTES_PATH, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)
        
    return note_data

def get_eval_results_db() -> dict:
    ensure_file_exists(EVALS_PATH, {})
    try:
        with open(EVALS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_eval_results_db(results: dict) -> dict:
    ensure_file_exists(EVALS_PATH, {})
    with open(EVALS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return results
