"""
Core simulation abstractions - the foundational layer for all Apriori simulations.

Design: One abstract simulation pattern powers both Ad and Flow use cases.
- Persona (target user) + Stimulus (ad creative OR product flow) → Decision/Reaction
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Protocol, TypeVar, Generic
from pathlib import Path


# ---------------------------------------------------------------------------
# Persona Protocol - minimum interface for simulation
# ---------------------------------------------------------------------------

class PersonaLike(Protocol):
    """Minimum persona interface - company plugins can extend with domain-specific fields."""
    uuid: str
    occupation: str
    age: int
    sex: str
    state: str
    district: str
    education_level: str
    monthly_income_inr: int
    digital_literacy: int
    primary_device: str


# ---------------------------------------------------------------------------
# Stimulus Types
# ---------------------------------------------------------------------------

@dataclass
class AdStimulus:
    """An ad creative - stimulus for Ad Simulation."""
    ad_id: str
    name: str
    copy: str
    image_path: str | None = None
    image_url: str | None = None
    description: str = ""


@dataclass
class FlowScreen:
    """A single screen/view in a product flow."""
    view_id: str
    view_number: int
    view_name: str
    image_path: str
    description: str = ""
    step_type: str = "MANDATORY"  # MANDATORY | OPTIONAL
    intervention_applied: str | None = None  # e.g. "social_proof", "urgency", "incentive"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowStimulus:
    """A product flow - ordered list of screens. Stimulus for Flow Simulation."""
    flow_id: str
    flow_name: str
    screens: List[FlowScreen]
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Result Types
# ---------------------------------------------------------------------------

@dataclass
class AdReactionResult:
    """Reaction from a persona to an ad."""
    persona_uuid: str
    ad_id: str
    trust_score: int
    relevance_score: int
    action: str  # CLICK | IGNORE | REPORT
    intent_level: str
    reasoning: str
    emotional_response: str
    barriers: List[str] = field(default_factory=list)


@dataclass
class FlowStepDecision:
    """Decision at a single step in a flow."""
    persona_uuid: str
    flow_id: str
    view_id: str
    view_number: int
    step_type: str
    decision: str  # CONTINUE | DROP_OFF
    reasoning: str
    drop_off_reason: str | None = None  # Only set when decision=DROP_OFF
    trust_score: int = 5
    clarity_score: int = 5
    value_perception_score: int = 5
    emotional_state: str = "neutral"
    friction_points: List[str] = field(default_factory=list)
    time_spent_seconds: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)  # Company-specific rich data


@dataclass
class FlowJourneyResult:
    """Complete journey of a persona through a flow."""
    persona_uuid: str
    flow_id: str
    total_screens_seen: int
    completed_flow: bool
    dropped_off_at_view: int | None = None
    drop_off_reason: str | None = None
    decisions: List[FlowStepDecision] = field(default_factory=list)
    total_time_seconds: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Simulation Runner Protocol
# ---------------------------------------------------------------------------

TStimulus = TypeVar("TStimulus")
TResult = TypeVar("TResult")


class SimulationRunner(ABC, Generic[TStimulus, TResult]):
    """Abstract base for simulation runners. Persona + Stimulus → Result."""
    
    @abstractmethod
    async def simulate(
        self,
        persona: Any,  # PersonaLike or company-specific
        stimulus: TStimulus,
        context: Dict[str, Any] | None = None
    ) -> TResult:
        """Run simulation for one persona and one stimulus."""
        pass
    
    @abstractmethod
    async def run_batch(
        self,
        personas: List[Any],
        stimuli: List[TStimulus],
        context: Dict[str, Any] | None = None
    ) -> List[TResult]:
        """Run simulation for all persona × stimulus combinations."""
        pass
