ICD10_CODES_DB = [
    {"code": "I10", "keywords": ["hypertension", "bp", "blood pressure", "systolic", "diastolic"], "description": "Essential (primary) hypertension"},
    {"code": "E11.9", "keywords": ["diabetes", "t2dm", "hyperglycemia", "metformin", "glucose", "a1c"], "description": "Type 2 diabetes mellitus without complications"},
    {"code": "J45.909", "keywords": ["asthma", "wheezing", "reactive airway", "bronchospasm", "albuterol", "inhaler"], "description": "Unspecified asthma, uncomplicated"},
    {"code": "K52.9", "keywords": ["gastroenteritis", "diarrhea", "vomiting", "dehydration", "nausea", "stomach flu"], "description": "Noninfective gastroenteritis and colitis, unspecified"},
    {"code": "R07.9", "keywords": ["chest pain", "chest pressure", "substernal", "angina"], "description": "Chest pain, unspecified"},
    {"code": "I63.9", "keywords": ["stroke", "aphasia", "hemiparesis", "facial droop", "slurred speech"], "description": "Cerebral infarction, unspecified"},
    {"code": "R05", "keywords": ["cough"], "description": "Cough"},
    {"code": "R06.02", "keywords": ["shortness of breath", "dyspnea", "breathlessness"], "description": "Shortness of breath"}
]

def search_icd10_codes(query: str) -> list:
    if not query:
        return []
        
    query_lower = query.lower()
    matches = []
    
    for item in ICD10_CODES_DB:
        # Check if the code itself is query, or any keyword matches
        if item["code"].lower() in query_lower or any(kw in query_lower for kw in item["keywords"]):
            matches.append({
                "code": item["code"],
                "description": item["description"],
                "confidence": 0.95 if item["code"].lower() in query_lower else 0.80,
                "rationale": f"Identified patient details correlating with {item['description']} symptoms."
            })
            
    # Default fallback code if nothing matched
    if not matches:
        matches.append({
            "code": "Z00.00",
            "description": "Encounter for general adult medical examination without abnormal findings",
            "confidence": 0.50,
            "rationale": "General health encounter; no primary chronic disease markers detected."
        })
        
    return matches[:3]
