"""
Ohsou Company Plugin - D2C lingerie/fashion brand.

Target: Girls aged 15-40 in Tier 1 cities.
Modes: Ad (creative comparison, budget allocation)
Personas: EnrichedPersona (Raw + hydration)
"""

from pathlib import Path
from typing import List, Any

from src.companies.base import CompanyPlugin, CompanyConfig, SimulationMode
from src.core.simulation_engine import Ad
from src.core.persona_hydrator import persona_hydrator
from src.utils.config import DATA_DIR
from src.utils.ad_copy_extractor import extract_copy_for_all_ads
from src.utils.schemas import RawPersona, EnrichedPersona


# Lazy import to avoid circular deps - ohsou_simulator has generate_tier1_young_women_personas
def _get_ohsou_persona_generator():
    from ohsou_simulator import generate_tier1_young_women_personas
    return generate_tier1_young_women_personas


class OhsouPlugin(CompanyPlugin):
    """Ohsou - D2C fashion/lingerie ad creative testing."""
    
    def __init__(self):
        self._config = CompanyConfig(
            company_id="ohsou",
            company_name="Ohsou",
            modes=[SimulationMode.AD],
            product_category="d2c_fashion",
            data_dir=DATA_DIR
        )
    
    @property
    def config(self) -> CompanyConfig:
        return self._config
    
    async def load_personas(self, count: int | None = 10, **kwargs) -> List[EnrichedPersona]:
        """Generate Ohsou target personas (Tier 1 young women) and hydrate."""
        generator = _get_ohsou_persona_generator()
        raw_personas: List[RawPersona] = generator(count=count or 10)
        enriched = await persona_hydrator.hydrate_batch(raw_personas)
        return enriched
    
    async def load_ads(self, ads_dir: Path | None = None) -> List[Ad]:
        """Load ad creatives from ads directory. Default: ads_ohsou/."""
        base = Path(__file__).parent.parent.parent
        ad_path = ads_dir or base / "ads_ohsou"
        ad_path = Path(ad_path)
        
        if not ad_path.exists():
            raise FileNotFoundError(f"Ads directory not found: {ad_path}")
        
        files = sorted(ad_path.glob("*.png")) + sorted(ad_path.glob("*.jpg")) + sorted(ad_path.glob("*.jpeg"))
        if not files:
            raise FileNotFoundError(f"No ad images in {ad_path}")
        
        copy_map = await extract_copy_for_all_ads(ad_path)
        
        ads = []
        for i, f in enumerate(files, 1):
            ad_id = f"ohsou_ad_{i}"
            copy = copy_map.get(str(f), "")
            ads.append(Ad(
                ad_id=ad_id,
                name=f"Creative {i}",
                copy=copy,
                image_path=str(f),
                description=f"Ohsou ad {i} from {f.name}"
            ))
        return ads
    
    async def load_flows(self, flows_dir: Path | None = None) -> List[Any]:
        raise NotImplementedError("Ohsou does not support Flow mode")
