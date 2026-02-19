# Apriori - AI-Powered User Simulation

Unified simulation platform for **Ad Creative** and **Product Flow** optimization. Simulate target users with AI to predict behavior, compare variants, and optimize decisions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPANY PLUGINS                                │
│  Loop Health │ Ohsou │ Blink Money (future)                      │
│  - Target users   - Ads/Flows   - Domain context                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    CORE SIMULATION                                │
│  Ad Simulator          │          Flow Simulator                 │
│  - Persona × Ad        │          - Persona × Flow               │
│  - Trust, click        │          - Step-by-step decisions       │
│  - Budget optimize     │          - Drop-off analysis            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    SHARED FOUNDATION                              │
│  Personas │ LLM (Gemini/OpenRouter) │ Validation │ Reports      │
└─────────────────────────────────────────────────────────────────┘
```

## Use Cases

### 1. Ad Simulator
- **Input**: Ad creatives (images)
- **Output**: Which ad performs best, budget allocation, segment ownership
- **Companies**: Ohsou (D2C fashion), CrediGo (fintech)

### 2. Flow Simulator
- **Input**: Multiple product flows (each = sequence of design screens)
- **Output**: Best flow per persona, dominant drop-off reasons, improvement recommendations
- **Companies**: Loop Health (insurance onboarding)

## Quick Start

```bash
# Ad simulation (Ohsou - D2C fashion)
python run_simulation.py --company ohsou --mode ad --num-personas 10

# Flow simulation (Loop Health)
python run_simulation.py --company loop_health --mode flow --num-personas 10

# Multiple flows for comparison
python run_simulation.py --company loop_health --mode flow \
  --flow-dirs product_flow product_flow_v2
```

## Project Structure

```
backend/
├── run_simulation.py      # Unified CLI entry point
├── src/
│   ├── core/              # Core simulation engine
│   │   ├── base.py        # Abstractions (FlowStimulus, AdStimulus, etc.)
│   │   ├── ad_simulator.py
│   │   ├── flow_simulator.py
│   │   ├── flow_analyzer.py   # Drop-off analysis, flow comparison
│   │   ├── simulation_engine.py  # Tiered Ad simulation (Pro + Flash)
│   │   ├── optimizer.py
│   │   └── validator.py
│   ├── companies/         # Company plugins
│   │   ├── base.py
│   │   ├── loop_health.py
│   │   └── ohsou.py
│   └── api/
│       └── gemini_client.py
├── product_flow/          # Loop Health flow screens
├── ads_ohsou/             # Ohsou ad creatives
└── data/                  # Outputs
```

## Adding a New Company

1. Create `src/companies/your_company.py`
2. Implement `CompanyPlugin` (load_personas, load_ads or load_flows)
3. Register in `run_simulation.py` COMPANY_REGISTRY

## Environment

- `OPENROUTER_API_KEY` - API key for LLM (Gemini, Claude via OpenRouter)
- `NUM_PERSONAS` - Override default persona count
