from pydantic import BaseModel, Field
from typing import List, Optional

class SoapNote(BaseModel):
    subjective: str = Field(description="Subjective history and reports from patient/physician")
    objective: str = Field(description="Objective clinical signs, vitals, examination facts")
    assessment: str = Field(description="Assessment, differential diagnosis, disclaimer stating suspected pending verification")
    plan: str = Field(description="Treatment plan, prescriptions, safety rails, follow up instructions")

class ICD10Suggestion(BaseModel):
    code: str = Field(description="The ICD-10-CM code")
    description: str = Field(description="Short clinical description of the code")
    confidence: Optional[float] = Field(default=1.0, description="Confidence score for the recommendation")
    rationale: Optional[str] = Field(default="", description="Brief reason for suggesting this code")

class SoapGenerationResponse(BaseModel):
    soapNote: SoapNote
    icd10: List[ICD10Suggestion]
    tests: List[str] = Field(default=[], description="List of suggested diagnostic tests")
    drugInteractions: List[str] = Field(default=[], description="Identified potential drug interaction warnings")
    acuityLevel: str = Field(default="Low", description="Low, Moderate, High acuity classification")
    isOutsideScope: bool = Field(default=False, description="True if case should be escalated out of virtual scope")
    safetyRefusals: List[str] = Field(default=[], description="Details of safety blocks or refusal assertions")
    relevantGuidelines: Optional[List[dict]] = Field(default=[], description="Metadata of NICE/guidelines matched")

class SaveNoteRequest(BaseModel):
    id: Optional[str] = None
    patientName: str
    transcript: str
    soapNote: SoapNote
    icd10: List[ICD10Suggestion]
    tests: List[str]
    drugInteractions: List[str]
    acuityLevel: str
    isOutsideScope: bool
    safetyRefusals: List[str]
    status: Optional[str] = "Approved"
