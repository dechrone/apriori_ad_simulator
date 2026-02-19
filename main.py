"""Main orchestrator - End-to-end simulation pipeline."""

import asyncio
import shutil
import time
import json
import os
from pathlib import Path
from typing import List

from src.data.loader import data_loader
from src.core.persona_hydrator import persona_hydrator
from src.core.simulation_engine import simulation_engine, Ad
from src.core.validator import validator
from src.core.optimizer import optimizer
from src.utils.config import DATA_DIR
from src.utils.report_generator import (
    generate_persona_comparison_report,
    generate_ad_comparison_report,
    generate_summary_report,
    generate_founder_ready_report
)
from src.utils.ad_copy_extractor import extract_copy_for_all_ads


class AprioriOrchestrator:
    """Coordinates the full simulation pipeline."""
    
    async def run_full_simulation(
        self,
        ads: List[Ad],
        num_personas: int = 10,
        output_path: str = None,
        target_segment: str = "exporters_freelancers_smes"
    ) -> dict:
        """Execute the complete simulation workflow."""
        
        print("\n" + "="*80)
        print("🚀 APRIORI AD-PORTFOLIO SIMULATOR v2.0")
        print("="*80)
        
        start_time = time.time()
        
        # STEP 1: Load Personas
        print("\n📚 STEP 1: Loading Persona Dataset...")
        personas_file_env = os.getenv("PERSONAS_FILE")
        if personas_file_env:
            path = Path(personas_file_env)
            if not path.is_absolute():
                path = (Path(__file__).parent / path).resolve()
            print(f"   Source: {path}")
            raw_personas = data_loader.load_from_json(path)
            print(f"   Count: {len(raw_personas)} personas (from file)")
        else:
            print(f"   Target: {target_segment}")
            print(f"   Count: {num_personas} personas")
            try:
                if not data_loader.conn:
                    print("   📥 Attempting to load from HuggingFace (Nvidia Nemotron Personas India)...")
                    data_loader.load_from_huggingface()
            except Exception as e:
                print(f"   ⚠️ Could not load from HuggingFace: {e}")
                print("   💡 Will use local data or generate synthetic personas")
            if target_segment == "exporters_freelancers_smes":
                raw_personas = data_loader.filter_exporters_freelancers_smes(count=num_personas)
            else:
                raw_personas = data_loader.load_sample_personas(count=num_personas)
        
        print(f"\n✅ Loaded {len(raw_personas)} personas")
        
        selected_file = DATA_DIR / "selected_personas.json"
        with open(selected_file, 'w') as f:
            json.dump([p.model_dump() for p in raw_personas], f, indent=2)
        print(f"📄 Personas saved to: {selected_file}")
        
        print("\n📋 SELECTED PERSONAS:")
        print("-" * 80)
        skills_preview = lambda p: (p.skills_and_expertise_list or p.skills_and_expertise or "")[:60]
        for i, p in enumerate(raw_personas, 1):
            print(f"{i}. {p.occupation} | {p.age}yo {p.sex} | {p.district}, {p.state} ({p.zone})")
            print(f"   Education: {p.education_level} | Language: {p.first_language}")
            s = skills_preview(p)
            print(f"   Skills: {s}..." if s else "   Skills: —")
            print()
        
        # STEP 2: Hydrate Personas
        print("\n💧 STEP 2: Hydrating Personas (Adding Psychographic Data)...")
        print("   Enriching with: purchasing power, digital literacy, device type, scam vulnerability...")
        enriched_personas = await persona_hydrator.hydrate_batch(raw_personas)
        print(f"\n✅ Enriched {len(enriched_personas)} personas")
        
        # Save enriched personas to file
        enriched_file = DATA_DIR / "enriched_personas.json"
        with open(enriched_file, 'w') as f:
            json.dump([ep.model_dump() for ep in enriched_personas], f, indent=2)
        print(f"📄 Enriched personas saved to: {enriched_file}")
        
        print("\n📊 ENRICHMENT SUMMARY:")
        print("-" * 80)
        for i, ep in enumerate(enriched_personas, 1):
            print(f"{i}. {ep.occupation}")
            print(f"   💰 Purchasing Power: {ep.purchasing_power_tier} | Income: ₹{ep.monthly_income_inr:,}/month")
            print(f"   📱 Device: {ep.primary_device} | Digital Literacy: {ep.digital_literacy}/10")
            print(f"   ⚠️  Scam Vulnerability: {ep.scam_vulnerability} | Risk Tolerance: {ep.financial_risk_tolerance}")
            print()
        
        # STEP 3: Run Tiered Simulation
        print("\n🎬 STEP 3: Running Tiered Simulation (Pro + Flash)...")
        print(f"   - {len(ads)} ad creatives")
        print(f"   - {len(enriched_personas)} personas")
        print(f"   - Total simulations: {len(ads) * len(enriched_personas)}")
        print("\n   📸 Ad Creatives:")
        for ad in ads:
            print(f"      • {ad.ad_id}: {ad.name}")
            if ad.image_path:
                print(f"        Image: {ad.image_path}")
        
        reactions = await simulation_engine.run_simulation(enriched_personas, ads)
        print(f"\n✅ Generated {len(reactions)} reactions")
        
        # Save raw reactions to file
        reactions_file = DATA_DIR / "raw_reactions.json"
        with open(reactions_file, 'w') as f:
            json.dump([r.model_dump() for r in reactions], f, indent=2)
        print(f"📄 Raw reactions saved to: {reactions_file}")
        
        # Create detailed persona-ad matrix file
        print("\n📝 Creating detailed reaction report...")
        reaction_details = []
        persona_map = {p.uuid: p for p in enriched_personas}
        ad_map = {ad.ad_id: ad for ad in ads}
        
        for reaction in reactions:
            persona = persona_map[reaction.persona_uuid]
            ad = ad_map[reaction.ad_id]
            
            reaction_details.append({
                "persona": {
                    "uuid": persona.uuid,
                    "occupation": persona.occupation,
                    "age": persona.age,
                    "location": f"{persona.district}, {persona.state}",
                    "zone": persona.zone,
                    "income": persona.monthly_income_inr,
                    "digital_literacy": persona.digital_literacy,
                    "device": persona.primary_device
                },
                "ad": {
                    "ad_id": ad.ad_id,
                    "name": ad.name,
                    "image": ad.image_path,
                    "copy": ad.copy[:100] if ad.copy else "(empty)"
                },
                "reaction": {
                    "trust_score": reaction.trust_score,
                    "relevance_score": reaction.relevance_score,
                    "action": reaction.action,
                    "intent_level": reaction.intent_level,
                    "reasoning": reaction.reasoning,
                    "emotional_response": reaction.emotional_response,
                    "barriers": reaction.barriers
                }
            })
        
        detailed_file = DATA_DIR / "detailed_reactions.json"
        with open(detailed_file, 'w') as f:
            json.dump(reaction_details, f, indent=2)
        print(f"📄 Detailed reactions saved to: {detailed_file}")
        
        # Create human-readable report
        readable_file = DATA_DIR / "readable_reactions.txt"
        with open(readable_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("DETAILED PERSONA REACTIONS TO ADS\n")
            f.write("="*80 + "\n\n")
            
            for ad in ads:
                f.write(f"\n{'='*80}\n")
                f.write(f"AD: {ad.ad_id} - {ad.name}\n")
                f.write(f"Image: {ad.image_path}\n")
                f.write(f"Copy: {ad.copy if ad.copy else '(No copy provided)'}\n")
                f.write(f"{'='*80}\n\n")
                
                ad_reactions_list = [r for r in reactions if r.ad_id == ad.ad_id]
                
                for i, reaction in enumerate(ad_reactions_list, 1):
                    persona = persona_map[reaction.persona_uuid]
                    f.write(f"\nPERSONA {i}: {persona.occupation}\n")
                    f.write(f"{'-'*80}\n")
                    f.write(f"Demographics:\n")
                    f.write(f"  - Age: {persona.age}, Sex: {persona.sex}\n")
                    f.write(f"  - Location: {persona.district}, {persona.state} ({persona.zone})\n")
                    f.write(f"  - Income: ₹{persona.monthly_income_inr:,}/month ({persona.purchasing_power_tier})\n")
                    f.write(f"  - Device: {persona.primary_device}\n")
                    f.write(f"  - Digital Literacy: {persona.digital_literacy}/10\n")
                    f.write(f"  - Scam Vulnerability: {persona.scam_vulnerability}\n")
                    f.write(f"\nReaction:\n")
                    f.write(f"  - Trust Score: {reaction.trust_score}/10\n")
                    f.write(f"  - Relevance Score: {reaction.relevance_score}/10\n")
                    f.write(f"  - Action: {reaction.action}\n")
                    f.write(f"  - Intent Level: {reaction.intent_level}\n")
                    f.write(f"  - Emotional Response: {reaction.emotional_response}\n")
                    f.write(f"  - Reasoning: {reaction.reasoning}\n")
                    if reaction.barriers:
                        f.write(f"  - Barriers: {', '.join(reaction.barriers)}\n")
                    f.write(f"\n")
        
        print(f"📄 Readable report saved to: {readable_file}")
        
        print("\n📈 REACTION SUMMARY:")
        print("-" * 80)
        # Group by ad
        ad_reactions = {}
        for r in reactions:
            if r.ad_id not in ad_reactions:
                ad_reactions[r.ad_id] = []
            ad_reactions[r.ad_id].append(r)
        
        for ad_id, ad_rs in ad_reactions.items():
            clicks = sum(1 for r in ad_rs if r.action == "CLICK")
            high_intent = sum(1 for r in ad_rs if r.intent_level == "High")
            avg_trust = sum(r.trust_score for r in ad_rs) / len(ad_rs)
            avg_relevance = sum(r.relevance_score for r in ad_rs) / len(ad_rs)
            print(f"{ad_id}: {clicks}/{len(ad_rs)} clicks ({clicks/len(ad_rs)*100:.1f}%) | "
                  f"{high_intent} high-intent ({high_intent/len(ad_rs)*100:.1f}%) | "
                  f"Avg Trust: {avg_trust:.1f}/10 | Avg Relevance: {avg_relevance:.1f}/10")
        print()
        
        # STEP 4: Validate Reactions
        print("\n🔍 STEP 4: Validating Reactions (Anti-Hallucination Check)...")
        ad_contexts = {
            ad.ad_id: {
                "copy": ad.copy,
                "description": ad.description,
                "scam_indicators": "Unknown"
            }
            for ad in ads
        }
        
        validation_summary = validator.validate_batch(
            enriched_personas,
            reactions,
            ad_contexts
        )
        
        print(f"\n   📊 Validation Results:")
        print(f"      - Total: {validation_summary['total']}")
        print(f"      - Valid: {validation_summary['valid']}")
        print(f"      - Flagged: {validation_summary['flagged']} ({validation_summary['flagged_percentage']:.1f}%)")
        
        if validation_summary['flagged_reactions']:
            print(f"\n   ⚠️  FLAGGED REACTIONS (Removed):")
            print("-" * 80)
            for flagged in validation_summary['flagged_reactions'][:5]:  # Show first 5
                print(f"      • Persona: {flagged['persona_uuid'][:16]}... | Ad: {flagged['ad_id']}")
                for reason in flagged['flags']:
                    print(f"        - {reason}")
            if len(validation_summary['flagged_reactions']) > 5:
                print(f"      ... and {len(validation_summary['flagged_reactions']) - 5} more")
            print()
        
        # Filter to valid reactions only
        valid_reactions = validator.filter_valid_reactions(
            enriched_personas,
            reactions,
            ad_contexts
        )
        print(f"✅ Using {len(valid_reactions)} valid reactions for analysis")
        
        # STEP 5: Optimize Portfolio
        print("\n🎯 STEP 5: Optimizing Portfolio & Budget Allocation...")
        optimization_result = optimizer.optimize_portfolio(
            valid_reactions,
            enriched_personas,
            max_ads=len(ads)  # Allow all ads
        )
        print(f"\n✅ Portfolio optimized")
        
        # Display detailed performance analysis
        print("\n" + "="*80)
        print("📊 AD PERFORMANCE ANALYSIS (Sorted by High-Intent Leads)")
        print("="*80)
        
        # Sort ads by high-intent leads
        sorted_ads = sorted(
            optimization_result["all_performances"].items(),
            key=lambda x: x[1].high_intent_leads,
            reverse=True
        )
        
        for ad_id, perf in sorted_ads:
            print(f"\n{ad_id}:")
            print(f"   🎯 High-Intent Leads: {perf.high_intent_leads} ({perf.conversion_rate}% conversion)")
            print(f"   👆 Clicks: {perf.clicks} ({perf.click_rate}% click rate)")
            print(f"   👥 Unique Reach: {perf.unique_reach} personas")
            print(f"   📈 Impressions: {perf.total_impressions}")
            
            # Calculate conversion value
            conversion_value = perf.high_intent_leads * (1 + perf.conversion_rate / 100)
            print(f"   💎 Conversion Value Score: {conversion_value:.2f}")
        
        print("\n" + "="*80)
        print("🎯 WINNING PORTFOLIO & BUDGET ALLOCATION")
        print("="*80)
        print("\nBudget allocated based on HIGH-INTENT LEADS × CONVERSION QUALITY\n")
        
        for rec in optimization_result["winning_portfolio"]:
            print(f"✓ {rec.ad_id}: {rec.budget_split}% budget")
            print(f"  ├─ Role: {rec.role}")
            print(f"  ├─ Target Segment: {rec.target_segment}")
            print(f"  ├─ Expected Conversions: {rec.expected_conversions}")
            print(f"  └─ Unique Reach: {rec.unique_reach}")
            print()
        
        # Show coverage analysis
        print("\n" + "="*80)
        print("📍 AUDIENCE COVERAGE ANALYSIS")
        print("="*80)
        
        total_high_intent = sum(p.high_intent_leads for p in optimization_result["all_performances"].values())
        winning_high_intent = sum(rec.expected_conversions for rec in optimization_result["winning_portfolio"])
        coverage_pct = (winning_high_intent / total_high_intent * 100) if total_high_intent > 0 else 0
        
        print(f"\n   Total High-Intent Leads Available: {total_high_intent}")
        print(f"   Captured by Winning Portfolio: {winning_high_intent} ({coverage_pct:.1f}%)")
        
        if optimization_result["wasted_spend_alerts"]:
            print(f"\n⚠️  WASTED SPEND ALERTS:")
            for alert in optimization_result["wasted_spend_alerts"]:
                print(f"   • {alert}")
        
        print("\n" + "="*80)
        
        # STEP 6: Generate Heatmap
        print("\n🌡️ STEP 6: Generating Visual Heatmap...")
        ad_ids = [ad.ad_id for ad in ads]
        heatmap = optimizer.generate_heatmap_matrix(
            valid_reactions,
            enriched_personas,
            ad_ids
        )
        
        # Display heatmap in console
        print(f"\n🌡️ SEGMENT PERFORMANCE HEATMAP:")
        print(f"   Rows: {', '.join(heatmap['rows'])}")
        print(f"   Cols: {', '.join(heatmap['cols'])}")
        print(f"\n   Legend: 🟢 Strong (≥30%) | 🟡 Medium (≥15%) | 🟠 Weak (≥5%) | 🔴 Poor (<5%) | ⚪ No Data")
        print()
        for i, segment in enumerate(heatmap['rows']):
            print(f"   {segment:12} | {' '.join(heatmap['matrix'][i])}")
        
        print(f"\n✅ Heatmap generated and saved in report")
        
        # STEP 7: Generate Detailed Comparison Reports
        print("\n📊 STEP 7: Generating Detailed Comparison Reports...")
        
        generate_persona_comparison_report(enriched_personas, valid_reactions, ads, DATA_DIR)
        generate_ad_comparison_report(enriched_personas, valid_reactions, ads, DATA_DIR)
        
        # Generate Founder-Ready Report with "Oddly Specific" Insights
        print("\n✨ Generating Founder-Ready Portfolio Report...")
        generate_founder_ready_report(optimization_result, DATA_DIR)
        
        generate_summary_report(DATA_DIR)
        
        # STEP 8: Compile Final Report
        print("\n📊 STEP 8: Compiling Final Report...")
        
        # Serialize validation_summary to make it JSON serializable
        serialized_validation = {
            "total": validation_summary["total"],
            "valid": validation_summary["valid"],
            "flagged": validation_summary["flagged"],
            "flagged_percentage": validation_summary["flagged_percentage"],
            "flagged_reactions": [
                {
                    "persona_uuid": fr["persona_uuid"],
                    "ad_id": fr["ad_id"],
                    "flags": fr["flags"],
                    "reaction": fr["reaction"].model_dump()
                }
                for fr in validation_summary["flagged_reactions"]
            ]
        }
        
        # Prepare segment ownership data for JSON (convert persona objects to simplified dicts)
        serialized_segment_ownership = {}
        if "segment_ownership" in optimization_result:
            for cluster_id, ownership in optimization_result["segment_ownership"].items():
                serialized_segment_ownership[cluster_id] = {
                    "winning_ad": ownership["winning_ad"],
                    "trust_score": ownership["trust_score"],
                    "relevance_score": ownership["relevance_score"],
                    "conversion_rate": ownership["conversion_rate"],
                    "high_intent_count": ownership["high_intent_count"],
                    "persona_count": len(ownership["personas"]),
                    "reasoning": ownership["reasoning"],
                    "all_ad_scores": ownership["all_ad_scores"]
                }
        
        final_report = {
            "winning_portfolio": [rec.model_dump() for rec in optimization_result["winning_portfolio"]],
            "all_performances": {
                k: v.model_dump() 
                for k, v in optimization_result["all_performances"].items()
            },
            "overlap_matrix": optimization_result["overlap_matrix"],
            "audience_segments": optimization_result["audience_segments"],
            "segment_ownership": serialized_segment_ownership,
            "clusters": optimization_result.get("clusters", {}),
            "wasted_spend_alerts": optimization_result["wasted_spend_alerts"],
            "visual_heatmap": heatmap,
            "validation_summary": serialized_validation,
            "metadata": {
                "num_personas": len(enriched_personas),
                "num_ads": len(ads),
                "total_reactions": len(reactions),
                "valid_reactions": len(valid_reactions),
                "execution_time_seconds": round(time.time() - start_time, 2)
            }
        }
        
        # Save report
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(final_report, f, indent=2)
            
            print(f"✅ Report saved to: {output_file}")
        
        # Print Summary
        print("\n" + "="*80)
        print("🎉 SIMULATION COMPLETE!")
        print("="*80)
        print(f"\n⏱️  Execution Time: {final_report['metadata']['execution_time_seconds']} seconds")
        
        print(f"\n📈 Strategic Verdict (Budget allocation based on HIGH-INTENT LEADS):")
        for rec in optimization_result["winning_portfolio"]:
            print(f"   • {rec.ad_id}: {rec.budget_split}% budget")
            print(f"     ├─ {rec.expected_conversions} high-intent leads | {rec.role}")
            print(f"     └─ Target: {rec.target_segment}")
        
        if optimization_result["wasted_spend_alerts"]:
            print(f"\n⚠️  Wasted Spend Alerts:")
            for alert in optimization_result["wasted_spend_alerts"]:
                print(f"   • {alert}")
        
        print(f"\n📁 Output Files:")
        print(f"   • Full Report (JSON): {output_file if output_path else 'Not saved'}")
        print(f"   • ✨ Founder-Ready Report: {DATA_DIR}/founder_report.txt")
        print(f"   • Persona Comparison: {DATA_DIR}/persona_comparison.txt")
        print(f"   • Ad Comparison: {DATA_DIR}/ad_comparison.txt")
        print(f"   • Heatmap: Available in JSON report under 'visual_heatmap' key")
        
        print("\n" + "="*80)
        
        return final_report


# Global singleton
orchestrator = AprioriOrchestrator()


async def main():
    """Main execution with user's ad creatives."""
    
    # Load ad creatives from ads folder
    ads_dir = Path(__file__).parent / "ads"
    ad_files = sorted(ads_dir.glob("*.jpeg")) + sorted(ads_dir.glob("*.jpg")) + sorted(ads_dir.glob("*.png"))
    
    if not ad_files:
        print("❌ No ad images found in ads/ folder!")
        return
    
    print(f"📸 Found {len(ad_files)} ad creatives in ads/ folder")
    
    # Extract copy from all ad images
    print("\n" + "="*80)
    print("STEP 0: Extracting Ad Copy from Images")
    print("="*80)
    copy_map = await extract_copy_for_all_ads(ads_dir)
    
    # Create Ad objects from images with extracted copy
    sample_ads = []
    for i, ad_file in enumerate(ad_files, 1):
        ad_id = f"ad_{i}"
        extracted_copy = copy_map.get(str(ad_file), "")
        
        sample_ads.append(Ad(
            ad_id=ad_id,
            name=f"Creative {i}",
            copy=extracted_copy,  # Now has actual extracted copy
            image_path=str(ad_file),
            description=f"Ad creative {i} from {ad_file.name}"
        ))
        print(f"   • {ad_id}: {ad_file.name}")
        if extracted_copy:
            print(f"      Copy: {extracted_copy[:100]}...")
        else:
            print(f"      Copy: (No text extracted)")
    
    # Configuration
    NUM_PERSONAS = int(os.getenv("NUM_PERSONAS", "10"))
    
    # Run simulation
    output_path = DATA_DIR / "simulation_report.json"
    
    result = await orchestrator.run_full_simulation(
        ads=sample_ads,
        num_personas=NUM_PERSONAS,
        output_path=str(output_path),
        target_segment="exporters_freelancers_smes"
    )
    
    # Copy outputs to dashboard public data for UI
    dashboard_data = Path(__file__).parent / "dashboard" / "public" / "data"
    dashboard_data.mkdir(parents=True, exist_ok=True)
    for name in ("simulation_report.json", "raw_reactions.json", "enriched_personas.json"):
        src = DATA_DIR / name
        if src.exists():
            shutil.copy2(src, dashboard_data / name)
            print(f"   📋 Copied {name} → dashboard/public/data/")
    
    print(f"\n🎯 To view the dashboard: cd dashboard && npm run dev")
    print(f"📄 Raw report: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
