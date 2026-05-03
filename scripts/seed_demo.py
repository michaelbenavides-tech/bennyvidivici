from app.db import SessionLocal
from app.main import seed_demo

with SessionLocal() as db:
    seed_demo(db)
    print("Seeded AI-SGP demo data")
