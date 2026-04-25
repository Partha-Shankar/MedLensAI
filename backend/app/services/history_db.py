from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json, datetime
from app.utils.helpers import get_logger

logger = get_logger("HISTORY_DB")

DATABASE_URL = "sqlite:///./medlens_history.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)      # bcrypt hash
    name = Column(String)
    blood_group = Column(String, nullable=True)
    allergies = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)
    current_meds = Column(Text, nullable=True)
    emergency_contact = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PrescriptionHistory(Base):
    __tablename__ = "prescription_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=True)    # null for guest
    session_id = Column(String, index=True, nullable=True)  # for guest tracking
    patient_name = Column(String)
    patient_age = Column(String)
    prescriber = Column(String)
    prescription_date = Column(String)
    medications_json = Column(Text)          # JSON string of medications array
    interactions_json = Column(Text)         # JSON string of interactions found
    validity_score = Column(String)
    overall_confidence = Column(Float)
    raw_extraction_json = Column(Text)       # Full extraction JSON
    image_thumbnail_b64 = Column(Text)       # Base64 thumbnail (resized to 200px)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def save_prescription(user_id: int | None, session_id: str, data: dict, 
                      image_b64: str = "") -> int:
    db = SessionLocal()
    try:
        meds = data.get("Medications", [])
        record = PrescriptionHistory(
            user_id=user_id,
            session_id=session_id,
            patient_name=data.get("PatientName", ""),
            patient_age=data.get("Age", ""),
            prescriber=data.get("PrescriberName", ""),
            prescription_date=data.get("Date", ""),
            medications_json=json.dumps(meds),
            interactions_json=json.dumps(data.get("interactions", [])),
            validity_score=str(data.get("validity_score", "")),
            overall_confidence=data.get("overall_confidence", 0.0),
            raw_extraction_json=json.dumps(data),
            image_thumbnail_b64=image_b64,
            created_at=datetime.datetime.utcnow()
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"[HISTORY_DB] Saved prescription id={record.id} for user_id={user_id}")
        return record.id
    finally:
        db.close()

def get_user_history(user_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        records = db.query(PrescriptionHistory)\
            .filter(PrescriptionHistory.user_id == user_id)\
            .order_by(PrescriptionHistory.created_at.desc())\
            .all()
        return [_record_to_dict(r) for r in records]
    finally:
        db.close()

def _record_to_dict(r: PrescriptionHistory) -> dict:
    return {
        "id": r.id,
        "patient_name": r.patient_name,
        "patient_age": r.patient_age,
        "prescriber": r.prescriber,
        "prescription_date": r.prescription_date,
        "medications": json.loads(r.medications_json or "[]"),
        "interactions": json.loads(r.interactions_json or "[]"),
        "validity_score": r.validity_score,
        "overall_confidence": r.overall_confidence,
        "image_thumbnail_b64": r.image_thumbnail_b64,
        "created_at": r.created_at.isoformat()
    }

def get_user_profile(user_id: int) -> dict | None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "blood_group": user.blood_group,
            "allergies": user.allergies,
            "conditions": user.conditions,
            "current_meds": user.current_meds,
            "emergency_contact": user.emergency_contact
        }
    finally:
        db.close()

def update_user_profile(user_id: int, profile_data: dict) -> dict | None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        if "blood_group" in profile_data:
            user.blood_group = profile_data["blood_group"]
        if "allergies" in profile_data:
            user.allergies = profile_data["allergies"]
        if "conditions" in profile_data:
            user.conditions = profile_data["conditions"]
        if "current_meds" in profile_data:
            user.current_meds = profile_data["current_meds"]
        if "emergency_contact" in profile_data:
            user.emergency_contact = profile_data["emergency_contact"]
            
        db.commit()
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "blood_group": user.blood_group,
            "allergies": user.allergies,
            "conditions": user.conditions,
            "current_meds": user.current_meds,
            "emergency_contact": user.emergency_contact
        }
    finally:
        db.close()
