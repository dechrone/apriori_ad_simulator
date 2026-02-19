"""
Blink Money Company Plugin — Loan Against Mutual Funds (LAMF).

Product: Blink Money lets users pledge their MF portfolio as collateral and
         get instant credit/overdraft without redeeming their investments.

Target: Tier1 / High-Tier2 city residents, age 30+, with existing mutual fund
        portfolios who periodically face liquidity needs.

Persona psychology: They HAVE money (in MFs) but sometimes need cash FAST.
Core tension: "Do I sell my MFs (lose future returns) or do I pledge them for a loan?
              Is Blink Money trustworthy enough to manage my pledge?"
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any

from pydantic import BaseModel, Field
from tqdm.asyncio import tqdm

from src.companies.base import CompanyPlugin, CompanyConfig, SimulationMode
from src.core.base import FlowStimulus, FlowScreen, FlowJourneyResult, FlowStepDecision
from src.api.gemini_client import gemini_client
from src.utils.config import DATA_DIR


# ---------------------------------------------------------------------------
# Persona models — LAMF-specific
# ---------------------------------------------------------------------------

class MFPortfolio(BaseModel):
    """The mutual fund portfolio that is the collateral for the loan."""
    total_value_inr: int
    eligible_pledge_value_inr: int   # ~70-80% of portfolio (LTV)
    funds_count: int
    platforms: List[str]             # Where MFs are held (Groww, Zerodha, CAMS, etc.)
    has_used_lamf_before: bool
    comfort_with_pledging: str       # "comfortable", "nervous", "never_heard_of_it"


class LiquidityNeed(BaseModel):
    """The liquidity situation driving the persona to look at LAMF."""
    urgency: str              # "emergency", "planned", "opportunistic"
    amount_needed_inr: int
    purpose: str              # "medical", "business", "tax_payment", "home_renovation", "other"
    time_to_need: str         # "today", "this_week", "this_month", "not_urgent"
    alternatives_considered: List[str]  # ["personal_loan", "credit_card", "sell_mfs", "borrow_family"]


class FinancialBehavior(BaseModel):
    fintech_trust: float = Field(ge=0, le=1)
    loan_app_trust: float = Field(ge=0, le=1)   # Specific trust for loan apps (lower by default)
    app_switching_ease: float = Field(ge=0, le=1)
    data_privacy_concern: float = Field(ge=0, le=1)
    digital_literacy: int = Field(ge=0, le=10)
    risk_aversion_around_collateral: float = Field(ge=0, le=1)  # Fear of losing pledged MFs
    urgency_driven_decision: float = Field(ge=0, le=1)  # Makes faster decisions under urgency


class BlinkMoneyPersona(BaseModel):
    """Target user persona for Blink Money LAMF product."""
    uuid: str
    name: str
    occupation: str
    age: int
    sex: str
    city: str
    state: str
    city_tier: str
    education_level: str
    monthly_income_inr: int
    primary_device: str

    mf_portfolio: MFPortfolio
    liquidity_need: LiquidityNeed
    behavior: FinancialBehavior

    background: str      # Who are they
    loan_mindset: str    # How they think about borrowing against their MFs
    key_question: str    # The one question this screen must answer for them


# ---------------------------------------------------------------------------
# Persona Generator — 10 LAMF target users
# ---------------------------------------------------------------------------

class BlinkMoneyPersonaGenerator:

    @staticmethod
    def generate_10_personas() -> List[BlinkMoneyPersona]:
        # Constraint requested: Tier1/High-Tier2, age 30+, and MF portfolio within ₹5.5L–₹7.0L.
        return [
            BlinkMoneyPersona(
                uuid="bm_001",
                name="Rajesh Sharma",
                occupation="Senior Manager - Operations",
                age=43,
                sex="Male",
                city="Delhi",
                state="Delhi",
                city_tier="Tier1",
                education_level="MBA",
                monthly_income_inr=185000,
                primary_device="iPhone",
                mf_portfolio=MFPortfolio(
                    total_value_inr=670000,
                    eligible_pledge_value_inr=500000,
                    funds_count=3,
                    platforms=["Kuvera", "ET Money"],
                    has_used_lamf_before=False,
                    comfort_with_pledging="nervous",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="emergency",
                    amount_needed_inr=250000,
                    purpose="medical",
                    time_to_need="today",
                    alternatives_considered=["personal_loan", "credit_card", "borrow_family"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.7,
                    loan_app_trust=0.5,
                    app_switching_ease=0.4,
                    data_privacy_concern=0.65,
                    digital_literacy=7,
                    risk_aversion_around_collateral=0.78,
                    urgency_driven_decision=0.85,
                ),
                background="Disciplined MF investor with a ~₹6.7L portfolio. Sudden medical expense requires ₹2.5L today. Doesn’t want to redeem funds at a bad time.",
                loan_mindset="I need speed, but I won’t risk my mutual funds without understanding exactly how pledging works and what happens if I’m late on repayment.",
                key_question="Will my mutual funds ever be sold without my explicit consent, and under what conditions?",
            ),
            BlinkMoneyPersona(
                uuid="bm_002",
                name="Priya Mehta",
                occupation="Owner - Boutique Manufacturing Business",
                age=38,
                sex="Female",
                city="Mumbai",
                state="Maharashtra",
                city_tier="Tier1",
                education_level="Graduate (B.Com)",
                monthly_income_inr=260000,
                primary_device="Android",
                mf_portfolio=MFPortfolio(
                    total_value_inr=620000,
                    eligible_pledge_value_inr=465000,
                    funds_count=4,
                    platforms=["Zerodha Coin"],
                    has_used_lamf_before=True,
                    comfort_with_pledging="comfortable",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="planned",
                    amount_needed_inr=300000,
                    purpose="business",
                    time_to_need="this_week",
                    alternatives_considered=["overdraft_facility", "credit_card", "sell_mfs"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.82,
                    loan_app_trust=0.72,
                    app_switching_ease=0.7,
                    data_privacy_concern=0.45,
                    digital_literacy=8,
                    risk_aversion_around_collateral=0.42,
                    urgency_driven_decision=0.6,
                ),
                background="Small business owner with ~₹6.2L MF portfolio. Has used LAMF once before; cares about rate transparency and disbursal time.",
                loan_mindset="I’m okay pledging, but only if the interest rate + all fees are crystal clear and the money comes fast.",
                key_question="What is my final APR including all charges, and how fast is disbursal?",
            ),
            BlinkMoneyPersona(
                uuid="bm_003",
                name="Suresh Iyer",
                occupation="Finance Manager - Private Company",
                age=48,
                sex="Male",
                city="Chennai",
                state="Tamil Nadu",
                city_tier="Tier1",
                education_level="CA",
                monthly_income_inr=210000,
                primary_device="Android",
                mf_portfolio=MFPortfolio(
                    total_value_inr=690000,
                    eligible_pledge_value_inr=520000,
                    funds_count=5,
                    platforms=["Kuvera"],
                    has_used_lamf_before=False,
                    comfort_with_pledging="nervous",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="planned",
                    amount_needed_inr=200000,
                    purpose="tax_payment",
                    time_to_need="this_month",
                    alternatives_considered=["sell_mfs", "credit_card"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.65,
                    loan_app_trust=0.45,
                    app_switching_ease=0.3,
                    data_privacy_concern=0.82,
                    digital_literacy=8,
                    risk_aversion_around_collateral=0.86,
                    urgency_driven_decision=0.45,
                ),
                background="CA background with a ~₹6.9L MF portfolio. Wants a short-term bridge for tax payment; expects full disclosure and proper trust credentials.",
                loan_mindset="If I can’t see fees, lender entity, and pledge mechanics clearly, I’m out. I don’t do ‘trust me bro’ in finance.",
                key_question="What are all fees and who is the regulated lending partner behind this?",
            ),
            BlinkMoneyPersona(
                uuid="bm_004",
                name="Neha Gupta",
                occupation="Senior Software Engineer",
                age=33,
                sex="Female",
                city="Bangalore",
                state="Karnataka",
                city_tier="Tier1",
                education_level="B.Tech",
                monthly_income_inr=165000,
                primary_device="iPhone",
                mf_portfolio=MFPortfolio(
                    total_value_inr=580000,
                    eligible_pledge_value_inr=430000,
                    funds_count=3,
                    platforms=["Groww"],
                    has_used_lamf_before=False,
                    comfort_with_pledging="nervous",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="planned",
                    amount_needed_inr=350000,
                    purpose="home_renovation",
                    time_to_need="this_month",
                    alternatives_considered=["personal_loan", "credit_card", "sell_mfs"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.83,
                    loan_app_trust=0.68,
                    app_switching_ease=0.75,
                    data_privacy_concern=0.5,
                    digital_literacy=9,
                    risk_aversion_around_collateral=0.62,
                    urgency_driven_decision=0.5,
                ),
                background="Tech-savvy investor with ~₹5.8L in MFs via Groww. Considering LAMF vs personal loan for renovation; cares about clarity and whether SIPs/portfolio behavior changes during pledge.",
                loan_mindset="Explain the pledge step-by-step. If I sense hidden terms or weird access permissions, I’ll bounce.",
                key_question="Can I continue investing (SIPs/top-ups) and tracking normally while funds are pledged?",
            ),
            BlinkMoneyPersona(
                uuid="bm_005",
                name="Kiran Reddy",
                occupation="Tech Startup Founder",
                age=35,
                sex="Male",
                city="Hyderabad",
                state="Telangana",
                city_tier="Tier1",
                education_level="B.Tech + MBA",
                monthly_income_inr=350000,
                primary_device="iPhone",
                mf_portfolio=MFPortfolio(
                    total_value_inr=700000,
                    eligible_pledge_value_inr=530000,
                    funds_count=4,
                    platforms=["Zerodha Coin", "INDmoney"],
                    has_used_lamf_before=True,
                    comfort_with_pledging="comfortable",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="opportunistic",
                    amount_needed_inr=450000,
                    purpose="business",
                    time_to_need="today",
                    alternatives_considered=["sell_mfs", "credit_card"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.9,
                    loan_app_trust=0.82,
                    app_switching_ease=0.9,
                    data_privacy_concern=0.3,
                    digital_literacy=10,
                    risk_aversion_around_collateral=0.28,
                    urgency_driven_decision=0.95,
                ),
                background="Founder with ~₹7L MF portfolio. Has used LAMF before; optimizing for speed and clean UX.",
                loan_mindset="Don’t waste my time. Show max eligible credit line, time-to-cash, and repayment flexibility upfront.",
                key_question="How fast will I get funds, and what’s the maximum eligible credit line right now?",
            ),
            BlinkMoneyPersona(
                uuid="bm_006",
                name="Deepak Nair",
                occupation="Government Employee (Senior Grade)",
                age=52,
                sex="Male",
                city="Kochi",
                state="Kerala",
                city_tier="High-Tier2",
                education_level="Post Graduate",
                monthly_income_inr=120000,
                primary_device="Android",
                mf_portfolio=MFPortfolio(
                    total_value_inr=550000,
                    eligible_pledge_value_inr=410000,
                    funds_count=3,
                    platforms=["SBI MF Direct"],
                    has_used_lamf_before=False,
                    comfort_with_pledging="never_heard_of_it",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="planned",
                    amount_needed_inr=120000,
                    purpose="home_renovation",
                    time_to_need="this_month",
                    alternatives_considered=["bank_loan", "sell_mfs", "borrow_family"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.5,
                    loan_app_trust=0.35,
                    app_switching_ease=0.25,
                    data_privacy_concern=0.86,
                    digital_literacy=6,
                    risk_aversion_around_collateral=0.93,
                    urgency_driven_decision=0.25,
                ),
                background="Conservative saver with ~₹5.5L in MFs. First time hearing about LAMF; wants a small bridge amount but needs very simple explanations.",
                loan_mindset="I will not proceed unless it’s explained in simple words and I see official trust markers. Otherwise I’ll go to my bank.",
                key_question="In simple terms: what exactly changes for my mutual funds once I pledge them?",
            ),
            BlinkMoneyPersona(
                uuid="bm_007",
                name="Anjali Kapoor",
                occupation="Principal - Private School",
                age=44,
                sex="Female",
                city="Chandigarh",
                state="Punjab",
                city_tier="High-Tier2",
                education_level="M.Ed",
                monthly_income_inr=95000,
                primary_device="Android",
                mf_portfolio=MFPortfolio(
                    total_value_inr=600000,
                    eligible_pledge_value_inr=450000,
                    funds_count=2,
                    platforms=["Groww"],
                    has_used_lamf_before=False,
                    comfort_with_pledging="nervous",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="emergency",
                    amount_needed_inr=150000,
                    purpose="other",
                    time_to_need="this_week",
                    alternatives_considered=["personal_loan", "borrow_family", "credit_card"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.62,
                    loan_app_trust=0.48,
                    app_switching_ease=0.45,
                    data_privacy_concern=0.75,
                    digital_literacy=7,
                    risk_aversion_around_collateral=0.82,
                    urgency_driven_decision=0.7,
                ),
                background="School principal with ~₹6L MF portfolio. Needs quick cash for a personal emergency this week. Very sensitive to anything that feels pushy or unclear.",
                loan_mindset="I need speed but I can’t risk my savings. If you can’t clearly explain safety and repayment, I’m out.",
                key_question="What safeguards exist to ensure my mutual funds aren’t liquidated unexpectedly?",
            ),
            BlinkMoneyPersona(
                uuid="bm_008",
                name="Rohit Bansal",
                occupation="Product Manager - Unicorn Startup",
                age=31,
                sex="Male",
                city="Gurgaon",
                state="Haryana",
                city_tier="Tier1",
                education_level="IIT",
                monthly_income_inr=240000,
                primary_device="iPhone",
                mf_portfolio=MFPortfolio(
                    total_value_inr=660000,
                    eligible_pledge_value_inr=500000,
                    funds_count=5,
                    platforms=["INDmoney"],
                    has_used_lamf_before=True,
                    comfort_with_pledging="comfortable",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="opportunistic",
                    amount_needed_inr=300000,
                    purpose="other",
                    time_to_need="this_week",
                    alternatives_considered=["sell_mfs"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.92,
                    loan_app_trust=0.88,
                    app_switching_ease=0.92,
                    data_privacy_concern=0.32,
                    digital_literacy=10,
                    risk_aversion_around_collateral=0.22,
                    urgency_driven_decision=0.8,
                ),
                background="Fintech-fluent PM with ~₹6.6L MFs. Has used LAMF earlier. Low friction tolerance; will drop if terms are hidden or if UX is slow.",
                loan_mindset="If this is better than my bank’s flow, I’ll use it. But I need rate/fees and timeline clearly displayed.",
                key_question="Is this faster and more transparent than my bank’s LAMF flow?",
            ),
            BlinkMoneyPersona(
                uuid="bm_009",
                name="Sunita Krishnan",
                occupation="Retired Professor",
                age=61,
                sex="Female",
                city="Pune",
                state="Maharashtra",
                city_tier="Tier1",
                education_level="PhD",
                monthly_income_inr=75000,
                primary_device="Android",
                mf_portfolio=MFPortfolio(
                    total_value_inr=640000,
                    eligible_pledge_value_inr=480000,
                    funds_count=4,
                    platforms=["CAMS Online"],
                    has_used_lamf_before=False,
                    comfort_with_pledging="nervous",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="planned",
                    amount_needed_inr=100000,
                    purpose="other",
                    time_to_need="not_urgent",
                    alternatives_considered=["sell_mfs", "bank_fd_break"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.55,
                    loan_app_trust=0.4,
                    app_switching_ease=0.2,
                    data_privacy_concern=0.88,
                    digital_literacy=6,
                    risk_aversion_around_collateral=0.92,
                    urgency_driven_decision=0.15,
                ),
                background="Retired professor with ~₹6.4L in MFs, exploring LAMF as an option without urgency. Needs strong legitimacy signals and plain-language explanations.",
                loan_mindset="I will only proceed if I see who the lender is and what regulations apply. Otherwise I’ll consult family and stop.",
                key_question="Is this regulated and who exactly is the lender / partner behind this?",
            ),
            BlinkMoneyPersona(
                uuid="bm_010",
                name="Amit Joshi",
                occupation="Independent Management Consultant",
                age=40,
                sex="Male",
                city="Jaipur",
                state="Rajasthan",
                city_tier="High-Tier2",
                education_level="MBA",
                monthly_income_inr=200000,
                primary_device="Android",
                mf_portfolio=MFPortfolio(
                    total_value_inr=590000,
                    eligible_pledge_value_inr=440000,
                    funds_count=3,
                    platforms=["Groww"],
                    has_used_lamf_before=False,
                    comfort_with_pledging="nervous",
                ),
                liquidity_need=LiquidityNeed(
                    urgency="planned",
                    amount_needed_inr=200000,
                    purpose="business",
                    time_to_need="this_week",
                    alternatives_considered=["personal_loan", "sell_mfs", "credit_card"],
                ),
                behavior=FinancialBehavior(
                    fintech_trust=0.75,
                    loan_app_trust=0.6,
                    app_switching_ease=0.65,
                    data_privacy_concern=0.6,
                    digital_literacy=8,
                    risk_aversion_around_collateral=0.7,
                    urgency_driven_decision=0.55,
                ),
                background="Consultant with irregular cashflows and ~₹5.9L in MFs. Looking for a short bridge; distrustful of hidden fees and unclear repayment/prepayment terms.",
                loan_mindset="Show me the fee and repayment terms clearly. If there’s a surprise personal-loan upsell, I’m done.",
                key_question="What are the repayment and prepayment terms (and all fees) for this credit line?",
            ),
        ]


# ---------------------------------------------------------------------------
# LAMF-specific screen analyzer and decision prompt
# ---------------------------------------------------------------------------

LAMF_SYSTEM_PROMPT = """You are simulating a real person evaluating a Loan Against Mutual Funds (LAMF) app.

WHAT LAMF IS: The user pledges their mutual fund portfolio as collateral and gets
an instant loan/overdraft without selling the MFs. The MFs continue to earn returns
while pledged, but if the user defaults, the lender can sell them.

YOUR PRIME DIRECTIVE:
You ARE the person described. Make decisions as they would given:
- Their existing MF portfolio (this is REAL collateral they're risking)
- Their specific liquidity need and urgency
- Their prior experience (or lack thereof) with LAMF
- Their level of financial sophistication

CRITICAL REALISM RULES FOR LAMF:
1. COLLATERAL ANXIETY: Pledging MFs is psychologically hard. "What if they sell my MFs?"
   is the #1 fear. Any screen that doesn't address this clearly → distrust.

2. RATE & TERMS OBSESSION: Users compare this against personal loans, credit cards.
   If interest rate or charges aren't visible early, they assume it's hidden for a reason.

3. TRUST THRESHOLD IS HIGH: This is a loan app that wants access to your MF portfolio.
   Privacy, SEBI/RBI mentions, and partner bank trust signals matter enormously.

4. URGENCY IS THE JOKER CARD: High-urgency users (emergency, same-day need) will push
   through more friction. Low-urgency users drop at the first confusing screen.

5. FIRST-TIMER vs REPEAT USER: First-timers need education at every step.
   Repeat users want speed — they'll be annoyed by over-explanation.

Return ONLY valid JSON. Your decisions must be grounded in YOUR specific profile."""


LAMF_DECISION_PROMPT = """═══════════════════════════════════════════════════════════════
YOUR IDENTITY — LAMF USER PROFILE
═══════════════════════════════════════════════════════════════

WHO YOU ARE:
  {name} | {occupation} | {age}yo {sex}
  {city} ({city_tier}) | Income: ₹{monthly_income:,}/month

YOUR MF PORTFOLIO (the collateral):
  Total Value: ₹{portfolio_value} | Eligible for Loan: ₹{pledge_value}
  Held on: {platforms} | LAMF Experience: {lamf_experience}
  Comfort with pledging: {pledge_comfort}

YOUR LIQUIDITY NEED:
  Urgency: {urgency} | Need: ₹{amount_needed:,} for {purpose}
  Timeline: {time_to_need}
  Alternatives you considered: {alternatives}

YOUR BEHAVIOR:
  Trust in loan apps: {loan_trust:.0%} | Fintech trust: {fintech_trust:.0%}
  Fear of losing pledged MFs: {collateral_risk:.0%}
  Makes faster decisions under pressure: {urgency_driven:.0%}
  Digital literacy: {digital_literacy}/10

YOUR MINDSET:
  "{loan_mindset}"

THE ONE QUESTION THIS FLOW MUST ANSWER FOR YOU:
  "{key_question}"

═══════════════════════════════════════════════════════════════
CURRENT SCREEN ({view_number}/{total_views}): {view_name}
═══════════════════════════════════════════════════════════════

WHAT YOU SEE:
{view_description}

YOUR JOURNEY SO FAR: {journey_summary}

═══════════════════════════════════════════════════════════════
EVALUATE THIS SCREEN AS A LAMF USER
═══════════════════════════════════════════════════════════════

🔒 COLLATERAL SAFETY CHECK:
   Does this screen address your fear: "What happens to my MFs?"
   Any clarity on pledge mechanics, release conditions, or lender's rights?

💸 RATE & TERMS VISIBILITY:
   Can you see the interest rate, processing fee, or any charges yet?
   If not shown and it's late in the flow, that's a red flag.

🏛️ TRUST & LEGITIMACY:
   SEBI/RBI mention? Partner bank? Secure connection indicators?
   Does this look like a legitimate financial product or a fly-by-night app?

⚡ URGENCY MATCH:
   Given your urgency ({urgency}), is this screen moving fast enough?
   Or is it adding unnecessary steps?

🎯 KEY QUESTION ANSWERED?
   Does this screen answer: "{key_question}"?
   If yes → strong reason to continue. If no → is it coming next?

═══════════════════════════════════════════════════════════════
MANDATORY vs OPTIONAL:
  Screens 1-3: Almost always mandatory for a loan app (KYC, portfolio link, loan details)
  Later screens: Optional if they don't directly serve your liquidity need
═══════════════════════════════════════════════════════════════

RESPOND IN PURE JSON (no markdown, no backticks):

{{
    "step_type": "MANDATORY|OPTIONAL",
    "decision": "CONTINUE|DROP_OFF",

    "gut_reaction": "<Your instant reaction in your authentic voice>",
    "critical_audit": "<What your financial brain questions about this screen>",

    "trust_score": <0-10>,
    "clarity_score": <0-10>,
    "value_perception_score": <0-10>,

    "collateral_anxiety_triggered": <true/false, did this screen raise MF-safety fears?>,
    "key_question_addressed": <true/false, did this screen answer your key question?>,
    "rate_transparency_score": <0-10, how clearly are loan terms shown?>,

    "what_worked": ["<specific things that built trust>"],
    "friction_points": ["<specific things that confused or alarmed you>"],
    "missing_element": "<the one thing you wish this screen showed>",

    "emotional_state": "<1-2 words>",
    "reasoning": "<2-3 sentences of your full decision logic>",
    "drop_off_reason": "<ONLY if DROP_OFF: exact reason>",

    "time_spent_seconds": <realistic time>
}}"""


class BlinkMoneyFlowSimulator:
    """LAMF-specific flow simulator with collateral/loan-context prompts."""

    def __init__(self):
        self._screen_cache: Dict[str, Dict] = {}

    async def _analyze_screen(self, screen: FlowScreen) -> Dict:
        key = screen.image_path
        if key in self._screen_cache:
            return self._screen_cache[key]
        try:
            with open(screen.image_path, "rb") as f:
                image_data = f.read()
            prompt = """Analyze this Loan Against Mutual Funds (LAMF) app screen.

Describe exactly what you see:
1. main_content - What is the screen's purpose? (e.g., "loan amount selection", "MF portfolio linking", "KYC", "OTP verification", "loan offer screen", "pledge confirmation")
2. key_information - Any numbers shown? (loan amount, interest rate, processing fee, LTV ratio, repayment terms?)
3. required_action - What must the user do? (tap, enter, verify, confirm?)
4. trust_signals - Any SEBI/RBI/NBFC mentions, bank logos, security badges, regulated entity info?
5. collateral_info - Any information about how MFs will be pledged/released/handled?
6. friction_points - Confusing elements, missing information, alarming language?
7. design_quality - Professional and trust-building, or amateur and concerning?

Return ONLY valid JSON (no newlines inside values):
{"main_content": "...", "key_information": "...", "required_action": "...", "trust_signals": "...", "collateral_info": "...", "friction_points": "...", "design_quality": "..."}"""
            response = await gemini_client.generate_pro(prompt, image_data)
            result = gemini_client.parse_json_response(response)
            self._screen_cache[key] = result
            return result
        except Exception as e:
            return {
                "main_content": "LAMF app screen", "key_information": "Unknown",
                "required_action": "Review and proceed", "trust_signals": "Unknown",
                "collateral_info": "Not visible", "friction_points": str(e),
                "design_quality": "Unknown"
            }

    def _fmt_money(self, amount: int) -> str:
        if amount >= 10000000:
            return f"₹{amount/10000000:.1f}Cr"
        if amount >= 100000:
            return f"₹{amount//100000}L"
        return f"₹{amount:,}"

    def _build_context(
        self, persona: BlinkMoneyPersona,
        screen: FlowScreen, journey_history: List[str],
        view_analysis: Dict, total_views: int
    ) -> Dict:
        view_desc = "\n".join(
            f"{k.replace('_',' ').title()}: {v}"
            for k, v in view_analysis.items() if v
        )
        return {
            "name": persona.name, "occupation": persona.occupation,
            "age": persona.age, "sex": persona.sex,
            "city": persona.city, "city_tier": persona.city_tier,
            "monthly_income": persona.monthly_income_inr,
            "portfolio_value": self._fmt_money(persona.mf_portfolio.total_value_inr),
            "pledge_value": self._fmt_money(persona.mf_portfolio.eligible_pledge_value_inr),
            "platforms": ", ".join(persona.mf_portfolio.platforms),
            "lamf_experience": "Has used LAMF before" if persona.mf_portfolio.has_used_lamf_before else "First time",
            "pledge_comfort": persona.mf_portfolio.comfort_with_pledging,
            "urgency": persona.liquidity_need.urgency,
            "amount_needed": persona.liquidity_need.amount_needed_inr,
            "purpose": persona.liquidity_need.purpose,
            "time_to_need": persona.liquidity_need.time_to_need,
            "alternatives": ", ".join(persona.liquidity_need.alternatives_considered),
            "loan_trust": persona.behavior.loan_app_trust,
            "fintech_trust": persona.behavior.fintech_trust,
            "collateral_risk": persona.behavior.risk_aversion_around_collateral,
            "urgency_driven": persona.behavior.urgency_driven_decision,
            "digital_literacy": persona.behavior.digital_literacy,
            "loan_mindset": persona.loan_mindset,
            "key_question": persona.key_question,
            "view_number": screen.view_number, "total_views": total_views,
            "view_name": screen.view_name, "view_description": view_desc,
            "journey_summary": " → ".join(journey_history) if journey_history else "First screen",
        }

    async def simulate_journey(
        self, persona: BlinkMoneyPersona,
        flow: FlowStimulus, view_analyses: Dict
    ) -> FlowJourneyResult:
        decisions, total_time, history = [], 0, []
        dropped_at = drop_reason = None

        for screen in flow.screens:
            ctx = self._build_context(persona, screen, history, view_analyses.get(screen.view_id, {}), len(flow.screens))
            prompt = LAMF_DECISION_PROMPT.format(**ctx)
            try:
                raw = await gemini_client.generate_pro(prompt, system_prompt=LAMF_SYSTEM_PROMPT)
                data = gemini_client.parse_json_response(raw)
            except Exception as e:
                data = {
                    "step_type": "MANDATORY", "decision": "DROP_OFF",
                    "gut_reaction": "Simulation error", "critical_audit": str(e),
                    "trust_score": 5, "clarity_score": 5, "value_perception_score": 5,
                    "collateral_anxiety_triggered": False, "key_question_addressed": False,
                    "rate_transparency_score": 5, "what_worked": [], "friction_points": [str(e)],
                    "missing_element": "", "emotional_state": "confused",
                    "reasoning": str(e), "drop_off_reason": "Technical error", "time_spent_seconds": 5
                }

            dec = data.get("decision", "CONTINUE")
            step = FlowStepDecision(
                persona_uuid=persona.uuid, flow_id=flow.flow_id,
                view_id=screen.view_id, view_number=screen.view_number,
                step_type=data.get("step_type", "MANDATORY"), decision=dec,
                reasoning=data.get("reasoning", ""),
                drop_off_reason=data.get("drop_off_reason") if dec == "DROP_OFF" else None,
                trust_score=int(data.get("trust_score", 5)),
                clarity_score=int(data.get("clarity_score", 5)),
                value_perception_score=int(data.get("value_perception_score", 5)),
                emotional_state=data.get("emotional_state", "neutral"),
                friction_points=data.get("friction_points", []) if isinstance(data.get("friction_points"), list) else [],
                time_spent_seconds=int(data.get("time_spent_seconds", 10)),
                metadata={
                    "gut_reaction": data.get("gut_reaction", ""),
                    "critical_audit": data.get("critical_audit", ""),
                    "what_worked": data.get("what_worked", []),
                    "missing_element": data.get("missing_element", ""),
                    "collateral_anxiety_triggered": data.get("collateral_anxiety_triggered", False),
                    "key_question_addressed": data.get("key_question_addressed", False),
                    "rate_transparency_score": data.get("rate_transparency_score", 5),
                }
            )
            decisions.append(step)
            total_time += step.time_spent_seconds
            history.append(f"S{screen.view_number}")

            if dec == "DROP_OFF":
                dropped_at = screen.view_number
                drop_reason = step.drop_off_reason or step.reasoning
                break

        return FlowJourneyResult(
            persona_uuid=persona.uuid, flow_id=flow.flow_id,
            total_screens_seen=len(decisions), completed_flow=dropped_at is None,
            dropped_off_at_view=dropped_at, drop_off_reason=drop_reason,
            decisions=decisions, total_time_seconds=total_time,
            metadata={"persona_name": persona.name, "urgency": persona.liquidity_need.urgency,
                      "lamf_experience": persona.mf_portfolio.has_used_lamf_before}
        )

    async def run_flow(
        self, personas: List[BlinkMoneyPersona],
        flow: FlowStimulus, progress: bool = True
    ) -> List[FlowJourneyResult]:
        print(f"\n   🔍 Analyzing {len(flow.screens)} screens — {flow.flow_name}...")
        analyses = await tqdm.gather(
            *[self._analyze_screen(s) for s in flow.screens],
            desc=f"Screen analysis: {flow.flow_name}"
        )
        view_analyses = {flow.screens[i].view_id: analyses[i] for i in range(len(flow.screens))}

        print(f"   🧠 Simulating {len(personas)} personas — {flow.flow_name}...")
        tasks = [self.simulate_journey(p, flow, view_analyses) for p in personas]
        results = await (tqdm.gather(*tasks, desc=f"Journeys: {flow.flow_name}") if progress else asyncio.gather(*tasks))
        return list(results)


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------

class BlinkMoneyPlugin(CompanyPlugin):

    def __init__(self):
        self._config = CompanyConfig(
            company_id="blink_money", company_name="Blink Money",
            modes=[SimulationMode.FLOW], product_category="lamf",
            data_dir=DATA_DIR / "blink_money"
        )
        self._simulator: BlinkMoneyFlowSimulator | None = None

    @property
    def config(self) -> CompanyConfig:
        return self._config

    async def load_personas(self, count: int | None = None, **kwargs) -> List[BlinkMoneyPersona]:
        personas = BlinkMoneyPersonaGenerator.generate_10_personas()
        return personas[:count] if count else personas

    async def load_ads(self, ads_dir=None):
        raise NotImplementedError("Blink Money is Flow-only (LAMF product)")

    async def load_flows(self, flows_dir=None, flow_dirs=None, **kwargs) -> List[FlowStimulus]:
        base = Path(__file__).parent.parent.parent / "product_flow" / "blink_money"
        if flow_dirs:
            targets = [(Path(d).name, Path(d)) for d in flow_dirs]
        else:
            targets = [(s.name, s) for s in sorted(base.iterdir()) if s.is_dir()]

        flows = []
        for name, path in targets:
            screens = self._load_screens(path)
            if screens:
                flows.append(FlowStimulus(
                    flow_id=name.lower().replace(" ", "_"),
                    flow_name=name.replace("_", " ").title(),
                    screens=screens
                ))
        return flows

    def _load_screens(self, dir_path: Path) -> List[FlowScreen]:
        files = sorted(
            set(dir_path.glob("*.png")) | set(dir_path.glob("*.jpg")) | set(dir_path.glob("*.jpeg")),
            key=lambda f: int(f.stem) if f.stem.isdigit() else 999
        )
        return [
            FlowScreen(
                view_id=f"view_{i}", view_number=i,
                view_name=f"Screen {i}", image_path=str(f),
                step_type="OPTIONAL" if i >= len(files) else "MANDATORY"
            )
            for i, f in enumerate(files, 1)
        ]

    def get_flow_simulator(self) -> BlinkMoneyFlowSimulator:
        if self._simulator is None:
            self._simulator = BlinkMoneyFlowSimulator()
        return self._simulator
