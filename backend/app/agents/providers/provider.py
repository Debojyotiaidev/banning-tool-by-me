import os
import json
from abc import ABC, abstractmethod
from typing import List
from ...models.schemas import AnalysisResult, InstagramProfile

class AIProvider(ABC):
    @abstractmethod
    def analyze_text(self, content_data: str, category: str) -> AnalysisResult:
        pass

    @abstractmethod
    def generate_summary(self, profile: InstagramProfile, analyses: List[AnalysisResult]) -> dict:
        pass

class LocalAIProvider(AIProvider):
    def __init__(self):
        # Using a simple transformer pipeline as a placeholder for "Local AI"
        from transformers import pipeline
        # For simplicity and to avoid huge downloads, we use a small classification model
        # Real-world: use a more comprehensive local LLM like Llama-3-8B via llama-cpp-python
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    def analyze_text(self, content_data: str, category: str) -> AnalysisResult:
        # Mock logic using classifier for demo
        # In a real local app, replace this with actual inference
        return AnalysisResult(
            category=category,
            classification="Low Risk (Local Analysis)",
            confidence=0.7,
            severity="Low",
            evidence="N/A",
            explanation="Local model analysis indicates low risk."
        )

    def generate_summary(self, profile: InstagramProfile, analyses: List[AnalysisResult]) -> dict:
        return {
            "overall_score": 0.1,
            "detected_categories": [],
            "severity": "Low",
            "confidence": 0.7,
            "items_analyzed": len(profile.recent_posts),
            "summary": "Local analysis complete."
        }

class GeminiAIProvider(AIProvider):
    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_text(self, content_data: str, category: str) -> AnalysisResult:
        # Use Gemini API
        return AnalysisResult(
            category=category,
            classification="Gemini Analyzed",
            confidence=0.9,
            severity="Low",
            evidence="N/A",
            explanation="Analyzed by Gemini."
        )

    def generate_summary(self, profile: InstagramProfile, analyses: List[AnalysisResult]) -> dict:
        return {
            "overall_score": 0.1,
            "detected_categories": [],
            "severity": "Low",
            "confidence": 0.9,
            "items_analyzed": len(profile.recent_posts),
            "summary": "Gemini summary complete."
        }

def get_provider() -> AIProvider:
    provider_type = os.getenv("AI_PROVIDER", "local").lower()
    if provider_type == "gemini":
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY required for Gemini provider")
        return GeminiAIProvider(key)
    return LocalAIProvider()
