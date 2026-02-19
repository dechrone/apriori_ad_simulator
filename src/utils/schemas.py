"""Data schemas for Apriori."""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


class RawPersona(BaseModel):
    """Raw persona from dataset with full narrative context."""
    # Basic Demographics
    uuid: str
    occupation: str
    sex: str
    age: int
    marital_status: str
    education_level: str
    education_degree: Optional[str] = None
    
    # Geographic
    state: str
    district: str
    zone: Literal["Urban", "Rural"]
    country: Optional[str] = "India"
    
    # Language
    first_language: str
    second_language: Optional[str] = None
    third_language: Optional[str] = None
    
    # Rich Persona Narratives (these are the gold - full paragraph descriptions!)
    professional_persona: Optional[str] = None  # Full professional background & skills narrative
    linguistic_persona: Optional[str] = None     # Language usage, communication style
    cultural_background: Optional[str] = None    # Cultural context, traditions, upbringing
    sports_persona: Optional[str] = None         # Sports interests, teams, activities
    arts_persona: Optional[str] = None           # Arts, music, entertainment preferences
    travel_persona: Optional[str] = None         # Travel experiences and aspirations
    culinary_persona: Optional[str] = None       # Food preferences, cooking skills
    persona: Optional[str] = None                # Combined persona summary
    
    # Structured Lists (these are shorter, comma-separated)
    hobbies_and_interests_list: Optional[str] = None
    skills_and_expertise_list: Optional[str] = None
    
    # Full Narratives (more detailed than lists)
    hobbies_and_interests: Optional[str] = None       # Full paragraph
    skills_and_expertise: Optional[str] = None        # Full paragraph
    career_goals_and_ambitions: Optional[str] = None  # Full paragraph
    
    # Linguistic Background
    linguistic_background: Optional[str] = None  # Detailed language proficiency narrative


class EnrichedPersona(BaseModel):
    """Hydrated persona with psychographic data AND full narrative context."""
    # Basic Demographics
    uuid: str
    occupation: str
    state: str
    district: str
    zone: str
    age: int
    sex: str
    education_level: str
    first_language: str
    
    # Rich Narrative Fields (preserved from RawPersona)
    professional_persona: Optional[str] = None
    cultural_background: Optional[str] = None
    linguistic_persona: Optional[str] = None
    hobbies_and_interests: Optional[str] = None
    skills_and_expertise: Optional[str] = None
    career_goals_and_ambitions: Optional[str] = None
    sports_persona: Optional[str] = None
    arts_persona: Optional[str] = None
    travel_persona: Optional[str] = None
    culinary_persona: Optional[str] = None
    
    # Enriched Fields (LLM-generated)
    purchasing_power_tier: Literal["High", "Mid", "Low"]
    digital_literacy: int = Field(ge=0, le=10)
    primary_device: Literal["Android", "iPhone", "Desktop", "Feature Phone"]
    scam_vulnerability: Literal["High", "Low"]
    monthly_income_inr: int
    financial_risk_tolerance: Literal["High", "Low"]


class VisualAnchor(BaseModel):
    """Visual grounding description from Tier 1."""
    ad_id: str
    trust_signals: str
    visual_quality: str
    color_psychology: str
    brand_perception: str
    scam_indicators: str


class AdReaction(BaseModel):
    """User reaction to an ad."""
    persona_uuid: str
    ad_id: str
    trust_score: int = Field(ge=0, le=10)
    relevance_score: int = Field(ge=0, le=10)
    action: Literal["CLICK", "IGNORE", "REPORT"]
    intent_level: Literal["High", "Medium", "Low", "None"]
    reasoning: str
    emotional_response: str
    barriers: List[str] = []


class ValidationResult(BaseModel):
    """Validation check result."""
    status: Literal["VALID", "FLAGGED"]
    reasons: List[str] = []


class AdPerformance(BaseModel):
    """Aggregated ad performance metrics."""
    ad_id: str
    total_impressions: int
    clicks: int
    high_intent_leads: int
    click_rate: float
    conversion_rate: float
    unique_reach: int
    overlap_with_others: Dict[str, float] = {}


class PortfolioRecommendation(BaseModel):
    """Final portfolio optimization result."""
    ad_id: str
    role: str
    budget_split: float
    target_segment: str
    unique_reach: int
    expected_conversions: int
    reasoning: Optional[str] = None


class ClientReport(BaseModel):
    """Final deliverable to client."""
    strategic_verdict: Dict[str, Any]
    winning_portfolio: List[PortfolioRecommendation]
    wasted_spend_alerts: List[str]
    visual_heatmap: Dict[str, Any]
    detailed_performance: Dict[str, AdPerformance]
