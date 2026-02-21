"""Loop Health Product Flow Simulator - Corporate Health Insurance Onboarding Flow."""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from tqdm.asyncio import tqdm

from src.data.loader import data_loader
from src.core.persona_hydrator import persona_hydrator
from src.api.gemini_client import gemini_client
from src.utils.schemas import RawPersona, EnrichedPersona
from src.utils.config import DATA_DIR
from pydantic import BaseModel, Field


class FlowView(BaseModel):
    """Represents a single view in the onboarding flow."""
    view_id: str
    view_number: int
    view_name: str
    image_path: str
    description: str = ""


class PersonaFlowDecision(BaseModel):
    """Decision made by a persona at a specific view (Utility Mode)."""
    persona_uuid: str
    view_id: str
    view_number: int
    step_type: str = "MANDATORY"  # "MANDATORY" or "OPTIONAL"
    decision: str  # "CONTINUE" or "DROP_OFF"
    trust_score: int = Field(ge=0, le=10)
    clarity_score: int = Field(ge=0, le=10)
    value_perception_score: int = Field(ge=0, le=10)
    inertia_override: bool = False  # Did value overcome laziness?
    urgency_factor: str = "low"  # "high", "medium", "low"
    reasoning: str
    emotional_state: str
    friction_points: List[str] = []
    time_spent_seconds: int = 5  # Simulated time spent on view


class FlowSimulationResult(BaseModel):
    """Complete journey of a persona through the flow."""
    persona_uuid: str
    total_views_seen: int
    dropped_off_at_view: Optional[int] = None
    completed_flow: bool
    decisions: List[PersonaFlowDecision]
    total_time_seconds: int
    drop_off_reason: Optional[str] = None


class LoopHealthPersonaFilter:
    """Filter personas specifically for Loop Health - Corporate employees."""
    
    @staticmethod
    def filter_corporate_employees(count: int = 10) -> List[RawPersona]:
        """
        Filter personas for Loop Health target audience:
        - Corporate employees (not business owners or manual labor)
        - Age 18-55
        - CTC range: 7-8 LPA to CRs (representing all corporate levels)
        - Urban professionals with health insurance awareness
        """
        print("\n🏥 FILTERING FOR LOOP HEALTH - CORPORATE EMPLOYEES")
        print("="*80)
        print("Target: Corporate employees aged 18-55, CTC 7L-100Cr+ (fresher to C-suite)")
        print("-"*80)
        
        data_loader.connect()
        
        # Corporate occupations - employees at all levels
        corporate_occupations = [
            # Tech sector
            'software engineer', 'software developer', 'programmer', 'data scientist',
            'data analyst', 'product manager', 'project manager', 'tech lead',
            'engineering manager', 'cto', 'vp engineering', 'head of engineering',
            
            # Corporate roles
            'manager', 'senior manager', 'assistant manager', 'team lead',
            'executive', 'senior executive', 'associate', 'senior associate',
            'analyst', 'consultant', 'senior consultant', 'specialist',
            
            # Finance & Banking
            'banker', 'investment banker', 'finance manager', 'financial analyst',
            'accountant', 'chartered accountant', 'audit', 'compliance',
            
            # Marketing & Sales
            'marketing manager', 'brand manager', 'digital marketer',
            'sales manager', 'business development', 'account manager',
            
            # HR & Operations
            'hr manager', 'hr executive', 'operations manager', 'supply chain',
            'procurement', 'administration', 'office manager',
            
            # C-Suite
            'ceo', 'cfo', 'coo', 'managing director', 'director', 'vice president'
        ]
        
        # Exclude: business owners, freelancers, manual labor, students
        exclude_keywords = [
            'owner', 'proprietor', 'entrepreneur', 'freelance', 'consultant',
            'driver', 'worker', 'labor', 'farmer', 'vendor', 'shopkeeper',
            'student', 'unemployed', 'retired', 'housewife'
        ]
        
        print(f"✓ Target occupations: {len(corporate_occupations)} corporate roles")
        print(f"✓ Excluded: Business owners, freelancers, manual labor, students")
        
        # Education filter - corporate employees typically educated
        education_filter = """
            (LOWER(education_level) LIKE '%graduate%' 
             OR LOWER(education_level) LIKE '%diploma%')
        """
        
        # Build occupation filters
        occupation_include = " OR ".join([f"LOWER(occupation) LIKE '%{kw}%'" for kw in corporate_occupations])
        occupation_exclude = " AND ".join([f"LOWER(occupation) NOT LIKE '%{kw}%'" for kw in exclude_keywords])
        
        # Try with all fields
        try:
            query = f"""
            SELECT 
                uuid, occupation, first_language, second_language, third_language,
                sex, age, marital_status, education_level, education_degree,
                state, district, zone, country,
                professional_persona, linguistic_persona, cultural_background,
                sports_persona, arts_persona, travel_persona, culinary_persona, persona,
                hobbies_and_interests_list, skills_and_expertise_list,
                hobbies_and_interests, skills_and_expertise, 
                career_goals_and_ambitions, linguistic_background
            FROM personas 
            WHERE ({occupation_include})
                AND ({occupation_exclude})
                AND ({education_filter})
                AND age BETWEEN 18 AND 55
                AND zone = 'Urban'
            ORDER BY RANDOM() 
            LIMIT {count * 5}
            """
            
            print(f"\n⏳ Querying database for corporate employees...")
            df = data_loader.conn.execute(query).df()
            print(f"✓ Found {len(df)} initial matches")
            
            if len(df) < count:
                print(f"\n⚠️ Only found {len(df)} matching personas, generating synthetic ones...")
                synthetic_needed = count - len(df)
                synthetic = LoopHealthPersonaFilter._generate_corporate_employees(synthetic_needed)
                import pandas as pd
                df_synthetic = pd.DataFrame([p.model_dump() for p in synthetic])
                df = pd.concat([df, df_synthetic], ignore_index=True)
            else:
                # Take random sample
                df = df.sample(n=count)
            
            personas = []
            for _, row in df.iterrows():
                persona_data = {
                    'uuid': str(row['uuid']),
                    'occupation': row['occupation'],
                    'first_language': row.get('first_language', 'English'),
                    'second_language': row.get('second_language'),
                    'third_language': row.get('third_language'),
                    'sex': row['sex'],
                    'age': int(row['age']),
                    'marital_status': row.get('marital_status', 'Unknown'),
                    'education_level': row.get('education_level', 'Graduate'),
                    'education_degree': row.get('education_degree'),
                    'state': row['state'],
                    'district': row['district'],
                    'zone': row.get('zone', 'Urban'),
                    'country': row.get('country', 'India'),
                }
                
                # Add rich fields if available
                import pandas as pd
                if 'professional_persona' in row and pd.notna(row['professional_persona']):
                    persona_data['professional_persona'] = row['professional_persona']
                if 'cultural_background' in row and pd.notna(row['cultural_background']):
                    persona_data['cultural_background'] = row['cultural_background']
                if 'hobbies_and_interests' in row and pd.notna(row['hobbies_and_interests']):
                    persona_data['hobbies_and_interests'] = row['hobbies_and_interests']
                if 'skills_and_expertise' in row and pd.notna(row['skills_and_expertise']):
                    persona_data['skills_and_expertise'] = row['skills_and_expertise']
                
                personas.append(RawPersona(**persona_data))
            
            print(f"\n✅ Selected {len(personas)} corporate employee personas:")
            print("="*80)
            for i, p in enumerate(personas, 1):
                print(f"{i}. {p.occupation} | {p.age}yo {p.sex} | {p.district}, {p.state}")
            print("="*80)
            
            data_loader.close()
            return personas
            
        except Exception as e:
            print(f"⚠️ Error filtering personas: {e}")
            print("💡 Generating synthetic corporate employees...")
            data_loader.close()
            return LoopHealthPersonaFilter._generate_corporate_employees(count)
    
    @staticmethod
    def _generate_corporate_employees(count: int) -> List[RawPersona]:
        """Generate synthetic corporate employee personas."""
        import random
        import uuid as uuid_lib
        
        # Different corporate levels with realistic CTCs
        corporate_profiles = [
            # Entry level (7-12 LPA)
            {"occupation": "Software Engineer", "age_range": (22, 28), "ctc_range": (7, 12)},
            {"occupation": "Data Analyst", "age_range": (22, 27), "ctc_range": (7, 10)},
            {"occupation": "Marketing Executive", "age_range": (23, 28), "ctc_range": (6, 10)},
            {"occupation": "HR Executive", "age_range": (23, 28), "ctc_range": (6, 9)},
            
            # Mid level (12-30 LPA)
            {"occupation": "Senior Software Engineer", "age_range": (28, 35), "ctc_range": (15, 30)},
            {"occupation": "Product Manager", "age_range": (28, 38), "ctc_range": (20, 40)},
            {"occupation": "Engineering Manager", "age_range": (30, 40), "ctc_range": (25, 50)},
            {"occupation": "Finance Manager", "age_range": (30, 42), "ctc_range": (18, 35)},
            
            # Senior level (30-100 LPA)
            {"occupation": "Senior Manager", "age_range": (35, 45), "ctc_range": (35, 80)},
            {"occupation": "Director", "age_range": (38, 50), "ctc_range": (50, 120)},
            {"occupation": "Vice President", "age_range": (40, 52), "ctc_range": (80, 200)},
            
            # C-Suite (1Cr+)
            {"occupation": "CTO", "age_range": (38, 55), "ctc_range": (100, 300)},
            {"occupation": "CFO", "age_range": (40, 55), "ctc_range": (150, 400)},
            {"occupation": "CEO", "age_range": (42, 55), "ctc_range": (200, 1000)},
        ]
        
        cities = {
            "Karnataka": ["Bengaluru"],
            "Maharashtra": ["Mumbai", "Pune"],
            "Delhi": ["South Delhi", "Gurgaon"],
            "Tamil Nadu": ["Chennai"],
            "Telangana": ["Hyderabad"]
        }
        
        personas = []
        for _ in range(count):
            profile = random.choice(corporate_profiles)
            state = random.choice(list(cities.keys()))
            
            personas.append(RawPersona(
                uuid=str(uuid_lib.uuid4()).replace("-", ""),
                occupation=profile["occupation"],
                first_language=random.choice(["English", "Hindi", "Tamil", "Telugu"]),
                second_language="English" if random.random() > 0.3 else None,
                sex=random.choice(["Male", "Female"]),
                age=random.randint(*profile["age_range"]),
                marital_status=random.choice(["Currently Married", "Never Married"]),
                education_level=random.choice(["Graduate", "Post Graduate"]),
                state=state,
                district=random.choice(cities[state]),
                zone="Urban",
                hobbies_and_interests_list="Fitness, Reading, Travel",
                skills_and_expertise_list="Leadership, Team Management, Strategic Planning"
            ))
        
        return personas
    
    @staticmethod
    def generate_segmented_personas() -> List[RawPersona]:
        """Generate 20 personas: 10 young & fit, 10 older with health conditions."""
        import random
        import uuid as uuid_lib
        
        personas = []
        
        # SEGMENT 1: Young & Fit (20-30 years, mostly healthy)
        print("\n🏃 SEGMENT 1: Young & Fit Corporate Employees (Age 20-30)")
        young_occupations = [
            {"occupation": "Software Engineer", "age": (22, 28), "ctc": (7, 15)},
            {"occupation": "Data Analyst", "age": (22, 27), "ctc": (7, 12)},
            {"occupation": "Product Manager", "age": (26, 30), "ctc": (15, 25)},
            {"occupation": "Marketing Executive", "age": (23, 28), "ctc": (6, 12)},
            {"occupation": "Business Analyst", "age": (24, 29), "ctc": (8, 15)},
        ]
        
        cities = {
            "Karnataka": ["Bengaluru"],
            "Maharashtra": ["Mumbai", "Pune"],
            "Delhi": ["Gurgaon"],
            "Tamil Nadu": ["Chennai"],
            "Telangana": ["Hyderabad"]
        }
        
        for i in range(10):
            profile = random.choice(young_occupations)
            state = random.choice(list(cities.keys()))
            age = random.randint(*profile["age"])
            
            persona = RawPersona(
                uuid=str(uuid_lib.uuid4()).replace("-", ""),
                occupation=profile["occupation"],
                first_language=random.choice(["English", "Hindi", "Tamil"]),
                second_language="English",
                sex=random.choice(["Male", "Female"]),
                age=age,
                marital_status="Never Married" if age < 27 else random.choice(["Never Married", "Currently Married"]),
                education_level=random.choice(["Graduate", "Post Graduate"]),
                state=state,
                district=random.choice(cities[state]),
                zone="Urban",
                hobbies_and_interests_list="Gym, Running, Cricket, Travel, Gaming",
                skills_and_expertise_list="Programming, Data Analysis, Project Management",
                professional_persona=f"Young professional who is health-conscious and exercises regularly. Goes to gym 4-5 times a week. Rarely falls sick. Last doctor visit was 8 months ago for a routine checkup."
            )
            personas.append(persona)
            print(f"   {i+1}. {persona.occupation}, {persona.age}yo - FIT & HEALTHY")
        
        # SEGMENT 2: Older with Health Conditions (40+ years, ongoing health issues)
        print("\n🏥 SEGMENT 2: Older Employees with Health Conditions (Age 40+)")
        senior_occupations = [
            {"occupation": "Senior Manager", "age": (40, 50), "ctc": (35, 80)},
            {"occupation": "Director", "age": (42, 52), "ctc": (50, 120)},
            {"occupation": "Vice President", "age": (45, 55), "ctc": (80, 200)},
            {"occupation": "CTO", "age": (43, 52), "ctc": (100, 300)},
            {"occupation": "CFO", "age": (44, 54), "ctc": (150, 400)},
        ]
        
        health_conditions = [
            "Diabetes Type 2 - needs regular monitoring and medication",
            "Hypertension - on daily medication, regular BP checks needed",
            "High Cholesterol - on statins, needs quarterly checkups",
            "Chronic Back Pain - sees physiotherapist monthly",
            "Thyroid Disorder - on thyroid medication, regular blood tests",
            "Pre-diabetic - monitoring blood sugar, lifestyle changes needed",
            "Arthritis - joint pain, sees rheumatologist regularly",
            "Sleep Apnea - uses CPAP machine, needs follow-ups"
        ]
        
        for i in range(10):
            profile = random.choice(senior_occupations)
            state = random.choice(list(cities.keys()))
            age = random.randint(*profile["age"])
            condition = random.choice(health_conditions)
            
            persona = RawPersona(
                uuid=str(uuid_lib.uuid4()).replace("-", ""),
                occupation=profile["occupation"],
                first_language=random.choice(["English", "Hindi"]),
                second_language="English",
                sex=random.choice(["Male", "Female"]),
                age=age,
                marital_status="Currently Married",
                education_level=random.choice(["Graduate", "Post Graduate"]),
                state=state,
                district=random.choice(cities[state]),
                zone="Urban",
                hobbies_and_interests_list="Reading, Golf, Travel",
                skills_and_expertise_list="Leadership, Strategic Planning, Business Development",
                professional_persona=f"Senior executive with {condition}. Visits doctor every 2-3 months. Takes daily medication. Needs good health insurance coverage for ongoing treatment and regular checkups."
            )
            personas.append(persona)
            print(f"   {i+1}. {persona.occupation}, {persona.age}yo - {condition.split('-')[0].strip()}")
        
        return personas


class LoopHealthFlowSimulator:
    """Simulates personas going through Loop Health onboarding flow."""
    
    # System prompt for flow simulation - UTILITY MODE (B2B2C)
    FLOW_SIMULATION_SYSTEM_PROMPT = """You are simulating a real corporate employee using EMPLOYER-PROVIDED health insurance.

⚡ CRITICAL BEHAVIORAL CONTEXT: YOU ARE IN "UTILITY MODE" - NOT EVALUATION MODE

MENTAL FRAME (Your Pre-Set Mind):
1. ENTITLEMENT & APATHY: "This is free. My company already paid. I'll use it when I get sick."
2. ZERO RISK PERCEPTION: You are NOT paying for this. No financial risk to you personally.
3. LOW TRUST THRESHOLD: Your employer vetted this. You don't need to verify legitimacy.
4. HIGH INERTIA: You are LAZY. You won't explore optional features unless there's a clear incentive.
5. CAPTIVE AUDIENCE: You MUST complete basic signup (need insurance card). High friction tolerance for MANDATORY steps.
6. LOW PATIENCE FOR UPSELLS: Any optional add-ons or wellness features face HIGH skepticism.

DECISION FRAMEWORK:
- Mandatory Steps (Get Insurance Card): You'll tolerate friction, you NEED this
- Optional Features (Wellness, Add-ons): You'll ignore unless VERY compelling value
- Drop-off Triggers: Confusing mandatory steps, pushy upsells, too many clicks for basic card

You ARE NOT evaluating whether to buy insurance. You ARE evaluating if this app is worth your time."""
    
    VIEW_DECISION_PROMPT = """═══════════════════════════════════════════════════════════
IDENTITY: YOU ARE THIS CORPORATE EMPLOYEE (UTILITY MODE)
═══════════════════════════════════════════════════════════

YOU ARE: {occupation}, {age} years old, {sex}
LOCATION: {district}, {state} (Urban professional)
EDUCATION: {education_level}
MONTHLY INCOME: ₹{monthly_income_inr:,} (Annual CTC: ₹{annual_ctc} LPA)

YOUR CONTEXT:
{persona_context}

🎯 YOUR BEHAVIORAL PRIORS (UTILITY MODE - NOT EVALUATION):
- Trust Threshold: LOW (Employer vetted this, not evaluating legitimacy)
- Inertia Level: HIGH (Won't explore optional features unless clear value)
- Health Status: {health_status} (Affects urgency)
- Risk Perception: ZERO (Company paid, no personal financial risk)
- Friction Tolerance: 
  * HIGH for mandatory steps (need insurance card)
  * LOW for optional add-ons (will ignore upsells)

YOUR CURRENT STATE:
- Digital literacy: {digital_literacy}/10
- Device: {primary_device}
- Mindset: {mindset_state}
- Time available: {time_pressure}

═══════════════════════════════════════════════════════════
ONBOARDING FLOW - VIEW {view_number}/8
═══════════════════════════════════════════════════════════

VIEW NAME: {view_name}

WHAT YOU SEE:
{view_description}

YOUR JOURNEY SO FAR:
{journey_so_far}

═══════════════════════════════════════════════════════════
    DECISION TIME - CONTINUE OR DROP OFF?
═══════════════════════════════════════════════════════════

⚡ UTILITY MODE DECISION LOGIC (You are NOT evaluating whether to buy):

CRITICAL: Identify if this view is MANDATORY or OPTIONAL

🔒 If this seems MANDATORY (get insurance card, basic signup):
   - Your friction tolerance is HIGH
   - You'll push through even if confusing (you need the card)
   - Only drop off if: Technically broken, asks for payment, or impossible to proceed
   
🎁 If this seems OPTIONAL (add-ons, wellness features, upsells):
   - Your friction tolerance is VERY LOW
   - High inertia - "I'll explore this later" (you won't)
   - Only continue if: Clear immediate value OR nudged with incentive

EVALUATION CRITERIA:

1. STEP TYPE: Mandatory or Optional?
   - Mandatory: Getting insurance card, basic family details
   - Optional: Wellness programs, add-ons, extra features

2. CLARITY: Can I do this quickly?
   - If mandatory: Tolerates some confusion
   - If optional: Must be crystal clear or I ignore it

3. INERTIA CHECK: Do I care enough?
   - Default state: Apathy (won't explore unless nudged)
   - Override only if: Clear benefit, social proof, or incentive

4. URGENCY (Health Status Dependent):
   - If {health_status} == "Needs_Care": Will complete EVERYTHING quickly
   - If {health_status} == "Healthy": Will complete minimum only

5. TRUST: Already LOW threshold
   - You don't question legitimacy (employer vetted)
   - BUT you question if app is well-made

DECISION RULES (UTILITY MODE):
- CONTINUE if: 
  * View seems mandatory (need to complete)
  * OR view is optional BUT has clear compelling value
  * Not broken/buggy
  
- DROP OFF if: 
  * Mandatory step is technically broken or impossible
  * Optional step with weak value prop (high inertia wins)
  * Asks for payment (red flag - company should have paid)
  * Too many optional add-ons being pushed (annoyance)

Remember: You are CAPTIVE (must use this), but LAZY (won't explore optional features without clear reason).

═══════════════════════════════════════════════════════════
RESPONSE FORMAT (Pure JSON, no markdown)
═══════════════════════════════════════════════════════════

    {{
        "step_type": "MANDATORY|OPTIONAL",
        "decision": "CONTINUE|DROP_OFF",
        "clarity_score": <0-10, how clear is this view>,
        "value_perception_score": <0-10, how valuable is this step>,
        "trust_score": <0-10, how trustworthy does this feel>,
        "inertia_override": <true|false, did clear value overcome your laziness?>,
        "urgency_factor": <"high"|"medium"|"low", based on your health status>,
        "reasoning": "<UTILITY MODE logic: Is this mandatory or optional? Did you push through or ignore it?>",
        "emotional_state": "<How you feel: entitled|apathetic|annoyed|rushed|satisfied>",
        "friction_points": ["<Specific issues if any>"],
        "time_spent_seconds": <realistic time: 3-60 seconds, higher for mandatory steps>
    }}

If you DROP_OFF, specify: Was it a broken mandatory step or ignored optional step?
"""
    
    async def analyze_view_visual(self, view: FlowView) -> Dict[str, str]:
        """Use Gemini to analyze what's in the view image."""
        prompt = f"""Analyze this health insurance onboarding screen (View {view.view_number}/8).

Describe what you see:
1. Main elements: What's the primary content? (form, information page, options, etc.)
2. Key information: What details are being shown/asked?
3. Actions required: What does the user need to do?
4. Visual design: Professional? Cluttered? Clear?
5. Potential friction: Any confusing or concerning elements?

IMPORTANT: Return ONLY valid JSON with no newlines in string values. Use spaces instead of newlines.

Return as JSON:
{{
    "main_content": "brief description",
    "key_information": "what is being communicated",
    "required_action": "what user must do",
    "design_quality": "assessment",
    "friction_points": "potential issues"
}}
"""
        
        try:
            # Load image
            with open(view.image_path, 'rb') as f:
                image_data = f.read()
            
            response = await gemini_client.generate_pro(prompt, image_data)
            
            if not response or response.strip() == "":
                raise ValueError("Empty response from API")
            
            # Parse the JSON response
            parsed = gemini_client.parse_json_response(response)
            
            # Ensure all required keys exist
            required_keys = ["main_content", "key_information", "required_action", "design_quality", "friction_points"]
            for key in required_keys:
                if key not in parsed:
                    parsed[key] = "Not provided"
            
            return parsed
            
        except Exception as e:
            print(f"⚠️ Error analyzing view {view.view_id}: {e}")
            # Return a fallback that won't cause personas to drop off
            return {
                "main_content": "Health insurance onboarding screen with plan details and options",
                "key_information": "Insurance plan information, coverage details, and pricing options are displayed",
                "required_action": "Review the information and select plan options to continue",
                "design_quality": "Standard corporate health insurance interface with organized layout",
                "friction_points": "May contain multiple options requiring careful review"
            }
    
    def _build_persona_context(self, persona: EnrichedPersona) -> str:
        """Build rich context about the persona."""
        parts = []
        if persona.professional_persona:
            parts.append(persona.professional_persona[:300])
        if persona.cultural_background:
            parts.append(persona.cultural_background[:200])
        
        if not parts:
            parts.append(f"You work as a {persona.occupation} in {persona.district}. You're looking for good health insurance for yourself and potentially your family.")
        
        return " ".join(parts)
    
    def _infer_health_status(self, persona: EnrichedPersona) -> str:
        """Infer current health status (affects urgency in Utility Mode)."""
        # Check if persona has health condition info in professional_persona
        if persona.professional_persona:
            persona_text = persona.professional_persona.lower()
            # Keywords indicating health conditions
            condition_keywords = [
                'diabetes', 'hypertension', 'cholesterol', 'arthritis', 
                'thyroid', 'medication', 'chronic', 'pain', 'apnea',
                'doctor', 'treatment', 'checkup', 'monitoring'
            ]
            
            if any(keyword in persona_text for keyword in condition_keywords):
                # Has ongoing health condition
                if 'chronic' in persona_text or 'daily medication' in persona_text:
                    return "Needs_Care"
                else:
                    return "Minor_Concern"
            
            # Check for fitness keywords
            fitness_keywords = ['gym', 'exercise', 'fit', 'healthy', 'rarely falls sick']
            if any(keyword in persona_text for keyword in fitness_keywords):
                return "Healthy"
        
        # Fallback: age-based inference
        if persona.age < 30:
            return "Healthy"
        elif persona.age < 45:
            return "Minor_Concern"
        else:
            return "Needs_Care"
    
    def _infer_mindset_state(self, persona: EnrichedPersona, health_status: str) -> str:
        """Determine mindset based on Utility Mode framework."""
        if health_status == "Needs_Care":
            return "URGENT - Need medical care, will complete everything quickly"
        elif health_status == "Minor_Concern":
            return "ENGAGED - Somewhat motivated to understand coverage"
        else:
            # Healthy = Apathetic
            if "ceo" in persona.occupation.lower() or "director" in persona.occupation.lower():
                return "RUSHED - Will complete minimum to get card, no exploration"
            else:
                return "APATHETIC - Will complete signup for card, ignore extras"
    
    def _infer_time_pressure(self, persona: EnrichedPersona, view_number: int, health_status: str) -> str:
        """Calculate time pressure based on persona, journey, and health status."""
        # Health status overrides other factors
        if health_status == "Needs_Care":
            return "Low - Need this urgently, will take time needed"
        
        # Otherwise, executives are always rushed
        if "ceo" in persona.occupation.lower() or "director" in persona.occupation.lower():
            if view_number > 5:
                return "Very High - Too many steps, getting annoyed"
            return "High - Busy executive, want quick completion"
        
        # Regular employees have moderate patience
        if view_number > 6:
            return "High - This is taking too long for free insurance"
        elif view_number > 3:
            return "Moderate - Willing to complete but want it done"
        else:
            return "Low - Just started, patient for now"
    
    def _calculate_annual_ctc(self, monthly_income: int) -> str:
        """Convert monthly to annual CTC in LPA."""
        annual = (monthly_income * 12) / 100000
        if annual >= 100:
            return f"{annual/100:.1f}Cr"
        return f"{annual:.1f}"
    
    async def simulate_persona_journey(
        self,
        persona: EnrichedPersona,
        views: List[FlowView],
        view_analyses: Dict[str, Dict[str, str]]
    ) -> FlowSimulationResult:
        """Simulate a single persona's journey through all views."""
        
        decisions = []
        total_time = 0
        dropped_off_at = None
        drop_off_reason = None
        
        journey_history = []
        
        for view in views:
            # Build journey context
            if journey_history:
                journey_so_far = f"You've completed {len(journey_history)} view(s). " + " → ".join(journey_history)
            else:
                journey_so_far = "This is your first view in the onboarding flow."
            
            # Get view analysis
            view_analysis = view_analyses.get(view.view_id, {})
            view_description = f"""
Main Content: {view_analysis.get('main_content', 'Unknown')}
Key Information: {view_analysis.get('key_information', 'Unknown')}
What You Need To Do: {view_analysis.get('required_action', 'Unknown')}
Design Quality: {view_analysis.get('design_quality', 'Unknown')}
Potential Issues: {view_analysis.get('friction_points', 'Unknown')}
"""
            
            # Build persona context with Utility Mode priors
            persona_context = self._build_persona_context(persona)
            health_status = self._infer_health_status(persona)
            mindset_state = self._infer_mindset_state(persona, health_status)
            time_pressure = self._infer_time_pressure(persona, view.view_number, health_status)
            annual_ctc = self._calculate_annual_ctc(persona.monthly_income_inr)
            
            prompt = self.VIEW_DECISION_PROMPT.format(
                occupation=persona.occupation,
                age=persona.age,
                sex=persona.sex,
                district=persona.district,
                state=persona.state,
                education_level=persona.education_level,
                monthly_income_inr=persona.monthly_income_inr,
                annual_ctc=annual_ctc,
                persona_context=persona_context,
                digital_literacy=persona.digital_literacy,
                primary_device=persona.primary_device,
                health_status=health_status,
                mindset_state=mindset_state,
                time_pressure=time_pressure,
                view_number=view.view_number,
                view_name=view.view_name,
                view_description=view_description,
                journey_so_far=journey_so_far
            )
            
            try:
                response = await gemini_client.generate_flash(
                    prompt=prompt,
                    system_prompt=self.FLOW_SIMULATION_SYSTEM_PROMPT
                )
                decision_data = gemini_client.parse_json_response(response)
                
                decision = PersonaFlowDecision(
                    persona_uuid=persona.uuid,
                    view_id=view.view_id,
                    view_number=view.view_number,
                    step_type=decision_data.get("step_type", "MANDATORY"),
                    decision=decision_data.get("decision", "DROP_OFF"),
                    trust_score=decision_data.get("trust_score", 5),
                    clarity_score=decision_data.get("clarity_score", 5),
                    value_perception_score=decision_data.get("value_perception_score", 5),
                    inertia_override=decision_data.get("inertia_override", False),
                    urgency_factor=decision_data.get("urgency_factor", "low"),
                    reasoning=decision_data.get("reasoning", "No reason provided"),
                    emotional_state=decision_data.get("emotional_state", "apathetic"),
                    friction_points=decision_data.get("friction_points", []),
                    time_spent_seconds=decision_data.get("time_spent_seconds", 5)
                )
                
                decisions.append(decision)
                total_time += decision.time_spent_seconds
                
                # Update journey history
                journey_history.append(f"View {view.view_number}")
                
                # Check if dropped off
                if decision.decision == "DROP_OFF":
                    dropped_off_at = view.view_number
                    drop_off_reason = decision.reasoning
                    break
                
            except Exception as e:
                print(f"⚠️ Error simulating persona {persona.uuid[:8]} at view {view.view_number}: {e}")
                # Create fallback decision (drop off due to error)
                decision = PersonaFlowDecision(
                    persona_uuid=persona.uuid,
                    view_id=view.view_id,
                    view_number=view.view_number,
                    step_type="MANDATORY",
                    decision="DROP_OFF",
                    trust_score=5,
                    clarity_score=5,
                    value_perception_score=5,
                    inertia_override=False,
                    urgency_factor="low",
                    reasoning="Technical error in simulation",
                    emotional_state="confused",
                    friction_points=["Simulation error"],
                    time_spent_seconds=5
                )
                decisions.append(decision)
                dropped_off_at = view.view_number
                drop_off_reason = "Simulation error"
                break
        
        completed = dropped_off_at is None
        
        return FlowSimulationResult(
            persona_uuid=persona.uuid,
            total_views_seen=len(decisions),
            dropped_off_at_view=dropped_off_at,
            completed_flow=completed,
            decisions=decisions,
            total_time_seconds=total_time,
            drop_off_reason=drop_off_reason
        )


async def main():
    """Main execution for Loop Health flow simulation."""
    
    print("\n" + "="*80)
    print("🏥 LOOP HEALTH - PRODUCT FLOW SIMULATOR")
    print("="*80)
    print("Simulating corporate employees going through onboarding flow")
    print("="*80)
    
    start_time = time.time()
    
    # STEP 1: Load product flow views
    print("\n📸 STEP 1: Loading Product Flow Views...")
    product_flow_dir = Path(__file__).parent / "product_flow"
    view_files = sorted(product_flow_dir.glob("*.png"))
    
    if len(view_files) < 8:
        print(f"❌ Expected 8 views, found only {len(view_files)}")
        return
    
    views = []
    for i, view_file in enumerate(view_files[:8], 1):  # Take first 8
        views.append(FlowView(
            view_id=f"view_{i}",
            view_number=i,
            view_name=f"View {i}",
            image_path=str(view_file),
            description=f"Onboarding view {i} from {view_file.name}"
        ))
    
    print(f"✅ Loaded {len(views)} views from product flow")
    for view in views:
        print(f"   • {view.view_id}: {view.image_path}")
    
    # STEP 2: Generate Segmented Personas (10 young & fit + 10 older with health conditions)
    print("\n👥 STEP 2: Generating Segmented Corporate Employee Personas...")
    raw_personas = LoopHealthPersonaFilter.generate_segmented_personas()
    print(f"✅ Generated {len(raw_personas)} segmented personas (10 young & fit, 10 older with health conditions)")
    
    # STEP 3: Hydrate personas
    print("\n💧 STEP 3: Hydrating Personas...")
    enriched_personas = await persona_hydrator.hydrate_batch(raw_personas)
    print(f"✅ Enriched {len(enriched_personas)} personas")
    
    # Save enriched personas
    loop_data_dir = DATA_DIR / "loop_health"
    loop_data_dir.mkdir(exist_ok=True)
    
    with open(loop_data_dir / "enriched_personas.json", 'w') as f:
        json.dump([p.model_dump() for p in enriched_personas], f, indent=2)
    
    # STEP 4: Analyze all views visually
    print("\n🎨 STEP 4: Analyzing Flow Views...")
    simulator = LoopHealthFlowSimulator()
    
    view_analysis_tasks = [simulator.analyze_view_visual(view) for view in views]
    view_analyses_list = await tqdm.gather(*view_analysis_tasks, desc="Analyzing views")
    view_analyses = {views[i].view_id: analysis for i, analysis in enumerate(view_analyses_list)}
    
    print(f"✅ Analyzed {len(views)} views")
    
    # Save view analyses
    with open(loop_data_dir / "view_analyses.json", 'w') as f:
        json.dump(view_analyses, f, indent=2)
    
    # STEP 5: Run flow simulation for all personas
    print("\n🎬 STEP 5: Running Flow Simulations...")
    print(f"   Simulating {len(enriched_personas)} personas × {len(views)} views (max)")
    
    simulation_tasks = [
        simulator.simulate_persona_journey(persona, views, view_analyses)
        for persona in enriched_personas
    ]
    
    results = await tqdm.gather(*simulation_tasks, desc="Simulating journeys")
    
    print(f"\n✅ Completed {len(results)} persona journeys")
    
    # STEP 6: Analyze results
    print("\n📊 STEP 6: Analyzing Flow Performance...")
    print("="*80)
    
    completed = sum(1 for r in results if r.completed_flow)
    dropped = len(results) - completed
    completion_rate = (completed / len(results)) * 100
    
    print(f"\n🎯 OVERALL METRICS:")
    print(f"   Total Personas: {len(results)}")
    print(f"   Completed Flow: {completed} ({completion_rate:.1f}%)")
    print(f"   Dropped Off: {dropped} ({100-completion_rate:.1f}%)")
    
    # Drop-off analysis by view
    print(f"\n📉 DROP-OFF ANALYSIS BY VIEW:")
    drop_off_by_view = {}
    for r in results:
        if r.dropped_off_at_view:
            drop_off_by_view[r.dropped_off_at_view] = drop_off_by_view.get(r.dropped_off_at_view, 0) + 1
    
    for view_num in sorted(drop_off_by_view.keys()):
        count = drop_off_by_view[view_num]
        percentage = (count / len(results)) * 100
        print(f"   View {view_num}: {count} personas ({percentage:.1f}%)")
    
    # View-by-view progression
    print(f"\n📈 PROGRESSION FUNNEL:")
    for i in range(1, 9):
        reached = sum(1 for r in results if r.total_views_seen >= i)
        percentage = (reached / len(results)) * 100
        print(f"   View {i}: {reached}/{len(results)} personas ({percentage:.1f}%)")
    
    # Average scores per view
    print(f"\n⭐ AVERAGE SCORES BY VIEW:")
    for view in views:
        decisions_at_view = [d for r in results for d in r.decisions if d.view_id == view.view_id]
        if decisions_at_view:
            avg_clarity = sum(d.clarity_score for d in decisions_at_view) / len(decisions_at_view)
            avg_value = sum(d.value_perception_score for d in decisions_at_view) / len(decisions_at_view)
            avg_trust = sum(d.trust_score for d in decisions_at_view) / len(decisions_at_view)
            print(f"   View {view.view_number}:")
            print(f"      Clarity: {avg_clarity:.1f}/10 | Value: {avg_value:.1f}/10 | Trust: {avg_trust:.1f}/10")
    
    # Utility Mode Analysis: Mandatory vs Optional
    print(f"\n🎯 UTILITY MODE ANALYSIS:")
    mandatory_steps = [d for r in results for d in r.decisions if d.step_type == "MANDATORY"]
    optional_steps = [d for r in results for d in r.decisions if d.step_type == "OPTIONAL"]
    
    if mandatory_steps:
        mandatory_continues = sum(1 for d in mandatory_steps if d.decision == "CONTINUE")
        mandatory_rate = (mandatory_continues / len(mandatory_steps)) * 100
        print(f"   📋 Mandatory Steps: {mandatory_continues}/{len(mandatory_steps)} continued ({mandatory_rate:.1f}%)")
    
    if optional_steps:
        optional_continues = sum(1 for d in optional_steps if d.decision == "CONTINUE")
        optional_rate = (optional_continues / len(optional_steps)) * 100
        inertia_overrides = sum(1 for d in optional_steps if d.inertia_override)
        print(f"   🎁 Optional Steps: {optional_continues}/{len(optional_steps)} continued ({optional_rate:.1f}%)")
        print(f"   ⚡ Inertia Overridden: {inertia_overrides}/{len(optional_steps)} times ({(inertia_overrides/len(optional_steps)*100):.1f}%)")
    
    # Common drop-off reasons
    print(f"\n💡 COMMON DROP-OFF REASONS:")
    drop_off_reasons = [r.drop_off_reason for r in results if r.drop_off_reason]
    for i, reason in enumerate(drop_off_reasons[:5], 1):
        print(f"   {i}. {reason}")
    
    # STEP 7: Generate Dashboard-Ready Reports
    print("\n💾 STEP 7: Generating Dashboard-Ready Reports...")
    
    # Build comprehensive report for dashboard
    persona_map = {p.uuid: p for p in enriched_personas}
    
    # Calculate view performance metrics (similar to ad performance)
    view_performance = {}
    for view in views:
        view_decisions = [d for r in results for d in r.decisions if d.view_id == view.view_id]
        if view_decisions:
            continues = sum(1 for d in view_decisions if d.decision == "CONTINUE")
            mandatory_steps = [d for d in view_decisions if d.step_type == "MANDATORY"]
            optional_steps = [d for d in view_decisions if d.step_type == "OPTIONAL"]
            
            view_performance[view.view_id] = {
                "view_number": view.view_number,
                "view_name": view.view_name,
                "total_views": len(view_decisions),
                "continues": continues,
                "drop_offs": len(view_decisions) - continues,
                "continue_rate": round((continues / len(view_decisions)) * 100, 2),
                "avg_clarity": round(sum(d.clarity_score for d in view_decisions) / len(view_decisions), 2),
                "avg_value": round(sum(d.value_perception_score for d in view_decisions) / len(view_decisions), 2),
                "avg_trust": round(sum(d.trust_score for d in view_decisions) / len(view_decisions), 2),
                "avg_time_spent": round(sum(d.time_spent_seconds for d in view_decisions) / len(view_decisions), 1),
                "step_type_breakdown": {
                    "mandatory_count": len(mandatory_steps),
                    "optional_count": len(optional_steps),
                    "mandatory_continue_rate": round((sum(1 for d in mandatory_steps if d.decision == "CONTINUE") / len(mandatory_steps) * 100), 2) if mandatory_steps else 0,
                    "optional_continue_rate": round((sum(1 for d in optional_steps if d.decision == "CONTINUE") / len(optional_steps) * 100), 2) if optional_steps else 0
                },
                "inertia_overrides": sum(1 for d in view_decisions if d.inertia_override),
                "common_emotional_states": {}
            }
            
            # Count emotional states
            emotional_counts = {}
            for d in view_decisions:
                emotional_counts[d.emotional_state] = emotional_counts.get(d.emotional_state, 0) + 1
            view_performance[view.view_id]["common_emotional_states"] = emotional_counts
    
    # Segment analysis: Young & Fit vs Older with Health Conditions
    segment_analysis = {
        "young_fit": {"age_range": "20-30", "personas": [], "metrics": {}},
        "older_health_conditions": {"age_range": "40+", "personas": [], "metrics": {}}
    }
    
    for persona in enriched_personas:
        if persona.age <= 30:
            segment = "young_fit"
        else:
            segment = "older_health_conditions"
        
        segment_analysis[segment]["personas"].append({
            "uuid": persona.uuid,
            "occupation": persona.occupation,
            "age": persona.age,
            "health_context": persona.professional_persona if persona.professional_persona else "No health info"
        })
    
    # Calculate segment metrics
    for segment_key in ["young_fit", "older_health_conditions"]:
        segment_personas = [p["uuid"] for p in segment_analysis[segment_key]["personas"]]
        segment_results = [r for r in results if r.persona_uuid in segment_personas]
        
        if segment_results:
            segment_analysis[segment_key]["metrics"] = {
                "total_personas": len(segment_personas),
                "completed_flow": sum(1 for r in segment_results if r.completed_flow),
                "completion_rate": round((sum(1 for r in segment_results if r.completed_flow) / len(segment_results)) * 100, 2),
                "avg_views_seen": round(sum(r.total_views_seen for r in segment_results) / len(segment_results), 1),
                "avg_time_spent": round(sum(r.total_time_seconds for r in segment_results) / len(segment_results), 1),
                "common_drop_off_views": {}
            }
            
            # Common drop-off points
            drop_offs = {}
            for r in segment_results:
                if r.dropped_off_at_view:
                    drop_offs[r.dropped_off_at_view] = drop_offs.get(r.dropped_off_at_view, 0) + 1
            segment_analysis[segment_key]["metrics"]["common_drop_off_views"] = drop_offs
    
    # Utility Mode specific metrics
    all_decisions = [d for r in results for d in r.decisions]
    utility_mode_metrics = {
        "mandatory_steps": {
            "total": len([d for d in all_decisions if d.step_type == "MANDATORY"]),
            "continued": len([d for d in all_decisions if d.step_type == "MANDATORY" and d.decision == "CONTINUE"]),
            "continue_rate": 0
        },
        "optional_steps": {
            "total": len([d for d in all_decisions if d.step_type == "OPTIONAL"]),
            "continued": len([d for d in all_decisions if d.step_type == "OPTIONAL" and d.decision == "CONTINUE"]),
            "continue_rate": 0
        },
        "inertia_analysis": {
            "total_optional_steps": len([d for d in all_decisions if d.step_type == "OPTIONAL"]),
            "inertia_overridden": len([d for d in all_decisions if d.step_type == "OPTIONAL" and d.inertia_override]),
            "override_rate": 0
        },
        "urgency_distribution": {},
        "emotional_state_distribution": {}
    }
    
    # Calculate rates
    if utility_mode_metrics["mandatory_steps"]["total"] > 0:
        utility_mode_metrics["mandatory_steps"]["continue_rate"] = round(
            (utility_mode_metrics["mandatory_steps"]["continued"] / utility_mode_metrics["mandatory_steps"]["total"]) * 100, 2
        )
    
    if utility_mode_metrics["optional_steps"]["total"] > 0:
        utility_mode_metrics["optional_steps"]["continue_rate"] = round(
            (utility_mode_metrics["optional_steps"]["continued"] / utility_mode_metrics["optional_steps"]["total"]) * 100, 2
        )
    
    if utility_mode_metrics["inertia_analysis"]["total_optional_steps"] > 0:
        utility_mode_metrics["inertia_analysis"]["override_rate"] = round(
            (utility_mode_metrics["inertia_analysis"]["inertia_overridden"] / utility_mode_metrics["inertia_analysis"]["total_optional_steps"]) * 100, 2
        )
    
    # Urgency and emotional state distributions
    urgency_counts = {}
    emotional_counts = {}
    for d in all_decisions:
        urgency_counts[d.urgency_factor] = urgency_counts.get(d.urgency_factor, 0) + 1
        emotional_counts[d.emotional_state] = emotional_counts.get(d.emotional_state, 0) + 1
    
    utility_mode_metrics["urgency_distribution"] = urgency_counts
    utility_mode_metrics["emotional_state_distribution"] = emotional_counts
    
    # Build final dashboard report
    dashboard_report = {
        "metadata": {
            "simulation_type": "product_flow",
            "product": "Loop Health",
            "framework": "Utility Mode (B2B2C)",
            "total_personas": len(enriched_personas),
            "total_views": len(views),
            "execution_time_seconds": round(time.time() - start_time, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "overall_metrics": {
            "total_personas": len(results),
            "completed_flow": sum(1 for r in results if r.completed_flow),
            "dropped_off": sum(1 for r in results if not r.completed_flow),
            "completion_rate": round((sum(1 for r in results if r.completed_flow) / len(results)) * 100, 2),
            "avg_views_seen": round(sum(r.total_views_seen for r in results) / len(results), 1),
            "avg_time_spent": round(sum(r.total_time_seconds for r in results) / len(results), 1)
        },
        "view_performance": view_performance,
        "segment_analysis": segment_analysis,
        "utility_mode_metrics": utility_mode_metrics,
        "drop_off_analysis": {
            "by_view": {},
            "common_reasons": []
        },
        "personas": [
            {
                "uuid": p.uuid,
                "occupation": p.occupation,
                "age": p.age,
                "segment": "young_fit" if p.age <= 30 else "older_health_conditions",
                "health_context": p.professional_persona[:100] if p.professional_persona else "N/A",
                "digital_literacy": p.digital_literacy,
                "monthly_income": p.monthly_income_inr,
                "journey": next((r for r in results if r.persona_uuid == p.uuid), None).model_dump() if any(r.persona_uuid == p.uuid for r in results) else None
            }
            for p in enriched_personas
        ]
    }
    
    # Drop-off analysis
    drop_off_by_view = {}
    for r in results:
        if r.dropped_off_at_view:
            drop_off_by_view[r.dropped_off_at_view] = drop_off_by_view.get(r.dropped_off_at_view, 0) + 1
    dashboard_report["drop_off_analysis"]["by_view"] = drop_off_by_view
    dashboard_report["drop_off_analysis"]["common_reasons"] = [r.drop_off_reason for r in results if r.drop_off_reason][:10]
    
    # Save dashboard report
    with open(loop_data_dir / "dashboard_report.json", 'w') as f:
        json.dump(dashboard_report, f, indent=2)
    print(f"   ✅ Dashboard report: dashboard_report.json")
    
    # Save detailed results
    with open(loop_data_dir / "simulation_results.json", 'w') as f:
        json.dump([r.model_dump() for r in results], f, indent=2)
    print(f"   ✅ Detailed results: simulation_results.json")
    
    # Create summary report
    summary = {
        "metadata": {
            "total_personas": len(results),
            "total_views": len(views),
            "execution_time_seconds": round(time.time() - start_time, 2)
        },
        "overall_metrics": {
            "completed_flow": completed,
            "dropped_off": dropped,
            "completion_rate": round(completion_rate, 2)
        },
        "drop_off_by_view": drop_off_by_view,
        "view_scores": {
            view.view_id: {
                "view_number": view.view_number,
                "clarity_score": round(sum(d.clarity_score for r in results for d in r.decisions if d.view_id == view.view_id) / max(sum(1 for r in results for d in r.decisions if d.view_id == view.view_id), 1), 2),
                "value_score": round(sum(d.value_perception_score for r in results for d in r.decisions if d.view_id == view.view_id) / max(sum(1 for r in results for d in r.decisions if d.view_id == view.view_id), 1), 2),
                "trust_score": round(sum(d.trust_score for r in results for d in r.decisions if d.view_id == view.view_id) / max(sum(1 for r in results for d in r.decisions if d.view_id == view.view_id), 1), 2)
            }
            for view in views
        }
    }
    
    with open(loop_data_dir / "summary_report.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create human-readable report
    with open(loop_data_dir / "flow_report.txt", 'w') as f:
        f.write("="*80 + "\n")
        f.write("LOOP HEALTH - PRODUCT FLOW SIMULATION REPORT\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Total Personas Simulated: {len(results)}\n")
        f.write(f"Completion Rate: {completion_rate:.1f}%\n")
        f.write(f"Execution Time: {summary['metadata']['execution_time_seconds']} seconds\n\n")
        
        f.write("="*80 + "\n")
        f.write("DROP-OFF FUNNEL\n")
        f.write("="*80 + "\n\n")
        for i in range(1, 9):
            reached = sum(1 for r in results if r.total_views_seen >= i)
            percentage = (reached / len(results)) * 100
            bar = "█" * int(percentage / 2)
            f.write(f"View {i}: {bar} {reached}/{len(results)} ({percentage:.1f}%)\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("PERSONA JOURNEYS\n")
        f.write("="*80 + "\n\n")
        
        persona_map = {p.uuid: p for p in enriched_personas}
        for i, result in enumerate(results, 1):
            persona = persona_map[result.persona_uuid]
            f.write(f"\nPERSONA {i}: {persona.occupation}, {persona.age}yo, {persona.district}\n")
            f.write(f"{'-'*80}\n")
            f.write(f"Status: {'✅ COMPLETED' if result.completed_flow else f'❌ DROPPED OFF at View {result.dropped_off_at_view}'}\n")
            f.write(f"Total Time: {result.total_time_seconds} seconds\n")
            f.write(f"Views Seen: {result.total_views_seen}/8\n\n")
            
            for decision in result.decisions:
                f.write(f"  View {decision.view_number}: {decision.decision} ({decision.step_type})\n")
                f.write(f"    Scores: Clarity {decision.clarity_score}/10 | Value {decision.value_perception_score}/10 | Trust {decision.trust_score}/10\n")
                f.write(f"    Utility Mode: Inertia Override={decision.inertia_override} | Urgency={decision.urgency_factor}\n")
                f.write(f"    Reasoning: {decision.reasoning}\n")
                f.write(f"    Emotional State: {decision.emotional_state}\n")
                if decision.friction_points:
                    f.write(f"    Friction: {', '.join(decision.friction_points)}\n")
                f.write(f"\n")
    
    print(f"✅ Results saved to: {loop_data_dir}")
    print(f"   • dashboard_report.json - ⭐ DASHBOARD-READY (for frontend)")
    print(f"   • simulation_results.json - Detailed journey data")
    print(f"   • enriched_personas.json - Persona profiles with health status")
    print(f"   • view_analyses.json - View visual analyses")
    print(f"   • summary_report.json - Quick summary metrics")
    print(f"   • flow_report.txt - Human-readable report")
    
    print("\n" + "="*80)
    print("🎉 SIMULATION COMPLETE!")
    print("="*80)
    print(f"\n⏱️  Execution Time: {dashboard_report['metadata']['execution_time_seconds']} seconds")
    print(f"\n📊 Overall Completion Rate: {dashboard_report['overall_metrics']['completion_rate']}%")
    
    # Segment comparison
    print(f"\n👥 SEGMENT COMPARISON:")
    for segment_key, segment_name in [("young_fit", "Young & Fit (20-30)"), ("older_health_conditions", "Older with Health Conditions (40+)")]:
        segment = dashboard_report['segment_analysis'][segment_key]
        metrics = segment['metrics']
        print(f"   {segment_name}:")
        print(f"      Completion Rate: {metrics['completion_rate']}%")
        print(f"      Avg Views Seen: {metrics['avg_views_seen']}/8")
        print(f"      Avg Time Spent: {metrics['avg_time_spent']}s")
    
    # Utility Mode summary
    utility = dashboard_report['utility_mode_metrics']
    print(f"\n⚡ UTILITY MODE METRICS:")
    print(f"   Mandatory Steps: {utility['mandatory_steps']['continue_rate']}% completion")
    print(f"   Optional Steps: {utility['optional_steps']['continue_rate']}% completion")
    print(f"   Inertia Override Rate: {utility['inertia_analysis']['override_rate']}%")
    
    if drop_off_by_view:
        highest_dropout_view = max(drop_off_by_view.items(), key=lambda x: x[1])
        print(f"\n⚠️  Highest Drop-off: View {highest_dropout_view[0]} ({highest_dropout_view[1]} personas)")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
