from app.services.llm import generate_clinical_analysis

async def generate_soap_note_draft(transcript: str, force_offline: bool = False) -> dict:
    """Orchestrates RAG, drug safety verification, and LLM code matching to draft a SOAP note."""
    # 1. Run core generation pipeline
    result = await generate_clinical_analysis(transcript, force_offline)
    
    # 2. Return payload
    return result
