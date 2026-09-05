from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class InstagramProfile(BaseModel):
    username: str
    display_name: Optional[str] = "Unavailable"
    bio: Optional[str] = "Unavailable"
    profile_pic_url: Optional[str] = "Unavailable"
    is_private: bool = False
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    post_count: Optional[int] = None
    recent_posts: List[Dict] = []
    access_status: str = "Public"

class AnalysisResult(BaseModel):
    category: str
    classification: str
    confidence: float
    severity: str
    evidence: str
    explanation: str

class AccountRisk(BaseModel):
    overall_score: float
    detected_categories: List[str]
    severity: str
    confidence: float
    items_analyzed: int
    summary: str

class SimulationInput(BaseModel):
    violation_reports: int = 0
    spam_reports: int = 0
    impersonation_reports: int = 0
    reporting_sources: int = 0

class SimulationOutput(BaseModel):
    estimated_likelihood: float
    confidence: float
    uncertainty: float
    factors: List[str]
    scenario_description: str

class FullAnalysisResponse(BaseModel):
    profile: InstagramProfile
    content_analysis: List[AnalysisResult]
    account_risk: AccountRisk
    enforcement_simulation: Optional[SimulationOutput] = None
