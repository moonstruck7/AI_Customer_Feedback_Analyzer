"""
Bootstrap utility to initialize database tables and populate sample feedback data
"""
from app.database import engine, Base, SessionLocal
from app.main import seed_initial_data
from app.models import Source
from app.services.ingestion import ingest_csv_content

def initialize():
    print("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    print("Seeding default roles, sources, and themes...")
    seed_initial_data()

    db = SessionLocal()
    try:
        # Check if already populated
        from app.models import FeedbackItem
        if db.query(FeedbackItem).count() == 0:
            print("Populating initial realistic feedback data from CSV...")
            with open("sample_data/customer_feedback_sample.csv", "r", encoding="utf-8") as f:
                csv_text = f.read()

            source = db.query(Source).filter(Source.source_type == "csv").first()
            # pyrefly: ignore[bad-argument-type]
            source_id = int(source.source_id) if source else 1
            stats = ingest_csv_content(db, source_id, csv_text)
            print(f"Dataset successfully ingested: {stats}")
        else:
            print(f"Database already contains {db.query(FeedbackItem).count()} feedback items.")
    finally:
        db.close()

if __name__ == "__main__":
    initialize()
