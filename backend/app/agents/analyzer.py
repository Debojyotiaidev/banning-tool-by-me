from .providers.provider import get_provider
from ..models.schemas import AnalysisResult, InstagramProfile
from typing import List

class AnalysisAgent:
    def __init__(self):
        self.provider = get_provider()

    def analyze_content(self, content_data: str, category: str) -> AnalysisResult:
        return self.provider.analyze_text(content_data, category)

class AccountLevelAgent:
    def __init__(self):
        self.provider = get_provider()

    def aggregate_analysis(self, profile: InstagramProfile, analyses: List[AnalysisResult]) -> dict:
        return self.provider.generate_summary(profile, analyses)
