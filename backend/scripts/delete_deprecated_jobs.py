from src.infrastructure.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("DELETE FROM ingestion_jobs WHERE stage IN ('FORMULA', 'QUESTION', 'QUALITY')"))
    db.commit()
    print("Deleted old deprecated jobs")
except Exception as e:
    print("Error:", e)
finally:
    db.close()
