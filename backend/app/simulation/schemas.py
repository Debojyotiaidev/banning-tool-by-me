"""Schemas for the isolated hypothetical enforcement simulator.

These models exist ONLY for the standalone ``/api/simulate`` endpoint. The
normal read-only analysis pipeline never imports them and never produces
ban/enforcement probabilities.
"""
from pydantic import BaseModel, Field
from typing import List


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