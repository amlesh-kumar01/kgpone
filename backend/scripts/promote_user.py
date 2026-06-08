import sys
import os

# Add the parent directory to the python path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.database import SessionLocal
from src.infrastructure.models import User, UserRole

def promote_user(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Error: User with email '{email}' not found.")
            return

        user.role = UserRole.PUBLISHER
        user.can_upload = True
        db.commit()
        print(f"Success! User '{email}' has been promoted to PUBLISHER.")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_user.py <email>")
    else:
        promote_user(sys.argv[1])
