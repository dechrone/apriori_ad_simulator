"""Enhanced report generation with detailed logging."""

from typing import List, Dict
from pathlib import Path
import json

from src.utils.schemas import EnrichedPersona, AdReaction
from src.core.simulation_engine import Ad


def generate_persona_comparison_report(
    personas: List[EnrichedPersona],
    reactions: List[AdReaction],
    ads: List[Ad],
    output_dir: Path
):
    """Generate a comparison report showing how different personas reacted to the same ads."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create persona comparison matrix
    persona_map = {p.uuid: p for p in personas}
    ad_map = {ad.ad_id: ad for ad in ads}
    
    # Group reactions by persona
    persona_reactions = {}
    for reaction in reactions:
        if reaction.persona_uuid not in persona_reactions:
            persona_reactions[reaction.persona_uuid] = []
        persona_reactions[reaction.persona_uuid].append(reaction)
    
    # Generate comparison file
    comparison_file = output_dir / "persona_comparison.txt"
    with open(comparison_file, 'w') as f:
        f.write("="*100 + "\n")
        f.write("PERSONA COMPARISON: How Different Personas React to the Same Ads\n")
        f.write("="*100 + "\n\n")
        
        for persona_uuid, persona_rxns in persona_reactions.items():
            persona = persona_map[persona_uuid]
            
            f.write(f"\n{'='*100}\n")
            f.write(f"PERSONA: {persona.occupation}\n")
            f.write(f"{'='*100}\n")
            f.write(f"Age: {persona.age} | Sex: {persona.sex} | Location: {persona.district}, {persona.state}\n")
            f.write(f"Income: ₹{persona.monthly_income_inr:,}/month ({persona.purchasing_power_tier})\n")
            f.write(f"Digital Literacy: {persona.digital_literacy}/10 | Device: {persona.primary_device}\n")
            f.write(f"Scam Vulnerability: {persona.scam_vulnerability}\n\n")
            
            # Show reactions to each ad
            for reaction in sorted(persona_rxns, key=lambda x: x.ad_id):
                ad = ad_map[reaction.ad_id]
                f.write(f"\n  → {ad.ad_id} ({ad.name}):\n")
                f.write(f"     Trust: {reaction.trust_score}/10 | Relevance: {reaction.relevance_score}/10\n")
                f.write(f"     Action: {reaction.action} | Intent: {reaction.intent_level}\n")
                f.write(f"     Emotional Response: {reaction.emotional_response}\n")
                f.write(f"     Reasoning: {reaction.reasoning}\n")
                if reaction.barriers:
                    f.write(f"     Barriers: {', '.join(reaction.barriers)}\n")
            
            f.write("\n")
    
    print(f"📊 Persona comparison report saved to: {comparison_file}")


def generate_ad_comparison_report(
    personas: List[EnrichedPersona],
    reactions: List[AdReaction],
    ads: List[Ad],
    output_dir: Path
):
    """Generate a comparison report showing how the same personas react to different ads."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    persona_map = {p.uuid: p for p in personas}
    
    # Group reactions by ad
    ad_reactions = {}
    for reaction in reactions:
        if reaction.ad_id not in ad_reactions:
            ad_reactions[reaction.ad_id] = []
        ad_reactions[reaction.ad_id].append(reaction)
    
    comparison_file = output_dir / "ad_comparison.txt"
    with open(comparison_file, 'w') as f:
        f.write("="*100 + "\n")
        f.write("AD COMPARISON: How the Same Personas React to Different Ads\n")
        f.write("="*100 + "\n\n")
        
        for ad in ads:
            f.write(f"\n{'='*100}\n")
            f.write(f"AD: {ad.ad_id} - {ad.name}\n")
            f.write(f"{'='*100}\n")
            f.write(f"Image: {ad.image_path}\n")
            f.write(f"Copy: {ad.copy if ad.copy else '(No copy provided - may cause similar reactions)'}\n\n")
            
            ad_rxns = ad_reactions.get(ad.ad_id, [])
            
            # Calculate statistics
            clicks = sum(1 for r in ad_rxns if r.action == "CLICK")
            high_intent = sum(1 for r in ad_rxns if r.intent_level == "High")
            avg_trust = sum(r.trust_score for r in ad_rxns) / len(ad_rxns) if ad_rxns else 0
            avg_relevance = sum(r.relevance_score for r in ad_rxns) / len(ad_rxns) if ad_rxns else 0
            
            f.write(f"Statistics:\n")
            f.write(f"  - Total Impressions: {len(ad_rxns)}\n")
            f.write(f"  - Clicks: {clicks} ({clicks/len(ad_rxns)*100:.1f}%)\n")
            f.write(f"  - High Intent: {high_intent} ({high_intent/len(ad_rxns)*100:.1f}%)\n")
            f.write(f"  - Avg Trust: {avg_trust:.1f}/10\n")
            f.write(f"  - Avg Relevance: {avg_relevance:.1f}/10\n\n")
            
            f.write(f"Individual Reactions:\n")
            f.write(f"{'-'*100}\n")
            
            for i, reaction in enumerate(ad_rxns, 1):
                persona = persona_map[reaction.persona_uuid]
                f.write(f"\n{i}. {persona.occupation} ({persona.age}yo {persona.sex}, {persona.zone})\n")
                f.write(f"   Trust: {reaction.trust_score}/10 | Relevance: {reaction.relevance_score}/10 | ")
                f.write(f"Action: {reaction.action} | Intent: {reaction.intent_level}\n")
                f.write(f"   Reasoning: {reaction.reasoning}\n")
            
            f.write("\n")
    
    print(f"📊 Ad comparison report saved to: {comparison_file}")


def generate_summary_report(output_dir: Path):
    """Generate a summary of all reports created."""
    
    summary_file = output_dir / "README.txt"
    with open(summary_file, 'w') as f:
        f.write("="*100 + "\n")
        f.write("APRIORI SIMULATION REPORTS - FILE GUIDE\n")
        f.write("="*100 + "\n\n")
        
        f.write("This directory contains detailed reports from the Apriori simulation.\n\n")
        
        f.write("FILES:\n")
        f.write("-" * 100 + "\n\n")
        
        f.write("1. selected_personas.json\n")
        f.write("   - Raw personas selected from the database\n")
        f.write("   - Before enrichment\n\n")
        
        f.write("2. enriched_personas.json\n")
        f.write("   - Personas after psychographic enrichment\n")
        f.write("   - Includes: purchasing power, digital literacy, device type, etc.\n\n")
        
        f.write("3. raw_reactions.json\n")
        f.write("   - All raw reactions from the simulation\n")
        f.write("   - Machine-readable format\n\n")
        
        f.write("4. detailed_reactions.json\n")
        f.write("   - Structured format with persona + ad + reaction details\n")
        f.write("   - Useful for analysis\n\n")
        
        f.write("5. readable_reactions.txt\n")
        f.write("   - Human-readable format\n")
        f.write("   - Organized by ad, showing each persona's reaction\n\n")
        
        f.write("6. persona_comparison.txt\n")
        f.write("   - Shows how EACH PERSONA reacted to ALL ADS\n")
        f.write("   - Useful for understanding persona behavior patterns\n\n")
        
        f.write("7. ad_comparison.txt\n")
        f.write("   - Shows how ALL PERSONAS reacted to EACH AD\n")
        f.write("   - Useful for understanding ad effectiveness\n\n")
        
        f.write("8. simulation_report.json\n")
        f.write("   - Final aggregated report with portfolio optimization\n")
        f.write("   - Upload this to the dashboard\n\n")
        
        f.write("="*100 + "\n")
        f.write("TIP: Start with 'persona_comparison.txt' and 'ad_comparison.txt'\n")
        f.write("     to understand why results might be similar across ads.\n")
        f.write("="*100 + "\n")
    
    print(f"📄 Report guide saved to: {summary_file}")
