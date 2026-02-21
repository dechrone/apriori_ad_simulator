"""
POST /api/v1/simulations/run

Orchestrates the full simulation pipeline:
  simulation_type=0  →  Ad creative simulation (AdSimulator)
  simulation_type=1  →  Product flow simulation (FlowSimulator)

Image URLs in the request body are downloaded to a temp directory before simulation.
After completion the temp directory is cleaned up automatically.
"""

import asyncio
import json
import tempfile
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.firebase.client import (
    get_audience_by_id,
    get_folder_assets,
    get_asset_folder,
    get_user_by_clerk_id,
)
from src.api.middleware.auth import get_current_user
from src.api.models.requests import (
    AdPortfolioSimulationRequest,
    ProductFlowSimulationRequest,
    RunSimulationRequest,
)
from src.api.models.responses import (
    AdPerformanceSummary,
    AdReactionDetail,
    AdSimulationResult,
    FlowComparisonInsight,
    FlowSimulationResult,
    FlowStepOut,
    PersonaJourneyOut,
    PersonaSummary,
    PortfolioRecommendationOut,
    SimulationResponse,
)
from src.core.ad_simulator import AdSimulator
from src.core.base import FlowScreen, FlowStimulus
from src.core.flow_simulator import FlowSimulator, journey_result_to_dict
from src.core.optimizer import optimizer
from src.core.persona_hydrator import persona_hydrator
from src.core.validator import validator
from src.data.loader import data_loader
from src.utils.config import BASE_DIR

router = APIRouter(prefix="/simulations", tags=["Simulations"])

# ---------------------------------------------------------------------------
# Console logging (all logs go to stdout for debugging)
# ---------------------------------------------------------------------------

def _log(step: str, message: str, **kwargs: Any) -> None:
    """Log to console with a consistent prefix so logs are greppable."""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    line = f"[SIMULATION] [{step}] {message}"
    if extra:
        line += f" | {extra}"
    print(line)


def _log_response_before_send(response: SimulationResponse) -> None:
    """Log a summary of the response before sending it to the client."""
    try:
        r = response.result
        meta = getattr(r, "metadata", {}) or {}
        _log("RESPONSE", "Sending response", simulation_id=response.simulation_id, status=response.status)
        _log("RESPONSE", "Result summary", simulation_type=getattr(r, "simulation_type", "?"), metadata_keys=list(meta.keys()))
        if "execution_time_seconds" in meta:
            _log("RESPONSE", "Timing", execution_time_seconds=meta["execution_time_seconds"])
        # Log first 800 chars of JSON (no PII) so we can see structure
        try:
            body = response.model_dump()
            summary = json.dumps(body, default=str)[:800]
            _log("RESPONSE", "Body preview (first 800 chars)", preview=summary + "..." if len(json.dumps(body, default=str)) > 800 else "")
        except Exception as e:
            _log("RESPONSE", "Could not serialize body for log", error=str(e))
    except Exception as e:
        _log("RESPONSE", "Failed to log response", error=str(e))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DOWNLOAD_TIMEOUT = 30  # seconds per image
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _resolve_user_and_audience(profile_id: str, audience_id: str) -> tuple:
    """
    Resolve user profile by clerkId (profileId) and get audience description.
    Returns (user_doc_id, audience_description).
    Raises HTTPException if user or audience not found.
    """
    _log("FIRESTORE", "Resolving user and audience", profile_id=profile_id, audience_id=audience_id)
    user = get_user_by_clerk_id(profile_id)
    if not user:
        _log("FIRESTORE", "User not found", profile_id=profile_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User profile not found for profileId (clerkId): {profile_id}",
        )
    user_doc_id, _ = user
    _log("FIRESTORE", "User found", user_doc_id=user_doc_id)
    audience = get_audience_by_id(user_doc_id, audience_id)
    if not audience:
        _log("FIRESTORE", "Audience not found", user_doc_id=user_doc_id, audience_id=audience_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audience not found: {audience_id} for user {user_doc_id}",
        )
    description = (audience.get("description") or "").strip()
    if not description:
        _log("FIRESTORE", "Audience has no description", audience_id=audience_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Audience '{audience_id}' has no description; cannot use as target user descriptor.",
        )
    _log("FIRESTORE", "Audience resolved", audience_id=audience_id, description_len=len(description))
    return user_doc_id, description


def _get_ordered_asset_urls_from_folders(user_doc_id: str, folder_ids: List[str]) -> List[str]:
    """
    Get ordered list of image URLs from one or more asset folders.
    Order: by folder order in folder_ids, then by stepNumber within each folder.
    Raises HTTPException if a folder is missing or has no assets with url.
    """
    _log("ASSETS", "Fetching asset URLs from folders", user_doc_id=user_doc_id, folder_ids=folder_ids)
    urls = []
    for folder_id in folder_ids:
        folder = get_asset_folder(user_doc_id, folder_id)
        if not folder:
            _log("ASSETS", "Folder not found", folder_id=folder_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset folder not found: {folder_id}",
            )
        assets = get_folder_assets(user_doc_id, folder_id)
        n_with_url = sum(1 for a in assets if (a.get("url") or "").strip())
        _log("ASSETS", "Folder assets", folder_id=folder_id, total_assets=len(assets), with_url=n_with_url)
        for a in assets:
            u = (a.get("url") or "").strip()
            if u:
                urls.append(u)
    if not urls:
        _log("ASSETS", "No URLs found in any folder")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No assets with url found in the selected folder(s).",
        )
    _log("ASSETS", "Total URLs to download", count=len(urls))
    return urls


def _resolve_local_image_paths(local_ads_dir: str) -> List[Path]:
    """
    Resolve local_ads_dir (relative to backend root or absolute) and return
    sorted list of image file paths. Raises HTTPException if folder missing or no images.
    """
    path = Path(local_ads_dir)
    if not path.is_absolute():
        path = BASE_DIR / local_ads_dir
    if not path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Local folder not found: {path}",
        )
    images = sorted(
        [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in _IMAGE_EXTENSIONS],
        key=lambda p: (p.name.lower(), p.name),
    )
    if not images:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No image files (jpg/png/webp/gif) found in {path}",
        )
    return images


async def _download_images(urls: List[str], dest_dir: Path) -> List[Path]:
    """Download all image URLs concurrently into dest_dir. Returns local paths (same order)."""
    async def _fetch(url: str, idx: int) -> Path:
        ext = Path(url.split("?")[0]).suffix or ".jpg"
        local = dest_dir / f"img_{idx:03d}{ext}"
        async with httpx.AsyncClient(timeout=_DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        local.write_bytes(resp.content)
        return local

    tasks = [_fetch(str(url), i) for i, url in enumerate(urls)]
    try:
        paths = await asyncio.gather(*tasks)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to download image from {exc.request.url}: HTTP {exc.response.status_code}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image download error: {exc}",
        )
    return list(paths)


def _persona_to_summary(persona) -> PersonaSummary:
    return PersonaSummary(
        uuid=persona.uuid,
        occupation=persona.occupation,
        age=persona.age,
        sex=persona.sex,
        location=f"{persona.district}, {persona.state}",
        zone=persona.zone,
        monthly_income_inr=persona.monthly_income_inr,
        digital_literacy=persona.digital_literacy,
        primary_device=persona.primary_device,
        purchasing_power_tier=persona.purchasing_power_tier,
        scam_vulnerability=persona.scam_vulnerability,
        financial_risk_tolerance=persona.financial_risk_tolerance,
    )


async def _build_ad_reaction_monologue(persona, ad, reaction) -> str:
    """Generate first-person internal monologue for this persona's reaction to this ad."""
    from src.api.gemini_client import gemini_client

    ad_copy_preview = (ad.copy or ad.description or "")[:500]
    prompt = f"""You are {persona.occupation}, {persona.age} years old, {persona.sex}, from {persona.district}, {persona.state} ({persona.zone}).
Your income is ₹{persona.monthly_income_inr:,}/month. Digital literacy: {persona.digital_literacy}/10. Device: {persona.primary_device}.
Purchasing power: {persona.purchasing_power_tier}. Scam vulnerability: {persona.scam_vulnerability}.

You just saw an ad (Creative: {ad.ad_id}). Ad copy or description: {ad_copy_preview or 'Visual ad.'}

Your simulated reaction was: {reaction.action} (trust {reaction.trust_score}/10, relevance {reaction.relevance_score}/10). Intent: {reaction.intent_level}.
Reasoning: {reaction.reasoning}. Emotional response: {reaction.emotional_response}.
{f"Barriers: {', '.join(reaction.barriers)}" if reaction.barriers else ""}

Write your full internal monologue in first person, as if you are thinking to yourself while looking at this ad. Include your immediate gut reaction, what catches your eye or puts you off, how it fits (or doesn't) your life and budget, and why you would {reaction.action} it. Be specific and in character. Write 3-6 sentences. Return only the monologue text, no labels or quotes."""

    try:
        return await gemini_client.generate_flash(prompt)
    except Exception as exc:
        return f"[Monologue unavailable: {exc}]"


# ---------------------------------------------------------------------------
# Persona loading (dynamic target group)
# ---------------------------------------------------------------------------

async def _load_and_hydrate_personas(n: int, target_group: str):
    """
    Load raw personas filtered to the requested target group description,
    then hydrate them with psychographic data.

    We use a best-effort approach:
      1. Try DB keyword filter derived from target_group
      2. Fallback to generic sample
    Then hydrate with LLM.
    """
    _log("PERSONA", "Loading and hydrating personas", n=n, target_group_len=len(target_group))
    # Ensure DB is loaded
    try:
        if not data_loader.conn:
            _log("PERSONA", "DB not connected, loading from HuggingFace")
            data_loader.load_from_huggingface()
        else:
            _log("PERSONA", "DB already connected (personas table available)")
    except Exception as e:
        _log("PERSONA", "HuggingFace load failed (will try sample fallback)", error=str(e))

    # Try dynamic filter first (keyword search on occupation / professional_persona)
    keywords = [kw.strip() for kw in target_group.replace(",", " ").split() if len(kw.strip()) > 3]
    raw_personas = []

    if data_loader.conn and keywords:
        try:
            _log("PERSONA", "Filtering by keywords", keywords=keywords[:5])
            raw_personas = data_loader.filter_by_keywords(keywords, count=n)
            _log("PERSONA", "Filter returned", count=len(raw_personas))
        except Exception as e:
            _log("PERSONA", "filter_by_keywords failed, using fallback", error=str(e))

    # Fallback: generic sample
    if not raw_personas:
        try:
            _log("PERSONA", "Loading sample personas", count=n)
            raw_personas = data_loader.load_sample_personas(count=n)
            _log("PERSONA", "Sample personas loaded", count=len(raw_personas))
        except Exception as e:
            _log("PERSONA", "load_sample_personas failed", error=str(e))
            raw_personas = []

    if not raw_personas:
        _log("PERSONA", "No personas available, raising 500")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load persona dataset. Ensure DB is initialised.",
        )

    _log("PERSONA", "Hydrating personas with LLM", count=len(raw_personas))
    enriched = await persona_hydrator.hydrate_batch(raw_personas)
    _log("PERSONA", "Hydration complete", count=len(enriched))
    return enriched


# ---------------------------------------------------------------------------
# Ad simulation pipeline
# ---------------------------------------------------------------------------

async def _run_ad_simulation(
    body: RunSimulationRequest,
    image_paths: List[Path],
) -> AdSimulationResult:
    from src.core.simulation_engine import Ad  # local import avoids circular deps
    from src.utils.ad_copy_extractor import extract_copy_for_all_ads

    # Build Ad objects from downloaded images
    ads_dir = image_paths[0].parent
    copy_map = await extract_copy_for_all_ads(ads_dir)

    ads = []
    for idx, path in enumerate(image_paths, 1):
        ad_id = f"ad_{idx}"
        extracted_copy = copy_map.get(str(path), "")
        ads.append(
            Ad(
                ad_id=ad_id,
                name=f"Creative {idx}",
                copy=extracted_copy,
                image_path=str(path),
                description=f"Ad creative {idx} from URL {idx}",
            )
        )

    # Load & hydrate personas
    personas = await _load_and_hydrate_personas(body.n, body.target_group)

    # Run simulation
    sim = AdSimulator(product_category=body.product_category or "general")
    result = await sim.run(personas, ads)
    reactions = result.reactions

    # Validate
    ad_contexts = {
        ad.ad_id: {"copy": ad.copy, "description": ad.description, "scam_indicators": "Unknown"}
        for ad in ads
    }
    validation = validator.validate_batch(personas, reactions, ad_contexts)
    valid_reactions = validator.filter_valid_reactions(personas, reactions, ad_contexts)

    # Optimize
    optimization = optimizer.optimize_portfolio(valid_reactions, personas, max_ads=len(ads))

    # Build heatmap
    ad_ids = [ad.ad_id for ad in ads]
    heatmap = optimizer.generate_heatmap_matrix(valid_reactions, personas, ad_ids)

    # Shape response: generate internal monologue for each reaction, then build details
    persona_map = {p.uuid: p for p in personas}
    ad_map = {ad.ad_id: ad for ad in ads}

    monologue_tasks = [
        _build_ad_reaction_monologue(persona_map[r.persona_uuid], ad_map[r.ad_id], r)
        for r in valid_reactions
    ]
    monologues = await asyncio.gather(*monologue_tasks, return_exceptions=True)

    def _mono_for(i: int):
        m = monologues[i]
        if isinstance(m, str):
            return m
        if isinstance(m, Exception):
            return f"[Monologue unavailable: {m}]"
        return None

    reaction_details = [
        AdReactionDetail(
            persona=_persona_to_summary(persona_map[r.persona_uuid]),
            ad_id=r.ad_id,
            trust_score=r.trust_score,
            relevance_score=r.relevance_score,
            action=r.action,
            intent_level=r.intent_level,
            reasoning=r.reasoning,
            emotional_response=r.emotional_response,
            barriers=r.barriers or [],
            internal_monologue=_mono_for(i),
        )
        for i, r in enumerate(valid_reactions)
    ]

    performances = {
        k: AdPerformanceSummary(
            ad_id=k,
            total_impressions=v.total_impressions,
            clicks=v.clicks,
            click_rate=v.click_rate,
            high_intent_leads=v.high_intent_leads,
            conversion_rate=v.conversion_rate,
            unique_reach=v.unique_reach,
        )
        for k, v in optimization["all_performances"].items()
    }

    portfolio = [
        PortfolioRecommendationOut(
            ad_id=r.ad_id,
            role=r.role,
            budget_split=r.budget_split,
            target_segment=r.target_segment,
            unique_reach=r.unique_reach,
            expected_conversions=r.expected_conversions,
            reasoning=getattr(r, "reasoning", None),
        )
        for r in optimization["winning_portfolio"]
    ]

    serialized_validation = {
        "total": validation["total"],
        "valid": validation["valid"],
        "flagged": validation["flagged"],
        "flagged_percentage": validation["flagged_percentage"],
    }

    return AdSimulationResult(
        personas=[_persona_to_summary(p) for p in personas],
        reactions=reaction_details,
        performance=performances,
        winning_portfolio=portfolio,
        wasted_spend_alerts=optimization.get("wasted_spend_alerts", []),
        visual_heatmap=heatmap,
        validation_summary=serialized_validation,
        metadata={
            "target_group": body.target_group,
            "num_personas": len(personas),
            "num_ads": len(ads),
            "total_reactions": len(reactions),
            "valid_reactions": len(valid_reactions),
        },
    )


# ---------------------------------------------------------------------------
# Product flow simulation pipeline
# ---------------------------------------------------------------------------

async def _build_persona_monologue(persona, journey_dict: Dict[str, Any]) -> str:
    """Generate a brief internal-monologue summary for one persona's journey."""
    from src.api.gemini_client import gemini_client

    completed = journey_dict.get("completed_flow", False)
    drop_reason = journey_dict.get("drop_off_reason", "")
    decisions_text = "\n".join(
        f"  Screen {d['view_number']} ({d['view_name']}): {d['decision']} — {d['reasoning']}"
        for d in journey_dict.get("decisions", [])
    )

    prompt = f"""You are {persona.occupation}, {persona.age}yo {persona.sex} from {persona.district}, {persona.state}.
Digital literacy: {persona.digital_literacy}/10. Income: ₹{persona.monthly_income_inr:,}/month.

You just went through a product onboarding flow. Here's what happened:
{decisions_text}

Result: {"COMPLETED ✅" if completed else f"DROPPED OFF ❌ — {drop_reason}"}

Write a 2-3 sentence first-person internal monologue capturing your experience, feelings, and key friction point (if any).
Be specific and stay in character. Return only the monologue text."""

    try:
        return await gemini_client.generate_flash(prompt)
    except Exception:
        if completed:
            return f"I made it through. The process felt manageable and worth my time."
        return f"I stopped partway through. {drop_reason or 'It was not clear enough for me.'}"


async def _run_flow_simulation(
    body: RunSimulationRequest,
    image_paths: List[Path],
) -> FlowSimulationResult:
    # Build a single FlowStimulus from the ordered image list
    flow_id = f"flow_{uuid.uuid4().hex[:6]}"
    screens = [
        FlowScreen(
            view_id=f"screen_{i}",
            view_number=i,
            view_name=f"Screen {i}",
            image_path=str(path),
            description=f"Screen {i} of the product flow",
            step_type="MANDATORY",
        )
        for i, path in enumerate(image_paths, 1)
    ]
    flow = FlowStimulus(flow_id=flow_id, flow_name="Uploaded Flow", screens=screens)

    # Load & hydrate personas
    personas = await _load_and_hydrate_personas(body.n, body.target_group)

    # Run flow simulation
    flow_sim = FlowSimulator()
    journey_results = await flow_sim.run_flow(personas, flow, analyze_screens=True, progress=False)

    # Build persona map
    persona_map = {p.uuid: p for p in personas}

    # Generate monologues concurrently
    journey_dicts = [journey_result_to_dict(j) for j in journey_results]
    monologue_tasks = [
        _build_persona_monologue(persona_map[jd["persona_uuid"]], jd)
        for jd in journey_dicts
    ]
    monologues = await asyncio.gather(*monologue_tasks, return_exceptions=True)

    # Shape journeys
    journeys_out: List[PersonaJourneyOut] = []
    for jd, monologue in zip(journey_dicts, monologues):
        persona = persona_map[jd["persona_uuid"]]
        steps = [
            FlowStepOut(
                view_id=d["view_id"],
                view_number=d["view_number"],
                view_name=screens[d["view_number"] - 1].view_name if d["view_number"] <= len(screens) else f"Screen {d['view_number']}",
                step_type=d["step_type"],
                decision=d["decision"],
                reasoning=d["reasoning"],
                drop_off_reason=d.get("drop_off_reason"),
                trust_score=d.get("trust_score", 5),
                clarity_score=d.get("clarity_score", 5),
                value_perception_score=d.get("value_perception_score", 5),
                emotional_state=d.get("emotional_state", "neutral"),
                time_spent_seconds=d.get("time_spent_seconds", 10),
            )
            for d in jd.get("decisions", [])
        ]
        journeys_out.append(
            PersonaJourneyOut(
                persona=_persona_to_summary(persona),
                flow_id=flow_id,
                completed_flow=jd["completed_flow"],
                dropped_off_at_view=jd.get("dropped_off_at_view"),
                drop_off_reason=jd.get("drop_off_reason"),
                total_screens_seen=jd["total_screens_seen"],
                total_time_seconds=jd["total_time_seconds"],
                steps=steps,
                monologue=monologue if isinstance(monologue, str) else None,
            )
        )

    # Aggregate insights
    total = len(journeys_out)
    completed_count = sum(1 for j in journeys_out if j.completed_flow)
    completion_rate = round(completed_count / total * 100, 1) if total else 0.0
    avg_time = round(sum(j.total_time_seconds for j in journeys_out) / total, 1) if total else 0.0

    # Top drop-off screen
    drop_screens = [j.dropped_off_at_view for j in journeys_out if j.dropped_off_at_view is not None]
    top_drop_screen = None
    if drop_screens:
        top_drop_screen = f"Screen {max(set(drop_screens), key=drop_screens.count)}"

    drop_reasons = [j.drop_off_reason for j in journeys_out if j.drop_off_reason]
    top_drop_reason = max(set(drop_reasons), key=drop_reasons.count) if drop_reasons else None

    # Friction points: collect all unique friction points across all steps
    all_friction: List[str] = []
    for j in journeys_out:
        for step in j.steps:
            pass  # FlowStepOut doesn't carry friction_points list; we rely on drop_off_reason

    flow_insights = [
        FlowComparisonInsight(
            flow_id=flow_id,
            flow_name="Uploaded Flow",
            completion_rate=completion_rate,
            avg_time_seconds=avg_time,
            top_drop_off_screen=top_drop_screen,
            top_drop_off_reason=top_drop_reason,
            friction_points=list({r for r in drop_reasons if r}),
        )
    ]

    return FlowSimulationResult(
        personas=[_persona_to_summary(p) for p in personas],
        journeys=journeys_out,
        flow_insights=flow_insights,
        metadata={
            "target_group": body.target_group,
            "num_personas": total,
            "num_screens": len(screens),
            "completion_rate_pct": completion_rate,
            "avg_time_seconds": avg_time,
        },
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/run",
    response_model=SimulationResponse,
    summary="Run a simulation",
    description=(
        "Runs an AI-powered simulation on the supplied image set.\n\n"
        "**simulation_type=0 (Ad simulation):** Each URL is an ad creative. "
        "Personas react to each ad; the engine returns click rates, trust scores, "
        "emotional responses, and an optimal budget allocation.\n\n"
        "**simulation_type=1 (Product flow simulation):** URLs are ordered product flow screens. "
        "Personas step through the flow; the engine returns per-screen decisions, "
        "completion rates, drop-off reasons, and a first-person internal monologue per persona."
    ),
)
async def run_simulation(
    body: RunSimulationRequest,
    current_user: dict = Depends(get_current_user),
) -> SimulationResponse:
    simulation_id = uuid.uuid4().hex
    start = time.time()

    if body.local_ads_dir and (not body.image_urls or len(body.image_urls) == 0):
        # Use local folder: resolve and get sorted image paths
        image_paths = _resolve_local_image_paths(body.local_ads_dir)
        if body.simulation_type == 0:
            result = await _run_ad_simulation(body, image_paths)
        else:
            result = await _run_flow_simulation(body, image_paths)
    else:
        # Download from URLs into a temp dir (auto-cleaned on exit)
        with tempfile.TemporaryDirectory(prefix="apriori_sim_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_paths = await _download_images([str(u) for u in body.image_urls], tmp_path)
            if body.simulation_type == 0:
                result = await _run_ad_simulation(body, image_paths)
            else:
                result = await _run_flow_simulation(body, image_paths)

    elapsed = round(time.time() - start, 2)
    result.metadata["execution_time_seconds"] = elapsed
    result.metadata["simulation_id"] = simulation_id
    result.metadata["run_by_uid"] = current_user["uid"]

    response = SimulationResponse(simulation_id=simulation_id, result=result)
    _log_response_before_send(response)
    return response


# ---------------------------------------------------------------------------
# Frontend contract: product-flow and ad-portfolio (profileId + Firestore)
# ---------------------------------------------------------------------------

async def _run_simulation_from_firestore(
    profile_id: str,
    audience_id: str,
    folder_ids: List[str],
    simulation_type: int,
    simulation_name: str,
    optimize_metric: str = "",
) -> SimulationResponse:
    """
    Shared flow: resolve user/audience from Firestore, get ordered asset URLs
    from folder(s), download images, run engine with n=1 and audience description.
    """
    start = time.time()
    sim_type_label = "ad-portfolio" if simulation_type == 0 else "product-flow"
    _log("START", "Simulation from Firestore", name=simulation_name, type=sim_type_label, profile_id=profile_id)

    user_doc_id, target_group = _resolve_user_and_audience(profile_id, audience_id)
    _log("PERSONA", "Target group from audience", target_group_len=len(target_group), preview=target_group[:80] + "..." if len(target_group) > 80 else target_group)

    urls = _get_ordered_asset_urls_from_folders(user_doc_id, folder_ids)
    # Internal body for engine: n=1 (personaDepth low/medium/high all use n=1)
    body = SimpleNamespace(n=1, target_group=target_group, product_category="general")

    simulation_id = uuid.uuid4().hex
    _log("DOWNLOAD", "Downloading images to temp dir", url_count=len(urls))
    with tempfile.TemporaryDirectory(prefix="apriori_sim_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        image_paths = await _download_images(urls, tmp_path)
        _log("DOWNLOAD", "Download complete", path_count=len(image_paths))
        _log("ENGINE", "Running simulation engine", simulation_type=sim_type_label)
        if simulation_type == 0:
            result = await _run_ad_simulation(body, image_paths)
        else:
            result = await _run_flow_simulation(body, image_paths)
        _log("ENGINE", "Simulation complete", result_type=type(result).__name__)

    elapsed = round(time.time() - start, 2)
    result.metadata["execution_time_seconds"] = elapsed
    result.metadata["simulation_name"] = simulation_name
    result.metadata["profile_id"] = profile_id
    result.metadata["audience_id"] = audience_id
    result.metadata["folder_ids"] = folder_ids
    if optimize_metric:
        result.metadata["optimize_metric"] = optimize_metric
    result.metadata["simulation_id"] = simulation_id

    response = SimulationResponse(simulation_id=simulation_id, result=result)
    _log_response_before_send(response)
    return response


@router.post(
    "/product-flow",
    response_model=SimulationResponse,
    summary="Run product flow simulation (frontend contract)",
    description=(
        "Runs a product flow simulation using profileId, audience, and selected asset folders from Firestore. "
        "Resolves user by clerkId, audience description for target group, and ordered assets (by stepNumber) from each folder. "
        "Persona depth is fixed at n=1."
    ),
)
async def run_product_flow_simulation(body: ProductFlowSimulationRequest) -> SimulationResponse:
    return await _run_simulation_from_firestore(
        profile_id=body.profileId,
        audience_id=body.audience,
        folder_ids=body.selectedFolderIds,
        simulation_type=1,
        simulation_name=body.name,
        optimize_metric=body.optimizeMetric,
    )


@router.post(
    "/ad-portfolio",
    response_model=SimulationResponse,
    summary="Run ad portfolio simulation (frontend contract)",
    description=(
        "Runs an ad portfolio simulation using profileId, audience, and a single ad-creative folder from Firestore. "
        "Resolves user by clerkId, audience description for target group, and ordered assets (by stepNumber) from the folder. "
        "Persona depth is fixed at n=1."
    ),
)
async def run_ad_portfolio_simulation(body: AdPortfolioSimulationRequest) -> SimulationResponse:
    return await _run_simulation_from_firestore(
        profile_id=body.profileId,
        audience_id=body.audience,
        folder_ids=[body.selectedFolderId],
        simulation_type=0,
        simulation_name=body.name,
        optimize_metric="",
    )
