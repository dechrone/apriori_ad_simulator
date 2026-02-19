"""
Loop Health Company Plugin - Corporate health insurance onboarding.

Target: Corporate employees going through health insurance signup.
Modes: Flow (product flow comparison)
Personas: EnhancedPersona with health profiles, behavioral traits.
"""

from pathlib import Path
from typing import List, Any


def _import_loop_health():
    """Lazy import to avoid circular deps and heavy load."""
    from loop_health_simulator_v2 import (
        EnhancedPersona,
        EnhancedPersonaGenerator,
        FlowView,
        EnhancedFlowSimulator,
    )
    return EnhancedPersona, EnhancedPersonaGenerator, FlowView, EnhancedFlowSimulator


from src.companies.base import CompanyPlugin, CompanyConfig, SimulationMode
from src.core.base import FlowStimulus, FlowScreen
from src.utils.config import DATA_DIR


class LoopHealthPlugin(CompanyPlugin):
    """Loop Health - corporate health insurance flow simulation."""
    
    def __init__(self):
        self._config = CompanyConfig(
            company_id="loop_health",
            company_name="Loop Health",
            modes=[SimulationMode.FLOW],
            product_category="healthcare",
            data_dir=DATA_DIR / "loop_health"
        )
        self._enhanced_simulator: EnhancedFlowSimulator | None = None
    
    @property
    def config(self) -> CompanyConfig:
        return self._config
    
    async def load_personas(self, count: int | None = None, **kwargs) -> List[Any]:
        """Generate Loop Health's diverse corporate employee personas."""
        _, EnhancedPersonaGenerator, _, _ = _import_loop_health()
        personas = EnhancedPersonaGenerator.generate_diverse_personas()
        if count:
            personas = personas[:count]
        return personas
    
    async def load_ads(self, ads_dir: Path | None = None) -> List[Any]:
        raise NotImplementedError("Loop Health does not support Ad mode")
    
    async def load_flows(
        self,
        flows_dir: Path | None = None,
        flow_dirs: List[Path] | None = None
    ) -> List[FlowStimulus]:
        """
        Load product flows. Each subdir in flows_dir = one flow.
        Or pass flow_dirs as list of paths, each with .png screens.
        """
        base = flows_dir or Path(__file__).parent.parent.parent / "product_flow"
        
        if flow_dirs:
            # Multiple flow directories
            flows = []
            for i, fd in enumerate(flow_dirs):
                screens = self._load_screens_from_dir(fd, flow_num=i + 1)
                if screens:
                    flows.append(FlowStimulus(
                        flow_id=f"flow_{i+1}",
                        flow_name=fd.name,
                        screens=screens
                    ))
            return flows
        
        # Single flow from base dir
        screens = self._load_screens_from_dir(base, flow_num=1)
        return [FlowStimulus(
            flow_id="flow_1",
            flow_name="Onboarding",
            screens=screens
        )] if screens else []
    
    def _load_screens_from_dir(self, dir_path: Path, flow_num: int = 1) -> List[FlowScreen]:
        """Load screens from a directory of PNGs."""
        dir_path = Path(dir_path)
        if not dir_path.exists():
            return []
        
        files = sorted(dir_path.glob("*.png"))[:12]  # Max 12 screens
        screens = []
        for i, f in enumerate(files, 1):
            screens.append(FlowScreen(
                view_id=f"view_{i}",
                view_number=i,
                view_name=f"View {i}",
                image_path=str(f),
                description=f"Onboarding view {i}",
                step_type="OPTIONAL" if i >= 7 else "MANDATORY"  # Loop Health convention
            ))
        return screens
    
    def get_enhanced_flow_simulator(self):
        """Get the Loop Health specific flow simulator (uses rich prompts)."""
        if self._enhanced_simulator is None:
            _, _, _, EnhancedFlowSimulator = _import_loop_health()
            self._enhanced_simulator = EnhancedFlowSimulator()
        return self._enhanced_simulator


def convert_flow_to_loop_health_views(flow: FlowStimulus) -> List[Any]:
    """Convert FlowStimulus to Loop Health FlowView list."""
    _, _, FlowView, _ = _import_loop_health()
    views = []
    for s in flow.screens:
        views.append(FlowView(
            view_id=s.view_id,
            view_number=s.view_number,
            view_name=s.view_name,
            image_path=s.image_path,
            description=s.description,
            intervention_applied=s.intervention_applied
        ))
    return views
