"""Persona hydration layer - enriches raw personas with psychographic data."""

import asyncio
import json
from typing import Dict, Any
from tqdm.asyncio import tqdm

from src.utils.schemas import RawPersona, EnrichedPersona
from src.api.gemini_client import gemini_client


class PersonaHydrator:
    """Enriches personas with purchasing power and psychographic data."""
    
    HYDRATION_PROMPT_TEMPLATE = """You are an expert demographer analyzing Indian consumer profiles.

Profile:
- Occupation: {occupation}
- Location: {district}, {state} ({zone})
- Age: {age}
- Sex: {sex}
- Education: {education_level}
- Language: {first_language}

Task: Estimate the following attributes based on Indian economic data, regional context, and occupation:

Return ONLY valid JSON (no markdown, no explanation):
{{
    "purchasing_power_tier": "High|Mid|Low",
    "digital_literacy": 0-10,
    "primary_device": "Android|iPhone|Desktop|Feature Phone",
    "scam_vulnerability": "High|Low",
    "monthly_income_inr": <realistic number>,
    "financial_risk_tolerance": "High|Low"
}}

Guidelines:
- A "Farmer" in Punjab (mechanized farming) = High tier
- A "Farmer" in Bihar (subsistence) = Low tier
- Urban tech workers = High digital literacy
- Rural manual labor = Low digital literacy
- Age 18-30 = Higher digital literacy
- Age 60+ = Lower digital literacy
- iPhone ownership is rare (<5% of population)
- Feature phones still common in rural areas
- Scam vulnerability HIGH if: Low education + Low literacy + Rural
- Risk tolerance HIGH if: Young + Mid-High income + Urban
"""
    
    async def hydrate_persona(self, persona: RawPersona) -> EnrichedPersona:
        """Enrich a single persona with psychographic data, preserving rich narratives."""
        prompt = self.HYDRATION_PROMPT_TEMPLATE.format(
            occupation=persona.occupation,
            district=persona.district,
            state=persona.state,
            zone=persona.zone,
            age=persona.age,
            sex=persona.sex,
            education_level=persona.education_level,
            first_language=persona.first_language
        )
        
        try:
            response = await gemini_client.generate_flash(prompt)
            enriched_data = gemini_client.parse_json_response(response)
            
            # Merge raw and enriched data - PRESERVE all rich narrative fields
            return EnrichedPersona(
                uuid=persona.uuid,
                occupation=persona.occupation,
                state=persona.state,
                district=persona.district,
                zone=persona.zone,
                age=persona.age,
                sex=persona.sex,
                education_level=persona.education_level,
                first_language=persona.first_language,
                # Preserve rich narrative fields from raw persona
                professional_persona=persona.professional_persona,
                cultural_background=persona.cultural_background,
                linguistic_persona=persona.linguistic_persona,
                hobbies_and_interests=persona.hobbies_and_interests,
                skills_and_expertise=persona.skills_and_expertise,
                career_goals_and_ambitions=persona.career_goals_and_ambitions,
                sports_persona=persona.sports_persona,
                arts_persona=persona.arts_persona,
                travel_persona=persona.travel_persona,
                culinary_persona=persona.culinary_persona,
                # Add LLM-generated enrichment
                **enriched_data
            )
        except Exception as e:
            # Fallback to heuristic enrichment
            return self._fallback_enrichment(persona)
    
    def _fallback_enrichment(self, persona: RawPersona) -> EnrichedPersona:
        """Rule-based fallback if LLM fails."""
        # Simple heuristics
        is_urban = persona.zone == "Urban"
        is_young = persona.age < 35
        has_education = persona.education_level not in ["Illiterate", "Primary"]
        
        digital_literacy = 7 if (is_urban and is_young and has_education) else 3
        
        return EnrichedPersona(
            uuid=persona.uuid,
            occupation=persona.occupation,
            state=persona.state,
            district=persona.district,
            zone=persona.zone,
            age=persona.age,
            sex=persona.sex,
            education_level=persona.education_level,
            first_language=persona.first_language,
            # Preserve rich narrative fields
            professional_persona=persona.professional_persona,
            cultural_background=persona.cultural_background,
            linguistic_persona=persona.linguistic_persona,
            hobbies_and_interests=persona.hobbies_and_interests,
            skills_and_expertise=persona.skills_and_expertise,
            career_goals_and_ambitions=persona.career_goals_and_ambitions,
            sports_persona=persona.sports_persona,
            arts_persona=persona.arts_persona,
            travel_persona=persona.travel_persona,
            culinary_persona=persona.culinary_persona,
            # Heuristic enrichment
            purchasing_power_tier="Mid" if is_urban else "Low",
            digital_literacy=digital_literacy,
            primary_device="Android" if is_young else "Feature Phone",
            scam_vulnerability="Low" if has_education else "High",
            monthly_income_inr=25000 if is_urban else 12000,
            financial_risk_tolerance="High" if is_young else "Low"
        )
    
    async def hydrate_batch(self, personas: list[RawPersona]) -> list[EnrichedPersona]:
        """Hydrate multiple personas concurrently."""
        tasks = [self.hydrate_persona(p) for p in personas]
        return await tqdm.gather(*tasks, desc="Hydrating personas")


# Global singleton
persona_hydrator = PersonaHydrator()
