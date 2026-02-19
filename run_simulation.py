#!/usr/bin/env python3
"""
Unified Simulation Runner - One entry point for all Apriori simulations.

Usage:
  python run_simulation.py --company ohsou --mode ad
  python run_simulation.py --company loop_health --mode flow
  python run_simulation.py --company loop_health --mode flow --flows-dir product_flow

Company plugins define: target users, assets (ads/flows), domain context.
Core simulation engine: abstract, shared between both use cases.
"""

import argparse
import asyncio
import json
import shutil
import time
from pathlib import Path

from src.companies.base import SimulationMode
from src.companies.loop_health import LoopHealthPlugin
from src.companies.ohsou import OhsouPlugin
from src.companies.blink_money import BlinkMoneyPlugin
from src.core.ad_simulator import AdSimulator
from src.core.flow_simulator import FlowSimulator, journey_result_to_dict
from src.core.flow_analyzer import compare_flows
from src.utils.config import DATA_DIR
from src.core.validator import validator
from src.core.optimizer import optimizer
from src.utils.report_generator import (
    generate_persona_comparison_report,
    generate_ad_comparison_report,
    generate_founder_ready_report,
    generate_summary_report
)


COMPANY_REGISTRY = {
    "ohsou": OhsouPlugin,
    "loop_health": LoopHealthPlugin,
    "blink_money": BlinkMoneyPlugin,
}


def get_plugin(company_id: str):
    """Get company plugin by id."""
    if company_id not in COMPANY_REGISTRY:
        raise ValueError(
            f"Unknown company: {company_id}. Available: {list(COMPANY_REGISTRY.keys())}"
        )
    return COMPANY_REGISTRY[company_id]()


async def run_ad_simulation(plugin, args):
    """Run ad simulation: load personas, ads, simulate, optimize, report."""
    print("\n" + "=" * 80)
    print(f"🎯 APRIORI AD SIMULATOR - {plugin.config.company_name}")
    print("=" * 80)
    
    start = time.time()
    
    # Load
    print("\n📚 Loading personas...")
    personas = await plugin.load_personas(count=args.num_personas)
    print(f"   ✅ {len(personas)} personas")
    
    print("\n📸 Loading ads...")
    ads_dir = Path(args.ads_dir) if args.ads_dir else None
    ads = await plugin.load_ads(ads_dir=ads_dir)
    print(f"   ✅ {len(ads)} ad creatives")
    
    # Simulate
    print("\n🎬 Running simulation...")
    ad_sim = AdSimulator(product_category=plugin.config.product_category)
    result = await ad_sim.run(personas, ads)
    reactions = result.reactions
    
    # Validate
    print("\n🔍 Validating reactions...")
    ad_contexts = {
        ad.ad_id: {"copy": ad.copy, "description": ad.description, "scam_indicators": "Unknown"}
        for ad in ads
    }
    validation = validator.validate_batch(personas, reactions, ad_contexts)
    valid_reactions = validator.filter_valid_reactions(personas, reactions, ad_contexts)
    print(f"   ✅ {len(valid_reactions)}/{len(reactions)} valid")
    
    # Optimize
    print("\n📊 Optimizing portfolio...")
    optimization = optimizer.optimize_portfolio(
        valid_reactions, personas, max_ads=len(ads)
    )
    
    # Save outputs
    out_dir = plugin.config.data_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / "raw_reactions.json", "w") as f:
        json.dump([r.model_dump() for r in reactions], f, indent=2)
    with open(out_dir / "enriched_personas.json", "w") as f:
        json.dump([p.model_dump() for p in personas], f, indent=2)
    
    generate_persona_comparison_report(personas, valid_reactions, ads, out_dir)
    generate_ad_comparison_report(personas, valid_reactions, ads, out_dir)
    generate_founder_ready_report(optimization, out_dir)
    generate_summary_report(out_dir)
    
    report = {
        "winning_portfolio": [r.model_dump() for r in optimization["winning_portfolio"]],
        "metadata": {
            "company": plugin.config.company_id,
            "num_personas": len(personas),
            "num_ads": len(ads),
            "execution_time_seconds": round(time.time() - start, 2)
        }
    }
    report_path = out_dir / "simulation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    # Summary
    print("\n" + "=" * 80)
    print("🎉 AD SIMULATION COMPLETE")
    print("=" * 80)
    print(f"\n⏱️  Time: {report['metadata']['execution_time_seconds']}s")
    print("\n📈 Winning portfolio:")
    for r in optimization["winning_portfolio"]:
        print(f"   • {r.ad_id}: {r.budget_split}% | {r.expected_conversions} high-intent")
    print(f"\n📁 Outputs: {out_dir}")
    
    return report


async def run_flow_simulation(plugin, args):
    """Run flow simulation: load personas, flows, simulate each, compare, report."""
    print("\n" + "=" * 80)
    print(f"  APRIORI FLOW SIMULATOR — {plugin.config.company_name}")
    print("=" * 80)

    start = time.time()

    # -- Load personas --
    print("\n  Loading personas...")
    personas = await plugin.load_personas(count=args.num_personas)
    print(f"   ✓ {len(personas)} personas loaded")

    # -- Load flows --
    print("\n  Loading flows...")
    flows_dir = Path(args.flows_dir) if args.flows_dir else None
    flow_dirs = [Path(p) for p in args.flow_dirs] if args.flow_dirs else None
    flows = await plugin.load_flows(flows_dir=flows_dir, flow_dirs=flow_dirs)
    if not flows:
        print("   ✗ No flows found. Check --flows-dir or --flow-dirs")
        return None
    print(f"   ✓ {len(flows)} flow(s): {[f.flow_name for f in flows]}")

    # -- Simulate --
    # Priority 1: Company plugin exposes its own specialized simulator (e.g. BlinkMoney, Loop Health)
    # Priority 2: Generic FlowSimulator
    flow_results: Dict[str, list] = {}

    if hasattr(plugin, "get_flow_simulator"):
        sim = plugin.get_flow_simulator()
        for flow in flows:
            journeys = await sim.run_flow(personas, flow)
            flow_results[flow.flow_id] = [journey_result_to_dict(j) for j in journeys]

    elif hasattr(plugin, "get_enhanced_flow_simulator"):
        # Loop Health legacy path
        enh_sim = plugin.get_enhanced_flow_simulator()
        for flow in flows:
            from loop_health_simulator_v2 import FlowView
            views = [
                FlowView(
                    view_id=s.view_id, view_number=s.view_number,
                    view_name=s.view_name, image_path=s.image_path,
                    description=s.description,
                    intervention_applied=s.intervention_applied
                )
                for s in flow.screens
            ]
            view_analyses_list = await asyncio.gather(
                *[enh_sim.analyze_view_with_interventions(v) for v in views]
            )
            view_analyses = {views[i].view_id: view_analyses_list[i] for i in range(len(views))}
            journeys = await asyncio.gather(
                *[enh_sim.simulate_enhanced_journey(p, views, view_analyses) for p in personas]
            )
            flow_results[flow.flow_id] = [
                {
                    "persona_uuid": j.persona_uuid, "flow_id": flow.flow_id,
                    "completed_flow": j.completed_flow,
                    "dropped_off_at_view": j.dropped_off_at_view,
                    "drop_off_reason": j.drop_off_reason,
                    "total_screens_seen": j.total_views_seen,
                    "total_time_seconds": j.total_time_seconds,
                    "decisions": [
                        {
                            "view_id": d.view_id if hasattr(d, "view_id") else f"view_{d.view_number}",
                            "view_number": d.view_number, "decision": d.decision,
                            "reasoning": d.reasoning,
                            "drop_off_reason": j.drop_off_reason if d.decision == "DROP_OFF" else None,
                        }
                        for d in j.decisions
                    ],
                    "metadata": {}
                }
                for j in journeys
            ]
    else:
        flow_sim = FlowSimulator()
        raw = await flow_sim.run_multiple_flows(personas, flows)
        flow_results = {
            fid: [journey_result_to_dict(r) for r in results]
            for fid, results in raw.items()
        }

    # -- Analyze & compare --
    print("\n  Analyzing and comparing flows...")
    flow_names = {f.flow_id: f.flow_name for f in flows}
    comparison = compare_flows(flow_results, flow_names)

    # -- Console summary --
    print("\n" + "=" * 80)
    print("  FLOW COMPARISON RESULT")
    print("=" * 80)
    print(f"\n  Winner: {comparison.winning_flow_name}  ({comparison.winning_completion_rate:.1f}% completion)")
    print(f"\n  Why: {comparison.why_winner_wins}")
    print("\n  Rankings:")
    for r in comparison.flow_rankings:
        dov = r.get("dominant_drop_off_view", "-")
        dor = r.get("dominant_drop_off_reason", "-")
        print(f"    {r['flow_name']}: {r['completion_rate']:.1f}%  |  "
              f"Top drop-off → Screen {dov}: {dor}")

    # -- Persist raw results --
    out_dir = plugin.config.data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "flow_simulation_results.json", "w") as f:
        json.dump(flow_results, f, indent=2, default=str)

    # -- Build and persist rich JSON report --
    report = {
        "winning_flow_id": comparison.winning_flow_id,
        "winning_flow_name": comparison.winning_flow_name,
        "winning_completion_rate": comparison.winning_completion_rate,
        "why_winner_wins": comparison.why_winner_wins,
        "flow_rankings": comparison.flow_rankings,
        "per_flow_analysis": {
            fid: {
                "completion_rate": a.completion_rate,
                "dominant_drop_off_view": a.dominant_drop_off_view,
                "dominant_drop_off_reason": a.dominant_drop_off_reason,
                "dominant_reason_count": a.dominant_reason_count,
            }
            for fid, a in comparison.per_flow_analysis.items()
        },
        "improvement_recommendations": comparison.improvement_recommendations,
        "metadata": {
            "company": plugin.config.company_id,
            "num_personas": len(personas),
            "num_flows": len(flows),
            "execution_time_seconds": round(time.time() - start, 2),
        },
    }
    with open(out_dir / "flow_comparison_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    # -- Build rich Markdown report --
    _write_markdown_report(
        out_dir / "flow_comparison_report.md",
        plugin, personas, flows, flow_results, comparison, flow_names
    )

    print(f"\n  Outputs written to: {out_dir}")
    print(f"    • flow_comparison_report.md   ← start here")
    print(f"    • flow_comparison_report.json")
    print(f"    • flow_simulation_results.json")

    return report


def _write_markdown_report(path, plugin, personas, flows, flow_results, comparison, flow_names):
    """Write a complete, human-readable markdown report."""
    lines = []
    a = lines.append

    a(f"# {plugin.config.company_name} — Flow Comparison Report\n")
    a(f"**Product**: {plugin.config.product_category.upper()}")
    a(f"**Personas**: {len(personas)} | **Flows tested**: {len(flows)}\n")

    # 1. Personas
    a("---\n## 1. Target Personas\n")
    for p in personas:
        # BlinkMoneyPersona fields
        city = getattr(p, "city", "")
        city_tier = getattr(p, "city_tier", "")
        age = getattr(p, "age", "")
        occ = getattr(p, "occupation", "")
        background = getattr(p, "background", "")
        key_q = getattr(p, "key_question", "")
        mfp = getattr(p, "mf_portfolio", None)
        liq = getattr(p, "liquidity_need", None)
        a(f"### {p.name}  `{p.uuid}`")
        a(f"- **{occ}** | {age}yo | {city} ({city_tier})")
        if mfp:
            a(f"- MF Portfolio: ₹{mfp.total_value_inr:,} | Platforms: {', '.join(mfp.platforms)}")
            a(f"- LAMF experience: {'Yes' if mfp.has_used_lamf_before else 'First time'} | Pledge comfort: {mfp.comfort_with_pledging}")
        if liq:
            a(f"- Need: ₹{liq.amount_needed_inr:,} ({liq.purpose}) | Urgency: **{liq.urgency}** | Timeline: {liq.time_to_need}")
        a(f"- *Background*: {background}")
        a(f"- *Key question*: \"{key_q}\"\n")

    # 2. Winner
    a("---\n## 2. Verdict\n")
    a(f"### 🏆 Winner: {comparison.winning_flow_name}")
    a(f"**Completion Rate**: {comparison.winning_completion_rate:.1f}%\n")
    a(f"**Why this flow wins**:\n\n{comparison.why_winner_wins}\n")

    # 3. Rankings table
    a("---\n## 3. Flow Rankings\n")
    a("| Rank | Flow | Completion | Dominant Drop-off Screen | Dominant Reason |")
    a("|------|------|------------|--------------------------|-----------------|")
    for i, r in enumerate(comparison.flow_rankings, 1):
        dov = r.get("dominant_drop_off_view", "—")
        dor = r.get("dominant_drop_off_reason") or "—"
        a(f"| {i} | {r['flow_name']} | {r['completion_rate']:.1f}% | Screen {dov} | {dor} |")
    a("")

    # 4. Per-flow detailed journey logs
    a("---\n## 4. Per-Flow Persona Journey Logs\n")
    for flow in flows:
        fid = flow.flow_id
        fname = flow.flow_name
        results = flow_results.get(fid, [])
        completions = sum(1 for r in results if r.get("completed_flow"))
        a(f"### {fname}  —  {completions}/{len(results)} completed ({100*completions/max(len(results),1):.0f}%)\n")

        for journey in results:
            pid = journey.get("persona_uuid", "?")
            completed = journey.get("completed_flow", False)
            dropped_at = journey.get("dropped_off_at_view")
            drop_reason = journey.get("drop_off_reason", "")
            meta = journey.get("metadata", {})
            persona_name = meta.get("persona_name", pid)
            urgency = meta.get("urgency", "")
            lamf_exp = meta.get("lamf_experience", "")

            status = "✅ Completed" if completed else f"❌ Dropped at Screen {dropped_at}"
            a(f"#### {persona_name}  ({status})")
            if urgency:
                a(f"- Urgency: {urgency} | LAMF exp: {'Yes' if lamf_exp else 'No'}")

            decisions = journey.get("decisions", [])
            for d in decisions:
                vnum = d.get("view_number", "?")
                dec = d.get("decision", "?")
                icon = "✅" if dec == "CONTINUE" else "🚪"
                reasoning = d.get("reasoning", "")
                dmeta = d.get("metadata", {})
                gut = dmeta.get("gut_reaction", "")
                audit = dmeta.get("critical_audit", "")
                friction = dmeta.get("friction_points") or d.get("friction_points", [])
                missing = dmeta.get("missing_element", "")
                trust = d.get("trust_score", "?")
                clarity = d.get("clarity_score", "?")

                a(f"\n**Screen {vnum}** — {icon} {dec}  (Trust: {trust}/10 | Clarity: {clarity}/10)")
                if gut:
                    a(f"> *Gut reaction*: {gut}")
                if audit:
                    a(f"> *Critical audit*: {audit}")
                a(f"- **Decision reasoning**: {reasoning}")
                if d.get("drop_off_reason"):
                    a(f"- **Drop-off reason**: {d['drop_off_reason']}")
                if friction:
                    a(f"- **Friction points**: {'; '.join(friction) if isinstance(friction, list) else friction}")
                if missing:
                    a(f"- **Missing**: {missing}")

            if not completed and drop_reason:
                a(f"\n> **Final drop-off**: {drop_reason}\n")
            else:
                a("")

    # 5. Improvement recommendations
    a("---\n## 5. Improvement Recommendations\n")
    for fid, recs in comparison.improvement_recommendations.items():
        name = flow_names.get(fid, fid)
        a(f"### {name}\n")
        for rec in recs:
            a(f"- {rec}")
        a("")

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Apriori Simulation Runner")
    parser.add_argument("--company", "-c", required=True,
                        choices=list(COMPANY_REGISTRY.keys()),
                        help="Company plugin (ohsou, loop_health, blink_money)")
    parser.add_argument("--mode", "-m", required=True, choices=["ad", "flow"],
                        help="Simulation mode")
    parser.add_argument("--num-personas", "-n", type=int, default=10,
                        help="Number of personas (default: 10)")
    parser.add_argument("--ads-dir", type=str, help="Ads directory (ad mode)")
    parser.add_argument("--flows-dir", type=str, help="Flows directory (flow mode)")
    parser.add_argument("--flow-dirs", type=str, nargs="+",
                        help="Multiple flow directories for comparison")
    
    args = parser.parse_args()
    
    plugin = get_plugin(args.company)
    
    if args.mode == "ad":
        if SimulationMode.AD not in plugin.config.modes:
            print(f"❌ {plugin.config.company_name} does not support Ad mode")
            return 1
        asyncio.run(run_ad_simulation(plugin, args))
    else:
        if SimulationMode.FLOW not in plugin.config.modes:
            print(f"❌ {plugin.config.company_name} does not support Flow mode")
            return 1
        asyncio.run(run_flow_simulation(plugin, args))
    
    return 0


if __name__ == "__main__":
    exit(main())
