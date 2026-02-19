"""
Ad Simulator - simulates persona reactions to ad creatives.

Wraps the proven TieredSimulationEngine (Pro for visual grounding, Flash for scale).
Output: reactions per persona per ad, used for budget optimization.
"""

from typing import List, Any
from dataclasses import dataclass

# Re-export from existing simulation_engine for backward compatibility
from src.core.simulation_engine import (
    TieredSimulationEngine,
    Ad,
    simulation_engine,
)
from src.utils.schemas import EnrichedPersona, AdReaction


@dataclass
class AdSimulationResult:
    """Result of ad simulation - compatible with existing AdReaction."""
    reactions: List[AdReaction]
    persona_count: int
    ad_count: int


class AdSimulator:
    """
    Ad simulation orchestrator.
    
    Uses TieredSimulationEngine (10% Pro for visual grounding, 90% Flash for scale).
    Company plugins provide product_category for threshold tuning.
    """
    
    def __init__(self, product_category: str = "fintech"):
        self.engine = TieredSimulationEngine(product_category=product_category)
    
    async def run(
        self,
        personas: List[EnrichedPersona],
        ads: List[Ad]
    ) -> AdSimulationResult:
        """
        Run ad simulation: each persona sees each ad, we get their reaction.
        
        Returns AdSimulationResult with all reactions.
        """
        reactions = await self.engine.run_simulation(personas, ads)
        return AdSimulationResult(
            reactions=reactions,
            persona_count=len(personas),
            ad_count=len(ads)
        )
