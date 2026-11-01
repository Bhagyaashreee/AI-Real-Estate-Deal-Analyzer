"""
CLI script to safely seed simulated Indian properties into the local SQLite database.
Usage:
    cd backend
    python seed.py
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, init_db
from app.services.seed_data import seed_demo_properties


def main():
    print("=" * 60)
    print("AI Real Estate Deal Analyzer - Database Seeder")
    print("=" * 60)
    print("Initializing SQLite database tables...")
    init_db()

    db = SessionLocal()
    try:
        print("Seeding simulated Indian property listings...")
        result = seed_demo_properties(db)
        print(f"-> Successfully inserted: {result['inserted']} properties")
        print(f"-> Skipped (already exist): {result['skipped']} properties")
        print(f"-> Total demo catalog size: {result['total_demo_catalog']} properties")
        print("Note: All seeded records are marked as 'DEMO DATA' for simulation purposes only.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

