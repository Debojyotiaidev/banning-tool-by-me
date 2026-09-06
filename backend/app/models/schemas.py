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
    violation_reports: int = Field(default=0, ge=0)
    spam_reports: int = Field(default=0, ge=0)
    impersonation_reports: int = Field(default=0, ge=0)
    reporting_sources: int = Field(default=0, ge=0)

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


# =====================================================================
# Evidence-confidence policy assessment (Phase 2 five-role architecture)
# =====================================================================

class ContentObservation(BaseModel):
    reference: str
    quote: Optional[str] = None
    text: str
    content_signal: Optional[str] = None
    context_clue: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

class ContentAnalysis(BaseModel):
    observations: List[ContentObservation] = []
    status: str = "completed"
    note: Optional[str] = None

class DiscourseMode(BaseModel):
    mode: str
    detail: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

class ContextSignal(BaseModel):
    trait: str
    description: str
    reference: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

class ContextAnalysis(BaseModel):
    discourse_modes: List[DiscourseMode] = []
    signals: List[ContextSignal] = []
    status: str = "completed"
    note: Optional[str] = None

class CandidateCategory(BaseModel):
    category: str
    relevant: bool = False
    rationale: Optional[str] = None
    evidence_refs: List[str] = []
    initial_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

class CategoryScan(BaseModel):
    candidates: List[CandidateCategory] = []
    status: str = "completed"
    note: Optional[str] = None

class EvidenceItem(BaseModel):
    source: str
    reference: str
    text: str
    quote: Optional[str] = None
    strength: str = "moderate"
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    verification: str = "unverified"

class VerifiedFinding(BaseModel):
    category: str
    accepted: bool = False
    evidence: List[EvidenceItem] = []
    rejection_reason: Optional[str] = None
    confidence_adjustment: float = Field(default=0.0, ge=-1.0, le=1.0)
    verification: str = "verified"

class PolicyAssessment(BaseModel):
    rank: int = 0
    category: str
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    severity: str = "low"
    evidence: List[EvidenceItem] = []
    reasoning: str = ""
    context: str = ""
    verification: str = "verified"

class Observation(BaseModel):
    aspect: str
    detail: str
    reference: Optional[str] = None

class Uncertainty(BaseModel):
    factor: str
    detail: str

class PolicyAnalysisResponse(BaseModel):
    policy_categories: List[PolicyAssessment] = []
    overall_observations: List[Observation] = []
    uncertainties: List[Uncertainty] = []
    analysis_status: str = "completed"
    provider: str = "ollama"
    notes: List[str] = []
