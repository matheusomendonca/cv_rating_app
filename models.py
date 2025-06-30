from pydantic import BaseModel, Field
from typing import List, Optional

class CandidateInfo(BaseModel):
    candidate_id: str
    file: str
    name: str
    email: str
    phone: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    years_experience: Optional[int] = None
    education: Optional[str] = None
    summary: Optional[str] = None

class CandidateRating(BaseModel):
    candidate_id: str
    file: str
    score: float
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    rationale: Optional[str] = None

class JudgeRating(BaseModel):
    candidate_id: str
    file: str
    score: float
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    rationale: Optional[str] = None
    initial_score: Optional[float] = None
    score_adjustment: Optional[str] = None
