import hashlib
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    inspector_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    yard = Column(String(128), default="Nashik APMC Main Yard #4")
    role = Column(String(64), default="Inspector")
    pin_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def hash_pin(pin: str) -> str:
        # Standard SHA256 hashing for PIN security
        return hashlib.sha256(pin.encode("utf-8")).hexdigest()

    def verify_pin(self, pin: str) -> bool:
        return self.pin_hash == self.hash_pin(pin)
