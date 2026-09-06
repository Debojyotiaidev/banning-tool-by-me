"""Centralized policy taxonomy for Sonics.

Single source of truth for policy categories used by the Policy Category
Analyst. NOT enforcement-probability predictions.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class PolicyCategory(BaseModel):
    key: str
    name: str
    description: str
    indicators: List[str] = []


POLICY_CATEGORIES: List[PolicyCategory] = [
    PolicyCategory(
        key="spam",
        name="Spam",
        description="Deceptive, repetitive, or unsolicited content engineered to artificially drive traffic, growth, or engagement.",
        indicators=["follow-for-follow or engagement-bait offers", "buy followers / likes / engagement services", "repetitive promotional captions across posts", "link-in-bio traffic or sales-funnel patterns"],
    ),
    PolicyCategory(
        key="impersonation",
        name="Impersonation",
        description="Accounts or content that misrepresent identity, such as posing as a person, brand, or organization without authorization.",
        indicators=["claims of being official without verification", "name/photo patterns matching a notable entity", "fake-support direct-message contact patterns"],
    ),
    PolicyCategory(
        key="bullying_harassment",
        name="Bullying & Harassment",
        description="Targeted abuse, degradation, or intimidation directed at specific individuals or groups.",
        indicators=["repeated personal attacks or insults", "encouraging others to harass a target", "threats embedded in community interactions"],
    ),
    PolicyCategory(
        key="hateful_conduct",
        name="Hateful Conduct",
        description="Attacks on people based on protected characteristics such as race, ethnicity, national origin, religion, sexual orientation, gender, or disability.",
        indicators=["dehumanizing language or slurs targeting identity groups", "calls for exclusion based on identity", "attacks framed around protected characteristics"],
    ),
    PolicyCategory(
        key="violence_incitement",
        name="Violence & Incitement",
        description="Content that encourages, threatens, or glorifies violence or physical harm.",
        indicators=["credible threats of physical harm", "incitement to harm individuals or groups", "glorification of violent acts"],
    ),
    PolicyCategory(
        key="dangerous_organizations",
        name="Dangerous Organizations & Individuals",
        description="Content that expresses support, praise, or promotion of designated dangerous organizations or individuals. Discussing, reporting, or condemning such groups is NOT support.",
        indicators=["explicit praise or support for a designated dangerous entity", "recruitment or affiliation signals", "symbols/imagery promoting a designated dangerous entity"],
    ),
    PolicyCategory(
        key="coordinating_harm_crime",
        name="Coordinating Harm / Promoting Crime",
        description="Content that coordinates or promotes criminal activity, including joint planning of harm or unlawful acts.",
        indicators=["calls to coordinate unlawful activity", "instructions or coordination for harm", "promotion of criminal enterprises"],
    ),
    PolicyCategory(
        key="human_exploitation",
        name="Human Exploitation",
        description="Content that promotes, facilitates, or depicts the exploitation of people, including trafficking or forced labor.",
        indicators=["trafficking or forced-labor promotion signals", "facilitation of exploitation services"],
    ),
    PolicyCategory(
        key="child_sexual_exploitation",
        name="Child Sexual Exploitation",
        description="Sexual exploitation of minors. Requires explicit, direct, strong evidence. Discussing or condemning the topic is NOT evidence of engaging in exploitation.",
        indicators=["explicit sexual content involving minors", "solicitation or distribution signals of CSAM"],
    ),
    PolicyCategory(
        key="adult_sexual_exploitation",
        name="Adult Sexual Exploitation",
        description="Non-consensual sexual content or coercion, including non-consensual intimate imagery. General adult content is not evidence by itself.",
        indicators=["non-consensual intimate image signals", "coercion or solicitation of explicit material"],
    ),
    PolicyCategory(
        key="suicide_self_injury",
        name="Suicide & Self-Injury",
        description="Content that promotes, encourages, or instructs self-harm or suicide. Supporting discussion of mental health struggles is not a violation.",
        indicators=["instructions or encouragement for self-harm", "glorification of suicide methods"],
    ),
    PolicyCategory(
        key="fraud_scams",
        name="Fraud / Scams / Deceptive Practices",
        description="Content that deceives people for financial or personal gain, including fake promotions, phishing, and fraudulent schemes.",
        indicators=["fake giveaways or prize schemes", "selling followers/engagement or counterfeit services", "phishing or credential-harvesting patterns"],
    ),
    PolicyCategory(
        key="restricted_goods",
        name="Restricted Goods & Services",
        description="Content promoting or facilitating the sale of restricted or regulated goods or services.",
        indicators=["sale or facilitation signals for restricted items", "exchange of regulated goods through direct messages"],
    ),
    PolicyCategory(
        key="other",
        name="Other Policy Areas",
        description="Relevant signals that do not clearly map to a more specific category above. Used sparingly and only when evidence supports it.",
        indicators=[],
    ),
]

POLICY_NAMES: Dict[str, str] = {p.name: p.key for p in POLICY_CATEGORIES}


def policy_by_name(name: str) -> Optional[PolicyCategory]:
    """Return the taxonomy entry for an exact category name (or None)."""
    key = POLICY_NAMES.get(name)
    for category in POLICY_CATEGORIES:
        if category.key == key:
            return category
    return None