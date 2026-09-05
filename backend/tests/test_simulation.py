import pytest
from app.simulation.simulator import SonicsSimulator
from app.models.schemas import SimulationInput, AccountRisk

def test_simulator_basic():
    simulator = SonicsSimulator()
    risk = AccountRisk(
        overall_score=0.2,
        detected_categories=[],
        severity="Low",
        confidence=0.9,
        items_analyzed=5,
        summary="Low risk"
    )
    inputs = SimulationInput(violation_reports=10, reporting_sources=5)
    
    result = simulator.calculate_likelihood(risk, inputs)
    
    assert result.estimated_likelihood >= 0
    assert result.estimated_likelihood <= 100
    assert "10 violation reports" in result.factors

def test_simulator_no_reports():
    simulator = SonicsSimulator()
    risk = AccountRisk(
        overall_score=0.1,
        detected_categories=[],
        severity="Low",
        confidence=0.8,
        items_analyzed=5,
        summary="Low risk"
    )
    inputs = SimulationInput(violation_reports=0, reporting_sources=0)
    
    result = simulator.calculate_likelihood(risk, inputs)
    assert result.estimated_likelihood < 50
