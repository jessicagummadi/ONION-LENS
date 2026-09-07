from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(String(64), primary_key=True, index=True)
    lot_id = Column(String(64), index=True, nullable=False)
    inspector_id = Column(String(64), default="INSP-APMC-8492")
    timestamp = Column(String(64), nullable=False)
    quantity_kg = Column(String(32), default="500 kg")
    variety = Column(String(64), default="Nashik Red")

    # Count-first core metrics
    total_onions = Column(Integer, default=0)
    healthy_onions = Column(Integer, default=0)
    defective_onions = Column(Integer, default=0)

    quality_score = Column(Integer, default=0)
    grade = Column(String(32), nullable=False)
    grade_name = Column(String(64), nullable=False)
    avg_diameter = Column(String(32), default="0 mm")
    color_uniformity = Column(String(32), default="0%")

    defects_json = Column(Text, default="{}")
    recommendations_json = Column(Text, default="[]")
    image_path = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    detections = relationship("OnionDetection", back_populates="inspection", cascade="all, delete-orphan")
    defects = relationship("OnionDefect", back_populates="inspection", cascade="all, delete-orphan")


class OnionDetection(Base):
    __tablename__ = "onion_detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    inspection_id = Column(String(64), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    onion_id = Column(Integer, nullable=False)  # 1, 2, 3...
    confidence = Column(Float, default=0.90)
    is_healthy = Column(Boolean, default=True)

    # Bounding Box Coordinates (pixels or normalized)
    bbox_x = Column(Float, default=0.0)
    bbox_y = Column(Float, default=0.0)
    bbox_width = Column(Float, default=0.0)
    bbox_height = Column(Float, default=0.0)

    # Percentage coordinates for UI pins
    center_x_pct = Column(Float, default=0.0)
    center_y_pct = Column(Float, default=0.0)
    diameter_mm = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="detections")
    defects = relationship("OnionDefect", back_populates="detection", cascade="all, delete-orphan")


class OnionDefect(Base):
    __tablename__ = "onion_defects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    inspection_id = Column(String(64), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    onion_detection_id = Column(Integer, ForeignKey("onion_detections.id", ondelete="CASCADE"), nullable=False)
    defect_type = Column(String(64), nullable=False)  # sprouting, mold, mechanical_damage, skin_peeling, etc.
    confidence = Column(Float, default=0.85)
    severity = Column(String(32), default="medium")   # low, medium, high
    affected_area_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="defects")
    detection = relationship("OnionDetection", back_populates="defects")
