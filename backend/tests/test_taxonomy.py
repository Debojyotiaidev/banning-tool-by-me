"""Policy taxonomy normalization + schema isolation tests.

These cover Phase 3 cleanup:
- legacy category names normalize into the canonical taxonomy everywhere,
- the deterministic fallback always emits canonical names,
- simulation models are isolated away from the read-only analysis schemas.
"""
import pytest

from app.models.policies import (
    LEGACY_CATEGORY_NAMES,
    POLICY_CATEGORIES,
    canonical_category_names,
    normalize_category_name,
)
from app.agents.providers.provider import (
    LocalAIProvider,
    _SIGNALS,
)


def test_canonical_names_pass_through():
    for name in canonical_category_names():
        assert normalize_category_name(name) == name


def test_legacy_names_normalize_to_canonical():
    for legacy, canonical in LEGACY_CATEGORY_NAMES.items():
        assert normalize_category_name(legacy) == canonical


def test_unknown_names_are_left_unchanged():
    assert normalize_category_name("Something Completely New") == "Something Completely New"
    assert normalize_category_name("") == ""


def test_taxonomy_names_are_unique():
    names = [c.name for c in POLICY_CATEGORIES]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("legacy,canonical", [
    ("Hate Speech", "Hateful Conduct"),
    ("Harassment / Bullying", "Bullying & Harassment"),
    ("Harassment & Bullying", "Bullying & Harassment"),
    ("Impersonation Risk", "Impersonation"),
    ("General Policy Risk", "Other Policy Areas"),
])
def test_rules_engine_emits_canonical_category(legacy, canonical):
    provider = LocalAIProvider()
    result = provider.analyze_text(
        "go back to your country, you people don't belong here", legacy
    )
    assert result.category == canonical


def test_rules_engine_signal_keys_are_canonical():
    canonical = set(canonical_category_names())
    assert set(_SIGNALS.keys()) <= canonical


def test_simulation_schemas_isolated_from_analysis_schemas():
    # Old Phase-1/2 simulation models must not live in the shared schema module.
    import app.models.schemas as schemas
    for name in ("AccountRisk", "SimulationInput", "SimulationOutput"):
        assert not hasattr(schemas, name), f"{name} should live in app.simulation.schemas"


def test_simulation_models_only_in_simulation_package():
    from app.simulation.schemas import AccountRisk, SimulationInput, SimulationOutput
    # The simulator must import its own schemas, not the shared ones.
    import app.simulation.simulator as simulator_module
    assert "simulation.schemas" in simulator_module.__dict__.get("SimulationInput").__module__
    assert AccountRisk.__module__ == "app.simulation.schemas"
    assert SimulationInput.__module__ == "app.simulation.schemas"
    assert SimulationOutput.__module__ == "app.simulation.schemas"