"""Initialize database with HuggingFace personas dataset."""

import sys
from pathlib import Path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.data.loader import data_loader

def main():
    print("\n" + "="*100)
    print("📥 INITIALIZING DATABASE WITH HUGGINGFACE PERSONAS")
    print("="*100)
    print("\nThis will download and load the Nvidia Nemotron Personas India dataset.")
    print("Dataset size: ~15,000 rich Indian personas")
    print("This may take a few minutes...\n")
    
    try:
        data_loader.load_from_huggingface()
        print("\n✅ Database initialized successfully!")
        print(f"📍 Location: {data_loader.db_path}")
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
