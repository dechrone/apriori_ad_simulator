"""
Company Plugin Base - defines the interface for company-specific configurations.

Each company (Loop Health, Ohsou, Blink Money, etc.) provides:
- Target user groups / personas
- Assets (ads or product flows)
- Domain-specific simulation context
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Callable, Awaitable


class SimulationMode(str, Enum):
    AD = "ad"       # Ad creative comparison
    FLOW = "flow"   # Product flow comparison


@dataclass
class CompanyConfig:
    """Configuration for a company plugin."""
    company_id: str
    company_name: str
    modes: List[SimulationMode]  # Which modes this company supports
    product_category: str = "general"  # fintech, d2c_fashion, healthcare, etc.
    data_dir: Path = field(default_factory=Path)
    
    def __post_init__(self):
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)


class CompanyPlugin(ABC):
    """
    Base class for company-specific plugins.
    
    Company plugins are responsible for:
    1. Loading/generating target personas
    2. Loading company-specific assets (ads or flows)
    3. Providing domain context for simulation prompts
    """
    
    @property
    @abstractmethod
    def config(self) -> CompanyConfig:
        """Company configuration."""
        pass
    
    @abstractmethod
    async def load_personas(self, count: int | None = None, **kwargs) -> List[Any]:
        """
        Load or generate target personas for this company.
        
        Returns list of personas (RawPersona, EnrichedPersona, EnhancedPersona, etc.)
        depending on company needs.
        """
        pass
    
    @abstractmethod
    async def load_ads(self, ads_dir: Path | None = None) -> List[Any]:
        """
        Load ad creatives for Ad mode.
        
        Returns list of Ad objects (or compatible).
        Raises if mode not supported.
        """
        pass
    
    @abstractmethod
    async def load_flows(self, flows_dir: Path | None = None) -> List[Any]:
        """
        Load product flows for Flow mode.
        
        Returns list of FlowStimulus objects.
        Each flow has flow_id, flow_name, screens (list of FlowScreen).
        Raises if mode not supported.
        """
        pass
    
    def get_domain_context(self) -> Dict[str, Any]:
        """
        Return domain-specific context for simulation prompts.
        Override in subclasses for company-specific guidance.
        """
        return {"product_category": self.config.product_category}
