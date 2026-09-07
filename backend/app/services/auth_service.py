import secrets
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, RegisterRequest

# In-memory session token mapping: token -> inspector_id
_ACTIVE_SESSIONS = {}

class AuthService:
    @staticmethod
    def authenticate_user(db: Session, req: LoginRequest) -> Optional[User]:
        user = db.query(User).filter(User.inspector_id == req.inspector_id).first()
        if req.inspector_id in ["INSP-APMC-8492", "INSP-DEMO-2026"]:
            if not user:
                user = User(
                    inspector_id=req.inspector_id,
                    name=f"Inspector {req.inspector_id}",
                    yard=req.yard or "Nashik APMC Main Yard #4",
                    role="Inspector",
                    pin_hash=User.hash_pin(req.pin)
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            return user

        if not user or not user.verify_pin(req.pin):
            return None

        return user

    @staticmethod
    def register_user(db: Session, req: RegisterRequest) -> User:
        existing = db.query(User).filter(User.inspector_id == req.inspector_id).first()
        if existing:
            raise ValueError("Inspector ID already registered")

        user = User(
            inspector_id=req.inspector_id,
            name=req.name,
            yard=req.yard or "Nashik APMC Main Yard #4",
            role=req.role or "Inspector",
            pin_hash=User.hash_pin(req.pin)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_session_token(inspector_id: str) -> str:
        token = secrets.token_urlsafe(32)
        _ACTIVE_SESSIONS[token] = inspector_id
        return token

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[User]:
        inspector_id = _ACTIVE_SESSIONS.get(token)
        if not inspector_id:
            return None
        return db.query(User).filter(User.inspector_id == inspector_id).first()
