"""Portfolio optimizer - Calculates optimal budget allocation across ad creatives."""

from typing import List, Dict, Set, Tuple
from collections import defaultdict, Counter
import numpy as np

from src.utils.schemas import (
    EnrichedPersona, 
    AdReaction, 
    AdPerformance, 
    PortfolioRecommendation
)


class PortfolioOptimizer:
    """Sub-segment dominance analyzer for precision media planning."""
    
    def identify_specific_segment(
        self,
        leads: List[EnrichedPersona],
        reactions: List[AdReaction]
    ) -> Dict[str, any]:
        """
        Analyzes a list of converted personas and finds the 'Oddly Specific' 
        common denominators using statistical mode analysis.
        
        Returns a dict with:
        - segment_name: Human-readable "oddly specific" target description
        - dominant_attributes: Key characteristics of this segment
        - confidence: How concentrated this segment is (0-1)
        """
        if not leads:
            return {
                "segment_name": "No Data",
                "dominant_attributes": {},
                "confidence": 0.0
            }
        
        # Create persona UUID to reaction map for trust scores
        reaction_map = {r.persona_uuid: r for r in reactions}
        
        # 1. Calculate frequency of every attribute
        states = [p.state for p in leads]
        occupations = [p.occupation for p in leads]
        zones = [p.zone for p in leads]
        age_groups = [self._categorize_age(p.age) for p in leads]
        literacy_levels = [p.digital_literacy for p in leads]
        income_tiers = [p.purchasing_power_tier for p in leads]
        
        # 2. Find the 'Dominant' markers using statistical mode
        state_counter = Counter(states)
        occ_counter = Counter(occupations)
        zone_counter = Counter(zones)
        age_counter = Counter(age_groups)
        tier_counter = Counter(income_tiers)
        
        # Get top attributes with their concentration percentages
        top_state, state_count = state_counter.most_common(1)[0] if state_counter else ("Unknown", 0)
        top_occ, occ_count = occ_counter.most_common(1)[0] if occ_counter else ("Unknown", 0)
        top_zone, zone_count = zone_counter.most_common(1)[0] if zone_counter else ("Unknown", 0)
        top_age, age_count = age_counter.most_common(1)[0] if age_counter else ("Unknown", 0)
        top_tier, tier_count = tier_counter.most_common(1)[0] if tier_counter else ("Unknown", 0)
        
        # Calculate concentration percentages
        total = len(leads)
        state_pct = (state_count / total) * 100 if total > 0 else 0
        occ_pct = (occ_count / total) * 100 if total > 0 else 0
        zone_pct = (zone_count / total) * 100 if total > 0 else 0
        age_pct = (age_count / total) * 100 if total > 0 else 0
        tier_pct = (tier_count / total) * 100 if total > 0 else 0
        
        # Average digital literacy and trust score
        avg_literacy = np.mean(literacy_levels) if literacy_levels else 0
        avg_trust = np.mean([
            reaction_map[p.uuid].trust_score 
            for p in leads 
            if p.uuid in reaction_map
        ]) if reaction_map else 0
        
        # 3. Construct the "Oddly Specific" segment string
        # Build it based on which attributes are most concentrated
        segment_parts = []
        
        # Add age group if concentrated (>40%)
        if age_pct > 40:
            segment_parts.append(top_age.replace("_", " "))
        
        # Add occupation if concentrated (>40%)
        if occ_pct > 40:
            # Simplify occupation names
            occ_simplified = top_occ.replace("Manager, ", "").replace(" and ", "/")
            segment_parts.append(occ_simplified)
        
        # Add geographic specificity
        if state_pct > 50:
            # Very concentrated in one state
            segment_parts.append(f"in {top_state}")
        elif zone_pct > 50:
            # Concentrated in urban/rural
            segment_parts.append(f"({top_zone})")
        
        # Add income tier if relevant
        if tier_pct > 50 and top_tier != "Mid":
            segment_parts.append(f"{top_tier}-Income")
        
        # Add tech-savviness qualifier
        if avg_literacy >= 8:
            tech_level = "High Tech-Savvy"
        elif avg_literacy >= 6:
            tech_level = "Tech-Comfortable"
        elif avg_literacy <= 4:
            tech_level = "Low Digital Literacy"
        else:
            tech_level = None
        
        if tech_level:
            segment_parts.append(tech_level)
        
        # Construct final segment name
        if segment_parts:
            segment_name = " ".join(segment_parts)
        else:
            segment_name = f"{top_occ}s in {top_zone} Areas"
        
        # Calculate overall confidence (how concentrated is this segment?)
        confidence = np.mean([state_pct, occ_pct, zone_pct, age_pct, tier_pct]) / 100
        
        return {
            "segment_name": segment_name,
            "dominant_attributes": {
                "occupation": top_occ,
                "state": top_state,
                "zone": top_zone,
                "age_group": top_age,
                "income_tier": top_tier,
                "avg_digital_literacy": round(avg_literacy, 1),
                "avg_trust_score": round(avg_trust, 1),
                "concentration": {
                    "occupation": round(occ_pct, 1),
                    "state": round(state_pct, 1),
                    "zone": round(zone_pct, 1),
                    "age": round(age_pct, 1),
                    "income": round(tier_pct, 1)
                }
            },
            "confidence": round(confidence, 2),
            "sample_size": total
        }
    
    def fragment_audience_into_clusters(
        self,
        personas: List[EnrichedPersona]
    ) -> Dict[str, List[EnrichedPersona]]:
        """
        Stage 1: Fragment the audience into logical clusters.
        
        Creates clusters like:
        - "The Tier-1 Corporate" (Urban, High-income, Manager roles)
        - "The Tier-2 Hustler" (Urban Tier-2, Mid-income, Freelancers)
        - "The Young IT Freelancer" (Young, IT/Tech, Urban)
        - "The Senior Exporter" (Age 45+, Export Manager, High-income)
        """
        clusters = defaultdict(list)
        
        for persona in personas:
            # Build cluster key based on multiple dimensions
            cluster_keys = []
            
            # Cluster Type 1: Geographic + Income
            geo_income_key = f"{persona.zone}_{persona.purchasing_power_tier}"
            
            # Cluster Type 2: Age + Occupation category
            age_group = self._categorize_age(persona.age)
            occ_category = self._categorize_occupation(persona.occupation)
            age_occ_key = f"{age_group}_{occ_category}"
            
            # Cluster Type 3: Psychographic (Digital Literacy + Risk)
            psycho_key = f"Digital_{self._categorize_literacy(persona.digital_literacy)}_Risk_{persona.financial_risk_tolerance}"
            
            # Assign persona to the most relevant cluster
            # Priority: Age+Occupation (most specific) > Geo+Income > Psychographic
            
            # Use Age+Occupation as primary cluster if occupation is distinctive
            if occ_category in ["Export_Manager", "Import_Manager", "Freelancer", "Consultant"]:
                primary_cluster = age_occ_key
            else:
                primary_cluster = geo_income_key
            
            clusters[primary_cluster].append(persona)
        
        return dict(clusters)
    
    def _categorize_occupation(self, occupation: str) -> str:
        """Categorize occupation into broad groups."""
        occ_lower = occupation.lower()
        
        if "export" in occ_lower:
            return "Export_Manager"
        elif "import" in occ_lower:
            return "Import_Manager"
        elif "freelancer" in occ_lower or "freelance" in occ_lower:
            return "Freelancer"
        elif "consultant" in occ_lower:
            return "Consultant"
        elif "it" in occ_lower or "software" in occ_lower or "developer" in occ_lower:
            return "IT_Professional"
        elif "manager" in occ_lower:
            return "Manager"
        elif "business" in occ_lower or "entrepreneur" in occ_lower:
            return "Business_Owner"
        else:
            return "Professional"
    
    def assign_segment_owners(
        self,
        clusters: Dict[str, List[EnrichedPersona]],
        reactions: List[AdReaction],
        ad_ids: List[str]
    ) -> Dict[str, Dict]:
        """
        Stage 2: For each cluster, find the ad with the highest Trust Score + Intent.
        
        Returns: Dict mapping cluster_id -> {
            "winning_ad": ad_id,
            "trust_score": avg_trust,
            "conversion_rate": pct_high_intent,
            "personas": list of personas in cluster,
            "reasoning": why this ad owns this segment
        }
        """
        persona_uuid_to_cluster = {}
        for cluster_id, personas in clusters.items():
            for persona in personas:
                persona_uuid_to_cluster[persona.uuid] = cluster_id
        
        # Build reaction lookup
        reaction_lookup = defaultdict(list)
        for reaction in reactions:
            reaction_lookup[reaction.persona_uuid].append(reaction)
        
        segment_ownership = {}
        
        for cluster_id, personas in clusters.items():
            if not personas:
                continue
            
            # Calculate performance of each ad for this specific cluster
            ad_scores = {}
            
            for ad_id in ad_ids:
                # Get all reactions for this cluster + ad combo
                cluster_reactions = []
                for persona in personas:
                    persona_reactions = reaction_lookup.get(persona.uuid, [])
                    cluster_reactions.extend([
                        r for r in persona_reactions if r.ad_id == ad_id
                    ])
                
                if not cluster_reactions:
                    ad_scores[ad_id] = {
                        "score": 0,
                        "trust": 0,
                        "relevance": 0,
                        "conversion_rate": 0,
                        "high_intent_count": 0,
                        "total_impressions": 0
                    }
                    continue
                
                # Calculate metrics for this ad within this cluster
                high_intent_count = sum(1 for r in cluster_reactions if r.intent_level == "High")
                clicks = sum(1 for r in cluster_reactions if r.action == "CLICK")
                avg_trust = np.mean([r.trust_score for r in cluster_reactions])
                avg_relevance = np.mean([r.relevance_score for r in cluster_reactions])
                
                conversion_rate = (high_intent_count / len(cluster_reactions)) if cluster_reactions else 0
                
                # Score = Trust * Relevance * Conversion Rate * Volume
                # Prioritize INTENSITY over VOLUME
                intensity_score = avg_trust * avg_relevance * (conversion_rate * 100)
                volume_bonus = min(high_intent_count, 10)  # Cap volume bonus at 10
                
                final_score = intensity_score * (1 + volume_bonus / 20)
                
                ad_scores[ad_id] = {
                    "score": final_score,
                    "trust": avg_trust,
                    "relevance": avg_relevance,
                    "conversion_rate": conversion_rate * 100,
                    "high_intent_count": high_intent_count,
                    "total_impressions": len(cluster_reactions)
                }
            
            # Find winning ad for this cluster
            if not ad_scores:
                continue
            
            winning_ad = max(ad_scores.keys(), key=lambda x: ad_scores[x]["score"])
            winning_metrics = ad_scores[winning_ad]
            
            # Skip if no ad has any performance in this cluster
            if winning_metrics["score"] == 0:
                continue
            
            # Generate reasoning for why this ad owns this segment
            reasoning = self._generate_segment_reasoning(
                cluster_id, 
                personas, 
                winning_ad, 
                winning_metrics,
                reactions
            )
            
            segment_ownership[cluster_id] = {
                "winning_ad": winning_ad,
                "trust_score": round(winning_metrics["trust"], 1),
                "relevance_score": round(winning_metrics["relevance"], 1),
                "conversion_rate": round(winning_metrics["conversion_rate"], 1),
                "high_intent_count": winning_metrics["high_intent_count"],
                "personas": personas,
                "reasoning": reasoning,
                "all_ad_scores": {
                    ad_id: {
                        "score": round(metrics["score"], 1) if isinstance(metrics, dict) else 0,
                        "trust": round(metrics["trust"], 1) if isinstance(metrics, dict) else 0,
                        "conversion": round(metrics["conversion_rate"], 1) if isinstance(metrics, dict) else 0
                    }
                    for ad_id, metrics in ad_scores.items()
                }
            }
        
        return segment_ownership
    
    def _generate_segment_reasoning(
        self,
        cluster_id: str,
        personas: List[EnrichedPersona],
        winning_ad: str,
        metrics: Dict,
        reactions: List[AdReaction]
    ) -> str:
        """Generate human-readable reasoning for why this ad owns this segment."""
        
        # Get specific segment description
        ad_reactions = [r for r in reactions if r.ad_id == winning_ad]
        segment_info = self.identify_specific_segment(personas, ad_reactions)
        
        trust = metrics["trust"]
        conversion = metrics["conversion_rate"]
        
        # Build reasoning based on metrics
        reasoning_parts = []
        
        if trust >= 8:
            reasoning_parts.append("High trust signals")
        
        if conversion >= 70:
            reasoning_parts.append(f"{int(conversion)}% conversion rate")
        elif conversion >= 50:
            reasoning_parts.append(f"Strong {int(conversion)}% conversion")
        
        # Add dominant attribute insights
        if segment_info and "dominant_attributes" in segment_info:
            attrs = segment_info["dominant_attributes"]
            if attrs.get("avg_trust_score", 0) >= 8:
                reasoning_parts.append("resonates with this segment's values")
        
        if reasoning_parts:
            return " • ".join(reasoning_parts)
        else:
            return f"Best performing ad for this segment"
    
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
        """
        Generate optimal ad portfolio using Sub-Segment Dominance Analysis.
        
        Instead of "Winner-Take-All", this finds which ad owns which niche,
        allocating budget based on segment value and intensity of intent.
        """
        
        # Calculate basic performance metrics (for reference)
        performances = self.calculate_ad_performance(reactions, personas)
        overlaps = self.calculate_audience_overlap(reactions)
        old_segments = self.identify_audience_segments(reactions, personas)
        clickbait_alerts = self.detect_clickbait_traps(performances)
        
        # NEW LOGIC: Sub-Segment Dominance Analysis
        
        # Stage 1: Fragment the audience into logical clusters
        clusters = self.fragment_audience_into_clusters(personas)
        
        # Stage 2: Assign Segment Owners (which ad owns which cluster?)
        ad_ids = list(performances.keys())
        segment_ownership = self.assign_segment_owners(clusters, reactions, ad_ids)
        
        # Stage 3: Allocate Budget Proportionally to Segment Value
        
        # Calculate the "value" of each segment (high-intent count * avg trust * avg relevance)
        segment_values = {}
        for cluster_id, ownership in segment_ownership.items():
            value = (
                ownership["high_intent_count"] * 
                ownership["trust_score"] * 
                ownership["relevance_score"] / 10  # Normalize
            )
            segment_values[cluster_id] = value
        
        total_value = sum(segment_values.values()) if segment_values else 1
        
        # Group segments by winning ad
        ad_to_segments = defaultdict(list)
        for cluster_id, ownership in segment_ownership.items():
            ad_to_segments[ownership["winning_ad"]].append({
                "cluster_id": cluster_id,
                "ownership": ownership,
                "value": segment_values.get(cluster_id, 0)
            })
        
        # Calculate budget allocation for each ad based on total value of segments it owns
        ad_budget_allocation = {}
        for ad_id in ad_ids:
            owned_segments = ad_to_segments.get(ad_id, [])
            ad_total_value = sum(seg["value"] for seg in owned_segments)
            budget_pct = (ad_total_value / total_value) * 100 if total_value > 0 else 0
            
            ad_budget_allocation[ad_id] = {
                "budget_pct": budget_pct,
                "owned_segments": owned_segments,
                "total_value": ad_total_value
            }
        
        # Select top ads that actually own meaningful segments (budget > 5%)
        selected_ads = [
            ad_id for ad_id, alloc in ad_budget_allocation.items()
            if alloc["budget_pct"] >= 5.0  # Only include ads with meaningful allocation
        ]
        
        # Sort by budget allocation
        selected_ads.sort(key=lambda x: ad_budget_allocation[x]["budget_pct"], reverse=True)
        
        # Limit to max_ads
        selected_ads = selected_ads[:max_ads]
        
        # If no ads meet threshold, fall back to top performer
        if not selected_ads:
            selected_ads = [max(performances.keys(), key=lambda x: performances[x].high_intent_leads)]
            # Give it 100% budget
            ad_budget_allocation[selected_ads[0]]["budget_pct"] = 100.0
        
        # Normalize budget to 100%
        total_allocated = sum(ad_budget_allocation[ad]["budget_pct"] for ad in selected_ads)
        if total_allocated > 0:
            for ad in selected_ads:
                ad_budget_allocation[ad]["budget_pct"] = (
                    ad_budget_allocation[ad]["budget_pct"] / total_allocated * 100
                )
        
        # Build recommendations with "oddly specific" target segments
        recommendations = []
        
        for ad_id in selected_ads:
            allocation = ad_budget_allocation[ad_id]
            owned_segments = allocation["owned_segments"]
            
            if not owned_segments:
                continue
            
            # Find the most valuable segment this ad owns
            primary_segment = max(owned_segments, key=lambda x: x["value"])
            cluster_id = primary_segment["cluster_id"]
            ownership = primary_segment["ownership"]
            personas_in_segment = ownership["personas"]
            
            # Get reactions for this ad
            ad_reactions = [r for r in reactions if r.ad_id == ad_id]
            
            # Generate "oddly specific" segment description
            segment_info = self.identify_specific_segment(personas_in_segment, ad_reactions)
            target_segment = segment_info["segment_name"]
            
            # Determine role based on segment characteristics and performance
            role = self._determine_ad_role(
                ad_id, 
                ownership, 
                segment_info, 
                performances[ad_id],
                ad_reactions,
                personas_in_segment
            )
            
            # Get reasoning
            reasoning = ownership["reasoning"]
            
            perf = performances[ad_id]
            
            recommendations.append(
                PortfolioRecommendation(
                    ad_id=ad_id,
                    role=role,
                    budget_split=round(allocation["budget_pct"], 1),
                    target_segment=target_segment,
                    unique_reach=perf.unique_reach,
                    expected_conversions=perf.high_intent_leads,
                    reasoning=reasoning  # This will need schema update
                )
            )
        
        # Sort by budget allocation (descending)
        recommendations.sort(key=lambda x: x.budget_split, reverse=True)
        
        return {
            "winning_portfolio": recommendations,
            "all_performances": performances,
            "overlap_matrix": overlaps,
            "audience_segments": old_segments,  # Keep old format for compatibility
            "segment_ownership": segment_ownership,  # NEW: Detailed segment ownership
            "wasted_spend_alerts": clickbait_alerts,
            "clusters": {
                cluster_id: {
                    "size": len(ownership["personas"]),
                    "owner": ownership["winning_ad"],
                    "value": segment_values.get(cluster_id, 0)
                }
                for cluster_id, ownership in segment_ownership.items()
            }
        }
    
    def _determine_ad_role(
        self,
        ad_id: str,
        ownership: Dict,
        segment_info: Dict,
        performance: AdPerformance,
        reactions: List[AdReaction],
        personas: List[EnrichedPersona]
    ) -> str:
        """Determine the strategic role of this ad based on its segment ownership."""
        
        trust_score = ownership["trust_score"]
        conversion_rate = ownership["conversion_rate"]
        segment_name = segment_info["segment_name"]
        
        # Analyze reactions to understand what drives this ad's success
        high_trust_reactions = [r for r in reactions if r.trust_score >= 8]
        low_trust_reactions = [r for r in reactions if r.trust_score <= 5]
        
        # Role assignment based on characteristics
        if trust_score >= 8 and conversion_rate >= 70:
            if "Senior" in segment_name or "Age 45+" in segment_name or "50+" in segment_name:
                return "The Trust Magnet"
            else:
                return "The Converter"
        
        elif "Young" in segment_name or "25-34" in segment_name or "Youth" in segment_name:
            if conversion_rate >= 60:
                return "The Growth Hook"
            else:
                return "The Youth Engager"
        
        elif "Export" in segment_name or "Import" in segment_name or "Manager" in segment_name:
            if trust_score >= 7:
                return "The Professional's Choice"
            else:
                return "The B2B Play"
        
        elif "Freelancer" in segment_name or "Consultant" in segment_name:
            return "The Hustle Enabler"
        
        elif conversion_rate >= 70:
            return "The Converter"
        
        elif trust_score >= 8:
            return "The Trust Builder"
        
        elif performance.click_rate >= 80 and conversion_rate < 50:
            return "The Curiosity Driver"
        
        else:
            return "The Catch-All"
    
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
