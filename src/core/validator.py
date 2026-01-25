"""Validator - Anti-hallucination layer to catch LLM inconsistencies."""

from typing import List
from src.utils.schemas import EnrichedPersona, AdReaction, ValidationResult
from src.utils.config import TRUST_SCORE_THRESHOLD, MIN_LITERACY_FOR_COMPLEX_FORM


class ReactionValidator:
    """Cross-checks LLM reactions for logical consistency."""
    
    def validate_reaction(self, persona: EnrichedPersona, reaction: AdReaction, ad_context: dict = None) -> ValidationResult:
        """Run multiple validation checks on a single reaction."""
        flags = []
        
        # CHECK 1: The "Scam Paradox"
        # User says "This looks sketchy" but still clicks
        if reaction.trust_score < TRUST_SCORE_THRESHOLD and reaction.action == "CLICK":
            flags.append(
                f"SUSPICIOUS_CLICK_DESPITE_LOW_TRUST: trust={reaction.trust_score}, action={reaction.action}"
            )
        
        # CHECK 2: The "Device Mismatch"
        # iOS app ad shown to Android/Feature Phone user
        if ad_context:
            ad_copy_lower = ad_context.get("copy", "").lower()
            
            if "ios" in ad_copy_lower or "app store" in ad_copy_lower or "iphone" in ad_copy_lower:
                if persona.primary_device in ["Android", "Feature Phone"]:
                    if reaction.action == "CLICK" and reaction.intent_level in ["High", "Medium"]:
                        flags.append(
                            f"IMPOSSIBLE_CONVERSION_DEVICE_MISMATCH: ad_requires=iOS, user_device={persona.primary_device}"
                        )
            
            # Android app to Feature Phone user
            if "download app" in ad_copy_lower or "install now" in ad_copy_lower:
                if persona.primary_device == "Feature Phone":
                    if reaction.action == "CLICK":
                        flags.append(
                            f"IMPOSSIBLE_ACTION_FEATURE_PHONE: ad_requires=smartphone, user_device=Feature Phone"
                        )
        
        # CHECK 3: The "Literacy Barrier"
        # Complex form/action for low-literacy user
        if ad_context:
            ad_copy_lower = ad_context.get("copy", "").lower()
            requires_form = any(word in ad_copy_lower for word in [
                "fill", "form", "register", "sign up", "apply now", "details"
            ])
            
            if requires_form and persona.digital_literacy < MIN_LITERACY_FOR_COMPLEX_FORM:
                if reaction.action == "CLICK" and reaction.intent_level == "High":
                    # Check if barriers were mentioned
                    if not any("literacy" in b.lower() or "form" in b.lower() for b in reaction.barriers):
                        flags.append(
                            f"UNREALISTIC_CONVERSION_LOW_LITERACY: literacy={persona.digital_literacy}, requires_form=True"
                        )
        
        # CHECK 4: The "Affordability Paradox"
        # High-intent for luxury product by low-income user
        if ad_context:
            ad_copy_lower = ad_context.get("copy", "").lower()
            
            # Detect luxury/high-price indicators
            is_luxury = any(word in ad_copy_lower for word in [
                "premium", "luxury", "exclusive", "₹50", "₹1 lakh", "₹2 lakh"
            ])
            
            if is_luxury and persona.purchasing_power_tier == "Low":
                if reaction.intent_level == "High":
                    if not any("afford" in b.lower() or "expensive" in b.lower() for b in reaction.barriers):
                        flags.append(
                            f"UNLIKELY_HIGH_INTENT_LOW_INCOME: income_tier=Low, product=luxury, intent=High"
                        )
        
        # CHECK 5: The "Scam Vulnerability Mismatch"
        # High scam vulnerability person shows no suspicion of suspicious ad
        if persona.scam_vulnerability == "High":
            if ad_context and "scam_indicators" in ad_context:
                has_red_flags = ad_context["scam_indicators"] != "None detected"
                
                if has_red_flags and reaction.trust_score >= 7:
                    flags.append(
                        f"UNREALISTIC_TRUST_HIGH_VULNERABILITY: vulnerability=High, scam_indicators=Yes, trust={reaction.trust_score}"
                    )
        
        # CHECK 6: The "Relevance-Action Mismatch"
        # Very low relevance but still high intent
        if reaction.relevance_score <= 2 and reaction.intent_level == "High":
            flags.append(
                f"INCONSISTENT_INTENT: relevance={reaction.relevance_score}, intent=High"
            )
        
        # CHECK 7: The "Report Action Validation"
        # User reports ad but has high trust/relevance
        if reaction.action == "REPORT":
            if reaction.trust_score >= 6 or reaction.relevance_score >= 7:
                flags.append(
                    f"CONTRADICTORY_REPORT: action=REPORT, trust={reaction.trust_score}, relevance={reaction.relevance_score}"
                )
        
        if flags:
            return ValidationResult(status="FLAGGED", reasons=flags)
        
        return ValidationResult(status="VALID", reasons=[])
    
    def validate_batch(
        self, 
        personas: List[EnrichedPersona], 
        reactions: List[AdReaction],
        ad_contexts: dict = None
    ) -> dict:
        """Validate all reactions and return summary."""
        persona_map = {p.uuid: p for p in personas}
        
        valid_count = 0
        flagged_count = 0
        flagged_reactions = []
        
        for reaction in reactions:
            persona = persona_map.get(reaction.persona_uuid)
            if not persona:
                continue
            
            ad_ctx = ad_contexts.get(reaction.ad_id) if ad_contexts else None
            
            validation = self.validate_reaction(persona, reaction, ad_ctx)
            
            if validation.status == "VALID":
                valid_count += 1
            else:
                flagged_count += 1
                flagged_reactions.append({
                    "persona_uuid": reaction.persona_uuid,
                    "ad_id": reaction.ad_id,
                    "flags": validation.reasons,
                    "reaction": reaction
                })
        
        flagged_percentage = (flagged_count / len(reactions) * 100) if reactions else 0
        
        return {
            "total": len(reactions),
            "valid": valid_count,
            "flagged": flagged_count,
            "flagged_percentage": flagged_percentage,
            "flagged_reactions": flagged_reactions
        }
    
    def filter_valid_reactions(
        self,
        personas: List[EnrichedPersona],
        reactions: List[AdReaction],
        ad_contexts: dict = None
    ) -> List[AdReaction]:
        """Return only valid reactions, discarding flagged ones."""
        persona_map = {p.uuid: p for p in personas}
        valid_reactions = []
        
        for reaction in reactions:
            persona = persona_map.get(reaction.persona_uuid)
            if not persona:
                continue
            
            ad_ctx = ad_contexts.get(reaction.ad_id) if ad_contexts else None
            validation = self.validate_reaction(persona, reaction, ad_ctx)
            
            if validation.status == "VALID":
                valid_reactions.append(reaction)
        
        return valid_reactions


# Global singleton
validator = ReactionValidator()
