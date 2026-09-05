from ..models.schemas import SimulationInput, SimulationOutput, AccountRisk
import math

class SonicsSimulator:
    def calculate_likelihood(self, risk: AccountRisk, inputs: SimulationInput) -> SimulationOutput:
        # This is a hypothetical mathematical model
        # NOT based on actual Instagram algorithms
        
        base_risk = risk.overall_score
        
        # Hypothetical weights
        report_weight = 0.05
        source_weight = 0.02
        
        total_reports = inputs.violation_reports + inputs.spam_reports + inputs.impersonation_reports
        source_multiplier = min(inputs.reporting_sources / 10.0, 2.0) if inputs.reporting_sources > 0 else 1.0
        
        # Logistic function to map reports to a probability increase
        report_impact = 1 / (1 + math.exp(-(total_reports * 0.1 - 2)))
        
        # Combine base risk and report impact
        # This is just a model simulation
        estimated_likelihood = min((base_risk * 0.4) + (report_impact * 0.6 * source_multiplier), 1.0)
        
        factors = []
        if inputs.violation_reports > 0: factors.append(f"{inputs.violation_reports} violation reports")
        if inputs.spam_reports > 0: factors.append(f"{inputs.spam_reports} spam reports")
        if inputs.impersonation_reports > 0: factors.append(f"{inputs.impersonation_reports} impersonation reports")
        if risk.overall_score > 0.5: factors.append("High account risk score")
        
        return SimulationOutput(
            estimated_likelihood=round(estimated_likelihood * 100, 2),
            confidence=round(risk.confidence * 80, 2), # Model confidence is capped
            uncertainty=round((1 - risk.confidence) * 20 + 5, 2),
            factors=factors,
            scenario_description=f"Simulation based on {total_reports} total reports from {inputs.reporting_sources} sources."
        )
