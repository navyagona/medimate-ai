import asyncio
import pytest
from app.services.llm import run_offline_clinical_expert_system, generate_clinical_analysis

def test_soap_generator_hypertension_case():
    """Verify SOAP note draft generation for non-emergency Hypertension case."""
    transcript = "55-year-old male with history of hypertension, home blood pressure 145/92, mild headaches."
    result = run_offline_clinical_expert_system(transcript)
    
    assert "soapNote" in result
    soap = result["soapNote"]
    assert "subjective" in soap and "objective" in soap and "assessment" in soap and "plan" in soap
    assert result["acuityLevel"] == "Moderate"
    assert result["isOutsideScope"] is False
    assert len(result["icd10"]) > 0
    # Mandatory safety disclaimer check
    assert "Suspected" in soap["assessment"] or "pending physician verification" in soap["assessment"].lower()

def test_emergency_chest_pain_trigger():
    """Verify high-acuity chest pain triggers out-of-scope emergency pathway and safety refusal."""
    transcript = "Patient presents with crushing substernal chest pain radiating to left arm and jaw."
    result = run_offline_clinical_expert_system(transcript)
    
    assert result["acuityLevel"] == "High"
    assert result["isOutsideScope"] is True
    assert len(result["safetyRefusals"]) > 0
    assert "CRITICAL REFUSAL" in result["safetyRefusals"][0]
    assert "EMERGENCY PATHWAY ACTIVATED" in result["soapNote"]["plan"]

def test_emergency_stroke_trigger():
    """Verify stroke symptoms (facial droop, slurred speech) trigger high acuity emergency refusal."""
    transcript = "Patient has acute facial droop, arm drift, and slurred speech starting 30 minutes ago."
    result = run_offline_clinical_expert_system(transcript)
    
    assert result["acuityLevel"] == "High"
    assert result["isOutsideScope"] is True
    assert any("stroke" in ref.lower() for ref in result["safetyRefusals"])

def test_generate_clinical_analysis_offline_force():
    """Verify forced offline generation completes asynchronously and produces valid schema."""
    transcript = "34-year-old female with asthma complaining of shortness of breath and wheezing."
    result = asyncio.run(generate_clinical_analysis(transcript, force_offline=True))
    
    assert result["acuityLevel"] in ["Low", "Moderate", "High"]
    assert isinstance(result["icd10"], list)
    assert isinstance(result["tests"], list)

