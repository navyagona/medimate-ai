import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

DRUG_INTERACTIONS_DB = [
    {
        "drugs": ["aspirin", "warfarin"],
        "severity": "CRITICAL",
        "message": "CRITICAL: Co-administration of Aspirin and Warfarin significantly increases the risk of severe gastrointestinal hemorrhage and internal bleeding. Close monitoring of INR or alternative therapy is recommended."
    },
    {
        "drugs": ["lisinopril", "losartan"],
        "severity": "CRITICAL",
        "message": "CRITICAL: Never combine an ACE inhibitor (Lisinopril) and an ARB (Losartan) due to high risk of hyperkalemia, severe hypotension, and acute kidney injury."
    },
    {
        "drugs": ["metformin", "contrast"],
        "severity": "WARNING",
        "message": "WARNING: Temporarily discontinue Metformin prior to and for 48 hours after iodinated contrast imaging studies to prevent contrast-induced acute kidney injury and lactic acidosis."
    },
    {
        "drugs": ["ibuprofen", "lisinopril"],
        "severity": "MODERATE",
        "message": "MODERATE: NSAIDs (Ibuprofen) may decrease the antihypertensive effect of ACE inhibitors (Lisinopril) and increase risk of acute renal impairment."
    },
    {
        "drugs": ["sildenafil", "nitroglycerin"],
        "severity": "CRITICAL",
        "message": "CRITICAL: Severe, potentially fatal hypotension. Co-administration of Sildenafil and Nitroglycerin is strictly contraindicated."
    }
]

def check_local_interactions(drugs_list: list) -> list:
    if not drugs_list:
        return []
    
    normalized_list = [d.lower().strip() for d in drugs_list]
    warnings = []
    
    for item in DRUG_INTERACTIONS_DB:
        # Check if all drugs in this interaction are in the patient's list
        match = True
        for interaction_drug in item["drugs"]:
            # Check if any drug in the user list contains this text
            if not any(interaction_drug in user_d for user_d in normalized_list):
                match = False
                break
        if match:
            warnings.append(item["message"])
            
    return warnings

# Global status tracking to avoid repeating connection timeouts if RxNav API is unreachable
_rxnav_offline = False

def fetch_rxcui(drug_name: str) -> str:
    """Fetch RxNorm CUI for a drug name from public RxNav API."""
    global _rxnav_offline
    if _rxnav_offline:
        return None
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={urllib.parse.quote(drug_name)}"
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=2.0) as response:
            data = json.loads(response.read().decode('utf-8'))
            id_group = data.get("idGroup", {})
            rxnorm_ids = id_group.get("rxnormId", [])
            if rxnorm_ids:
                return rxnorm_ids[0]
    except Exception as e:
        logger.warning(f"RxNav API unreachable or timed out ({e}). Activating offline fallback mode for drug interaction checks.")
        _rxnav_offline = True
    return None

def check_rxnav_interactions(drugs_list: list) -> list:
    """Query RxNav REST API for drug interactions."""
    if len(drugs_list) < 2:
        return []
        
    rxcuis = []
    for drug in drugs_list:
        cui = fetch_rxcui(drug)
        if cui:
            rxcuis.append(cui)
            
    if len(rxcuis) < 2:
        return []
        
    try:
        cui_str = "+".join(rxcuis)
        url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={cui_str}"
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=3.0) as response:
            data = json.loads(response.read().decode('utf-8'))
            warnings = []
            
            # Parse RxNav interaction report
            full_interaction_groups = data.get("fullInteractionTypeGroup", [])
            for group in full_interaction_groups:
                interaction_types = group.get("fullInteractionType", [])
                for itype in interaction_types:
                    interaction_pairs = itype.get("interactionPair", [])
                    for pair in interaction_pairs:
                        desc = pair.get("description", "")
                        severity = pair.get("severity", "N/A").upper()
                        warnings.append(f"RxNav API ({severity}): {desc}")
            return warnings
    except Exception as e:
        logger.warning(f"Failed to fetch or parse RxNav interaction list for CUIs {rxcuis}: {e}")
        
    return []

def check_drug_safety(drugs_list: list) -> list:
    """Hybrid check: checks local database for critical interactions, falls back or appends RxNav results."""
    # Standard local check
    warnings = check_local_interactions(drugs_list)
    
    # Try RxNav check
    rxnav_warnings = check_rxnav_interactions(drugs_list)
    for warning in rxnav_warnings:
        if warning not in warnings:
            warnings.append(warning)
            
    return warnings

