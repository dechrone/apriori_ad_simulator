"""Portfolio optimizer - Calculates optimal budget allocation across ad creatives."""

from typing import List, Dict, Set
from collections import defaultdict
import numpy as np

from src.utils.schemas import (
    EnrichedPersona, 
    AdReaction, 
    AdPerformance, 
    PortfolioRecommendation
)


class PortfolioOptimizer:
    """Inverse-overlap allocation for maximum reach efficiency."""
    
    def calculate_ad_performance(
        self,
        reactions: List[AdReaction],
        personas: List[EnrichedPersona]
    ) -> Dict[str, AdPerformance]:
        """Aggregate performance metrics per ad."""
        persona_map = {p.uuid: p for p in personas}
        ad_stats = defaultdict(lambda: {
            "impressions": 0,
            "clicks": 0,
            "high_intent_leads": 0,
            "reached_personas": set()
        })
        
        for reaction in reactions:
            ad_id = reaction.ad_id
            ad_stats[ad_id]["impressions"] += 1
            
            if reaction.action == "CLICK":
                ad_stats[ad_id]["clicks"] += 1
            
            if reaction.intent_level == "High":
                ad_stats[ad_id]["high_intent_leads"] += 1
            
            ad_stats[ad_id]["reached_personas"].add(reaction.persona_uuid)
        
        # Convert to AdPerformance objects
        performances = {}
        for ad_id, stats in ad_stats.items():
            click_rate = stats["clicks"] / stats["impressions"] if stats["impressions"] > 0 else 0
            conversion_rate = stats["high_intent_leads"] / stats["impressions"] if stats["impressions"] > 0 else 0
            
            performances[ad_id] = AdPerformance(
                ad_id=ad_id,
                total_impressions=stats["impressions"],
                clicks=stats["clicks"],
                high_intent_leads=stats["high_intent_leads"],
                click_rate=round(click_rate * 100, 2),
                conversion_rate=round(conversion_rate * 100, 2),
                unique_reach=len(stats["reached_personas"])
            )
        
        return performances
    
    def calculate_audience_overlap(
        self,
        reactions: List[AdReaction]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate overlap between ad audiences."""
        # Build persona sets for each ad
        ad_audiences = defaultdict(set)
        for reaction in reactions:
            if reaction.action == "CLICK" or reaction.intent_level in ["High", "Medium"]:
                ad_audiences[reaction.ad_id].add(reaction.persona_uuid)
        
        # Calculate pairwise overlaps
        ad_ids = list(ad_audiences.keys())
        overlap_matrix = {}
        
        for ad_a in ad_ids:
            overlap_matrix[ad_a] = {}
            audience_a = ad_audiences[ad_a]
            
            for ad_b in ad_ids:
                if ad_a == ad_b:
                    overlap_matrix[ad_a][ad_b] = 1.0
                    continue
                
                audience_b = ad_audiences[ad_b]
                if len(audience_a) == 0:
                    overlap_matrix[ad_a][ad_b] = 0.0
                else:
                    overlap = len(audience_a & audience_b)
                    overlap_pct = overlap / len(audience_a)
                    overlap_matrix[ad_a][ad_b] = round(overlap_pct, 3)
        
        return overlap_matrix
    
    def identify_audience_segments(
        self,
        reactions: List[AdReaction],
        personas: List[EnrichedPersona]
    ) -> Dict[str, Dict[str, int]]:
        """Identify dominant audience segments per ad dynamically from actual data."""
        persona_map = {p.uuid: p for p in personas}
        ad_segments = defaultdict(lambda: defaultdict(int))
        
        for reaction in reactions:
            if reaction.action == "CLICK" or reaction.intent_level in ["High", "Medium"]:
                persona = persona_map.get(reaction.persona_uuid)
                if not persona:
                    continue
                
                # Create dynamic segment keys based on persona characteristics
                # We'll create multiple segment dimensions
                
                # 1. Geographic + Income segment
                geo_income = f"{persona.zone}_{persona.purchasing_power_tier}"
                ad_segments[reaction.ad_id][geo_income] += 1
                
                # 2. Digital literacy segment
                literacy_segment = f"Digital_{self._categorize_literacy(persona.digital_literacy)}"
                ad_segments[reaction.ad_id][literacy_segment] += 1
                
                # 3. Age group segment
                age_segment = self._categorize_age(persona.age)
                ad_segments[reaction.ad_id][age_segment] += 1
                
                # 4. Device segment
                ad_segments[reaction.ad_id][f"Device_{persona.primary_device}"] += 1
        
        return dict(ad_segments)
    
    def _categorize_literacy(self, score: int) -> str:
        """Categorize digital literacy score into segment."""
        if score >= 8:
            return "High"
        elif score >= 5:
            return "Medium"
        else:
            return "Low"
    
    def _categorize_age(self, age: int) -> str:
        """Categorize age into segment."""
        if age < 25:
            return "Youth_18-24"
        elif age < 35:
            return "Young_Adults_25-34"
        elif age < 50:
            return "Middle_Age_35-49"
        else:
            return "Senior_50+"
    
    def detect_clickbait_traps(
        self,
        performances: Dict[str, AdPerformance]
    ) -> List[str]:
        """Identify ads with high clicks but low conversion (clickbait)."""
        traps = []
        
        for ad_id, perf in performances.items():
            # High click rate but very low high-intent leads
            if perf.click_rate > 15 and perf.conversion_rate < 5:
                trap_msg = (
                    f"Ad {ad_id} has {perf.click_rate}% click rate but only "
                    f"{perf.conversion_rate}% high-intent conversion. This is a 'Clickbait Trap' - "
                    f"generating curiosity clicks without real purchase intent."
                )
                traps.append(trap_msg)
        
        return traps
    
    def optimize_portfolio(
        self,
        reactions: List[AdReaction],
        personas: List[EnrichedPersona],
        max_ads: int = 3
    ) -> Dict:
        """Generate optimal ad portfolio with budget allocation based on high-intent leads."""
        
        # Calculate performance metrics
        performances = self.calculate_ad_performance(reactions, personas)
        overlaps = self.calculate_audience_overlap(reactions)
        segments = self.identify_audience_segments(reactions, personas)
        clickbait_alerts = self.detect_clickbait_traps(performances)
        
        # Rank ads by HIGH-INTENT LEADS (conversions), not just reach
        ad_scores = {}
        for ad_id, perf in performances.items():
            # Score = high_intent_leads * quality_weight * (1 - avg_overlap)
            # Prioritize actual conversions over vanity metrics
            
            avg_overlap = np.mean([
                overlaps[ad_id].get(other_ad, 0) 
                for other_ad in overlaps[ad_id] 
                if other_ad != ad_id
            ]) if len(overlaps[ad_id]) > 1 else 0
            
            # High-intent leads are the PRIMARY metric (weighted heavily)
            conversion_score = perf.high_intent_leads * 10  # Heavy weight on conversions
            
            # Quality multiplier: reward high conversion rates
            quality_multiplier = 1 + (perf.conversion_rate / 100)
            
            # Reach multiplier: secondary consideration (scaled down)
            reach_multiplier = 1 + (perf.unique_reach / 100)
            
            # Uniqueness multiplier: penalize overlap
            uniqueness_multiplier = 1 - (avg_overlap * 0.5)
            
            score = conversion_score * quality_multiplier * reach_multiplier * uniqueness_multiplier
            ad_scores[ad_id] = score
        
        # Select top N ads with minimal overlap
        selected_ads = []
        remaining_ads = sorted(ad_scores.keys(), key=lambda x: ad_scores[x], reverse=True)
        
        while remaining_ads and len(selected_ads) < max_ads:
            # Pick highest scoring ad
            candidate = remaining_ads.pop(0)
            
            # Check overlap with already selected ads
            if selected_ads:
                max_overlap = max([
                    overlaps[candidate].get(selected, 0)
                    for selected in selected_ads
                ])
                
                # Skip if more than 70% overlap
                if max_overlap > 0.7:
                    continue
            
            selected_ads.append(candidate)
        
        # Calculate budget allocation based on HIGH-INTENT LEADS + coverage
        total_conversion_value = sum([
            performances[ad].high_intent_leads * (1 + performances[ad].conversion_rate / 100)
            for ad in selected_ads
        ])
        
        recommendations = []
        for ad_id in selected_ads:
            perf = performances[ad_id]
            
            # Budget share based on conversion value (high-intent leads * quality)
            conversion_value = perf.high_intent_leads * (1 + perf.conversion_rate / 100)
            budget_share = (conversion_value / total_conversion_value) if total_conversion_value > 0 else 0
            
            # Get all segments for this ad and find the most dominant one
            all_segments = segments[ad_id] if ad_id in segments else {}
            
            if all_segments:
                # Find the most dominant segment across all dimensions
                dominant_segment = max(all_segments.items(), key=lambda x: x[1])[0]
            else:
                dominant_segment = "General"
            
            # Assign creative role based on performance and segment characteristics
            if perf.conversion_rate > 20:
                role = "The Converter"
            elif perf.click_rate > 20:
                role = "The Engager"
            elif "High" in dominant_segment or "Premium" in dominant_segment:
                role = "The Premium Play"
            elif "Rural" in dominant_segment:
                role = "The Trust Builder"
            elif "Youth" in dominant_segment or "Young" in dominant_segment:
                role = "The Youth Magnet"
            elif "Digital_High" in dominant_segment:
                role = "The Tech-Savvy Performer"
            else:
                role = "The Reach Extender"
            
            recommendations.append(
                PortfolioRecommendation(
                    ad_id=ad_id,
                    role=role,
                    budget_split=round(budget_share * 100, 1),
                    target_segment=dominant_segment,
                    unique_reach=perf.unique_reach,
                    expected_conversions=perf.high_intent_leads
                )
            )
        
        return {
            "winning_portfolio": recommendations,
            "all_performances": performances,
            "overlap_matrix": overlaps,
            "audience_segments": segments,
            "wasted_spend_alerts": clickbait_alerts
        }
    
    def generate_heatmap_matrix(
        self,
        reactions: List[AdReaction],
        personas: List[EnrichedPersona],
        ad_ids: List[str]
    ) -> Dict:
        """Generate visual heatmap data for UI with dynamically discovered segments."""
        persona_map = {p.uuid: p for p in personas}
        
        # Dynamically discover all unique segments from actual data
        discovered_segments = set()
        for reaction in reactions:
            if reaction.action == "CLICK" or reaction.intent_level in ["High", "Medium"]:
                persona = persona_map.get(reaction.persona_uuid)
                if persona:
                    segment = f"{persona.zone}_{persona.purchasing_power_tier}"
                    discovered_segments.add(segment)
        
        # Sort segments for consistent ordering
        segments = sorted(list(discovered_segments))
        
        if not segments:
            # If no segments discovered, return empty heatmap
            return {
                "rows": ["No_Data"],
                "cols": ad_ids,
                "matrix": [["⚪" for _ in ad_ids]]
            }
        
        # Build matrix
        matrix = []
        for segment in segments:
            row = []
            for ad_id in ad_ids:
                # Filter reactions for this segment + ad
                segment_parts = segment.split("_")
                if len(segment_parts) < 2:
                    row.append("⚪")
                    continue
                    
                zone, tier = segment_parts[0], segment_parts[1]
                
                matching_reactions = [
                    r for r in reactions
                    if r.ad_id == ad_id
                    and persona_map.get(r.persona_uuid)
                    and persona_map[r.persona_uuid].zone == zone
                    and persona_map[r.persona_uuid].purchasing_power_tier == tier
                ]
                
                if not matching_reactions:
                    row.append("⚪")  # No data
                    continue
                
                # Calculate conversion rate
                high_intent = sum(1 for r in matching_reactions if r.intent_level == "High")
                conv_rate = high_intent / len(matching_reactions)
                
                # Map to emoji
                if conv_rate >= 0.3:
                    row.append("🟢")  # Strong
                elif conv_rate >= 0.15:
                    row.append("🟡")  # Medium
                elif conv_rate >= 0.05:
                    row.append("🟠")  # Weak
                else:
                    row.append("🔴")  # Poor
            
            matrix.append(row)
        
        return {
            "rows": segments,
            "cols": ad_ids,
            "matrix": matrix
        }


# Global singleton
optimizer = PortfolioOptimizer()
