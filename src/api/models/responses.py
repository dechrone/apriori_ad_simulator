"""API response models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class SignupResponse(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    message: str = "Account created successfully"


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

class AssetUploadResponse(BaseModel):
    asset_id: str
    url: str
    asset_type: str  # "adset" | "product_flow"
    filename: str
    message: str = "Asset uploaded successfully"


# ---------------------------------------------------------------------------
# Simulation - shared building blocks
# ---------------------------------------------------------------------------

class PersonaSummary(BaseModel):
    uuid: str
    occupation: str
    age: int
    sex: str
    location: str
    zone: str
    monthly_income_inr: int
    digital_literacy: int
    primary_device: str
    purchasing_power_tier: str
    scam_vulnerability: str
    financial_risk_tolerance: str


# ---------------------------------------------------------------------------
# Simulation - Ad type
# ---------------------------------------------------------------------------

class AdReactionDetail(BaseModel):
    persona: PersonaSummary
    ad_id: str
    trust_score: int
    relevance_score: int
    action: str
    intent_level: str
    reasoning: str
    emotional_response: str
    barriers: List[str]
    internal_monologue: Optional[str] = None  # First-person internal monologue for this reaction


class AdPerformanceSummary(BaseModel):
    ad_id: str
    total_impressions: int
    clicks: int
    click_rate: float
    high_intent_leads: int
    conversion_rate: float
    unique_reach: int


class PortfolioRecommendationOut(BaseModel):
    ad_id: str
    role: str
    budget_split: float
    target_segment: str
    unique_reach: int
    expected_conversions: int
    reasoning: Optional[str] = None


class AdSimulationResult(BaseModel):
    simulation_type: str = "ad"
    personas: List[PersonaSummary]
    reactions: List[AdReactionDetail]
    performance: Dict[str, AdPerformanceSummary]
    winning_portfolio: List[PortfolioRecommendationOut]
    wasted_spend_alerts: List[str]
    visual_heatmap: Dict[str, Any]
    validation_summary: Dict[str, Any]
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Simulation - Product Flow type
# ---------------------------------------------------------------------------

class FlowStepOut(BaseModel):
    view_id: str
    view_number: int
    view_name: str
    step_type: str
    decision: str
    reasoning: str
    drop_off_reason: Optional[str] = None
    trust_score: int
    clarity_score: int
    value_perception_score: int
    emotional_state: str
    time_spent_seconds: int


class PersonaJourneyOut(BaseModel):
    persona: PersonaSummary
    flow_id: str
    completed_flow: bool
    dropped_off_at_view: Optional[int] = None
    drop_off_reason: Optional[str] = None
    total_screens_seen: int
    total_time_seconds: int
    steps: List[FlowStepOut]
    monologue: Optional[str] = None  # Per-persona internal monologue / summary


class FlowComparisonInsight(BaseModel):
    flow_id: str
    flow_name: str
    completion_rate: float
    avg_time_seconds: float
    top_drop_off_screen: Optional[str] = None
    top_drop_off_reason: Optional[str] = None
    friction_points: List[str]


class FlowSimulationResult(BaseModel):
    simulation_type: str = "product_flow"
    personas: List[PersonaSummary]
    journeys: List[PersonaJourneyOut]
    flow_insights: List[FlowComparisonInsight]
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Generic wrapper
# ---------------------------------------------------------------------------

class SimulationResponse(BaseModel):
    """Top-level envelope returned by POST /api/v1/simulations/run."""
    status: str = "success"
    simulation_id: str
    result: Any  # AdSimulationResult | FlowSimulationResult
