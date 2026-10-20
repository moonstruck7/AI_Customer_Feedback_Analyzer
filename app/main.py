import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.models import User, Source, Theme
from app.routers import auth, feedback, analytics, alerts, sources
from app.nlp.theme_clusterer import DEFAULT_THEME_DEFINITIONS

def seed_initial_data():
    """
    Seeds initial system roles, default sources, and core theme clusters.
    """
    db = SessionLocal()
    try:
        # Seed 3 Primary Stakeholders (Section 5.1, Table 2)
        if db.query(User).count() == 0:
            users = [
                User(name="Aarav Sharma", email="owner@quickretail.com", password_hash="hash_owner", role="SMB Owner"),
                User(name="Pooja Verma", email="support@quickretail.com", password_hash="hash_support", role="Support Manager"),
                User(name="Kiran Patil", email="admin@quickretail.com", password_hash="hash_admin", role="System Admin")
            ]
            db.add_all(users)
            db.commit()

        # Seed Default Channels / Sources
        owner = db.query(User).filter(User.role == "SMB Owner").first()
        owner_id = owner.user_id if owner else 1

        if db.query(Source).count() == 0:
            demo_sources = [
                Source(user_id=owner_id, source_type="google_play", name="Google Play Store App", api_config='{"package": "com.quickretail.app"}'),
                Source(user_id=owner_id, source_type="google_business", name="Google Maps / Business Profile", api_config='{"place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"}'),
                Source(user_id=owner_id, source_type="helpdesk", name="Zendesk Support Webhook", api_config='{"endpoint": "/api/webhook/helpdesk"}'),
                Source(user_id=owner_id, source_type="survey", name="NPS Quarterly Customer Survey", api_config='{"survey_id": "nps-q4-2026"}'),
                Source(user_id=owner_id, source_type="csv", name="Bulk Customer Feedback CSV", api_config='{"type": "manual_upload"}')
            ]
            db.add_all(demo_sources)
            db.commit()

        # Seed Core Theme Categories
        if db.query(Theme).count() == 0:
            for t_def in DEFAULT_THEME_DEFINITIONS:
                theme = Theme(label=t_def["label"], keywords=t_def["keywords"])
                db.add(theme)
            db.commit()

    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    # Seed initial data
    seed_initial_data()
    yield

app = FastAPI(
    title="AI Customer Feedback Analyzer",
    description="Lightweight NLP & Machine Learning decision-support system for SMBs",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(feedback.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(sources.router)

# Mount Static Files (Frontend UI)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
