"""
Batch Processing Script for Production Use

This script allows running multiple simulation campaigns in parallel
with different configurations.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List

from src.core.simulation_engine import Ad
from main import orchestrator


class CampaignConfig:
    """Configuration for a simulation campaign."""
    def __init__(self, name: str, ads: List[Ad], num_personas: int = 1000):
        self.name = name
        self.ads = ads
        self.num_personas = num_personas
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @property
    def output_path(self):
        return f"data/campaigns/{self.name}_{self.timestamp}.json"


# Define multiple campaigns
CAMPAIGNS = [
    
    # Campaign 1: Premium vs Budget Positioning
    CampaignConfig(
        name="premium_vs_budget",
        ads=[
            Ad(
                ad_id="premium_v1",
                name="Premium Exclusive",
                copy="Exclusive ₹1 Lakh credit line for premium customers. VIP support. Apply via our iOS app.",
                description="Luxury gold/black theme, minimalist design, VIP badge, Apple aesthetic"
            ),
            Ad(
                ad_id="budget_v1",
                name="Budget Friendly",
                copy="₹5,000 से शुरू करें अपना सपना। आसान EMI। कोई hidden charges नहीं।",
                description="Warm colors, Hindi text, family imagery, simple form, trust signals"
            ),
        ],
        num_personas=500
    ),
    
    # Campaign 2: Fear vs Aspiration
    CampaignConfig(
        name="fear_vs_aspiration",
        ads=[
            Ad(
                ad_id="fear_v1",
                name="Fear-Based",
                copy="Medical emergency? Don't let cash shortage stop you. Instant ₹25K approval in 10 minutes.",
                description="Urgent red tones, hospital imagery, fast approval badge, security symbols"
            ),
            Ad(
                ad_id="aspiration_v1",
                name="Aspiration-Based",
                copy="Start your dream business today. ₹50,000 entrepreneur loan. Join 10,000+ successful founders.",
                description="Inspiring imagery, success stories, modern design, entrepreneur photos, growth charts"
            ),
        ],
        num_personas=500
    ),
    
    # Campaign 3: Language Mix
    CampaignConfig(
        name="language_test",
        ads=[
            Ad(
                ad_id="english_formal",
                name="English Formal",
                copy="Personal loan up to ₹2 lakh. Competitive interest rates. RBI registered NBFC. Apply now.",
                description="Professional corporate design, English text, formal tone, certifications"
            ),
            Ad(
                ad_id="hindi_conversational",
                name="Hindi Conversational",
                copy="अपने सपनों को पूरा करें! ₹2 लाख तक का पर्सनल लोन। आसान प्रक्रिया। आज ही apply करें!",
                description="Friendly design, Hindi Devanagari script, warm colors, relatable imagery"
            ),
            Ad(
                ad_id="hinglish_youth",
                name="Hinglish Youth",
                copy="Apne dreams ke liye ready? ₹2 lakh instant loan! Simple process, fast approval. Let's go! 🚀",
                description="Modern trendy design, emoji use, Hinglish text, youth-oriented visuals"
            ),
        ],
        num_personas=750
    ),
    
    # Campaign 4: Urgency Levels
    CampaignConfig(
        name="urgency_test",
        ads=[
            Ad(
                ad_id="high_urgency",
                name="High Urgency",
                copy="⚠️ LAST 2 HOURS! ₹50K loan at 0% interest! Limited slots! APPLY NOW! ⏰",
                description="Red/yellow warning colors, countdown timer, multiple emojis, flashing elements"
            ),
            Ad(
                ad_id="medium_urgency",
                name="Medium Urgency",
                copy="Special offer: Get ₹50K loan at reduced interest. Offer valid this week. Apply today.",
                description="Orange accent colors, limited-time badge, clean design, subtle urgency"
            ),
            Ad(
                ad_id="no_urgency",
                name="No Urgency",
                copy="Personal loan up to ₹50K available. Apply anytime. Competitive rates. Reliable service.",
                description="Calm blue tones, professional layout, no time pressure, trustworthy design"
            ),
        ],
        num_personas=600
    ),
]


async def run_campaign(config: CampaignConfig):
    """Run a single campaign simulation."""
    print(f"\n{'='*80}")
    print(f"🎯 Starting Campaign: {config.name}")
    print(f"{'='*80}")
    
    try:
        result = await orchestrator.run_full_simulation(
            ads=config.ads,
            num_personas=config.num_personas,
            output_path=config.output_path
        )
        
        print(f"\n✅ Campaign '{config.name}' completed successfully!")
        print(f"📄 Report saved to: {config.output_path}")
        
        return {
            "campaign": config.name,
            "status": "success",
            "output_path": config.output_path,
            "result": result
        }
        
    except Exception as e:
        print(f"\n❌ Campaign '{config.name}' failed: {str(e)}")
        return {
            "campaign": config.name,
            "status": "failed",
            "error": str(e)
        }


async def run_all_campaigns_sequential():
    """Run all campaigns one by one (safe for rate limits)."""
    print("\n🚀 BATCH PROCESSING MODE: SEQUENTIAL")
    print("Running campaigns one at a time to respect API rate limits...\n")
    
    results = []
    for config in CAMPAIGNS:
        result = await run_campaign(config)
        results.append(result)
        
        # Cool down between campaigns
        print("\n⏸️  Cooling down for 30 seconds before next campaign...")
        await asyncio.sleep(30)
    
    return results


async def run_all_campaigns_parallel():
    """Run all campaigns in parallel (requires high rate limits)."""
    print("\n🚀 BATCH PROCESSING MODE: PARALLEL")
    print("⚠️  Warning: This will generate many concurrent API calls.")
    print("Only use if you have high Gemini API rate limits!\n")
    
    tasks = [run_campaign(config) for config in CAMPAIGNS]
    results = await asyncio.gather(*tasks)
    
    return results


def generate_comparison_report(results: list):
    """Generate cross-campaign comparison report."""
    comparison = {
        "batch_summary": {
            "total_campaigns": len(results),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "timestamp": datetime.now().isoformat()
        },
        "campaigns": []
    }
    
    for result in results:
        if result["status"] == "success":
            campaign_data = result["result"]
            
            # Extract key metrics
            best_ad = campaign_data["winning_portfolio"][0] if campaign_data["winning_portfolio"] else None
            
            comparison["campaigns"].append({
                "name": result["campaign"],
                "output_path": result["output_path"],
                "best_performer": {
                    "ad_id": best_ad["ad_id"] if best_ad else None,
                    "budget_split": best_ad["budget_split"] if best_ad else None,
                    "expected_conversions": best_ad["expected_conversions"] if best_ad else None
                },
                "execution_time": campaign_data["metadata"]["execution_time_seconds"],
                "personas_tested": campaign_data["metadata"]["num_personas"],
                "ads_tested": campaign_data["metadata"]["num_ads"]
            })
        else:
            comparison["campaigns"].append({
                "name": result["campaign"],
                "status": "failed",
                "error": result.get("error")
            })
    
    # Save comparison report
    output_path = f"data/campaigns/batch_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n📊 Batch comparison report saved to: {output_path}")
    
    return comparison


async def main():
    """Main entry point for batch processing."""
    
    # Choose mode
    print("\n" + "="*80)
    print("🎯 APRIORI BATCH PROCESSING")
    print("="*80)
    print(f"\nTotal campaigns queued: {len(CAMPAIGNS)}")
    print("\nSelect mode:")
    print("1. Sequential (Safe - respects rate limits)")
    print("2. Parallel (Fast - requires high rate limits)")
    
    # For demo, use sequential by default
    mode = "sequential"
    
    if mode == "sequential":
        results = await run_all_campaigns_sequential()
    else:
        results = await run_all_campaigns_parallel()
    
    # Generate comparison report
    comparison = generate_comparison_report(results)
    
    print("\n" + "="*80)
    print("🎉 BATCH PROCESSING COMPLETE!")
    print("="*80)
    print(f"\nSuccessful: {comparison['batch_summary']['successful']}/{comparison['batch_summary']['total_campaigns']}")
    print(f"Failed: {comparison['batch_summary']['failed']}/{comparison['batch_summary']['total_campaigns']}")
    
    print("\n📁 All reports saved to: data/campaigns/")
    print("\n🎯 Jai Mata Di! 🚀")


if __name__ == "__main__":
    asyncio.run(main())
