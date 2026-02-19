"""
Flow Simulator - simulates personas through product flows.

Core logic: For each flow, each persona steps through screens. At each step,
the LLM decides CONTINUE or DROP_OFF. We log every decision and drop-off reason.

Supports multiple flows - run same personas through each flow for comparison.
Also supports company-specific simulators (e.g. Loop Health EnhancedFlowSimulator).
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Callable, Awaitable, Protocol
from tqdm.asyncio import tqdm

from src.api.gemini_client import gemini_client
from src.core.base import FlowStimulus, FlowScreen, FlowJourneyResult, FlowStepDecision


# Type for context builder: (persona, screen, journey_history, view_analysis) -> dict
ContextBuilder = Callable[[Any, Any, List[str], Dict], Dict[str, Any]]


@dataclass
class FlowSimulatorConfig:
    """Configuration for flow simulation."""
    system_prompt: str = ""
    max_concurrent: int = 5
    use_vision_for_analysis: bool = True


DEFAULT_FLOW_SYSTEM_PROMPT = """You are simulating a real user going through a product flow.

You have a specific profile and make decisions as THAT person would:
- Consider clarity, value, trust, and effort at each step
- Mandatory steps: High tolerance, but you may drop if overwhelmed
- Optional steps: Your motivation and personality determine if you continue
- Be consistent with your profile - different personas make different choices

Return ONLY valid JSON. No markdown, no explanation."""


DEFAULT_DECISION_PROMPT = """You are {occupation}, {age}yo {sex}, in {district}, {state}.

Your profile: {profile_summary}

CURRENT SCREEN ({view_number}/{total_views}): {view_name}
What you see: {view_description}

Journey so far: {journey_summary}

DECIDE: CONTINUE or DROP_OFF?
- MANDATORY steps: Usually continue unless something blocks you
- OPTIONAL steps: Continue only if value is clear for YOU

Return JSON:
{{
    "step_type": "MANDATORY|OPTIONAL",
    "decision": "CONTINUE|DROP_OFF",
    "reasoning": "<why - in your voice>",
    "drop_off_reason": "<only if DROP_OFF - the main reason>",
    "trust_score": 0-10,
    "clarity_score": 0-10,
    "value_perception_score": 0-10,
    "emotional_state": "<1-2 words>",
    "time_spent_seconds": 5-60
}}
"""


class FlowSimulatorProtocol(Protocol):
    """Protocol for flow simulators - core or company-specific."""

    async def run_flow(
        self,
        personas: List[Any],
        flow: FlowStimulus,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Run personas through one flow. Returns list of journey results (dicts)."""
        ...


class FlowSimulator:
    """
    Generic flow simulator - works with any persona type via context_builder.
    
    Company plugins with rich personas (e.g. Loop Health) can use a custom
    simulator for higher accuracy.
    """
    
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        config: FlowSimulatorConfig | None = None
    ):
        self.context_builder = context_builder or self._default_context_builder
        self.config = config or FlowSimulatorConfig()
        self._screen_analysis_cache: Dict[str, Dict[str, Any]] = {}
    
    def _default_context_builder(
        self,
        persona: Any,
        screen: FlowScreen,
        journey_history: List[str],
        view_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build minimal context from persona dict or object with standard fields."""
        if isinstance(persona, dict):
            p = persona
        else:
            p = getattr(persona, "__dict__", {}) or {}
            if hasattr(persona, "model_dump"):
                p = persona.model_dump()
        
        profile_parts = [
            f"Occupation: {p.get('occupation', 'Unknown')}",
            f"Income: ₹{p.get('monthly_income_inr', 0):,}/month",
            f"Digital literacy: {p.get('digital_literacy', 5)}/10",
        ]
        if "health_urgency_score" in p:
            profile_parts.append(f"Health urgency: {p['health_urgency_score']}/10")
        if "behavioral_profile" in p:
            bp = p["behavioral_profile"] if isinstance(p.get("behavioral_profile"), dict) else {}
            profile_parts.append(f"Inertia: {bp.get('inertia_level', 5)}/10")
        
        return {
            "occupation": p.get("occupation", "Professional"),
            "age": p.get("age", 30),
            "sex": p.get("sex", "Unknown"),
            "district": p.get("district", ""),
            "state": p.get("state", ""),
            "profile_summary": "; ".join(profile_parts),
            "view_number": screen.view_number,
            "view_name": screen.view_name,
            "view_description": self._format_view_analysis(view_analysis),
            "journey_summary": " → ".join(journey_history) if journey_history else "First screen",
            "total_views": screen.view_number,
        }
    
    def _format_view_analysis(self, analysis: Dict) -> str:
        parts = []
        for k in ["main_content", "key_information", "required_action", "design_quality", "friction_points"]:
            if k in analysis and analysis[k]:
                parts.append(f"{k.replace('_', ' ').title()}: {analysis[k]}")
        return "\n".join(parts) if parts else "Standard screen"
    
    async def _analyze_screen(self, screen: FlowScreen, flow_name: str = "") -> Dict[str, Any]:
        """Analyze a flow screen using vision model."""
        cache_key = f"{screen.view_id}_{screen.image_path}"
        if cache_key in self._screen_analysis_cache:
            return self._screen_analysis_cache[cache_key]
        
        try:
            with open(screen.image_path, "rb") as f:
                image_data = f.read()
            
            prompt = f"""Analyze this product flow screen (View {screen.view_number}).

Describe:
1. main_content - What is the main purpose?
2. key_information - What info is shown?
3. required_action - What must the user do?
4. design_quality - Layout and clarity
5. friction_points - Potential issues

Return ONLY valid JSON:
{{"main_content": "...", "key_information": "...", "required_action": "...", "design_quality": "...", "friction_points": "..."}}
"""
            response = await gemini_client.generate_pro(prompt, image_data)
            result = gemini_client.parse_json_response(response)
            self._screen_analysis_cache[cache_key] = result
            return result
        except Exception as e:
            return {
                "main_content": "Product flow screen",
                "key_information": "User must review and proceed",
                "required_action": "Continue or complete step",
                "design_quality": "Standard",
                "friction_points": str(e)
            }
    
    async def _simulate_step(
        self,
        persona: Any,
        flow: FlowStimulus,
        screen: FlowScreen,
        journey_history: List[str],
        view_analyses: Dict[str, Dict[str, Any]],
        total_views: int
    ) -> tuple[FlowStepDecision, bool]:
        """Simulate one step. Returns (decision, should_continue)."""
        view_analysis = view_analyses.get(screen.view_id, {})
        context = self.context_builder(persona, screen, journey_history, view_analysis)
        context["total_views"] = total_views
        
        prompt = DEFAULT_DECISION_PROMPT.format(**context)
        system = self.config.system_prompt or DEFAULT_FLOW_SYSTEM_PROMPT
        
        try:
            response = await gemini_client.generate_flash(prompt, system_prompt=system)
            data = gemini_client.parse_json_response(response)
        except Exception as e:
            data = {
                "decision": "DROP_OFF",
                "reasoning": str(e),
                "drop_off_reason": "Technical error",
                "trust_score": 5,
                "clarity_score": 5,
                "value_perception_score": 5,
                "emotional_state": "confused",
                "time_spent_seconds": 5
            }
        
        decision = data.get("decision", "CONTINUE")
        drop_reason = data.get("drop_off_reason") if decision == "DROP_OFF" else None
        step_type = getattr(screen, "step_type", None) or (
            getattr(screen, "metadata", {}) or {}
        ).get("step_type", "MANDATORY")
        
        step_decision = FlowStepDecision(
            persona_uuid=persona.uuid if hasattr(persona, "uuid") else persona.get("uuid", ""),
            flow_id=flow.flow_id,
            view_id=screen.view_id,
            view_number=screen.view_number,
            step_type=data.get("step_type", step_type),
            decision=decision,
            reasoning=data.get("reasoning", ""),
            drop_off_reason=drop_reason,
            trust_score=int(data.get("trust_score", 5)),
            clarity_score=int(data.get("clarity_score", 5)),
            value_perception_score=int(data.get("value_perception_score", 5)),
            emotional_state=data.get("emotional_state", "neutral"),
            friction_points=data.get("friction_points", []) if isinstance(data.get("friction_points"), list) else [],
            time_spent_seconds=int(data.get("time_spent_seconds", 5))
        )
        
        return step_decision, decision == "CONTINUE"
    
    async def simulate_journey(
        self,
        persona: Any,
        flow: FlowStimulus,
        view_analyses: Dict[str, Dict[str, Any]]
    ) -> FlowJourneyResult:
        """Simulate one persona through one flow."""
        decisions = []
        total_time = 0
        journey_history = []
        dropped_at = None
        drop_reason = None
        
        for screen in flow.screens:
            step_decision, continue_flow = await self._simulate_step(
                persona, flow, screen, journey_history, view_analyses, len(flow.screens)
            )
            decisions.append(step_decision)
            total_time += step_decision.time_spent_seconds
            journey_history.append(f"V{screen.view_number}")
            
            if not continue_flow:
                dropped_at = screen.view_number
                drop_reason = step_decision.drop_off_reason or step_decision.reasoning
                break
        
        persona_uuid = persona.uuid if hasattr(persona, "uuid") else persona.get("uuid", "")
        
        return FlowJourneyResult(
            persona_uuid=persona_uuid,
            flow_id=flow.flow_id,
            total_screens_seen=len(decisions),
            completed_flow=dropped_at is None,
            dropped_off_at_view=dropped_at,
            drop_off_reason=drop_reason,
            decisions=decisions,
            total_time_seconds=total_time
        )
    
    async def run_flow(
        self,
        personas: List[Any],
        flow: FlowStimulus,
        analyze_screens: bool = True,
        progress: bool = True
    ) -> List[FlowJourneyResult]:
        """
        Run all personas through one flow.
        Returns list of FlowJourneyResult.
        """
        view_analyses = {}
        if analyze_screens:
            tasks = [self._analyze_screen(s, flow.flow_name) for s in flow.screens]
            analyses = await tqdm.gather(*tasks, desc=f"Analyzing {flow.flow_name}") if progress else await asyncio.gather(*tasks)
            view_analyses = {flow.screens[i].view_id: analyses[i] for i in range(len(flow.screens))}
        
        tasks = [self.simulate_journey(p, flow, view_analyses) for p in personas]
        if progress:
            results = await tqdm.gather(*tasks, desc=f"Simulating {flow.flow_name}")
        else:
            results = await asyncio.gather(*tasks)
        
        return list(results)
    
    async def run_multiple_flows(
        self,
        personas: List[Any],
        flows: List[FlowStimulus],
        analyze_screens: bool = True,
        progress: bool = True
    ) -> Dict[str, List[FlowJourneyResult]]:
        """
        Run all personas through all flows.
        Returns: flow_id -> list of FlowJourneyResult
        """
        all_results: Dict[str, List[FlowJourneyResult]] = {}
        
        for flow in flows:
            results = await self.run_flow(
                personas, flow,
                analyze_screens=analyze_screens,
                progress=progress
            )
            all_results[flow.flow_id] = results
        
        return all_results


def journey_result_to_dict(r: FlowJourneyResult) -> Dict[str, Any]:
    """Convert FlowJourneyResult to dict, preserving all decision fields for reporting."""
    return {
        "persona_uuid": r.persona_uuid,
        "flow_id": r.flow_id,
        "completed_flow": r.completed_flow,
        "dropped_off_at_view": r.dropped_off_at_view,
        "drop_off_reason": r.drop_off_reason,
        "total_screens_seen": r.total_screens_seen,
        "total_time_seconds": r.total_time_seconds,
        "metadata": r.metadata,
        "decisions": [
            {
                "view_id": d.view_id,
                "view_number": d.view_number,
                "step_type": d.step_type,
                "decision": d.decision,
                "reasoning": d.reasoning,
                "drop_off_reason": d.drop_off_reason,
                "trust_score": d.trust_score,
                "clarity_score": d.clarity_score,
                "value_perception_score": d.value_perception_score,
                "emotional_state": d.emotional_state,
                "friction_points": d.friction_points,
                "time_spent_seconds": d.time_spent_seconds,
                "metadata": d.metadata,
            }
            for d in r.decisions
        ],
    }
