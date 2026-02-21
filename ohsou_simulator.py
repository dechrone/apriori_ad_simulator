"""Ohsou Ad Simulator - Target: Girls aged 15-40 in Tier 1 cities."""

import asyncio
import shutil
import time
import json
import os
from pathlib import Path
from typing import List
import random
import uuid as uuid_lib

from src.data.loader import data_loader
from src.core.persona_hydrator import persona_hydrator
from src.core.simulation_engine import TieredSimulationEngine, Ad
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
from src.utils.schemas import RawPersona


def generate_tier1_young_women_personas(count: int = 10) -> List[RawPersona]:
    """Generate personas for girls aged 15-40 living in tier 1 cities."""
    
    # Tier 1 cities in India
    tier1_cities = {
        "Mumbai": {"state": "Maharashtra", "district": "Mumbai"},
        "Delhi": {"state": "Delhi", "district": "Central Delhi"},
        "Bangalore": {"state": "Karnataka", "district": "Bengaluru"},
        "Hyderabad": {"state": "Telangana", "district": "Hyderabad"},
        "Chennai": {"state": "Tamil Nadu", "district": "Chennai"},
        "Kolkata": {"state": "West Bengal", "district": "Kolkata"},
        "Pune": {"state": "Maharashtra", "district": "Pune"},
        "Ahmedabad": {"state": "Gujarat", "district": "Ahmedabad"},
    }
    
    # Age-appropriate occupations for 15-40 range
    occupations = [
        # Young students (15-22)
        "High School Student",
        "College Student (Arts)",
        "College Student (Science)",
        "College Student (Commerce)",
        "Medical Student",
        "Engineering Student",
        # Young professionals (22-30)
        "Marketing Executive",
        "Content Creator",
        "Graphic Designer",
        "Social Media Manager",
        "HR Executive",
        "Software Developer",
        "Fashion Designer",
        "Interior Designer",
        "Teacher",
        "Nurse",
        "Fitness Instructor",
        "Makeup Artist",
        "Fashion Stylist",
        # Established professionals (30-40)
        "Marketing Manager",
        "Product Manager",
        "Senior Designer",
        "Business Owner",
        "Entrepreneur",
        "Consultant",
        "Doctor",
        "Architect",
        "Lawyer",
        "CA (Chartered Accountant)",
    ]
    
    # Education levels appropriate for age ranges
    def get_education_for_age(age: int) -> str:
        if age < 18:
            return "Higher Secondary"
        elif age < 22:
            return random.choice(["Higher Secondary", "Graduate (pursuing)"])
        elif age < 25:
            return "Graduate"
        elif age < 35:
            return random.choice(["Graduate", "Post Graduate"])
        else:
            return random.choice(["Graduate", "Post Graduate", "Professional Degree"])
    
    # Languages common in tier 1 cities
    languages = ["English", "Hindi", "Kannada", "Tamil", "Telugu", "Marathi", "Gujarati", "Bengali"]
    
    # Interests relevant to young women
    interests_pool = [
        "Fashion, Beauty, Lifestyle",
        "Social Media, Content Creation, Photography",
        "Travel, Food, Lifestyle Blogging",
        "Fitness, Yoga, Wellness",
        "Reading, Writing, Art",
        "Music, Dance, Theater",
        "Shopping, Fashion Trends, Styling",
        "Skincare, Makeup, Beauty",
        "Sustainable Living, Organic Products",
        "Technology, Apps, Digital Trends"
    ]
    
    # Skills relevant to young urban women
    skills_pool = [
        "Digital Marketing, Social Media Management",
        "Creative Design, Content Creation",
        "Communication, Presentation Skills",
        "Fashion Styling, Trend Analysis",
        "Photography, Video Editing",
        "Project Management, Team Collaboration",
        "Beauty & Skincare Knowledge",
        "Fitness & Nutrition Planning",
        "Writing, Blogging, Storytelling",
        "Online Shopping, E-commerce Savvy"
    ]
    
    personas = []
    for i in range(count):
        age = random.randint(15, 40)
        
        # Select occupation appropriate for age
        if age < 22:
            occupation = random.choice([o for o in occupations if "Student" in o])
        elif age < 30:
            occupation = random.choice([o for o in occupations if "Student" not in o and "Manager" not in o and "Senior" not in o])
        else:
            occupation = random.choice([o for o in occupations if "Student" not in o])
        
        # Select city
        city_name = random.choice(list(tier1_cities.keys()))
        city_info = tier1_cities[city_name]
        
        # Get appropriate education
        education = get_education_for_age(age)
        
        # Select language based on city
        if city_name == "Bangalore":
            first_lang = random.choice(["English", "Kannada"])
        elif city_name == "Chennai":
            first_lang = random.choice(["English", "Tamil"])
        elif city_name == "Hyderabad":
            first_lang = random.choice(["English", "Telugu"])
        elif city_name == "Kolkata":
            first_lang = random.choice(["English", "Bengali"])
        elif city_name == "Ahmedabad":
            first_lang = random.choice(["English", "Gujarati", "Hindi"])
        elif city_name in ["Mumbai", "Pune"]:
            first_lang = random.choice(["English", "Hindi", "Marathi"])
        else:
            first_lang = random.choice(["English", "Hindi"])
        
        # Marital status appropriate for age
        if age < 22:
            marital = "Never Married"
        elif age < 28:
            marital = random.choice(["Never Married", "Never Married", "Never Married", "Currently Married"])
        else:
            marital = random.choice(["Never Married", "Currently Married", "Currently Married"])
        
        persona = RawPersona(
            uuid=str(uuid_lib.uuid4()).replace("-", ""),
            occupation=occupation,
            first_language=first_lang,
            second_language="English" if first_lang != "English" else "Hindi",
            third_language=None,
            sex="Female",
            age=age,
            marital_status=marital,
            education_level=education,
            education_degree=None,
            state=city_info["state"],
            district=city_info["district"],
            zone="Urban",
            country="India",
            hobbies_and_interests=random.choice(interests_pool),
            skills_and_expertise=random.choice(skills_pool),
            hobbies_and_interests_list=random.choice(interests_pool),
            skills_and_expertise_list=random.choice(skills_pool),
        )
        
        personas.append(persona)
    
    return personas


async def main():
    """Run Ohsou ad simulation."""
    
    print("\n" + "="*80)
    print("🌸 OHSOU AD-PORTFOLIO SIMULATOR")
    print("="*80)
    print("\n🎯 Target Segment: Girls aged 15-40 in Tier 1 cities")
    print("-"*80)
    
    start_time = time.time()
    
    # Load ad creatives from ads_ohsou folder
    ads_dir = Path(__file__).parent / "ads_ohsou"
    ad_files = sorted(ads_dir.glob("*.png")) + sorted(ads_dir.glob("*.jpg")) + sorted(ads_dir.glob("*.jpeg"))
    
    if not ad_files:
        print("❌ No ad images found in ads_ohsou/ folder!")
        return
    
    print(f"\n📸 Found {len(ad_files)} ad creatives in ads_ohsou/ folder")
    for ad_file in ad_files:
        print(f"   • {ad_file.name}")
    
    # Extract copy from all ad images
    print("\n" + "="*80)
    print("STEP 0: Extracting Ad Copy from Images")
    print("="*80)
    copy_map = await extract_copy_for_all_ads(ads_dir)
    
    # Create Ad objects from images with extracted copy
    sample_ads = []
    for i, ad_file in enumerate(ad_files, 1):
        ad_id = f"ohsou_ad_{i}"
        extracted_copy = copy_map.get(str(ad_file), "")
        
        sample_ads.append(Ad(
            ad_id=ad_id,
            name=f"Ohsou Creative {i}",
            copy=extracted_copy,
            image_path=str(ad_file),
            description=f"Ohsou ad creative {i} from {ad_file.name}"
        ))
        print(f"   • {ad_id}: {ad_file.name}")
        if extracted_copy:
            print(f"      Copy: {extracted_copy[:100]}...")
        else:
            print(f"      Copy: (No text extracted)")
    
    # STEP 1: Generate Target Personas
    print("\n" + "="*80)
    print("📚 STEP 1: Generating Target Personas")
    print("="*80)
    print("   Target: Girls aged 15-40 in Tier 1 cities")
    print("   Count: 10 personas")
    
    raw_personas = generate_tier1_young_women_personas(count=10)
    print(f"\n✅ Generated {len(raw_personas)} personas")
    
    selected_file = DATA_DIR / "selected_personas.json"
    with open(selected_file, 'w') as f:
        json.dump([p.model_dump() for p in raw_personas], f, indent=2)
    print(f"📄 Personas saved to: {selected_file}")
    
    print("\n📋 SELECTED PERSONAS:")
    print("-" * 80)
    for i, p in enumerate(raw_personas, 1):
        print(f"{i}. {p.occupation} | {p.age}yo {p.sex} | {p.district}, {p.state}")
        print(f"   Education: {p.education_level} | Language: {p.first_language}")
        print(f"   Interests: {p.hobbies_and_interests}")
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
        print(f"{i}. {ep.occupation} | {ep.age}yo")
        print(f"   💰 Purchasing Power: {ep.purchasing_power_tier} | Income: ₹{ep.monthly_income_inr:,}/month")
        print(f"   📱 Device: {ep.primary_device} | Digital Literacy: {ep.digital_literacy}/10")
        print(f"   ⚠️  Scam Vulnerability: {ep.scam_vulnerability} | Risk Tolerance: {ep.financial_risk_tolerance}")
        print()
    
    # STEP 3: Run Tiered Simulation
    print("\n🎬 STEP 3: Running Tiered Simulation (Pro + Flash)...")
    print(f"   - {len(sample_ads)} ad creatives")
    print(f"   - {len(enriched_personas)} personas")
    print(f"   - Total simulations: {len(sample_ads) * len(enriched_personas)}")
    print(f"   - Product Category: D2C Fashion (adjusted thresholds for consumer behavior)")
    
    # Create D2C-specific simulation engine
    d2c_simulation_engine = TieredSimulationEngine(product_category="d2c_fashion")
    
    reactions = await d2c_simulation_engine.run_simulation(enriched_personas, sample_ads)
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
    ad_map = {ad.ad_id: ad for ad in sample_ads}
    
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
        for ad in sample_ads
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
        max_ads=len(sample_ads)
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
    
    # STEP 6: Generate Heatmap
    print("\n🌡️ STEP 6: Generating Visual Heatmap...")
    ad_ids = [ad.ad_id for ad in sample_ads]
    heatmap = optimizer.generate_heatmap_matrix(
        valid_reactions,
        enriched_personas,
        ad_ids
    )
    
    print(f"\n🌡️ SEGMENT PERFORMANCE HEATMAP:")
    print(f"   Legend: 🟢 Strong (≥30%) | 🟡 Medium (≥15%) | 🟠 Weak (≥5%) | 🔴 Poor (<5%) | ⚪ No Data")
    print()
    for i, segment in enumerate(heatmap['rows']):
        print(f"   {segment:12} | {' '.join(heatmap['matrix'][i])}")
    
    # STEP 7: Generate Reports
    print("\n📊 STEP 7: Generating Detailed Reports...")
    
    generate_persona_comparison_report(enriched_personas, valid_reactions, sample_ads, DATA_DIR)
    generate_ad_comparison_report(enriched_personas, valid_reactions, sample_ads, DATA_DIR)
    generate_founder_ready_report(optimization_result, DATA_DIR)
    generate_summary_report(DATA_DIR)
    
    # STEP 8: Compile Final Report
    print("\n📊 STEP 8: Compiling Final Report...")
    
    # Serialize validation_summary
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
    
    # Serialize segment ownership
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
            "brand": "ohsou",
            "target_segment": "Girls aged 15-40 in Tier 1 cities",
            "num_personas": len(enriched_personas),
            "num_ads": len(sample_ads),
            "total_reactions": len(reactions),
            "valid_reactions": len(valid_reactions),
            "execution_time_seconds": round(time.time() - start_time, 2)
        }
    }
    
    # Save report
    output_file = DATA_DIR / "simulation_report.json"
    with open(output_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print(f"✅ Report saved to: {output_file}")
    
    # Copy outputs to dashboard public data
    print("\n📋 Copying data to dashboard...")
    dashboard_data = Path(__file__).parent / "dashboard" / "public" / "data"
    dashboard_data.mkdir(parents=True, exist_ok=True)
    for name in ("simulation_report.json", "raw_reactions.json", "enriched_personas.json"):
        src = DATA_DIR / name
        if src.exists():
            shutil.copy2(src, dashboard_data / name)
            print(f"   ✓ Copied {name} → dashboard/public/data/")
    
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
    print(f"   • Full Report (JSON): {output_file}")
    print(f"   • Founder-Ready Report: {DATA_DIR}/founder_report.txt")
    print(f"   • Persona Comparison: {DATA_DIR}/persona_comparison.txt")
    print(f"   • Ad Comparison: {DATA_DIR}/ad_comparison.txt")
    
    print("\n" + "="*80)
    print("🌐 NEXT STEP: View the Dashboard")
    print("="*80)
    print("\nRun: cd dashboard && npm run dev")
    print("Then open: http://localhost:3000")
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
