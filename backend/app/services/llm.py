import os
import json
import re
import logging
from openai import OpenAI
from app.config import OPENAI_API_KEY, IS_API_KEY_VALID
import app.services.rag as rag
from app.services.drug_interactions import check_drug_safety
from app.services.icd10 import search_icd10_codes, ICD10_CODES_DB
from app.models.schemas import SoapGenerationResponse, SoapNote, ICD10Suggestion

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=OPENAI_API_KEY if IS_API_KEY_VALID else "dummy_key", max_retries=0)

# Guidelines retrieval will use rag.retrieve_guidelines

def run_offline_clinical_expert_system(transcript: str) -> dict:
    """Offline Python expert system using keyword extraction, guideline retrieval, and clinical logic."""
    logger.info("Executing offline clinical expert system rules engine...")
    text_lower = transcript.lower()
    
    # 1. Retrieve RAG guidelines context
    guidelines = rag.retrieve_guidelines(transcript, limit=2)
    guideline_titles = [g["title"] for g in guidelines]
    
    # 2. Match condition domains
    matched_conditions = []
    if re.search(r"hypertension|blood pressure|high bp|systolic|diastolic|140/\d+|150/\d+", text_lower):
        matched_conditions.append("Hypertension")
    if re.search(r"diabetes|diabetic|metformin|sugar|a1c|glucose", text_lower):
        matched_conditions.append("Type 2 Diabetes")
    if re.search(r"asthma|wheez|inhaler|albuterol|shortness of breath|dyspnea", text_lower):
        matched_conditions.append("Asthma")
    if re.search(r"diarrhea|vomit|nausea|gastroenteritis|stomach", text_lower):
        matched_conditions.append("Acute Gastroenteritis")
        
    # 3. Check safety flags & acuity
    acuity_level = "Low"
    is_outside_scope = False
    safety_refusals = []
    
    is_chest_pain = re.search(r"chest pain|chest pressure|substernal|radiat.*arm|radiat.*jaw|crushing pain", text_lower)
    is_stroke = re.search(r"facial droop|arm drift|slur.*speech|stroke|numbness.*side|weakness.*side|fast", text_lower)
    
    if is_chest_pain or is_stroke:
        acuity_level = "High"
        is_outside_scope = True
        matched_conditions.append("Emergency Medicine")
        if is_chest_pain:
            safety_refusals.append("CRITICAL REFUSAL: Patient reports high-acuity chest symptoms (substernal pain/pressure) suggestive of potential Acute Coronary Syndrome. Outpatient virtual assistance is bypassed. Patient must report to the nearest emergency department immediately.")
        if is_stroke:
            safety_refusals.append("CRITICAL REFUSAL: Patient reports acute onset focal neurological deficits (slurred speech, facial droop, arm drift) indicating a stroke. Emergency medical services must be activated immediately.")
    elif matched_conditions:
        acuity_level = "Moderate"
        
    # 4. Drug safety checks
    detected_drugs = []
    for d in ["aspirin", "warfarin", "lisinopril", "losartan", "metformin", "contrast", "dye", "ct scan", "ibuprofen", "sildenafil", "viagra", "nitroglycerin", "nitro"]:
        if d in text_lower:
            detected_drugs.append(d)
    drug_warnings = check_drug_safety(detected_drugs)
    
    # 5. Suggest ICD-10 codes
    icd10_suggestions = []
    for cond in matched_conditions:
        for code_obj in search_icd10_codes(cond):
            if not any(x["code"] == code_obj["code"] for x in icd10_suggestions):
                icd10_suggestions.append(code_obj)
                
    if not icd10_suggestions:
        icd10_suggestions.append({
            "code": "Z00.00",
            "description": "Encounter for general adult medical examination without abnormal findings",
            "confidence": 0.5,
            "rationale": "No primary active condition matches detected."
        })
        
    # 6. Suggested tests
    suggested_tests = []
    if "Hypertension" in matched_conditions:
        suggested_tests.extend(["Home Blood Pressure Log", "Basic Metabolic Panel (BMP)", "Lipid Panel", "ECG"])
    if "Type 2 Diabetes" in matched_conditions:
        suggested_tests.extend(["Hemoglobin A1c (HbA1c)", "eGFR and Serum Creatinine", "Urine Albumin-to-Creatinine Ratio (UACR)"])
    if "Asthma" in matched_conditions:
        suggested_tests.extend(["Spirometry with bronchodilator reversibility", "Peak Expiratory Flow Rate log"])
    if "Acute Gastroenteritis" in matched_conditions:
        suggested_tests.extend(["Oral hydration assessment", "Stool culture (if fever or bloody stools)"])
    if "Emergency Medicine" in matched_conditions:
        suggested_tests.extend(["Immediate 12-lead ECG", "Serum Cardiac Troponins", "Urgent Head CT scan"])
        
    if not suggested_tests:
        suggested_tests.append("Routine clinical observation")
        
    # 7. Draft SOAP content
    subjective = "Patient presents for clinical evaluation.\n"
    objective = "Vital signs reviewed.\n"
    assessment = f"Clinical guidelines referenced: {', '.join(guideline_titles) if guideline_titles else 'General Outpatient'}.\n"
    plan = ""
    
    if is_outside_scope:
        subjective += "• EMERGENCY WARNING: High-acuity presentation with life-threatening symptoms.\n"
        objective += "• Patient requires clinical stabilization immediately.\n"
        assessment += "• WARNING: Out-of-scope emergency scenario. Definitive outpatient assessment is withheld.\n"
        plan += "1. **EMERGENCY PATHWAY ACTIVATED**: Direct patient to call 911 or report to the nearest emergency department immediately.\n2. Arrange emergency transportation.\n3. Hold all standard oral outpatient therapy.\n"
    else:
        if "Hypertension" in matched_conditions:
            subjective += "• Patient reporting history of elevated blood pressures at home.\n"
            objective += "• Vitals show blood pressure elevated. No signs of target organ damage.\n"
            assessment += "• Suspected Stage 1/2 Hypertension, pending verification of home BP log.\n• Disclaimer: Suspected diagnosis only, pending physician verification.\n"
            plan += "1. Prescribe standard first-line antihypertensive therapy (e.g. Lisinopril 10mg daily).\n2. Request 2-week home blood pressure log.\n"
        if "Type 2 Diabetes" in matched_conditions:
            subjective += "• Patient presents for follow up of diabetes management.\n"
            objective += "• Discussion of home fingerstick readings and dietary adherence.\n"
            assessment += "• Suspected Type 2 Diabetes Mellitus under review.\n• Disclaimer: Suspected diagnosis, pending physician verification.\n"
            plan += "1. Review and adjust Metformin dose as tolerated.\n2. Advise low glycemic diet and exercise.\n"
        if "Asthma" in matched_conditions:
            subjective += "• Complaints of episodic shortness of breath and wheezing.\n"
            objective += "• Patient chest exam shows expiratory wheezing.\n"
            assessment += "• Suspected asthma, uncomplicated.\n• Disclaimer: Suspected diagnosis, pending pulmonary function tests.\n"
            plan += "1. Prescribe low-dose Inhaled Corticosteroid (ICS) controller as needed.\n2. Provide Asthma Action Plan.\n"
        if "Acute Gastroenteritis" in matched_conditions:
            subjective += "• Reports diarrhea, vomiting, and abdominal cramping.\n"
            objective += "• Mucous membranes dry. No severe hemodynamic compromise.\n"
            assessment += "• Acute gastroenteritis, suspected viral etiology.\n"
            plan += "1. Initiate oral rehydration therapy (ORS).\n2. Ondansetron 4mg as-needed for nausea.\n3. Avoid anti-motility agents.\n"
            
        if not matched_conditions:
            subjective += "• Patient routine check-up request.\n"
            objective += "• Examination normal.\n"
            assessment += "• General health consultation.\n"
            plan += "1. Standard health counseling and follow-up.\n"
            
    if drug_warnings:
        plan += "\n\n⚠️ **CLINICAL DRUG WARNINGS**:\n" + "\n".join([f"• {w}" for w in drug_warnings])
        
    return {
        "soapNote": {
            "subjective": subjective,
            "objective": objective,
            "assessment": assessment,
            "plan": plan
        },
        "icd10": icd10_suggestions,
        "tests": list(set(suggested_tests)),
        "drugInteractions": drug_warnings,
        "acuityLevel": acuity_level,
        "isOutsideScope": is_outside_scope,
        "safetyRefusals": safety_refusals,
        "relevantGuidelines": [{"id": g["id"], "title": g["title"], "condition": g["condition"]} for g in guidelines]
    }

async def generate_clinical_analysis(transcript: str, force_offline: bool = False) -> dict:
    """Generates SOAP note using OpenAI gpt-4o-mini, falling back to local expert system on error."""
    if force_offline or not IS_API_KEY_VALID or rag._api_quota_exceeded:
        return run_offline_clinical_expert_system(transcript)
        
    try:
        # Retrieve guidelines context
        guidelines = rag.retrieve_guidelines(transcript, limit=3)
        context = "\n\n".join([
            f"Guideline {g['id']} ({g['condition']} - {g['title']}):\n{g['content']}" 
            for g in guidelines
        ])
        
        prompt = f"""You are MediMate, an expert B2B clinical copilot.
Analyze the doctor-patient conversation or clinical summary below, and produce a structured analysis.

## Clinical RAG Guidelines Context:
{context}

## Patient Dialogue / Summary:
"{transcript}"

## Safety Instructions:
1. **Diagnosis Refusal Rails**: NEVER assert a definitive diagnosis for any condition. Under the Assessment (S) section, list suspected conditions with a clear disclaimer: "Suspected, pending physician verification". If the user asks for a finalized diagnosis, explicitly refuse in the 'safetyRefusals' field.
2. **Acuity & Scope Screening**: Detect emergency situations (e.g. active MI/chest pain, stroke, acute severe respiratory distress). If found:
   - Set 'acuityLevel' to "High"
   - Set 'isOutsideScope' to true
   - In 'safetyRefusals', state the reason why virtual outpatient care is bypassed and emergency care is needed.
   - Refuse to make standard diagnosis statements, and guide the patient to immediate ER dispatch in the Plan (P).
3. **Drug-Drug Interactions**: Screen the transcript for drugs. If you detect combinations like Warfarin+Aspirin, Lisinopril+Losartan, Metformin+Contrast Dye, Sildenafil+Nitroglycerin, list them in the 'drugInteractions' list and detail them in the Plan.

Generate the output matching this JSON schema exactly:
{{
  "soapNote": {{
    "subjective": "Subjective summary of patient symptoms",
    "objective": "Objective vitals and examination facts",
    "assessment": "Assessment detailing suspected conditions and guidelines matched. NEVER state definitive diagnoses.",
    "plan": "Plan detailing next steps, prescriptions, lifestyle advice, and drug interaction warnings"
  }},
  "icd10": [
    {{ "code": "ICD-10-CM code", "description": "Short code description", "confidence": 0.9, "rationale": "Why" }}
  ],
  "tests": [
    "Recommended test names"
  ],
  "drugInteractions": [
    "Text description of any detected drug interaction"
  ],
  "acuityLevel": "Low" | "Moderate" | "High",
  "isOutsideScope": true | false,
  "safetyRefusals": [
    "Refusal message details if acuity is high or diagnostics are asserted"
  ]
}}

Return ONLY valid JSON."""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(response.choices[0].message.content)
        parsed["relevantGuidelines"] = [{"id": g["id"], "title": g["title"], "condition": g["condition"]} for g in guidelines]
        logger.info("Successfully generated clinical SOAP note via gpt-4o-mini")
        return parsed
    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "limit" in error_msg or "429" in error_msg or "billing" in error_msg:
            logger.warning("OpenAI quota limit detected. Dynamic failover to offline expert system activated.")
            rag._api_quota_exceeded = True
        else:
            logger.warning(f"OpenAI agent call failed: {e}. Falling back to offline clinical expert system.")
        return run_offline_clinical_expert_system(transcript)

