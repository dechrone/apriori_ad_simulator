"""Data loader for persona dataset and DuckDB storage."""

import duckdb
import pandas as pd
from typing import List, Optional
from pathlib import Path

from src.utils.schemas import RawPersona
from src.utils.config import DATA_DIR, DB_PATH


class PersonaDataLoader:
    """Load and manage persona data using DuckDB."""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.conn = None
    
    def connect(self):
        """Connect to DuckDB."""
        self.conn = duckdb.connect(self.db_path)
    
    def close(self):
        """Close connection."""
        if self.conn:
            self.conn.close()
    
    def load_from_csv(self, csv_path: str, limit: int = None):
        """Load personas from CSV file."""
        self.connect()
        
        # Read CSV with DuckDB
        query = f"SELECT * FROM read_csv_auto('{csv_path}')"
        if limit:
            query += f" LIMIT {limit}"
        
        df = self.conn.execute(query).df()
        
        # Create table
        self.conn.execute("DROP TABLE IF EXISTS personas")
        self.conn.execute("CREATE TABLE personas AS SELECT * FROM df")
        
        print(f"✅ Loaded {len(df)} personas into DuckDB")
        
        self.close()
        return df
    
    def load_from_huggingface(self, dataset_name: str = "nvidia/Nemotron-Personas-India", split: str = "en_IN"):
        """Load personas from HuggingFace dataset."""
        try:
            from datasets import load_dataset
            print(f"📥 Loading dataset from HuggingFace: {dataset_name} (split: {split})...")
            dataset = load_dataset(dataset_name, split=split)
            df = dataset.to_pandas()
            
            self.connect()
            self.conn.execute("DROP TABLE IF EXISTS personas")
            self.conn.execute("CREATE TABLE personas AS SELECT * FROM df")
            print(f"✅ Loaded {len(df)} personas from HuggingFace into DuckDB")
            # Do not close() here so filter_by_keywords / load_sample_personas can reuse this connection
            return df
        except ImportError:
            print("⚠️ datasets library not installed. Install with: pip install datasets")
            raise
        except Exception as e:
            print(f"⚠️ Error loading from HuggingFace: {e}")
            raise
    
    def filter_exporters_freelancers_smes(self, count: int = 10) -> List[RawPersona]:
        """Filter personas for B2B fintech: business owners, managers, professionals doing international business/payments."""
        print("\n🎯 FILTERING FOR B2B FINTECH PERSONAS")
        print("="*80)
        print("Target: Business decision-makers who use international payment solutions")
        print("-"*80)
        
        self.connect()
        
        # Target: Business decision-makers who would use B2B fintech for international payments
        # Relevant occupations: Business owners, managers (especially export/import), finance professionals, entrepreneurs
        relevant_occupations = [
            'manager, export', 'manager, import', 'export manager', 'import manager',
            'business owner', 'entrepreneur', 'ceo', 'cfo', 'finance manager',
            'managing director', 'director', 'proprietor', 'founder',
            'export agent', 'export consultant', 'international trade',
            'freelance', 'consultant', 'business consultant',
            'accountant', 'chartered accountant', 'finance professional',
            'supply chain manager', 'logistics manager', 'operations manager',
            'procurement manager', 'purchase manager'
        ]
        print(f"✓ Occupation types: {len(relevant_occupations)} categories")
        
        # International business indicators - must have actual business dealings
        business_keywords = [
            'international payment', 'cross-border payment', 'foreign exchange',
            'export business', 'import business', 'international trade',
            'overseas client', 'foreign client', 'global client',
            'international buyer', 'overseas buyer', 'export market',
            'international market', 'global business', 'cross-border',
            'international transaction', 'foreign transaction',
            'remittance', 'wire transfer', 'swift payment'
        ]
        print(f"✓ Business keywords: {len(business_keywords)} international payment indicators")
        
        # Education filter - B2B fintech users are typically educated
        education_filter = """
            (LOWER(education_level) LIKE '%graduate%' 
             OR LOWER(education_level) LIKE '%diploma%'
             OR LOWER(education_level) LIKE '%higher secondary%'
             OR LOWER(education_level) LIKE '%secondary%')
        """
        print(f"✓ Education filter: Graduate/Diploma/Secondary+ required")
        
        # Build SQL filters
        occupation_filter = " OR ".join([f"LOWER(occupation) LIKE '%{kw}%'" for kw in relevant_occupations])
        
        # Try with professional_persona field first, fallback to occupation/skills
        try:
            # Check if professional_persona column exists
            test_query = "SELECT professional_persona FROM personas LIMIT 1"
            self.conn.execute(test_query)
            has_professional = True
        except:
            has_professional = False
        
        # STRICT FILTER: Must have relevant occupation AND (business keywords OR high education)
        if has_professional:
            # Professional persona must contain actual business context
            business_filter = " OR ".join([f"LOWER(professional_persona) LIKE '%{kw}%'" for kw in business_keywords])
            skills_business_filter = " OR ".join([f"LOWER(skills_and_expertise) LIKE '%{kw}%'" for kw in business_keywords])
            
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
            WHERE ({occupation_filter})
                AND ({education_filter})
                AND (({business_filter}) OR ({skills_business_filter}) OR LOWER(occupation) LIKE '%export%' OR LOWER(occupation) LIKE '%import%')
            ORDER BY RANDOM() 
            LIMIT {count * 3}
            """
        else:
            skills_business_filter = " OR ".join([f"LOWER(skills_and_expertise_list) LIKE '%{kw}%'" for kw in business_keywords])
            
            query = f"""
            SELECT 
                uuid, occupation, first_language, second_language, third_language,
                sex, age, marital_status, education_level, education_degree,
                state, district, zone, country,
                hobbies_and_interests_list, skills_and_expertise_list
            FROM personas 
            WHERE ({occupation_filter})
                AND ({education_filter})
                AND ({skills_business_filter} OR LOWER(occupation) LIKE '%export%' OR LOWER(occupation) LIKE '%import%')
            ORDER BY RANDOM() 
            LIMIT {count * 3}
            """
        
        try:
            print(f"\n⏳ Querying database for relevant personas...")
            df = self.conn.execute(query).df()
            print(f"✓ Found {len(df)} initial matches")
            
            # Score and rank personas by relevance
            print(f"\n📊 Scoring personas by B2B fintech relevance...")
            df = self._score_b2b_fintech_relevance(df)
            
            # Take top N by relevance score
            df = df.nsmallest(count, 'relevance_rank')
            
            print(f"\n✅ Selected top {len(df)} most relevant personas:")
            print("="*80)
            for idx, (_, row) in enumerate(df.iterrows(), 1):
                score = row.get('relevance_score', 0)
                print(f"{idx}. {row['occupation']}")
                print(f"   Age: {row['age']}, Education: {row['education_level']}, Zone: {row['zone']}")
                print(f"   Relevance Score: {score:.1f}")
            print("="*80)
            
            if len(df) < count:
                print(f"\n⚠️ Only found {len(df)} matching personas, generating synthetic ones to reach {count}...")
                # Fill with synthetic if needed
                synthetic_needed = count - len(df)
                synthetic = self._generate_exporters_freelancers(synthetic_needed)
                df_synthetic = pd.DataFrame([p.model_dump() for p in synthetic])
                df = pd.concat([df, df_synthetic], ignore_index=True)
            
            personas = []
            for _, row in df.iterrows():
                # Build persona dict with all available fields
                persona_data = {
                    'uuid': str(row['uuid']),
                    'occupation': row['occupation'],
                    'first_language': row['first_language'],
                    'second_language': row.get('second_language'),
                    'third_language': row.get('third_language'),
                    'sex': row['sex'],
                    'age': int(row['age']),
                    'marital_status': row['marital_status'],
                    'education_level': row['education_level'],
                    'education_degree': row.get('education_degree'),
                    'state': row['state'],
                    'district': row['district'],
                    'zone': row['zone'],
                    'country': row.get('country', 'India'),
                }
                
                # Add rich narrative fields if available
                if 'professional_persona' in row and pd.notna(row['professional_persona']):
                    persona_data['professional_persona'] = row['professional_persona']
                if 'linguistic_persona' in row and pd.notna(row['linguistic_persona']):
                    persona_data['linguistic_persona'] = row['linguistic_persona']
                if 'cultural_background' in row and pd.notna(row['cultural_background']):
                    persona_data['cultural_background'] = row['cultural_background']
                if 'sports_persona' in row and pd.notna(row['sports_persona']):
                    persona_data['sports_persona'] = row['sports_persona']
                if 'arts_persona' in row and pd.notna(row['arts_persona']):
                    persona_data['arts_persona'] = row['arts_persona']
                if 'travel_persona' in row and pd.notna(row['travel_persona']):
                    persona_data['travel_persona'] = row['travel_persona']
                if 'culinary_persona' in row and pd.notna(row['culinary_persona']):
                    persona_data['culinary_persona'] = row['culinary_persona']
                if 'persona' in row and pd.notna(row['persona']):
                    persona_data['persona'] = row['persona']
                if 'hobbies_and_interests' in row and pd.notna(row['hobbies_and_interests']):
                    persona_data['hobbies_and_interests'] = row['hobbies_and_interests']
                if 'skills_and_expertise' in row and pd.notna(row['skills_and_expertise']):
                    persona_data['skills_and_expertise'] = row['skills_and_expertise']
                if 'career_goals_and_ambitions' in row and pd.notna(row['career_goals_and_ambitions']):
                    persona_data['career_goals_and_ambitions'] = row['career_goals_and_ambitions']
                if 'linguistic_background' in row and pd.notna(row['linguistic_background']):
                    persona_data['linguistic_background'] = row['linguistic_background']
                if 'hobbies_and_interests_list' in row and pd.notna(row['hobbies_and_interests_list']):
                    persona_data['hobbies_and_interests_list'] = row['hobbies_and_interests_list']
                if 'skills_and_expertise_list' in row and pd.notna(row['skills_and_expertise_list']):
                    persona_data['skills_and_expertise_list'] = row['skills_and_expertise_list']
                
                personas.append(RawPersona(**persona_data))
            
            self.close()
            return personas
            
        except Exception as e:
            print(f"⚠️ Error filtering personas: {e}")
            print("💡 Generating synthetic exporters/freelancers instead...")
            self.close()
            return self._generate_exporters_freelancers(count)
    
    def _score_b2b_fintech_relevance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score and rank personas by relevance to B2B fintech/international payments."""
        
        def calculate_score(row):
            score = 0
            
            # Occupation scoring (higher is better)
            occupation_lower = str(row['occupation']).lower()
            if 'export' in occupation_lower or 'import' in occupation_lower:
                score += 10  # Direct export/import managers are top priority
            if 'manager' in occupation_lower:
                score += 5   # Business managers are good
            if 'owner' in occupation_lower or 'entrepreneur' in occupation_lower or 'director' in occupation_lower:
                score += 8   # Business owners/decision-makers are high priority
            if 'finance' in occupation_lower or 'accountant' in occupation_lower:
                score += 6   # Finance professionals understand payment systems
            if 'consultant' in occupation_lower:
                score += 4   # Consultants may advise on payments
                
            # Exclude manual labor occupations (should be filtered already but double-check)
            manual_labor_keywords = ['forklift', 'driver', 'operator', 'worker', 'labor', 
                                    'carpenter', 'plumber', 'electrician', 'mason',
                                    'weaver', 'tailor', 'dyer', 'carver', 'embroiderer']
            if any(kw in occupation_lower for kw in manual_labor_keywords):
                score -= 100  # Strongly penalize manual labor
            
            # Education scoring
            education = str(row.get('education_level', '')).lower()
            if 'graduate' in education or 'post graduate' in education:
                score += 5
            elif 'diploma' in education:
                score += 3
            elif 'higher secondary' in education or 'secondary' in education:
                score += 2
            else:
                score -= 5  # Penalize low education for B2B fintech
            
            # Age scoring (prime business age is better)
            age = int(row.get('age', 30))
            if 25 <= age <= 55:
                score += 3  # Prime working age for business decision-makers
            elif age < 25:
                score -= 2  # Too young to be decision-maker
            elif age > 60:
                score -= 1  # May be less tech-savvy
            
            # Zone scoring
            zone = str(row.get('zone', '')).lower()
            if 'urban' in zone:
                score += 2  # Urban businesses more likely to use fintech
            
            # Professional persona scoring (if available)
            if 'professional_persona' in row and pd.notna(row['professional_persona']):
                prof = str(row['professional_persona']).lower()
                business_terms = ['international payment', 'cross-border', 'export', 'import', 
                                'international trade', 'overseas', 'global business', 'foreign']
                score += sum(3 for term in business_terms if term in prof)
            
            return score
        
        df['relevance_score'] = df.apply(calculate_score, axis=1)
        df['relevance_rank'] = df['relevance_score'].rank(ascending=False, method='first')
        
        return df
    
    def _generate_exporters_freelancers(self, count: int) -> List[RawPersona]:
        """Generate synthetic exporters/freelancers/SMEs."""
        import random
        import uuid as uuid_lib
        
        occupations = [
            "Export Manager", "Freelance Software Developer", "Export Business Owner",
            "International Freelancer", "SME Export Consultant", "Freelance Designer",
            "Export Agent", "International Business Owner", "Freelance Writer",
            "Export Coordinator", "SME Owner (Export)", "Freelance Consultant"
        ]
        
        states = ["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Delhi"]
        districts = {
            "Maharashtra": ["Mumbai", "Pune"],
            "Karnataka": ["Bengaluru"],
            "Tamil Nadu": ["Chennai"],
            "Gujarat": ["Ahmedabad", "Surat"],
            "Delhi": ["South Delhi", "Central Delhi"]
        }
        
        skills = [
            "International Business, Export Management, Client Relations",
            "Freelancing, Remote Work, International Clients",
            "Export Documentation, International Trade, Business Development"
        ]
        
        personas = []
        for _ in range(count):
            state = random.choice(states)
            district = random.choice(districts[state])
            
            personas.append(RawPersona(
                uuid=str(uuid_lib.uuid4()).replace("-", ""),
                occupation=random.choice(occupations),
                first_language=random.choice(["English", "Hindi", "Gujarati", "Tamil"]),
                second_language=random.choice(["English", "Hindi", None]),
                sex=random.choice(["Male", "Female"]),
                age=random.randint(25, 50),
                marital_status=random.choice(["Currently Married", "Never Married"]),
                education_level=random.choice(["Graduate", "Post Graduate"]),
                state=state,
                district=district,
                zone="Urban",
                hobbies_and_interests_list="Business Networking, Travel",
                skills_and_expertise_list=random.choice(skills)
            ))
        
        return personas
    
    def load_from_json(self, path: Path) -> List[RawPersona]:
        """Load personas from a JSON file (e.g. test_100_personas.json)."""
        import json
        with open(path) as f:
            data = json.load(f)
        personas = []
        for row in data:
            zone = row.get("zone", "Urban")
            if zone not in ("Urban", "Rural"):
                zone = "Urban"
            persona_data = {
                "uuid": str(row["uuid"]),
                "occupation": row["occupation"],
                "first_language": row.get("first_language", "English"),
                "sex": row["sex"],
                "age": int(row["age"]),
                "marital_status": row.get("marital_status", "Unknown"),
                "education_level": row.get("education_level", "Graduate & above"),
                "state": row["state"],
                "district": row["district"],
                "zone": zone,
                "country": "India",
            }
            if row.get("professional_persona"):
                persona_data["professional_persona"] = row["professional_persona"]
            if row.get("cultural_background"):
                persona_data["cultural_background"] = row["cultural_background"]
            if row.get("hobbies_and_interests"):
                persona_data["hobbies_and_interests"] = row["hobbies_and_interests"]
            if row.get("skills_and_expertise"):
                persona_data["skills_and_expertise"] = row["skills_and_expertise"]
                persona_data["skills_and_expertise_list"] = row["skills_and_expertise"]
            if row.get("career_goals_and_ambitions"):
                persona_data["career_goals_and_ambitions"] = row["career_goals_and_ambitions"]
            personas.append(RawPersona(**persona_data))
        return personas

    def load_sample_personas(self, count: int = 1000) -> List[RawPersona]:
        """Load a random sample of personas with full narrative context."""
        self.connect()
        
        # Check if table exists
        try:
            # Try to get all rich fields if they exist
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
            ORDER BY RANDOM() 
            LIMIT {count}
            """
            
            df = self.conn.execute(query).df()
            
            personas = []
            for _, row in df.iterrows():
                # Build persona dict with all available fields
                persona_data = {
                    'uuid': str(row['uuid']),
                    'occupation': row['occupation'],
                    'first_language': row['first_language'],
                    'second_language': row.get('second_language'),
                    'third_language': row.get('third_language'),
                    'sex': row['sex'],
                    'age': int(row['age']),
                    'marital_status': row['marital_status'],
                    'education_level': row['education_level'],
                    'education_degree': row.get('education_degree'),
                    'state': row['state'],
                    'district': row['district'],
                    'zone': row['zone'],
                    'country': row.get('country', 'India'),
                }
                
                # Add rich narrative fields if available
                if 'professional_persona' in row and pd.notna(row['professional_persona']):
                    persona_data['professional_persona'] = row['professional_persona']
                if 'linguistic_persona' in row and pd.notna(row['linguistic_persona']):
                    persona_data['linguistic_persona'] = row['linguistic_persona']
                if 'cultural_background' in row and pd.notna(row['cultural_background']):
                    persona_data['cultural_background'] = row['cultural_background']
                if 'sports_persona' in row and pd.notna(row['sports_persona']):
                    persona_data['sports_persona'] = row['sports_persona']
                if 'arts_persona' in row and pd.notna(row['arts_persona']):
                    persona_data['arts_persona'] = row['arts_persona']
                if 'travel_persona' in row and pd.notna(row['travel_persona']):
                    persona_data['travel_persona'] = row['travel_persona']
                if 'culinary_persona' in row and pd.notna(row['culinary_persona']):
                    persona_data['culinary_persona'] = row['culinary_persona']
                if 'persona' in row and pd.notna(row['persona']):
                    persona_data['persona'] = row['persona']
                if 'hobbies_and_interests' in row and pd.notna(row['hobbies_and_interests']):
                    persona_data['hobbies_and_interests'] = row['hobbies_and_interests']
                if 'skills_and_expertise' in row and pd.notna(row['skills_and_expertise']):
                    persona_data['skills_and_expertise'] = row['skills_and_expertise']
                if 'career_goals_and_ambitions' in row and pd.notna(row['career_goals_and_ambitions']):
                    persona_data['career_goals_and_ambitions'] = row['career_goals_and_ambitions']
                if 'linguistic_background' in row and pd.notna(row['linguistic_background']):
                    persona_data['linguistic_background'] = row['linguistic_background']
                if 'hobbies_and_interests_list' in row and pd.notna(row['hobbies_and_interests_list']):
                    persona_data['hobbies_and_interests_list'] = row['hobbies_and_interests_list']
                if 'skills_and_expertise_list' in row and pd.notna(row['skills_and_expertise_list']):
                    persona_data['skills_and_expertise_list'] = row['skills_and_expertise_list']
                
                personas.append(RawPersona(**persona_data))
            
            self.close()
            return personas
            
        except Exception as e:
            print(f"⚠️ Error loading personas: {e}")
            print("💡 Generating synthetic personas instead...")
            self.close()
            return self._generate_synthetic_personas(count)
    
    def filter_by_keywords(self, keywords: List[str], count: int = 10) -> List[RawPersona]:
        """
        Filter personas from the DB whose occupation or professional_persona
        matches any of the provided keywords (case-insensitive LIKE).
        Falls back to load_sample_personas if no matches found.
        """
        if not self.conn:
            self.connect()

        # Build LIKE clauses across occupation and professional_persona
        conditions = []
        for kw in keywords[:10]:  # cap to avoid overly large queries
            safe = kw.replace("'", "''")
            conditions.append(f"LOWER(occupation) LIKE '%{safe}%'")
            conditions.append(f"LOWER(COALESCE(professional_persona, '')) LIKE '%{safe}%'")
            conditions.append(f"LOWER(COALESCE(skills_and_expertise, '')) LIKE '%{safe}%'")

        where_clause = " OR ".join(conditions)

        try:
            base_cols = (
                "uuid, occupation, first_language, second_language, third_language, "
                "sex, age, marital_status, education_level, education_degree, "
                "state, district, zone, country"
            )
            # Try with rich narrative columns
            try:
                df = self.conn.execute(
                    f"SELECT {base_cols}, professional_persona, linguistic_persona, "
                    f"cultural_background, sports_persona, arts_persona, travel_persona, "
                    f"culinary_persona, persona, hobbies_and_interests_list, "
                    f"skills_and_expertise_list, hobbies_and_interests, skills_and_expertise, "
                    f"career_goals_and_ambitions, linguistic_background "
                    f"FROM personas WHERE {where_clause} LIMIT {count * 3}"
                ).df()
            except Exception:
                df = self.conn.execute(
                    f"SELECT {base_cols} FROM personas WHERE {where_clause} LIMIT {count * 3}"
                ).df()

            if df.empty:
                self.close()
                return self.load_sample_personas(count=count)

            df = df.sample(min(count, len(df))).reset_index(drop=True)
            personas = []
            for _, row in df.iterrows():
                try:
                    persona_data = {
                        "uuid": str(row["uuid"]),
                        "occupation": row["occupation"],
                        "first_language": row["first_language"],
                        "second_language": row.get("second_language"),
                        "third_language": row.get("third_language"),
                        "sex": row["sex"],
                        "age": int(row["age"]),
                        "marital_status": row["marital_status"],
                        "education_level": row["education_level"],
                        "education_degree": row.get("education_degree"),
                        "state": row["state"],
                        "district": row["district"],
                        "zone": row["zone"],
                        "country": row.get("country", "India"),
                    }
                    for field in (
                        "professional_persona", "linguistic_persona", "cultural_background",
                        "sports_persona", "arts_persona", "travel_persona", "culinary_persona",
                        "persona", "hobbies_and_interests_list", "skills_and_expertise_list",
                        "hobbies_and_interests", "skills_and_expertise",
                        "career_goals_and_ambitions", "linguistic_background",
                    ):
                        if field in row and pd.notna(row[field]):
                            persona_data[field] = row[field]
                    personas.append(RawPersona(**persona_data))
                except Exception:
                    continue
            self.close()
            return personas if personas else self.load_sample_personas(count=count)
        except Exception as exc:
            print(f"[PERSONA] [filter_by_keywords] FAILED | error={exc!r} | error_type={type(exc).__name__}")
            self.close()
            print(f"[PERSONA] [filter_by_keywords] Falling back to load_sample_personas(count={count})")
            return self.load_sample_personas(count=count)

    def _generate_synthetic_personas(self, count: int) -> List[RawPersona]:
        """Generate synthetic personas for demo purposes."""
        import random
        import uuid as uuid_lib
        
        occupations = [
            "Software Engineer", "Teacher", "Farmer", "Small Business Owner",
            "Student", "Doctor", "Driver", "Sales Agent", "Manager",
            "Construction Worker", "Shop Owner", "Accountant"
        ]
        
        states = [
            "Maharashtra", "Karnataka", "Tamil Nadu", "West Bengal",
            "Gujarat", "Uttar Pradesh", "Delhi", "Punjab", "Rajasthan"
        ]
        
        districts = {
            "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
            "Karnataka": ["Bengaluru", "Mysore", "Hubli"],
            "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
            "West Bengal": ["Kolkata", "Howrah", "Siliguri"],
            "Gujarat": ["Ahmedabad", "Surat", "Rajkot"],
            "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
            "Delhi": ["Central Delhi", "South Delhi", "North Delhi"],
            "Punjab": ["Ludhiana", "Amritsar", "Jalandhar"],
            "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"]
        }
        
        education_levels = [
            "Illiterate", "Primary", "Matric/Secondary", 
            "Higher Secondary", "Graduate", "Post Graduate"
        ]
        
        languages = ["Hindi", "English", "Bengali", "Tamil", "Telugu", "Marathi", "Gujarati"]
        
        personas = []
        for _ in range(count):
            state = random.choice(states)
            district = random.choice(districts[state])
            zone = random.choice(["Urban", "Rural"])
            
            personas.append(RawPersona(
                uuid=str(uuid_lib.uuid4()).replace("-", ""),
                occupation=random.choice(occupations),
                first_language=random.choice(languages),
                second_language=random.choice(languages + [None]),
                sex=random.choice(["Male", "Female"]),
                age=random.randint(18, 65),
                marital_status=random.choice(["Currently Married", "Never Married", "Divorced"]),
                education_level=random.choice(education_levels),
                state=state,
                district=district,
                zone=zone,
                hobbies_and_interests_list="Reading, Sports",
                skills_and_expertise_list="Communication, Problem Solving"
            ))
        
        return personas


# Global singleton
data_loader = PersonaDataLoader()
