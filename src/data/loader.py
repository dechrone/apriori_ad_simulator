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
            self.close()
            return df
        except ImportError:
            print("⚠️ datasets library not installed. Install with: pip install datasets")
            raise
        except Exception as e:
            print(f"⚠️ Error loading from HuggingFace: {e}")
            raise
    
    def filter_exporters_freelancers_smes(self, count: int = 10) -> List[RawPersona]:
        """Filter personas for exporters, freelancers, SMEs doing business outside India."""
        self.connect()
        
        # STRICT filter: Must have international/overseas/export context
        # Not just "freelance" but "freelance" + international indicators
        international_keywords = [
            'international client', 'overseas client', 'global client', 'foreign client',
            'export business', 'exporting', 'international trade', 'cross-border',
            'offshore', 'overseas', 'international market', 'export market',
            'international business', 'global business', 'foreign market'
        ]
        
        # Occupation keywords (must be export-related)
        export_occupations = ['export', 'exporter', 'export manager', 'export agent', 
                            'export consultant', 'international trade']
        
        # Build SQL filter - require BOTH freelance/export AND international context
        occupation_filter = " OR ".join([f"LOWER(occupation) LIKE '%{kw}%'" for kw in export_occupations])
        
        # Professional persona must contain international business context
        professional_filter = " OR ".join([f"LOWER(professional_persona) LIKE '%{kw}%'" for kw in international_keywords])
        
        # Skills must indicate international work
        skills_filter = " OR ".join([f"LOWER(skills_and_expertise_list) LIKE '%{kw}%'" for kw in international_keywords])
        
        # Try with professional_persona field first, fallback to occupation/skills
        try:
            # Check if professional_persona column exists
            test_query = "SELECT professional_persona FROM personas LIMIT 1"
            self.conn.execute(test_query)
            has_professional = True
        except:
            has_professional = False
        
        # Require international context in professional_persona OR skills
        # OR explicit export occupation
        if has_professional:
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
            WHERE ({occupation_filter} OR ({professional_filter}) OR ({skills_filter}))
            ORDER BY RANDOM() 
            LIMIT {count}
            """
        else:
            query = f"""
            SELECT 
                uuid, occupation, first_language, second_language, third_language,
                sex, age, marital_status, education_level, education_degree,
                state, district, zone, country,
                hobbies_and_interests_list, skills_and_expertise_list
            FROM personas 
            WHERE ({occupation_filter} OR {skills_filter})
            ORDER BY RANDOM() 
            LIMIT {count}
            """
        
        try:
            df = self.conn.execute(query).df()
            
            if len(df) < count:
                print(f"⚠️ Only found {len(df)} matching personas, generating synthetic ones to reach {count}...")
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
