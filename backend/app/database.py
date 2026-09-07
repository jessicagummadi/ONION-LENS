from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models before create_all
    from backend.app.models.user import User
    from backend.app.models.inspection import Inspection, OnionDetection, OnionDefect
    Base.metadata.create_all(bind=engine)

    # Seed default inspector if not present
    db = SessionLocal()
    try:
        demo_user = db.query(User).filter(User.inspector_id == "INSP-APMC-8492").first()
        if not demo_user:
            default_user = User(
                inspector_id="INSP-APMC-8492",
                name="Nashik APMC Official Inspector",
                yard="Nashik APMC Main Yard #4",
                role="Senior Inspector",
                pin_hash=User.hash_pin("1234")
            )
            guest_user = User(
                inspector_id="INSP-DEMO-2026",
                name="Guest Inspector",
                yard="Nashik APMC Main Yard #4",
                role="Guest Inspector",
                pin_hash=User.hash_pin("1234")
            )
            db.add(default_user)
            db.add(guest_user)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"[DB INIT] Error seeding initial users: {e}")
    finally:
        db.close()
