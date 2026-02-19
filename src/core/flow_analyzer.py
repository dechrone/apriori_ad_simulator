"""
Flow Analyzer - drop-off analysis, dominant reasons, flow comparison.

Analyzes flow simulation results to:
1. Find the most dominant drop-off reason for each flow
2. Compare flows and determine which performs best
3. Identify major improvement areas per flow
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class DropOffAnalysis:
    """Analysis of drop-offs for a single flow."""
    flow_id: str
    flow_name: str
    total_personas: int
    completed_count: int
    dropped_count: int
    completion_rate: float
    drop_off_by_view: Dict[int, int]  # view_number -> count
    drop_off_reasons_by_view: Dict[int, List[str]]  # view_number -> list of reasons
    dominant_drop_off_view: Optional[int] = None  # The view with most drop-offs
    dominant_drop_off_reason: Optional[str] = None  # Most common reason at that view
    dominant_reason_count: int = 0
    all_reasons_ranked: List[tuple] = field(default_factory=list)  # (reason, count)


@dataclass
class FlowComparisonResult:
    """Result of comparing multiple flows."""
    winning_flow_id: str
    winning_flow_name: str
    winning_completion_rate: float
    flow_rankings: List[Dict[str, Any]]  # Sorted by completion rate
    per_flow_analysis: Dict[str, DropOffAnalysis]
    improvement_recommendations: Dict[str, List[str]]  # flow_id -> recommendations
    why_winner_wins: str  # Explanation


def _extract_reason_key(reason: str) -> str:
    """
    Normalize drop-off reason for grouping.
    LLM outputs can be verbose; we extract the core reason.
    """
    if not reason or not reason.strip():
        return "Unknown"
    r = reason.strip().lower()
    # Common patterns - extract key phrase
    if "optional" in r and "value" in r:
        return "Optional step - unclear value"
    if "optional" in r:
        return "Optional step - chose to skip"
    if "premium" in r or "price" in r or "cost" in r:
        return "Price/premium concerns"
    if "overwhelm" in r or "too much" in r or "complex" in r:
        return "Information overload / complexity"
    if "time" in r and ("need" in r or "think" in r or "later" in r):
        return "Need more time to decide"
    if "spouse" in r or "family" in r or "discuss" in r:
        return "Need to discuss with family"
    if "trust" in r or "skeptical" in r:
        return "Trust / legitimacy concerns"
    if "inertia" in r or "lazy" in r or "don't need" in r:
        return "Low motivation / inertia"
    if "mandatory" in r and "lengthy" in r:
        return "Flow too lengthy"
    if "error" in r or "technical" in r:
        return "Technical/UX friction"
    # Fallback: take first 60 chars as key
    return reason[:80] + ("..." if len(reason) > 80 else "")


def analyze_flow_drop_offs(
    flow_id: str,
    flow_name: str,
    journey_results: List[Dict[str, Any]]
) -> DropOffAnalysis:
    """
    Analyze drop-offs for a single flow.
    
    Args:
        flow_id: Flow identifier
        flow_name: Human-readable flow name
        journey_results: List of FlowJourneyResult (as dicts)
    
    Returns:
        DropOffAnalysis with dominant drop-off view and reason
    """
    total = len(journey_results)
    completed = sum(1 for r in journey_results if r.get("completed_flow", False))
    dropped = total - completed
    
    drop_by_view: Dict[int, int] = {}
    reasons_by_view: Dict[int, List[str]] = {}
    
    for r in journey_results:
        dropped_at = r.get("dropped_off_at_view")
        if dropped_at is None:
            continue
        
        drop_by_view[dropped_at] = drop_by_view.get(dropped_at, 0) + 1
        
        reason = r.get("drop_off_reason") or r.get("drop_off_reason") or "Unknown"
        if dropped_at not in reasons_by_view:
            reasons_by_view[dropped_at] = []
        reasons_by_view[dropped_at].append(reason)
    
    # Find dominant drop-off view (most drop-offs)
    dominant_view = None
    dominant_reason = None
    dominant_count = 0
    all_reasons_ranked: List[tuple] = []
    
    if drop_by_view:
        dominant_view = max(drop_by_view.keys(), key=lambda v: drop_by_view[v])
        dominant_count = drop_by_view[dominant_view]
        
        # Among drop-offs at dominant view, find most common reason
        view_reasons = reasons_by_view.get(dominant_view, [])
        if view_reasons:
            normalized = [_extract_reason_key(r) for r in view_reasons]
            reason_counter = Counter(normalized)
            dominant_reason, dominant_count = reason_counter.most_common(1)[0]
            
            all_reasons_ranked = reason_counter.most_common()
    
    return DropOffAnalysis(
        flow_id=flow_id,
        flow_name=flow_name,
        total_personas=total,
        completed_count=completed,
        dropped_count=dropped,
        completion_rate=(completed / total * 100) if total > 0 else 0,
        drop_off_by_view=drop_by_view,
        drop_off_reasons_by_view=reasons_by_view,
        dominant_drop_off_view=dominant_view,
        dominant_drop_off_reason=dominant_reason,
        dominant_reason_count=dominant_count,
        all_reasons_ranked=all_reasons_ranked
    )


def compare_flows(
    flow_results: Dict[str, List[Dict[str, Any]]],  # flow_id -> journey results
    flow_names: Dict[str, str] | None = None  # flow_id -> name
) -> FlowComparisonResult:
    """
    Compare multiple flows and determine the winner.
    
    Args:
        flow_results: Map of flow_id to list of journey results
        flow_names: Optional map of flow_id to human name
    
    Returns:
        FlowComparisonResult with winner, rankings, per-flow analysis
    """
    flow_names = flow_names or {fid: fid for fid in flow_results}
    
    per_flow: Dict[str, DropOffAnalysis] = {}
    for flow_id, journeys in flow_results.items():
        per_flow[flow_id] = analyze_flow_drop_offs(
            flow_id, flow_names.get(flow_id, flow_id), journeys
        )
    
    # Rank by completion rate (descending)
    rankings = sorted(
        per_flow.items(),
        key=lambda x: x[1].completion_rate,
        reverse=True
    )
    
    winner_id = rankings[0][0] if rankings else ""
    winner_analysis = per_flow.get(winner_id)
    winner_name = flow_names.get(winner_id, winner_id)
    winner_rate = winner_analysis.completion_rate if winner_analysis else 0
    
    # Build "why winner wins" explanation
    why_parts = []
    if winner_analysis:
        why_parts.append(
            f"{winner_name} achieves {winner_rate:.1f}% completion rate."
        )
        if winner_analysis.dominant_drop_off_view:
            why_parts.append(
                f"Main drop-off point for others: View {winner_analysis.dominant_drop_off_view} "
                f"(reason: {winner_analysis.dominant_drop_off_reason})."
            )
        if rankings and len(rankings) > 1:
            second = rankings[1][1]
            diff = winner_rate - second.completion_rate
            why_parts.append(
                f"Beats next best flow by {diff:.1f} percentage points."
            )
    
    why_winner_wins = " ".join(why_parts) if why_parts else "Insufficient data."
    
    # Improvement recommendations per flow
    recommendations: Dict[str, List[str]] = {}
    for flow_id, analysis in per_flow.items():
        recs = []
        if analysis.dominant_drop_off_view and analysis.dominant_drop_off_reason:
            recs.append(
                f"Address dominant drop-off at View {analysis.dominant_drop_off_view}: "
                f"{analysis.dominant_drop_off_reason}"
            )
        if analysis.completion_rate < 80:
            recs.append(
                f"Overall completion is {analysis.completion_rate:.1f}% - consider "
                "simplifying mandatory steps or adding progress indicators."
            )
        if analysis.drop_off_by_view:
            high_drop_views = [v for v, c in analysis.drop_off_by_view.items() if c >= 2]
            if len(high_drop_views) > 1:
                recs.append(
                    f"Multiple friction points (Views {sorted(high_drop_views)}) - "
                    "prioritize the highest drop-off first."
                )
        recommendations[flow_id] = recs
    
    return FlowComparisonResult(
        winning_flow_id=winner_id,
        winning_flow_name=winner_name,
        winning_completion_rate=winner_rate,
        flow_rankings=[
            {
                "flow_id": fid,
                "flow_name": flow_names.get(fid, fid),
                "completion_rate": a.completion_rate,
                "completed": a.completed_count,
                "dropped": a.dropped_count,
                "dominant_drop_off_view": a.dominant_drop_off_view,
                "dominant_drop_off_reason": a.dominant_drop_off_reason
            }
            for fid, a in rankings
        ],
        per_flow_analysis=per_flow,
        improvement_recommendations=recommendations,
        why_winner_wins=why_winner_wins
    )
