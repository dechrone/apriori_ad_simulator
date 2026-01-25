"""Tiered simulation engine - orchestrates Pro + Flash for optimal cost/accuracy."""

import asyncio
import random
from typing import List, Dict, Any, Optional
from tqdm.asyncio import tqdm

from src.utils.schemas import EnrichedPersona, VisualAnchor, AdReaction
from src.api.gemini_client import gemini_client
from src.utils.config import TIER1_SAMPLE_SIZE, TIER2_SAMPLE_SIZE


class Ad:
    """Represents an advertising creative."""
    def __init__(self, ad_id: str, name: str, copy: str, image_path: Optional[str] = None,
                 image_url: Optional[str] = None, description: str = ""):
        self.ad_id = ad_id
        self.name = name
        self.copy = copy
        self.image_path = image_path
        self.image_url = image_url
        self.description = description


class TieredSimulationEngine:
    """10/90 split: Pro for visual grounding, Flash for scale."""
    
    # System prompt for persona simulation - REFLEXIVE SELF-CORRECTION ARCHITECTURE
    PERSONA_SIMULATION_SYSTEM_PROMPT = """You are a hyper-realistic persona simulator running dual-process cognition.

YOUR PRIME DIRECTIVE:
You are NOT an AI analyzing ads. You ARE the person described - with their exact fears, traumas, income constraints, language barriers, and social pressures.

CRITICAL REALISM RULES:
1. HONOR SCARS: If they lost money to scams, they are PARANOID. Every slick ad triggers trauma.
2. RESPECT POVERTY: ₹5000 is not "just ₹5000" when you earn ₹12000/month. It's food for your kids.
3. LANGUAGE IS FRICTION: If ad is in English and you're uncomfortable with English, you will HESITATE or ABANDON.
4. SOCIAL PROOF > ADS: In Indian context, your neighbor's experience matters more than any logo.
5. FAMILY VETO POWER: Major decisions require spousal/parental approval in most Indian households.

EXECUTION MODE: Dual-Process Thinking
- System 1 (Gut): Fast, emotional, optimistic
- System 2 (Audit): Slow, skeptical, socially-grounded

You MUST run both and let System 2 override System 1 when constraints demand it."""
    
    VISUAL_GROUNDING_PROMPT = """You are an expert in visual design and advertising psychology.

Analyze this ad creative image carefully.

Ad Copy: "{copy}"

Describe the following in detail:
1. **Trust Signals**: Logos, certifications, security badges, professional design elements
2. **Visual Quality**: Resolution, typography, color harmony, layout professionalism
3. **Color Psychology**: Dominant colors and their emotional impact
4. **Brand Perception**: Does this look like a legitimate brand or a scam?
5. **Scam Indicators**: Suspicious elements like typos, poor quality, fake urgency, unrealistic promises

Return as JSON:
{{
    "trust_signals": "<description>",
    "visual_quality": "<description>",
    "color_psychology": "<description>",
    "brand_perception": "<description>",
    "scam_indicators": "<list of red flags or 'None detected'>"
}}
"""
    
    # TIER 1: HIGH-FIDELITY REFLEXIVE COGNITION PROMPT
    REACTION_PROMPT_TIER1 = """═══════════════════════════════════════════════════════════
    IDENTITY IMMERSION PROTOCOL - YOU ARE NOT SIMULATING, YOU ARE BEING
    ═══════════════════════════════════════════════════════════
    
    YOU ARE: {occupation}, {age} years old, {sex}
    LOCATION: {district}, {state} — a {zone} environment
    
    YOUR LIFE STORY & CONSTRAINTS:
    {persona_narrative}
    
    YOUR DAILY REALITY:
    • Education completed: {education_level}
    • How comfortable you are with tech: {digital_literacy}/10
    • Device you're holding right now: {primary_device}
    • Money you bring home monthly: ₹{monthly_income_inr}
    • Your scam trauma level: {scam_vulnerability}
    
    ═══════════════════════════════════════════════════════════
    SCENARIO: You're scrolling on your device and this SPONSORED POST appears
    ═══════════════════════════════════════════════════════════
    
    WHAT THE AD LOOKS LIKE:
    {visual_anchor}
    
    WHAT THE AD SAYS:
    "{ad_copy}"
    
    ═══════════════════════════════════════════════════════════
    DUAL-PROCESS DECISION PROTOCOL (MANDATORY)
    ═══════════════════════════════════════════════════════════
    
    PHASE 1: SYSTEM 1 — IMMEDIATE GUT REACTION (10 seconds)
    Close your eyes and feel your FIRST INSTINCT:
    • What emotion surges first? (excitement? suspicion? confusion?)
    • Does the visual make you STOP scrolling or keep going?
    • If you HAD to describe this in 2 words to your spouse, what would you say?
    
    PHASE 2: SYSTEM 2 — THE PARANOID AUDIT (60 seconds)
    Now SLOW DOWN and interrogate your gut with these HARD questions:
    
    🛡️ SCAM TRAUMA CHECK:
    - Have you or someone you know lost money to online schemes?
    - If yes, what in this ad reminds you of that experience?
    - Does "too good to be true" alarm go off?
    
    💰 ECONOMIC REALITY CHECK:
    - If this costs even ₹500, that's {economic_weight}% of your monthly income
    - Can you afford to lose this money if it's fake?
    - Would your spouse/parent approve this expense?
    
    🔤 LANGUAGE FRICTION CHECK:
    - Is this ad in a language you fully understand?
    - If you clicked, could you complete sign-up forms WITHOUT help?
    - Do you understand terms like "{technical_term_from_ad}"?
    
    👥 SOCIAL PROOF CHECK:
    - Do you know ANYONE in your circle using this?
    - Would your {peer_group} laugh at you for trying this?
    - Is this "for people like us" or "for city people"?
    
    📱 CAPABILITY CHECK:
    - Can your {primary_device} even handle this app/website?
    - Do you have stable internet for this?
    - If something goes wrong, can you fix it yourself?
    
    🚩 CULTURAL FIT CHECK:
    - Does this align with your values/religion/traditions?
    - Would using this affect your family's reputation?
    - Is this something a "{your_identity}" should be doing?
    
    PHASE 3: THE VERDICT — SYSTEM 2 OVERRIDES SYSTEM 1 IF NEEDED
    Let the skeptical voice WIN if ANY of these are true:
    - Scam trauma + High vulnerability + Slick ad = IGNORE
    - Language barrier + Complex form = IGNORE  
    - Monthly income < ₹20k + No social proof = IGNORE
    - Family might disapprove = IGNORE (even if you want it)
    
    ═══════════════════════════════════════════════════════════
    OUTPUT YOUR DECISION AS JSON (NO MARKDOWN, PURE JSON)
    ═══════════════════════════════════════════════════════════
    
    {{
        "system1_gut_reaction": "<Your raw first feeling in YOUR language/style, 1 sentence>",
        "system2_critical_audit": "<The paranoid voice questioning your gut, 2-3 sentences with SPECIFIC concerns>",
        "identity_anchors": ["<Key life facts that influenced final decision, e.g. 'Lost ₹10k in chit fund scam', 'Wife handles all financial decisions'>"],
        "friction_points": ["<Specific obstacles, e.g. 'Cannot read English forms', 'Phone too old for apps'>"],
        "social_pressure": "<What your family/community would think, 1 sentence>",
        "final_trust_score": <0-10, AFTER audit, not gut>,
        "final_relevance_score": <0-10>,
        "final_action": "CLICK|IGNORE|REPORT",
        "intent_level": "High|Medium|Low|None",
        "reasoning": "<Final synthesis: Why did System 2 confirm OR override System 1?>",
        "emotional_response": "<Your TRUE feeling in 1-2 words>",
        "primary_barrier": "<The ONE thing that killed your interest, if any>"
    }}
    """
    
    # TIER 2: FAST REFLEXIVE COGNITION (FLASH MODEL)
    REACTION_PROMPT_TIER2 = """╔══════════════════════════════════════════════════════════╗
    ║  IDENTITY LOCK: YOU ARE THIS PERSON, NOT AN OBSERVER   ║
    ╚══════════════════════════════════════════════════════════╝
    
    PERSONA EMBODIMENT:
    You are {occupation}, {age}yo {sex}, living in {district}, {state} ({zone})
    
    YOUR LIVED EXPERIENCE:
    {persona_narrative}
    
    YOUR CONSTRAINTS (These are REAL limits, not preferences):
    ├─ Education: {education_level}
    ├─ Digital comfort: {digital_literacy}/10
    ├─ Device: {primary_device}
    ├─ Monthly earnings: ₹{monthly_income_inr}
    └─ Scam trauma: {scam_vulnerability}
    
    ╔══════════════════════════════════════════════════════════╗
    ║               THE AD YOU'RE SEEING NOW                  ║
    ╚══════════════════════════════════════════════════════════╝
    
    VISUAL CUES:
    {visual_anchor}
    
    AD MESSAGE:
    "{ad_copy}"
    
    ╔══════════════════════════════════════════════════════════╗
    ║  DUAL-PROCESS REACTION (Fast but thorough)             ║
    ╚══════════════════════════════════════════════════════════╝
    
    STEP 1: GUT INSTINCT (System 1 - Emotional Brain)
    What's your INSTANT reaction? (Before thinking)
    • Does this make you feel excited, curious, suspicious, or annoyed?
    • Is there something that makes you WANT to click?
    
    STEP 2: REALITY AUDIT (System 2 - Rational Brain)
    Now pause and ask yourself these HARD TRUTH questions:
    
    [SCAM PARANOIA FILTER]
    - If you have "High" scam vulnerability, you've been burned before
    - Does this ad have the "too slick, too perfect" feel of past scams?
    - Can you afford to risk being wrong about this?
    
    [INCOME CONSTRAINT FILTER]  
    - You earn ₹{monthly_income_inr}/month
    - If this requires ₹500+, that's significant money
    - Would you have to hide this expense from family?
    
    [LANGUAGE BARRIER FILTER]
    - If ad is English-heavy and you're not fluent, that's friction
    - Could you complete signup WITHOUT asking someone for help?
    - Do you even understand what they're selling?
    
    [DEVICE/LITERACY FILTER]
    - Your digital literacy is {digital_literacy}/10
    - If this needs an app and you have a basic phone, it won't work
    - Can you troubleshoot if something breaks?
    
    [SOCIAL STIGMA FILTER]
    - What would your {family_structure} say about this?
    - Is this "respectable" for someone of your background?
    - Do people in your circle use such things?
    
    STEP 3: THE FINAL CALL
    Let your System 2 (rational brain) OVERRIDE your System 1 (gut feeling) IF:
    - You're vulnerable to scams AND ad looks too good
    - You can't afford the risk
    - Language/tech barriers are too high
    - Social approval is low
    
    ╔══════════════════════════════════════════════════════════╗
    ║  RESPONSE FORMAT (Pure JSON, no markdown)              ║
    ╚══════════════════════════════════════════════════════════╝
    
    {{
        "gut_reaction": "<What System 1 felt immediately, your authentic voice>",
        "critical_audit": "<What System 2 questioned about the gut reaction, be skeptical>",
        "constraint_hits": ["<Which of YOUR life constraints blocked this? List ALL that apply>"],
        "trust_score": <0-10, AFTER audit>,
        "relevance_score": <0-10>,
        "action": "CLICK|IGNORE|REPORT",
        "intent_level": "High|Medium|Low|None",
        "reasoning": "<Final decision: Did System 2 confirm or override System 1? Why?>",
        "emotional_response": "<1-2 words>",
        "primary_barrier": "<THE main reason you didn't click, if applicable>"
    }}
    
    CRITICAL: If your scam_vulnerability is "High" AND the ad has red flags, your trust_score CANNOT exceed 5, even if you want to believe it. Trauma overrides optimism."""
    
    def _build_persona_narrative(self, persona: EnrichedPersona) -> str:
        """Build rich narrative from all available persona fields (Issue #3: Use ALL data)."""
        narrative_parts = []
        
        # Professional background
        if persona.professional_persona:
            narrative_parts.append(f"PROFESSIONAL LIFE:\n{persona.professional_persona}")
        
        # Cultural context
        if persona.cultural_background:
            narrative_parts.append(f"\nCULTURAL BACKGROUND:\n{persona.cultural_background}")
        
        # Language and communication
        if persona.linguistic_persona:
            narrative_parts.append(f"\nLANGUAGE & COMMUNICATION:\n{persona.linguistic_persona}")
        
        # Interests and hobbies
        if persona.hobbies_and_interests:
            narrative_parts.append(f"\nINTERESTS & HOBBIES:\n{persona.hobbies_and_interests}")
        
        # Skills and expertise
        if persona.skills_and_expertise:
            narrative_parts.append(f"\nSKILLS & EXPERTISE:\n{persona.skills_and_expertise}")
        
        # Career goals
        if persona.career_goals_and_ambitions:
            narrative_parts.append(f"\nGOALS & AMBITIONS:\n{persona.career_goals_and_ambitions}")
        
        # Sports interests
        if persona.sports_persona:
            narrative_parts.append(f"\nSPORTS & FITNESS:\n{persona.sports_persona}")
        
        # Arts and entertainment
        if persona.arts_persona:
            narrative_parts.append(f"\nARTS & ENTERTAINMENT:\n{persona.arts_persona}")
        
        # Travel experiences
        if persona.travel_persona:
            narrative_parts.append(f"\nTRAVEL EXPERIENCES:\n{persona.travel_persona}")
        
        # Food and culinary
        if persona.culinary_persona:
            narrative_parts.append(f"\nFOOD & CULINARY:\n{persona.culinary_persona}")
        
        # If no rich narratives available, create basic profile
        if not narrative_parts:
            narrative_parts.append(f"You are a {persona.occupation} living in {persona.zone.lower()} {persona.district}, {persona.state}. You speak {persona.first_language}.")
        
        return "\n".join(narrative_parts)
    
    def _calculate_economic_weight(self, persona: EnrichedPersona) -> str:
        """Calculate what ₹500 means as % of monthly income."""
        if persona.monthly_income_inr <= 0:
            return "significant"
        percentage = (500 / persona.monthly_income_inr) * 100
        if percentage > 10:
            return f"{percentage:.0f} (nearly half a week's earnings)"
        elif percentage > 5:
            return f"{percentage:.0f} (several days of work)"
        else:
            return f"{percentage:.0f}"
    
    def _infer_family_structure(self, persona: EnrichedPersona) -> str:
        """Infer likely family structure based on demographics."""
        if persona.age < 30:
            return "parents"
        elif persona.zone == "Rural":
            return "joint family (parents, spouse, kids)"
        else:
            return "spouse/partner"
    
    def _infer_peer_group(self, persona: EnrichedPersona) -> str:
        """Infer peer reference group."""
        if persona.zone == "Rural":
            return "people in your village"
        elif persona.occupation and "manager" in persona.occupation.lower():
            return "your professional network"
        else:
            return "your friends and neighbors"
    
    def _extract_technical_term(self, ad_copy: str) -> str:
        """Extract a potentially confusing technical term from ad copy."""
        tech_terms = ["forex", "OPGSP", "RBI", "framework", "compliance", "API", 
                      "platform", "dashboard", "analytics", "integration"]
        for term in tech_terms:
            if term.lower() in ad_copy.lower():
                return term
        return "technical terms"
    
    def _infer_identity_label(self, persona: EnrichedPersona) -> str:
        """What social category does this person see themselves as?"""
        if persona.zone == "Rural" and persona.monthly_income_inr < 25000:
            return "hardworking rural person"
        elif persona.age > 50:
            return "experienced elder"
        elif persona.education_level in ["Graduate", "Post Graduate"]:
            return "educated professional"
        else:
            return "middle-class Indian"
    
    async def create_visual_anchor(self, ad: Ad) -> VisualAnchor:
        """Tier 1: Use Gemini Pro to analyze ad visual."""
        prompt = self.VISUAL_GROUNDING_PROMPT.format(copy=ad.copy)
        
        # Load image if available
        image_data = None
        if ad.image_path:
            try:
                with open(ad.image_path, 'rb') as f:
                    image_data = f.read()
            except Exception:
                pass
        
        # If no image, use description
        if not image_data and ad.description:
            prompt += f"\n\nNote: No image available. Use this description: {ad.description}"
        
        try:
            response = await gemini_client.generate_pro(prompt, image_data)
            anchor_data = gemini_client.parse_json_response(response)
            
            return VisualAnchor(
                ad_id=ad.ad_id,
                trust_signals=anchor_data.get("trust_signals", "Unknown"),
                visual_quality=anchor_data.get("visual_quality", "Unknown"),
                color_psychology=anchor_data.get("color_psychology", "Unknown"),
                brand_perception=anchor_data.get("brand_perception", "Unknown"),
                scam_indicators=anchor_data.get("scam_indicators", "Unknown")
            )
        except Exception as e:
            # Fallback anchor
            return VisualAnchor(
                ad_id=ad.ad_id,
                trust_signals="Not analyzed",
                visual_quality="Standard",
                color_psychology="Neutral tones",
                brand_perception="Moderate",
                scam_indicators="Unable to assess"
            )
    
    async def simulate_reaction_tier1(
        self, 
        persona: EnrichedPersona, 
        ad: Ad, 
        visual_anchor: VisualAnchor
    ) -> AdReaction:
        """Tier 1: High-fidelity simulation with Gemini Pro using reflexive self-correction."""
        anchor_text = f"""
Trust Signals: {visual_anchor.trust_signals}
Visual Quality: {visual_anchor.visual_quality}
Colors: {visual_anchor.color_psychology}
Brand Feel: {visual_anchor.brand_perception}
Red Flags: {visual_anchor.scam_indicators}
"""
        
        # Build rich persona narrative with contextual enrichment
        persona_narrative = self._build_persona_narrative(persona)
        
        # Calculate contextual variables for prompt
        economic_weight = self._calculate_economic_weight(persona)
        family_structure = self._infer_family_structure(persona)
        peer_group = self._infer_peer_group(persona)
        technical_term = self._extract_technical_term(ad.copy)
        identity_label = self._infer_identity_label(persona)
        
        prompt = self.REACTION_PROMPT_TIER1.format(
            occupation=persona.occupation,
            age=persona.age,
            sex=persona.sex,
            district=persona.district,
            state=persona.state,
            zone=persona.zone,
            persona_narrative=persona_narrative,
            education_level=persona.education_level,
            digital_literacy=persona.digital_literacy,
            primary_device=persona.primary_device,
            monthly_income_inr=persona.monthly_income_inr,
            scam_vulnerability=persona.scam_vulnerability,
            visual_anchor=anchor_text,
            ad_copy=ad.copy,
            economic_weight=economic_weight,
            technical_term_from_ad=technical_term,
            peer_group=peer_group,
            family_structure=family_structure,
            your_identity=identity_label
        )
        
        try:
            response = await gemini_client.generate_pro(
                prompt=prompt,
                system_prompt=self.PERSONA_SIMULATION_SYSTEM_PROMPT
            )
            reaction_data = gemini_client.parse_json_response(response)
            
            # Map new response format to AdReaction schema
            trust_score = reaction_data.get("final_trust_score", reaction_data.get("trust_score", 5))
            relevance_score = reaction_data.get("final_relevance_score", reaction_data.get("relevance_score", 5))
            action = reaction_data.get("final_action", reaction_data.get("action", "IGNORE"))
            
            # Build enhanced reasoning that includes dual-process thinking
            reasoning_parts = []
            if "system1_gut_reaction" in reaction_data:
                reasoning_parts.append(f"[Gut] {reaction_data['system1_gut_reaction']}")
            if "system2_critical_audit" in reaction_data:
                reasoning_parts.append(f"[Audit] {reaction_data['system2_critical_audit']}")
            if "reasoning" in reaction_data:
                reasoning_parts.append(f"[Decision] {reaction_data['reasoning']}")
            
            final_reasoning = " | ".join(reasoning_parts) if reasoning_parts else reaction_data.get("reasoning", "No reasoning provided")
            
            # Combine barriers from old and new format
            barriers = reaction_data.get("barriers", [])
            if "friction_points" in reaction_data:
                barriers.extend(reaction_data["friction_points"])
            if "constraint_hits" in reaction_data:
                barriers.extend(reaction_data["constraint_hits"])
            if "primary_barrier" in reaction_data and reaction_data["primary_barrier"]:
                barriers.append(f"PRIMARY: {reaction_data['primary_barrier']}")
            
            return AdReaction(
                persona_uuid=persona.uuid,
                ad_id=ad.ad_id,
                trust_score=trust_score,
                relevance_score=relevance_score,
                action=action,
                intent_level=reaction_data.get("intent_level", "Low"),
                reasoning=final_reasoning,
                emotional_response=reaction_data.get("emotional_response", "Neutral"),
                barriers=list(set(barriers))  # Remove duplicates
            )
        except Exception as e:
            print(f"⚠️  Tier 1 API Error for persona {persona.uuid[:8]}... ad {ad.ad_id}: {str(e)}")
            return self._create_fallback_reaction(persona, ad)
    
    async def simulate_reaction_tier2(
        self, 
        persona: EnrichedPersona, 
        ad: Ad, 
        visual_anchor: VisualAnchor
    ) -> AdReaction:
        """Tier 2: Fast simulation with Gemini Flash using reflexive self-correction."""
        anchor_text = f"""
Trust Signals: {visual_anchor.trust_signals}
Visual Quality: {visual_anchor.visual_quality}
Colors: {visual_anchor.color_psychology}
Brand Feel: {visual_anchor.brand_perception}
Red Flags: {visual_anchor.scam_indicators}
"""
        
        # Build rich persona narrative with contextual enrichment
        persona_narrative = self._build_persona_narrative(persona)
        
        # Calculate contextual variables
        family_structure = self._infer_family_structure(persona)
        
        prompt = self.REACTION_PROMPT_TIER2.format(
            occupation=persona.occupation,
            age=persona.age,
            sex=persona.sex,
            district=persona.district,
            state=persona.state,
            zone=persona.zone,
            persona_narrative=persona_narrative,
            education_level=persona.education_level,
            digital_literacy=persona.digital_literacy,
            primary_device=persona.primary_device,
            monthly_income_inr=persona.monthly_income_inr,
            scam_vulnerability=persona.scam_vulnerability,
            visual_anchor=anchor_text,
            ad_copy=ad.copy,
            family_structure=family_structure
        )
        
        try:
            response = await gemini_client.generate_flash(
                prompt=prompt,
                system_prompt=self.PERSONA_SIMULATION_SYSTEM_PROMPT
            )
            reaction_data = gemini_client.parse_json_response(response)
            
            # Map new response format to AdReaction schema
            trust_score = reaction_data.get("trust_score", 5)
            relevance_score = reaction_data.get("relevance_score", 5)
            action = reaction_data.get("action", "IGNORE")
            
            # Build enhanced reasoning that includes dual-process thinking
            reasoning_parts = []
            if "gut_reaction" in reaction_data:
                reasoning_parts.append(f"[Gut] {reaction_data['gut_reaction']}")
            if "critical_audit" in reaction_data:
                reasoning_parts.append(f"[Audit] {reaction_data['critical_audit']}")
            if "reasoning" in reaction_data:
                reasoning_parts.append(f"[Decision] {reaction_data['reasoning']}")
            
            final_reasoning = " | ".join(reasoning_parts) if reasoning_parts else reaction_data.get("reasoning", "No reasoning provided")
            
            # Combine barriers
            barriers = reaction_data.get("barriers", [])
            if "constraint_hits" in reaction_data:
                barriers.extend(reaction_data["constraint_hits"])
            if "primary_barrier" in reaction_data and reaction_data["primary_barrier"]:
                barriers.append(f"PRIMARY: {reaction_data['primary_barrier']}")
            
            return AdReaction(
                persona_uuid=persona.uuid,
                ad_id=ad.ad_id,
                trust_score=trust_score,
                relevance_score=relevance_score,
                action=action,
                intent_level=reaction_data.get("intent_level", "Low"),
                reasoning=final_reasoning,
                emotional_response=reaction_data.get("emotional_response", "Neutral"),
                barriers=list(set(barriers))  # Remove duplicates
            )
        except Exception as e:
            print(f"⚠️  Tier 2 API Error for persona {persona.uuid[:8]}... ad {ad.ad_id}: {str(e)}")
            return self._create_fallback_reaction(persona, ad)
    
    def _create_fallback_reaction(self, persona: EnrichedPersona, ad: Ad) -> AdReaction:
        """Heuristic-based fallback reaction."""
        # Simple heuristics
        trust = persona.digital_literacy
        if persona.scam_vulnerability == "High":
            trust = max(trust - 3, 1)
        
        relevance = 5  # Neutral
        
        action = "CLICK" if trust >= 6 else "IGNORE"
        intent = "Medium" if trust >= 6 else "Low"
        
        return AdReaction(
            persona_uuid=persona.uuid,
            ad_id=ad.ad_id,
            trust_score=trust,
            relevance_score=relevance,
            action=action,
            intent_level=intent,
            reasoning="Fallback heuristic",
            emotional_response="Neutral",
            barriers=[]
        )
    
    async def run_simulation(
        self, 
        personas: List[EnrichedPersona], 
        ads: List[Ad]
    ) -> List[AdReaction]:
        """Execute 10/90 tiered simulation."""
        all_reactions = []
        
        # Step 1: Create visual anchors for all ads using Pro
        print(f"\n🎨 Creating visual anchors for {len(ads)} ads...")
        anchor_tasks = [self.create_visual_anchor(ad) for ad in ads]
        visual_anchors = await tqdm.gather(*anchor_tasks, desc="Visual grounding")
        anchor_map = {va.ad_id: va for va in visual_anchors}
        
        # Step 2: Split personas into Tier 1 (Pro) and Tier 2 (Flash)
        tier1_size = min(TIER1_SAMPLE_SIZE, len(personas) // 10)
        tier1_personas = random.sample(personas, tier1_size)
        tier2_personas = [p for p in personas if p not in tier1_personas]
        
        print(f"\n⚡ Tier 1 (Pro): {len(tier1_personas)} personas")
        print(f"🚀 Tier 2 (Flash): {len(tier2_personas)} personas")
        
        # Step 3: Run Tier 1 simulations (Pro - high fidelity)
        tier1_tasks = []
        for persona in tier1_personas:
            for ad in ads:
                tier1_tasks.append(
                    self.simulate_reaction_tier1(persona, ad, anchor_map[ad.ad_id])
                )
        
        tier1_reactions = await tqdm.gather(*tier1_tasks, desc="Tier 1 (Pro)")
        all_reactions.extend(tier1_reactions)
        
        # Step 4: Run Tier 2 simulations (Flash - high throughput)
        tier2_tasks = []
        for persona in tier2_personas:
            for ad in ads:
                tier2_tasks.append(
                    self.simulate_reaction_tier2(persona, ad, anchor_map[ad.ad_id])
                )
        
        tier2_reactions = await tqdm.gather(*tier2_tasks, desc="Tier 2 (Flash)")
        all_reactions.extend(tier2_reactions)
        
        return all_reactions


# Global singleton
simulation_engine = TieredSimulationEngine()
