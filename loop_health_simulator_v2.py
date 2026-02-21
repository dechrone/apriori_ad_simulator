"""Loop Health Product Flow Simulator V2 - ENHANCED MODEL with Advanced Behavioral Priors."""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from tqdm.asyncio import tqdm
import random

from src.data.loader import data_loader
from src.core.persona_hydrator import persona_hydrator
from src.api.gemini_client import gemini_client
from src.utils.schemas import RawPersona, EnrichedPersona
from src.utils.config import DATA_DIR
from pydantic import BaseModel, Field


class HealthProfile(BaseModel):
    """Enhanced health profile with more nuanced data."""
    status: str  # "Excellent", "Good", "Fair", "Poor"
    ongoing_conditions: List[str] = []
    recent_health_events: List[str] = []  # "hospital_visit_3mo", "surgery_1yr", etc.
    medication_count: int = 0
    doctor_visit_frequency: str  # "never", "yearly", "quarterly", "monthly"
    health_anxiety_level: str  # "low", "medium", "high"
    fitness_level: str  # "sedentary", "moderate", "active", "very_active"
    bmi_category: str  # "underweight", "normal", "overweight", "obese"
    family_health_history: List[str] = []  # Inherited conditions
    

class FamilyProfile(BaseModel):
    """Family and dependents information."""
    marital_status: str
    has_children: bool = False
    children_count: int = 0
    children_ages: List[int] = []
    has_aging_parents: bool = False
    parent_health_concerns: bool = False
    spouse_employed: bool = False
    spouse_has_insurance: bool = False
    family_size_total: int = 1
    primary_health_decision_maker: bool = True
    

class BehavioralProfile(BaseModel):
    """Advanced behavioral characteristics."""
    inertia_level: int = Field(ge=0, le=10, description="0=highly motivated, 10=extremely lazy")
    decision_speed: str  # "impulsive", "quick", "deliberate", "slow"
    research_intensity: str  # "minimal", "moderate", "thorough", "obsessive"
    peer_influence_susceptibility: float = Field(ge=0, le=1)  # How much peers matter
    authority_trust: float = Field(ge=0, le=1)  # Trust in employer/authorities
    loss_aversion_strength: float = Field(ge=0, le=1)  # Fear of missing out
    gamification_response: float = Field(ge=0, le=1)  # Response to rewards/badges
    social_proof_sensitivity: float = Field(ge=0, le=1)  # "Others are doing it"
    urgency_response: float = Field(ge=0, le=1)  # Response to deadlines
    financial_anxiety: float = Field(ge=0, le=1)  # Worry about costs
    

class ContextualFactors(BaseModel):
    """Environmental and temporal factors."""
    season: str = "regular"  # "flu_season", "year_end", "new_year", "regular"
    work_culture: str = "corporate"  # "startup", "corporate", "mnc", "psu"
    recent_life_events: List[str] = []  # "new_baby", "wedding", "promotion", "layoff"
    insurance_experience: str = "neutral"  # "positive", "neutral", "negative", "none"
    previous_claim_experience: str = "none"  # "smooth", "difficult", "rejected", "none"
    time_in_company: str = "established"  # "new_joiner", "established", "long_term"
    job_security: str = "secure"  # "secure", "uncertain", "at_risk"
    

class EnhancedPersona(BaseModel):
    """Enhanced persona with rich behavioral and contextual data."""
    # Base data
    uuid: str
    occupation: str
    age: int
    sex: str
    state: str
    district: str
    education_level: str
    monthly_income_inr: int
    digital_literacy: int
    primary_device: str
    
    # Enhanced profiles
    health_profile: HealthProfile
    family_profile: FamilyProfile
    behavioral_profile: BehavioralProfile
    contextual_factors: ContextualFactors
    
    # Calculated scores
    health_urgency_score: float = Field(ge=0, le=10)  # Overall health urgency
    engagement_likelihood: float = Field(ge=0, le=1)  # Predicted engagement
    value_sensitivity: float = Field(ge=0, le=1)  # How much value matters
    feature_exploration_probability: float = Field(ge=0, le=1)  # Will they explore
    

class FlowView(BaseModel):
    """Represents a single view in the onboarding flow."""
    view_id: str
    view_number: int
    view_name: str
    image_path: str
    description: str = ""
    intervention_applied: Optional[str] = None  # "social_proof", "urgency", "incentive", None
    

class EnhancedFlowDecision(BaseModel):
    """Enhanced decision with more detailed tracking."""
    persona_uuid: str
    view_id: str
    view_number: int
    step_type: str = "MANDATORY"
    decision: str
    
    # Scores
    trust_score: int = Field(ge=0, le=10)
    clarity_score: int = Field(ge=0, le=10)
    value_perception_score: int = Field(ge=0, le=10)
    
    # Advanced behavioral tracking
    inertia_override: bool = False
    urgency_factor: str = "low"
    emotional_state: str
    cognitive_load: str = "low"  # "low", "medium", "high", "overwhelming"
    attention_level: str = "focused"  # "distracted", "partial", "focused", "engaged"
    
    # Intervention response
    intervention_present: Optional[str] = None
    intervention_effectiveness: Optional[float] = None  # 0-1
    
    # Decision factors
    primary_decision_driver: str = ""  # What made them continue/drop
    hesitation_points: List[str] = []
    positive_triggers: List[str] = []
    friction_points: List[str] = []
    
    # Context
    time_spent_seconds: int = 5
    revisit_count: int = 0  # Did they come back to this view?
    reasoning: str = ""
    
    # Predictions
    likelihood_to_use_feature: Optional[float] = None  # If they continue, will they use it?
    

class EnhancedSimulationResult(BaseModel):
    """Complete enhanced journey with predictions."""
    persona_uuid: str
    total_views_seen: int
    dropped_off_at_view: Optional[int] = None
    completed_flow: bool
    decisions: List[EnhancedFlowDecision]
    total_time_seconds: int
    drop_off_reason: Optional[str] = None
    
    # Enhanced tracking
    engagement_quality: str = "low"  # "low", "medium", "high"
    feature_adoption_predictions: Dict[str, float] = {}  # {"wellness": 0.3, "opd": 0.7}
    likely_claim_user: bool = False
    retention_risk: str = "low"  # "low", "medium", "high"
    recommended_interventions: List[str] = []
    

class EnhancedPersonaGenerator:
    """Generate 20 diverse personas with rich profiles."""
    
    @staticmethod
    def generate_diverse_personas() -> List[EnhancedPersona]:
        """Generate 20 highly diverse personas across all dimensions."""
        
        print("\n" + "="*80)
        print("🎯 GENERATING 20 HIGHLY DIVERSE PERSONAS - ENHANCED MODEL")
        print("="*80)
        
        personas = []
        
        # SEGMENT 1: Young & Healthy (Ages 22-30) - 6 personas
        print("\n📱 SEGMENT 1: Young & Healthy Professionals (22-30) - 6 personas")
        print("-"*80)
        
        young_profiles = [
            {
                "occupation": "Software Engineer",
                "age": 24,
                "sex": "Male",
                "income": 75000,
                "district": "Bengaluru",
                "state": "Karnataka",
                "health": HealthProfile(
                    status="Excellent",
                    ongoing_conditions=[],
                    recent_health_events=[],
                    medication_count=0,
                    doctor_visit_frequency="never",
                    health_anxiety_level="low",
                    fitness_level="very_active",
                    bmi_category="normal",
                    family_health_history=[]
                ),
                "family": FamilyProfile(
                    marital_status="Never Married",
                    has_children=False,
                    family_size_total=1,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=9,  # Very lazy
                    decision_speed="impulsive",
                    research_intensity="minimal",
                    peer_influence_susceptibility=0.7,
                    authority_trust=0.5,
                    loss_aversion_strength=0.3,
                    gamification_response=0.8,  # Loves games/challenges
                    social_proof_sensitivity=0.7,
                    urgency_response=0.4,
                    financial_anxiety=0.3
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="startup",
                    recent_life_events=[],
                    insurance_experience="none",
                    previous_claim_experience="none",
                    time_in_company="new_joiner",
                    job_security="secure"
                ),
                "education": "Graduate",
                "digital_literacy": 9,
                "device": "Android"
            },
            {
                "occupation": "Product Manager",
                "age": 28,
                "sex": "Female",
                "income": 120000,
                "district": "Gurgaon",
                "state": "Delhi",
                "health": HealthProfile(
                    status="Good",
                    ongoing_conditions=["Mild Anxiety"],
                    recent_health_events=["therapy_started_6mo"],
                    medication_count=1,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="active",
                    bmi_category="normal",
                    family_health_history=["Diabetes in family"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=False,
                    spouse_employed=True,
                    spouse_has_insurance=True,
                    family_size_total=2,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=5,  # Moderate
                    decision_speed="deliberate",
                    research_intensity="thorough",
                    peer_influence_susceptibility=0.5,
                    authority_trust=0.7,
                    loss_aversion_strength=0.6,
                    gamification_response=0.4,
                    social_proof_sensitivity=0.6,
                    urgency_response=0.7,
                    financial_anxiety=0.4
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=["wedding"],
                    insurance_experience="neutral",
                    previous_claim_experience="none",
                    time_in_company="established",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 9,
                "device": "iPhone"
            },
            {
                "occupation": "Data Analyst",
                "age": 26,
                "sex": "Male",
                "income": 60000,
                "district": "Pune",
                "state": "Maharashtra",
                "health": HealthProfile(
                    status="Good",
                    ongoing_conditions=[],
                    recent_health_events=[],
                    medication_count=0,
                    doctor_visit_frequency="yearly",
                    health_anxiety_level="low",
                    fitness_level="moderate",
                    bmi_category="overweight",
                    family_health_history=["Hypertension in family"]
                ),
                "family": FamilyProfile(
                    marital_status="Never Married",
                    has_children=False,
                    family_size_total=1,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=8,
                    decision_speed="slow",
                    research_intensity="obsessive",  # Analyst mindset
                    peer_influence_susceptibility=0.3,
                    authority_trust=0.6,
                    loss_aversion_strength=0.7,
                    gamification_response=0.3,
                    social_proof_sensitivity=0.4,
                    urgency_response=0.5,
                    financial_anxiety=0.6  # Lower income
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=[],
                    insurance_experience="neutral",
                    previous_claim_experience="none",
                    time_in_company="established",
                    job_security="secure"
                ),
                "education": "Graduate",
                "digital_literacy": 9,
                "device": "Android"
            },
            {
                "occupation": "Marketing Executive",
                "age": 25,
                "sex": "Female",
                "income": 55000,
                "district": "Mumbai",
                "state": "Maharashtra",
                "health": HealthProfile(
                    status="Excellent",
                    ongoing_conditions=[],
                    recent_health_events=[],
                    medication_count=0,
                    doctor_visit_frequency="never",
                    health_anxiety_level="low",
                    fitness_level="active",
                    bmi_category="normal",
                    family_health_history=[]
                ),
                "family": FamilyProfile(
                    marital_status="Never Married",
                    has_children=False,
                    family_size_total=1,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=7,
                    decision_speed="quick",
                    research_intensity="minimal",
                    peer_influence_susceptibility=0.9,  # Very high - marketing person
                    authority_trust=0.6,
                    loss_aversion_strength=0.4,
                    gamification_response=0.7,
                    social_proof_sensitivity=0.9,  # Very sensitive
                    urgency_response=0.6,
                    financial_anxiety=0.5
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="startup",
                    recent_life_events=[],
                    insurance_experience="none",
                    previous_claim_experience="none",
                    time_in_company="new_joiner",
                    job_security="uncertain"  # Startup
                ),
                "education": "Graduate",
                "digital_literacy": 8,
                "device": "iPhone"
            },
            {
                "occupation": "Business Analyst",
                "age": 29,
                "sex": "Male",
                "income": 85000,
                "district": "Hyderabad",
                "state": "Telangana",
                "health": HealthProfile(
                    status="Fair",
                    ongoing_conditions=["Lower Back Pain"],
                    recent_health_events=["physiotherapy_2mo"],
                    medication_count=1,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="sedentary",
                    bmi_category="overweight",
                    family_health_history=[]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=1,
                    children_ages=[1],
                    family_size_total=3,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=6,
                    decision_speed="deliberate",
                    research_intensity="thorough",
                    peer_influence_susceptibility=0.4,
                    authority_trust=0.7,
                    loss_aversion_strength=0.7,  # Has family
                    gamification_response=0.3,
                    social_proof_sensitivity=0.5,
                    urgency_response=0.6,
                    financial_anxiety=0.6  # New baby
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=["new_baby"],
                    insurance_experience="neutral",
                    previous_claim_experience="smooth",
                    time_in_company="established",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 8,
                "device": "Android"
            },
            {
                "occupation": "UI/UX Designer",
                "age": 27,
                "sex": "Female",
                "income": 70000,
                "district": "Bengaluru",
                "state": "Karnataka",
                "health": HealthProfile(
                    status="Good",
                    ongoing_conditions=["PCOS"],
                    recent_health_events=["gynec_visit_1mo"],
                    medication_count=2,
                    doctor_visit_frequency="monthly",
                    health_anxiety_level="high",  # Women's health concerns
                    fitness_level="moderate",
                    bmi_category="normal",
                    family_health_history=["Thyroid in family"]
                ),
                "family": FamilyProfile(
                    marital_status="Never Married",
                    has_children=False,
                    family_size_total=1,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=4,  # Lower due to health concern
                    decision_speed="deliberate",
                    research_intensity="thorough",
                    peer_influence_susceptibility=0.6,
                    authority_trust=0.6,
                    loss_aversion_strength=0.7,
                    gamification_response=0.5,
                    social_proof_sensitivity=0.7,
                    urgency_response=0.7,
                    financial_anxiety=0.5
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="startup",
                    recent_life_events=[],
                    insurance_experience="neutral",
                    previous_claim_experience="none",
                    time_in_company="established",
                    job_security="secure"
                ),
                "education": "Graduate",
                "digital_literacy": 9,
                "device": "iPhone"
            }
        ]
        
        # SEGMENT 2: Mid-Career (Ages 32-40) - 7 personas
        print("\n💼 SEGMENT 2: Mid-Career Professionals (32-40) - 7 personas")
        print("-"*80)
        
        mid_career_profiles = [
            {
                "occupation": "Senior Software Engineer",
                "age": 34,
                "sex": "Male",
                "income": 150000,
                "district": "Bengaluru",
                "state": "Karnataka",
                "health": HealthProfile(
                    status="Fair",
                    ongoing_conditions=["Pre-diabetes", "High Cholesterol"],
                    recent_health_events=["blood_test_1mo", "cardiologist_visit_3mo"],
                    medication_count=2,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="high",
                    fitness_level="sedentary",
                    bmi_category="obese",
                    family_health_history=["Diabetes", "Heart Disease"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=2,
                    children_ages=[5, 2],
                    family_size_total=4,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=3,  # Health scare reduces inertia
                    decision_speed="deliberate",
                    research_intensity="thorough",
                    peer_influence_susceptibility=0.3,
                    authority_trust=0.8,
                    loss_aversion_strength=0.9,  # Very high - family + health
                    gamification_response=0.2,
                    social_proof_sensitivity=0.4,
                    urgency_response=0.8,
                    financial_anxiety=0.5
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="mnc",
                    recent_life_events=["health_scare"],
                    insurance_experience="positive",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 9,
                "device": "iPhone"
            },
            {
                "occupation": "Engineering Manager",
                "age": 37,
                "sex": "Male",
                "income": 200000,
                "district": "Gurgaon",
                "state": "Delhi",
                "health": HealthProfile(
                    status="Good",
                    ongoing_conditions=["Hypertension"],
                    recent_health_events=["annual_checkup_2mo"],
                    medication_count=1,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="moderate",
                    bmi_category="overweight",
                    family_health_history=["Hypertension", "Stroke"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=1,
                    children_ages=[8],
                    has_aging_parents=True,
                    parent_health_concerns=True,
                    family_size_total=3,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=4,
                    decision_speed="quick",  # Manager mindset
                    research_intensity="moderate",
                    peer_influence_susceptibility=0.3,
                    authority_trust=0.7,
                    loss_aversion_strength=0.8,
                    gamification_response=0.3,
                    social_proof_sensitivity=0.4,
                    urgency_response=0.7,
                    financial_anxiety=0.4
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="mnc",
                    recent_life_events=[],
                    insurance_experience="positive",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 8,
                "device": "iPhone"
            },
            {
                "occupation": "Finance Manager",
                "age": 38,
                "sex": "Female",
                "income": 180000,
                "district": "Mumbai",
                "state": "Maharashtra",
                "health": HealthProfile(
                    status="Good",
                    ongoing_conditions=["Thyroid"],
                    recent_health_events=["thyroid_test_2mo"],
                    medication_count=1,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="active",
                    bmi_category="normal",
                    family_health_history=["Thyroid", "Diabetes"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=2,
                    children_ages=[10, 7],
                    family_size_total=4,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=3,  # Finance person - detail-oriented
                    decision_speed="deliberate",
                    research_intensity="obsessive",  # Finance background
                    peer_influence_susceptibility=0.2,
                    authority_trust=0.7,
                    loss_aversion_strength=0.9,  # Finance mindset
                    gamification_response=0.2,
                    social_proof_sensitivity=0.3,
                    urgency_response=0.6,
                    financial_anxiety=0.7  # Knows too much about money
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=[],
                    insurance_experience="neutral",
                    previous_claim_experience="difficult",  # Had issues before
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 7,
                "device": "Android"
            },
            {
                "occupation": "HR Manager",
                "age": 35,
                "sex": "Female",
                "income": 130000,
                "district": "Bengaluru",
                "state": "Karnataka",
                "health": HealthProfile(
                    status="Good",
                    ongoing_conditions=[],
                    recent_health_events=["annual_checkup_6mo"],
                    medication_count=0,
                    doctor_visit_frequency="yearly",
                    health_anxiety_level="low",
                    fitness_level="active",
                    bmi_category="normal",
                    family_health_history=[]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=1,
                    children_ages=[4],
                    family_size_total=3,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=5,
                    decision_speed="quick",
                    research_intensity="moderate",
                    peer_influence_susceptibility=0.5,
                    authority_trust=0.8,  # HR person - trusts company
                    loss_aversion_strength=0.6,
                    gamification_response=0.4,
                    social_proof_sensitivity=0.7,  # HR knows what others do
                    urgency_response=0.6,
                    financial_anxiety=0.4
                ),
                "contextual": ContextualFactors(
                    season="year_end",  # Benefits enrollment period
                    work_culture="corporate",
                    recent_life_events=[],
                    insurance_experience="positive",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 7,
                "device": "iPhone"
            },
            {
                "occupation": "Sales Manager",
                "age": 36,
                "sex": "Male",
                "income": 160000,
                "district": "Chennai",
                "state": "Tamil Nadu",
                "health": HealthProfile(
                    status="Fair",
                    ongoing_conditions=["Chronic Stress", "Insomnia"],
                    recent_health_events=["sleep_study_4mo"],
                    medication_count=2,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="moderate",
                    bmi_category="normal",
                    family_health_history=[]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=1,
                    children_ages=[6],
                    family_size_total=3,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=6,
                    decision_speed="impulsive",  # Sales personality
                    research_intensity="minimal",
                    peer_influence_susceptibility=0.6,
                    authority_trust=0.6,
                    loss_aversion_strength=0.5,
                    gamification_response=0.8,  # Sales loves competitions
                    social_proof_sensitivity=0.7,
                    urgency_response=0.9,  # Sales mindset
                    financial_anxiety=0.5
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=[],
                    insurance_experience="neutral",
                    previous_claim_experience="none",
                    time_in_company="established",
                    job_security="secure"
                ),
                "education": "Graduate",
                "digital_literacy": 6,
                "device": "Android"
            },
            {
                "occupation": "Operations Manager",
                "age": 39,
                "sex": "Male",
                "income": 140000,
                "district": "Pune",
                "state": "Maharashtra",
                "health": HealthProfile(
                    status="Fair",
                    ongoing_conditions=["Chronic Back Pain", "Cervical Spondylosis"],
                    recent_health_events=["mri_3mo", "physiotherapy_ongoing"],
                    medication_count=2,
                    doctor_visit_frequency="monthly",
                    health_anxiety_level="high",
                    fitness_level="sedentary",
                    bmi_category="overweight",
                    family_health_history=["Arthritis"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=2,
                    children_ages=[12, 9],
                    has_aging_parents=True,
                    parent_health_concerns=True,
                    family_size_total=4,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=2,  # Pain drives action
                    decision_speed="deliberate",
                    research_intensity="thorough",
                    peer_influence_susceptibility=0.3,
                    authority_trust=0.7,
                    loss_aversion_strength=0.9,  # High due to ongoing treatment
                    gamification_response=0.2,
                    social_proof_sensitivity=0.4,
                    urgency_response=0.8,
                    financial_anxiety=0.7  # Ongoing medical costs
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=[],
                    insurance_experience="positive",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Graduate",
                "digital_literacy": 6,
                "device": "Android"
            },
            {
                "occupation": "Product Manager",
                "age": 33,
                "sex": "Female",
                "income": 190000,
                "district": "Bengaluru",
                "state": "Karnataka",
                "health": HealthProfile(
                    status="Good",
                    ongoing_conditions=[],
                    recent_health_events=["pregnancy_planning"],
                    medication_count=0,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="active",
                    bmi_category="normal",
                    family_health_history=[]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=False,
                    spouse_employed=True,
                    spouse_has_insurance=True,
                    family_size_total=2,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=3,  # Planning pregnancy - proactive
                    decision_speed="deliberate",
                    research_intensity="thorough",
                    peer_influence_susceptibility=0.4,
                    authority_trust=0.7,
                    loss_aversion_strength=0.8,  # Planning ahead
                    gamification_response=0.4,
                    social_proof_sensitivity=0.6,
                    urgency_response=0.7,
                    financial_anxiety=0.4
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="mnc",
                    recent_life_events=["planning_pregnancy"],
                    insurance_experience="positive",
                    previous_claim_experience="none",
                    time_in_company="established",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 9,
                "device": "iPhone"
            }
        ]
        
        # SEGMENT 3: Senior Leadership (Ages 42-55) - 7 personas
        print("\n👔 SEGMENT 3: Senior Leadership & Executives (42-55) - 7 personas")
        print("-"*80)
        
        senior_profiles = [
            {
                "occupation": "Vice President",
                "age": 48,
                "sex": "Male",
                "income": 400000,
                "district": "Gurgaon",
                "state": "Delhi",
                "health": HealthProfile(
                    status="Fair",
                    ongoing_conditions=["Hypertension", "High Cholesterol", "Fatty Liver"],
                    recent_health_events=["cardiac_stress_test_3mo", "annual_executive_checkup_1mo"],
                    medication_count=3,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="high",
                    fitness_level="moderate",
                    bmi_category="overweight",
                    family_health_history=["Heart Disease", "Diabetes"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=2,
                    children_ages=[18, 15],
                    has_aging_parents=True,
                    parent_health_concerns=True,
                    family_size_total=4,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=2,  # Busy but health-conscious
                    decision_speed="quick",
                    research_intensity="minimal",  # Delegates research
                    peer_influence_susceptibility=0.2,
                    authority_trust=0.8,
                    loss_aversion_strength=0.7,
                    gamification_response=0.1,
                    social_proof_sensitivity=0.3,
                    urgency_response=0.6,
                    financial_anxiety=0.1  # High income
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="mnc",
                    recent_life_events=[],
                    insurance_experience="positive",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 7,
                "device": "iPhone"
            },
            {
                "occupation": "Director",
                "age": 52,
                "sex": "Female",
                "income": 350000,
                "district": "Mumbai",
                "state": "Maharashtra",
                "health": HealthProfile(
                    status="Fair",
                    ongoing_conditions=["Diabetes Type 2", "Hypertension", "Osteoarthritis"],
                    recent_health_events=["endocrinologist_visit_1mo", "orthopedic_consult_2mo"],
                    medication_count=4,
                    doctor_visit_frequency="monthly",
                    health_anxiety_level="high",
                    fitness_level="sedentary",
                    bmi_category="obese",
                    family_health_history=["Diabetes", "Heart Disease", "Arthritis"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=2,
                    children_ages=[22, 19],
                    has_aging_parents=True,
                    parent_health_concerns=True,
                    family_size_total=4,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=1,  # High urgency due to conditions
                    decision_speed="deliberate",
                    research_intensity="thorough",
                    peer_influence_susceptibility=0.2,
                    authority_trust=0.7,
                    loss_aversion_strength=0.9,  # Multiple conditions
                    gamification_response=0.1,
                    social_proof_sensitivity=0.2,
                    urgency_response=0.9,
                    financial_anxiety=0.2
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=[],
                    insurance_experience="positive",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 6,
                "device": "iPhone"
            },
            {
                "occupation": "CTO",
                "age": 45,
                "sex": "Male",
                "income": 500000,
                "district": "Bengaluru",
                "state": "Karnataka",
                "health": HealthProfile(
                    status="Good",
                    ongoing_conditions=["Sleep Apnea"],
                    recent_health_events=["sleep_study_6mo", "cpap_machine_prescribed"],
                    medication_count=1,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="moderate",
                    bmi_category="overweight",
                    family_health_history=[]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=2,
                    children_ages=[14, 11],
                    family_size_total=4,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=4,
                    decision_speed="quick",
                    research_intensity="moderate",
                    peer_influence_susceptibility=0.2,
                    authority_trust=0.7,
                    loss_aversion_strength=0.6,
                    gamification_response=0.2,
                    social_proof_sensitivity=0.3,
                    urgency_response=0.5,
                    financial_anxiety=0.1
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="mnc",
                    recent_life_events=[],
                    insurance_experience="positive",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 9,
                "device": "iPhone"
            },
            {
                "occupation": "CFO",
                "age": 51,
                "sex": "Male",
                "income": 600000,
                "district": "Mumbai",
                "state": "Maharashtra",
                "health": HealthProfile(
                    status="Poor",
                    ongoing_conditions=["Diabetes Type 2", "Hypertension", "High Cholesterol", "Chronic Kidney Disease Stage 2"],
                    recent_health_events=["hospitalization_6mo", "nephrologist_ongoing", "cardiac_evaluation_2mo"],
                    medication_count=6,
                    doctor_visit_frequency="monthly",
                    health_anxiety_level="high",
                    fitness_level="sedentary",
                    bmi_category="obese",
                    family_health_history=["Diabetes", "Heart Disease", "Kidney Disease"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=2,
                    children_ages=[20, 17],
                    has_aging_parents=True,
                    parent_health_concerns=True,
                    family_size_total=4,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=0,  # Critical health = no inertia
                    decision_speed="quick",
                    research_intensity="obsessive",  # Finance + health crisis
                    peer_influence_susceptibility=0.1,
                    authority_trust=0.8,
                    loss_aversion_strength=1.0,  # Maximum
                    gamification_response=0.0,
                    social_proof_sensitivity=0.1,
                    urgency_response=1.0,  # Maximum
                    financial_anxiety=0.4  # Despite high income, medical costs add up
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=["health_crisis"],
                    insurance_experience="neutral",
                    previous_claim_experience="difficult",  # Had claim issues
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 7,
                "device": "iPhone"
            },
            {
                "occupation": "Senior Manager",
                "age": 44,
                "sex": "Male",
                "income": 220000,
                "district": "Chennai",
                "state": "Tamil Nadu",
                "health": HealthProfile(
                    status="Fair",
                    ongoing_conditions=["Thyroid", "Vitamin D Deficiency"],
                    recent_health_events=["thyroid_test_1mo"],
                    medication_count=2,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="moderate",
                    bmi_category="normal",
                    family_health_history=["Thyroid"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=2,
                    children_ages=[16, 13],
                    family_size_total=4,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=4,
                    decision_speed="deliberate",
                    research_intensity="moderate",
                    peer_influence_susceptibility=0.3,
                    authority_trust=0.7,
                    loss_aversion_strength=0.7,
                    gamification_response=0.3,
                    social_proof_sensitivity=0.4,
                    urgency_response=0.6,
                    financial_anxiety=0.4
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=[],
                    insurance_experience="neutral",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Graduate",
                "digital_literacy": 6,
                "device": "Android"
            },
            {
                "occupation": "Director",
                "age": 49,
                "sex": "Female",
                "income": 380000,
                "district": "Pune",
                "state": "Maharashtra",
                "health": HealthProfile(
                    status="Good",
                    ongoing_conditions=["Menopause Management"],
                    recent_health_events=["gynec_visit_2mo", "bone_density_test_3mo"],
                    medication_count=2,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="active",
                    bmi_category="normal",
                    family_health_history=["Osteoporosis", "Breast Cancer"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=1,
                    children_ages=[21],
                    has_aging_parents=True,
                    parent_health_concerns=True,
                    family_size_total=3,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=3,
                    decision_speed="deliberate",
                    research_intensity="thorough",
                    peer_influence_susceptibility=0.3,
                    authority_trust=0.7,
                    loss_aversion_strength=0.8,  # Family history concerns
                    gamification_response=0.2,
                    social_proof_sensitivity=0.4,
                    urgency_response=0.7,
                    financial_anxiety=0.2
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="mnc",
                    recent_life_events=[],
                    insurance_experience="positive",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 7,
                "device": "iPhone"
            },
            {
                "occupation": "General Manager",
                "age": 46,
                "sex": "Male",
                "income": 250000,
                "district": "Hyderabad",
                "state": "Telangana",
                "health": HealthProfile(
                    status="Fair",
                    ongoing_conditions=["Pre-diabetes", "Hypertension"],
                    recent_health_events=["annual_checkup_2mo"],
                    medication_count=2,
                    doctor_visit_frequency="quarterly",
                    health_anxiety_level="medium",
                    fitness_level="moderate",
                    bmi_category="overweight",
                    family_health_history=["Diabetes", "Heart Disease"]
                ),
                "family": FamilyProfile(
                    marital_status="Currently Married",
                    has_children=True,
                    children_count=2,
                    children_ages=[17, 14],
                    has_aging_parents=True,
                    parent_health_concerns=True,
                    family_size_total=4,
                    primary_health_decision_maker=True
                ),
                "behavioral": BehavioralProfile(
                    inertia_level=4,
                    decision_speed="quick",
                    research_intensity="moderate",
                    peer_influence_susceptibility=0.3,
                    authority_trust=0.7,
                    loss_aversion_strength=0.7,
                    gamification_response=0.2,
                    social_proof_sensitivity=0.4,
                    urgency_response=0.7,
                    financial_anxiety=0.3
                ),
                "contextual": ContextualFactors(
                    season="regular",
                    work_culture="corporate",
                    recent_life_events=[],
                    insurance_experience="neutral",
                    previous_claim_experience="smooth",
                    time_in_company="long_term",
                    job_security="secure"
                ),
                "education": "Post Graduate",
                "digital_literacy": 6,
                "device": "Android"
            }
        ]
        
        # Convert to EnhancedPersona objects
        all_profiles = young_profiles + mid_career_profiles + senior_profiles
        
        for i, profile in enumerate(all_profiles, 1):
            # Calculate derived scores
            health_urgency = EnhancedPersonaGenerator._calculate_health_urgency(
                profile["health"],
                profile["family"],
                profile["contextual"]
            )
            
            engagement_likelihood = EnhancedPersonaGenerator._calculate_engagement_likelihood(
                profile["health"],
                profile["behavioral"],
                profile["contextual"]
            )
            
            value_sensitivity = EnhancedPersonaGenerator._calculate_value_sensitivity(
                profile["behavioral"],
                profile["income"]
            )
            
            feature_exploration = EnhancedPersonaGenerator._calculate_feature_exploration(
                profile["behavioral"],
                profile["health"],
                profile["contextual"]
            )
            
            persona = EnhancedPersona(
                uuid=f"enhanced_{i:03d}",
                occupation=profile["occupation"],
                age=profile["age"],
                sex=profile["sex"],
                state=profile["state"],
                district=profile["district"],
                education_level=profile["education"],
                monthly_income_inr=profile["income"],
                digital_literacy=profile["digital_literacy"],
                primary_device=profile["device"],
                health_profile=profile["health"],
                family_profile=profile["family"],
                behavioral_profile=profile["behavioral"],
                contextual_factors=profile["contextual"],
                health_urgency_score=health_urgency,
                engagement_likelihood=engagement_likelihood,
                value_sensitivity=value_sensitivity,
                feature_exploration_probability=feature_exploration
            )
            
            personas.append(persona)
            
            # Print persona summary
            segment_name = "Young & Healthy" if profile["age"] < 31 else ("Mid-Career" if profile["age"] < 42 else "Senior Leadership")
            health_summary = f"{profile['health'].status}"
            if profile['health'].ongoing_conditions:
                health_summary += f" ({', '.join(profile['health'].ongoing_conditions[:2])})"
            
            print(f"   {i:2d}. {profile['occupation']:<25} | {profile['age']}yo {profile['sex']:<6} | {health_summary:<30} | Inertia: {profile['behavioral'].inertia_level}/10")
        
        print("\n" + "="*80)
        print(f"✅ Generated {len(personas)} highly diverse personas with rich behavioral profiles")
        print("="*80)
        
        return personas
    
    @staticmethod
    def _calculate_health_urgency(health: HealthProfile, family: FamilyProfile, context: ContextualFactors) -> float:
        """Calculate health urgency score (0-10)."""
        score = 5.0  # Base
        
        # Health status impact
        status_scores = {"Excellent": -2, "Good": -1, "Fair": 1, "Poor": 3}
        score += status_scores.get(health.status, 0)
        
        # Ongoing conditions
        score += len(health.ongoing_conditions) * 1.5
        
        # Recent health events
        score += len(health.recent_health_events) * 1.0
        
        # Medication count
        score += health.medication_count * 0.5
        
        # Doctor visit frequency
        frequency_scores = {"never": -1, "yearly": 0, "quarterly": 1, "monthly": 2}
        score += frequency_scores.get(health.doctor_visit_frequency, 0)
        
        # Health anxiety
        anxiety_scores = {"low": 0, "medium": 1, "high": 2}
        score += anxiety_scores.get(health.health_anxiety_level, 0)
        
        # Family health history
        score += len(health.family_health_history) * 0.5
        
        # Family factors
        if family.parent_health_concerns:
            score += 1
        if family.has_children and family.children_count > 0:
            score += 0.5
        
        # Recent life events
        critical_events = ["health_scare", "health_crisis", "hospitalization"]
        if any(event in str(context.recent_life_events) for event in critical_events):
            score += 2
        
        return max(0, min(10, score))
    
    @staticmethod
    def _calculate_engagement_likelihood(health: HealthProfile, behavioral: BehavioralProfile, context: ContextualFactors) -> float:
        """Calculate engagement likelihood (0-1)."""
        # Start with health urgency as base
        score = 0.3  # Base engagement
        
        # Health drives engagement
        if health.status in ["Poor", "Fair"]:
            score += 0.3
        if len(health.ongoing_conditions) > 0:
            score += 0.2
        
        # Low inertia = high engagement
        score += (10 - behavioral.inertia_level) / 20  # 0-0.5
        
        # Research intensity
        research_scores = {"minimal": 0, "moderate": 0.1, "thorough": 0.15, "obsessive": 0.2}
        score += research_scores.get(behavioral.research_intensity, 0)
        
        # Previous experience
        if context.previous_claim_experience == "difficult":
            score += 0.1  # More engaged to avoid issues
        elif context.previous_claim_experience == "smooth":
            score -= 0.05  # Less worried
        
        return max(0, min(1, score))
    
    @staticmethod
    def _calculate_value_sensitivity(behavioral: BehavioralProfile, income: int) -> float:
        """Calculate how much value propositions matter (0-1)."""
        score = 0.5  # Base
        
        # Loss aversion
        score += behavioral.loss_aversion_strength * 0.3
        
        # Financial anxiety
        score += behavioral.financial_anxiety * 0.2
        
        # Income effect (lower income = more value sensitive)
        if income < 70000:
            score += 0.2
        elif income < 120000:
            score += 0.1
        elif income > 300000:
            score -= 0.1
        
        return max(0, min(1, score))
    
    @staticmethod
    def _calculate_feature_exploration(behavioral: BehavioralProfile, health: HealthProfile, context: ContextualFactors) -> float:
        """Calculate likelihood to explore optional features (0-1)."""
        score = 0.3  # Base
        
        # Inertia is the enemy
        score -= behavioral.inertia_level / 15  # Higher inertia = lower exploration
        
        # Research intensity helps
        research_scores = {"minimal": 0, "moderate": 0.1, "thorough": 0.2, "obsessive": 0.25}
        score += research_scores.get(behavioral.research_intensity, 0)
        
        # Health urgency drives exploration
        if health.status in ["Poor", "Fair"]:
            score += 0.2
        if len(health.ongoing_conditions) > 0:
            score += 0.15
        
        # Gamification response
        score += behavioral.gamification_response * 0.1
        
        # Social proof sensitivity
        score += behavioral.social_proof_sensitivity * 0.1
        
        return max(0, min(1, score))


class EnhancedFlowSimulator:
    """Enhanced simulator with interventions and advanced behavioral modeling."""
    
    # Enhanced system prompt
    ENHANCED_SYSTEM_PROMPT = """You are simulating a real corporate employee using EMPLOYER-PROVIDED health insurance.

⚡ ENHANCED BEHAVIORAL CONTEXT - UTILITY MODE V2

You have a RICH PERSONAL PROFILE:
- Health Status & Conditions
- Family Responsibilities  
- Behavioral Traits (inertia, decision speed, research habits)
- Life Context (recent events, work culture, insurance experience)

YOUR MENTAL FRAME:
1. BASELINE UTILITY MODE: This is company-provided, you're captive but lazy
2. HEALTH URGENCY MODIFIER: Your health status affects how motivated you are
3. FAMILY RESPONSIBILITY: Dependents make you more cautious
4. BEHAVIORAL TRAITS: Your personality affects decisions
5. CONTEXTUAL TRIGGERS: Recent events and experiences shape your mindset

ENHANCED DECISION FACTORS:
- Mandatory steps: Still high tolerance, but your patience varies
- Optional features: Your exploration depends on health urgency, family needs, and behavioral traits
- Interventions: You respond differently to social proof, urgency, and incentives based on your profile
- Cognitive load: You get tired if flow is too long or complex
- Attention: Your focus varies based on health urgency and personality

You make realistic, psychologically grounded decisions based on YOUR SPECIFIC PROFILE."""

    ENHANCED_DECISION_PROMPT = """═══════════════════════════════════════════════════════════
YOUR IDENTITY - ENHANCED PROFILE
═══════════════════════════════════════════════════════════

BASIC INFO:
- Occupation: {occupation}
- Age: {age} | Sex: {sex}
- Location: {district}, {state}
- Income: ₹{monthly_income:,}/month (₹{annual_ctc} LPA)
- Education: {education_level}
- Digital Literacy: {digital_literacy}/10 | Device: {device}

HEALTH PROFILE:
- Status: {health_status}
- Ongoing Conditions: {ongoing_conditions}
- Recent Events: {recent_health_events}
- Medications: {medication_count}
- Doctor Visits: {doctor_frequency}
- Health Anxiety: {health_anxiety}
- Fitness: {fitness_level}
- Health Urgency Score: {health_urgency_score}/10

FAMILY SITUATION:
- Marital Status: {marital_status}
- Children: {children_status}
- Aging Parents: {aging_parents}
- Family Size: {family_size}
- You are {decision_maker}

BEHAVIORAL TRAITS:
- Inertia Level: {inertia_level}/10 ({inertia_label})
- Decision Speed: {decision_speed}
- Research Intensity: {research_intensity}
- Peer Influence: {peer_influence:.0%}
- Loss Aversion: {loss_aversion:.0%}
- Gamification Response: {gamification:.0%}
- Social Proof Sensitivity: {social_proof:.0%}
- Urgency Response: {urgency_response:.0%}

CONTEXT:
- Work Culture: {work_culture}
- Time in Company: {time_in_company}
- Job Security: {job_security}
- Recent Life Events: {recent_events}
- Insurance Experience: {insurance_experience}
- Previous Claims: {previous_claims}

CALCULATED SCORES:
- Engagement Likelihood: {engagement_likelihood:.0%}
- Value Sensitivity: {value_sensitivity:.0%}
- Feature Exploration Probability: {feature_exploration:.0%}

═══════════════════════════════════════════════════════════
CURRENT VIEW - {view_number}/8: {view_name}
═══════════════════════════════════════════════════════════

WHAT YOU SEE:
{view_description}

{intervention_message}

YOUR JOURNEY SO FAR:
{journey_summary}

═══════════════════════════════════════════════════════════
YOUR DECISION - CONTINUE OR DROP OFF?
═══════════════════════════════════════════════════════════

ENHANCED DECISION LOGIC (based on YOUR profile):

1. IDENTIFY STEP TYPE: Is this MANDATORY or OPTIONAL?

2. APPLY YOUR BEHAVIORAL TRAITS:
   - Your Inertia: {inertia_level}/10 - {inertia_impact}
   - Your Health Urgency: {health_urgency_score}/10 - {urgency_impact}
   - Your Family Responsibility: {family_impact}
   - Your Decision Style: {decision_style_impact}

3. EVALUATE INTERVENTIONS (if any):
   {intervention_evaluation}

4. COGNITIVE STATE:
   - Views completed: {views_completed}
   - Getting tired? {cognitive_state}
   - Attention level: {attention_state}

5. DECISION CRITERIA FOR THIS VIEW:
   - Clarity: Can you understand this quickly?
   - Value: Does this solve a real problem for YOU?
   - Trust: Does this feel legitimate?
   - Effort: Is it worth the clicks/time?
   - Risk: Any concerns or fears?

MAKE YOUR DECISION based on YOUR COMPLETE PROFILE, not generic assumptions.

═══════════════════════════════════════════════════════════
RESPONSE FORMAT (Pure JSON, no markdown)
═══════════════════════════════════════════════════════════

{{
    "step_type": "MANDATORY|OPTIONAL",
    "decision": "CONTINUE|DROP_OFF",
    "clarity_score": <0-10>,
    "value_perception_score": <0-10>,
    "trust_score": <0-10>,
    "inertia_override": <true|false>,
    "urgency_factor": "high|medium|low",
    "emotional_state": "<current emotion>",
    "cognitive_load": "low|medium|high|overwhelming",
    "attention_level": "distracted|partial|focused|engaged",
    "intervention_present": "{intervention_type}",
    "intervention_effectiveness": <0-1, how much it influenced you>,
    "primary_decision_driver": "<main reason for decision>",
    "hesitation_points": ["<concerns if any>"],
    "positive_triggers": ["<what attracted you>"],
    "friction_points": ["<what annoyed you>"],
    "reasoning": "<detailed explanation in your voice>",
    "time_spent_seconds": <realistic time>,
    "likelihood_to_use_feature": <0-1, if this is optional, will you actually use it?>
}}

Be authentic to YOUR profile. Different personas make different decisions!
"""

    async def analyze_view_with_interventions(self, view: FlowView) -> Dict[str, str]:
        """Analyze view and optionally add interventions."""
        try:
            with open(view.image_path, 'rb') as f:
                image_data = f.read()
            
            prompt = f"""Analyze this health insurance onboarding screen (View {view.view_number}/8).

Describe what you see:
1. Main elements and purpose
2. Key information displayed
3. Required user actions
4. Design quality
5. Potential friction points

{f"INTERVENTION APPLIED: {view.intervention_applied}" if view.intervention_applied else ""}

Return ONLY valid JSON (no newlines in strings):
{{
    "main_content": "brief description",
    "key_information": "what is communicated",
    "required_action": "what user must do",
    "design_quality": "assessment",
    "friction_points": "potential issues"
}}
"""
            response = await gemini_client.generate_pro(prompt, image_data)
            return gemini_client.parse_json_response(response)
            
        except Exception as e:
            print(f"⚠️ Error analyzing view {view.view_id}: {e}")
            return {
                "main_content": "Insurance onboarding view",
                "key_information": "Plan details and options",
                "required_action": "Review and proceed",
                "design_quality": "Standard corporate interface",
                "friction_points": "May require careful review"
            }
    
    def _build_enhanced_context(self, persona: EnhancedPersona, view: FlowView, journey_history: List[str], view_analysis: Dict) -> Dict[str, str]:
        """Build rich context for decision making."""
        
        # Health profile strings
        conditions = ", ".join(persona.health_profile.ongoing_conditions) if persona.health_profile.ongoing_conditions else "None"
        recent_events = ", ".join(persona.health_profile.recent_health_events) if persona.health_profile.recent_health_events else "None"
        
        # Family strings
        if persona.family_profile.has_children:
            children_status = f"Yes - {persona.family_profile.children_count} {'child' if persona.family_profile.children_count == 1 else 'children'} (ages: {', '.join(map(str, persona.family_profile.children_ages))})"
        else:
            children_status = "No"
        
        aging_parents = "Yes - with health concerns" if persona.family_profile.parent_health_concerns else ("Yes" if persona.family_profile.has_aging_parents else "No")
        decision_maker = "the primary health decision maker" if persona.family_profile.primary_health_decision_maker else "not the primary decision maker"
        
        # Behavioral labels
        if persona.behavioral_profile.inertia_level >= 8:
            inertia_label = "Very High - Extremely lazy, will avoid optional tasks"
        elif persona.behavioral_profile.inertia_level >= 6:
            inertia_label = "High - Prefers minimal effort"
        elif persona.behavioral_profile.inertia_level >= 4:
            inertia_label = "Moderate - Will engage if value is clear"
        elif persona.behavioral_profile.inertia_level >= 2:
            inertia_label = "Low - Relatively proactive"
        else:
            inertia_label = "Very Low - Highly motivated and proactive"
        
        # Decision impacts
        inertia_impact = f"Very high barrier to optional actions" if persona.behavioral_profile.inertia_level >= 7 else ("Moderate barrier" if persona.behavioral_profile.inertia_level >= 4 else "Low barrier")
        
        if persona.health_urgency_score >= 7:
            urgency_impact = "HIGH urgency - health needs override inertia"
        elif persona.health_urgency_score >= 4:
            urgency_impact = "MODERATE urgency - somewhat motivated"
        else:
            urgency_impact = "LOW urgency - no health driver"
        
        family_impact = "High responsibility - careful about family coverage" if persona.family_profile.family_size_total > 2 else "Low responsibility - mainly personal"
        
        decision_style_impact = f"{persona.behavioral_profile.decision_speed.title()} decision maker, {persona.behavioral_profile.research_intensity} research"
        
        # Intervention messaging
        intervention_message = ""
        intervention_evaluation = "No intervention on this view."
        intervention = view.intervention_applied
        view_number = view.view_number
        
        if intervention:
            if intervention == "social_proof":
                intervention_message = f"\n🔔 NOTICE: '847 of your colleagues have already completed this step'\n"
                eval_text = f"Social Proof Intervention: You have {persona.behavioral_profile.social_proof_sensitivity:.0%} sensitivity to peer influence."
                if persona.behavioral_profile.social_proof_sensitivity > 0.6:
                    eval_text += " This STRONGLY influences you."
                elif persona.behavioral_profile.social_proof_sensitivity > 0.3:
                    eval_text += " This somewhat influences you."
                else:
                    eval_text += " This barely affects you."
                intervention_evaluation = eval_text
                
            elif intervention == "urgency":
                intervention_message = f"\n⏰ NOTICE: 'Complete within 48 hours to activate benefits'\n"
                eval_text = f"Urgency Intervention: You have {persona.behavioral_profile.urgency_response:.0%} response to deadlines."
                if persona.behavioral_profile.urgency_response > 0.6:
                    eval_text += " This STRONGLY motivates you."
                elif persona.behavioral_profile.urgency_response > 0.3:
                    eval_text += " This somewhat motivates you."
                else:
                    eval_text += " This barely affects you."
                intervention_evaluation = eval_text
                
            elif intervention == "incentive":
                intervention_message = f"\n🎁 NOTICE: 'Complete setup to unlock ₹500 wellness wallet'\n"
                eval_text = f"Incentive Intervention: You have {persona.behavioral_profile.gamification_response:.0%} response to rewards."
                if persona.behavioral_profile.gamification_response > 0.6:
                    eval_text += " This STRONGLY attracts you."
                elif persona.behavioral_profile.gamification_response > 0.3:
                    eval_text += " This somewhat attracts you."
                else:
                    eval_text += " This barely affects you."
                intervention_evaluation = eval_text
        
        # Journey summary
        if journey_history:
            journey_summary = f"You've seen {len(journey_history)} view(s): " + " → ".join(journey_history)
        else:
            journey_summary = "This is your first view."
        
        # Cognitive and attention state
        if view_number <= 3:
            cognitive_state = "No - still patient"
            attention_state = "Focused"
        elif view_number <= 5:
            cognitive_state = "Slightly - getting routine"
            attention_state = "Partial focus"
        elif view_number <= 7:
            if persona.behavioral_profile.inertia_level >= 7:
                cognitive_state = "Yes - this is taking too long"
                attention_state = "Distracted"
            else:
                cognitive_state = "Somewhat - but pushing through"
                attention_state = "Partial focus"
        else:
            if persona.behavioral_profile.inertia_level >= 7:
                cognitive_state = "VERY - ready to give up"
                attention_state = "Highly distracted"
            else:
                cognitive_state = "Yes - but almost done"
                attention_state = "Focused on finishing"
        
        # Recent events string
        recent_events = ", ".join(persona.contextual_factors.recent_life_events) if persona.contextual_factors.recent_life_events else "None"
        
        annual_ctc = (persona.monthly_income_inr * 12) / 100000
        if annual_ctc >= 100:
            ctc_str = f"{annual_ctc/100:.1f}Cr"
        else:
            ctc_str = f"{annual_ctc:.1f}"
        
        return {
            "occupation": persona.occupation,
            "age": persona.age,
            "sex": persona.sex,
            "district": persona.district,
            "state": persona.state,
            "monthly_income": persona.monthly_income_inr,
            "annual_ctc": ctc_str,
            "education_level": persona.education_level,
            "digital_literacy": persona.digital_literacy,
            "device": persona.primary_device,
            "health_status": persona.health_profile.status,
            "ongoing_conditions": conditions,
            "recent_health_events": recent_events,
            "medication_count": persona.health_profile.medication_count,
            "doctor_frequency": persona.health_profile.doctor_visit_frequency,
            "health_anxiety": persona.health_profile.health_anxiety_level,
            "fitness_level": persona.health_profile.fitness_level,
            "health_urgency_score": persona.health_urgency_score,
            "marital_status": persona.family_profile.marital_status,
            "children_status": children_status,
            "aging_parents": aging_parents,
            "family_size": persona.family_profile.family_size_total,
            "decision_maker": decision_maker,
            "inertia_level": persona.behavioral_profile.inertia_level,
            "inertia_label": inertia_label,
            "decision_speed": persona.behavioral_profile.decision_speed,
            "research_intensity": persona.behavioral_profile.research_intensity,
            "peer_influence": persona.behavioral_profile.peer_influence_susceptibility,
            "loss_aversion": persona.behavioral_profile.loss_aversion_strength,
            "gamification": persona.behavioral_profile.gamification_response,
            "social_proof": persona.behavioral_profile.social_proof_sensitivity,
            "urgency_response": persona.behavioral_profile.urgency_response,
            "work_culture": persona.contextual_factors.work_culture,
            "time_in_company": persona.contextual_factors.time_in_company,
            "job_security": persona.contextual_factors.job_security,
            "recent_events": recent_events,
            "insurance_experience": persona.contextual_factors.insurance_experience,
            "previous_claims": persona.contextual_factors.previous_claim_experience,
            "engagement_likelihood": persona.engagement_likelihood,
            "value_sensitivity": persona.value_sensitivity,
            "feature_exploration": persona.feature_exploration_probability,
            "inertia_impact": inertia_impact,
            "urgency_impact": urgency_impact,
            "family_impact": family_impact,
            "decision_style_impact": decision_style_impact,
            "intervention_message": intervention_message,
            "intervention_evaluation": intervention_evaluation,
            "intervention_type": intervention or "none",
            "journey_summary": journey_summary,
            "views_completed": view_number - 1,
            "cognitive_state": cognitive_state,
            "attention_state": attention_state,
            "view_number": view_number,
            "view_name": view.view_name,
            "view_description": self._format_view_description(view_analysis)
        }
    
    def _format_view_description(self, analysis: Dict) -> str:
        """Format view analysis into description."""
        return f"""Main Content: {analysis.get('main_content', 'Unknown')}
Key Information: {analysis.get('key_information', 'Unknown')}
Required Action: {analysis.get('required_action', 'Unknown')}
Design Quality: {analysis.get('design_quality', 'Unknown')}
Potential Issues: {analysis.get('friction_points', 'None')}"""
    
    async def simulate_enhanced_journey(
        self,
        persona: EnhancedPersona,
        views: List[FlowView],
        view_analyses: Dict[str, Dict[str, str]]
    ) -> EnhancedSimulationResult:
        """Simulate enhanced journey with rich behavioral modeling."""
        
        decisions = []
        total_time = 0
        dropped_off_at = None
        drop_off_reason = None
        journey_history = []
        
        for view in views:
            view_analysis = view_analyses.get(view.view_id, {})
            
            # Build enhanced context
            context = self._build_enhanced_context(
                persona,
                view,
                journey_history,
                view_analysis
            )
            
            prompt = self.ENHANCED_DECISION_PROMPT.format(**context)
            
            try:
                response = await gemini_client.generate_flash(
                    prompt=prompt,
                    system_prompt=self.ENHANCED_SYSTEM_PROMPT
                )
                decision_data = gemini_client.parse_json_response(response)
                
                decision = EnhancedFlowDecision(
                    persona_uuid=persona.uuid,
                    view_id=view.view_id,
                    view_number=view.view_number,
                    step_type=decision_data.get("step_type", "MANDATORY"),
                    decision=decision_data.get("decision", "CONTINUE"),
                    trust_score=decision_data.get("trust_score", 5),
                    clarity_score=decision_data.get("clarity_score", 5),
                    value_perception_score=decision_data.get("value_perception_score", 5),
                    inertia_override=decision_data.get("inertia_override", False),
                    urgency_factor=decision_data.get("urgency_factor", "low"),
                    emotional_state=decision_data.get("emotional_state", "neutral"),
                    cognitive_load=decision_data.get("cognitive_load", "low"),
                    attention_level=decision_data.get("attention_level", "focused"),
                    intervention_present=decision_data.get("intervention_present"),
                    intervention_effectiveness=decision_data.get("intervention_effectiveness"),
                    primary_decision_driver=decision_data.get("primary_decision_driver", ""),
                    hesitation_points=decision_data.get("hesitation_points", []),
                    positive_triggers=decision_data.get("positive_triggers", []),
                    friction_points=decision_data.get("friction_points", []),
                    time_spent_seconds=decision_data.get("time_spent_seconds", 5),
                    reasoning=decision_data.get("reasoning", ""),
                    likelihood_to_use_feature=decision_data.get("likelihood_to_use_feature")
                )
                
                decisions.append(decision)
                total_time += decision.time_spent_seconds
                journey_history.append(f"V{view.view_number}")
                
                if decision.decision == "DROP_OFF":
                    dropped_off_at = view.view_number
                    drop_off_reason = decision.reasoning
                    break
                    
            except Exception as e:
                print(f"⚠️ Error simulating {persona.uuid} at view {view.view_number}: {e}")
                # Fallback decision
                decision = EnhancedFlowDecision(
                    persona_uuid=persona.uuid,
                    view_id=view.view_id,
                    view_number=view.view_number,
                    step_type="MANDATORY",
                    decision="DROP_OFF",
                    trust_score=5,
                    clarity_score=5,
                    value_perception_score=5,
                    reasoning="Simulation error",
                    emotional_state="confused",
                    cognitive_load="high",
                    attention_level="distracted"
                )
                decisions.append(decision)
                dropped_off_at = view.view_number
                drop_off_reason = "Technical error"
                break
        
        # Calculate engagement quality
        if len(decisions) >= 7:
            avg_attention = sum(1 for d in decisions if d.attention_level in ["focused", "engaged"]) / len(decisions)
            engagement_quality = "high" if avg_attention > 0.6 else ("medium" if avg_attention > 0.3 else "low")
        else:
            engagement_quality = "low"
        
        # Feature adoption predictions
        feature_predictions = {}
        wellness_decisions = [d for d in decisions if "wellness" in d.reasoning.lower() or "gym" in d.reasoning.lower()]
        if wellness_decisions:
            feature_predictions["wellness"] = sum(d.likelihood_to_use_feature or 0 for d in wellness_decisions if d.likelihood_to_use_feature) / len(wellness_decisions)
        
        # Likely claim user based on health profile
        likely_claim_user = persona.health_urgency_score >= 5
        
        # Retention risk
        if len(decisions) < 4:
            retention_risk = "high"
        elif engagement_quality == "low":
            retention_risk = "medium"
        else:
            retention_risk = "low"
        
        # Recommended interventions
        recommendations = []
        if persona.behavioral_profile.social_proof_sensitivity > 0.6:
            recommendations.append("social_proof")
        if persona.behavioral_profile.gamification_response > 0.6:
            recommendations.append("gamification")
        if persona.behavioral_profile.urgency_response > 0.6:
            recommendations.append("urgency_nudges")
        if persona.behavioral_profile.loss_aversion_strength > 0.7:
            recommendations.append("loss_aversion_messaging")
        
        return EnhancedSimulationResult(
            persona_uuid=persona.uuid,
            total_views_seen=len(decisions),
            dropped_off_at_view=dropped_off_at,
            completed_flow=dropped_off_at is None,
            decisions=decisions,
            total_time_seconds=total_time,
            drop_off_reason=drop_off_reason,
            engagement_quality=engagement_quality,
            feature_adoption_predictions=feature_predictions,
            likely_claim_user=likely_claim_user,
            retention_risk=retention_risk,
            recommended_interventions=recommendations
        )


async def main():
    """Enhanced main execution with 20 diverse personas."""
    
    print("\n" + "="*100)
    print("🏥 LOOP HEALTH SIMULATOR V2 - ENHANCED MODEL WITH ADVANCED BEHAVIORAL PRIORS")
    print("="*100)
    
    start_time = time.time()
    
    # Load product flow views
    print("\n📸 STEP 1: Loading Product Flow Views...")
    product_flow_dir = Path(__file__).parent / "product_flow"
    view_files = sorted(product_flow_dir.glob("*.png"))[:8]
    
    if len(view_files) < 8:
        print(f"❌ Expected 8 views, found only {len(view_files)}")
        return
    
    views = []
    for i, view_file in enumerate(view_files, 1):
        # Randomly apply interventions to some views (views 7-8 are optional)
        intervention = None
        if i in [7, 8]:  # Optional views
            interventions = [None, "social_proof", "urgency", "incentive"]
            intervention = random.choice(interventions)
        
        views.append(FlowView(
            view_id=f"view_{i}",
            view_number=i,
            view_name=f"View {i}",
            image_path=str(view_file),
            intervention_applied=intervention
        ))
    
    print(f"✅ Loaded {len(views)} views")
    for view in views:
        intervention_msg = f" [+ {view.intervention_applied.upper()}]" if view.intervention_applied else ""
        print(f"   • View {view.view_number}{intervention_msg}")
    
    # Generate 20 diverse personas
    print("\n👥 STEP 2: Generating 20 Highly Diverse Personas...")
    personas = EnhancedPersonaGenerator.generate_diverse_personas()
    
    # Save personas
    loop_data_dir = DATA_DIR / "loop_health"
    loop_data_dir.mkdir(exist_ok=True)
    
    personas_data = [p.model_dump() for p in personas]
    with open(loop_data_dir / "enhanced_personas_v2.json", 'w') as f:
        json.dump(personas_data, f, indent=2)
    
    # Analyze views
    print("\n🎨 STEP 3: Analyzing Views...")
    simulator = EnhancedFlowSimulator()
    
    view_analysis_tasks = [simulator.analyze_view_with_interventions(view) for view in views]
    view_analyses_list = await tqdm.gather(*view_analysis_tasks, desc="Analyzing views")
    view_analyses = {views[i].view_id: analysis for i, analysis in enumerate(view_analyses_list)}
    
    print(f"✅ Analyzed {len(views)} views")
    
    # Run enhanced simulations
    print(f"\n🎬 STEP 4: Running Enhanced Simulations for {len(personas)} Personas...")
    print(f"   Each persona will experience personalized behavioral modeling")
    print(f"   Interventions will be evaluated based on individual traits")
    
    simulation_tasks = [
        simulator.simulate_enhanced_journey(persona, views, view_analyses)
        for persona in personas
    ]
    
    results = await tqdm.gather(*simulation_tasks, desc="Simulating enhanced journeys")
    
    print(f"\n✅ Completed {len(results)} enhanced persona journeys")
    
    # Generate comprehensive report
    print("\n📊 STEP 5: Generating Comprehensive Simulation Report...")
    
    # Save results
    results_data = [r.model_dump() for r in results]
    with open(loop_data_dir / "enhanced_simulation_results_v2.json", 'w') as f:
        json.dump(results_data, f, indent=2)
    
    with open(loop_data_dir / "view_analyses_v2.json", 'w') as f:
        json.dump(view_analyses, f, indent=2)
    
    execution_time = time.time() - start_time
    
    print(f"\n✅ All data saved to {loop_data_dir}")
    print(f"   • enhanced_personas_v2.json - 20 diverse personas with rich profiles")
    print(f"   • enhanced_simulation_results_v2.json - Detailed journey data")
    print(f"   • view_analyses_v2.json - View analyses")
    
    print(f"\n⏱️  Total Execution Time: {execution_time:.1f} seconds")
    print("\n🎉 ENHANCED SIMULATION COMPLETE!")
    print("   Next: Generating detailed markdown report...")


if __name__ == "__main__":
    asyncio.run(main())
