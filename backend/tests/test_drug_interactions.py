import pytest
from app.services.drug_interactions import check_local_interactions, check_drug_safety

def test_critical_drug_interaction_aspirin_warfarin():
    """Verify detection of critical bleeding risk with Aspirin and Warfarin."""
    drugs = ["Aspirin 81mg", "Warfarin 5mg daily"]
    warnings = check_local_interactions(drugs)
    assert len(warnings) >= 1
    assert "Aspirin" in warnings[0] and "Warfarin" in warnings[0]
    assert "CRITICAL" in warnings[0]

def test_critical_drug_interaction_sildenafil_nitroglycerin():
    """Verify detection of severe hypotension risk with Sildenafil and Nitroglycerin."""
    drugs = ["sildenafil", "nitroglycerin sublingual"]
    warnings = check_local_interactions(drugs)
    assert len(warnings) >= 1
    assert "Sildenafil" in warnings[0] or "sildenafil" in warnings[0].lower()
    assert "CRITICAL" in warnings[0]

def test_contraindicated_ace_arb_combination():
    """Verify detection of Lisinopril + Losartan dual block contraindication."""
    drugs = ["Lisinopril 10mg", "Losartan 50mg"]
    warnings = check_local_interactions(drugs)
    assert len(warnings) >= 1
    assert "ACE inhibitor" in warnings[0] or "Lisinopril" in warnings[0]

def test_safe_drug_list():
    """Verify that a non-interacting regimen returns zero critical warnings."""
    drugs = ["Acetaminophen 500mg", "Amoxicillin 500mg"]
    warnings = check_local_interactions(drugs)
    assert len(warnings) == 0

def test_empty_drug_list():
    """Verify graceful handling of empty drug lists."""
    assert check_local_interactions([]) == []
    assert check_drug_safety([]) == []
