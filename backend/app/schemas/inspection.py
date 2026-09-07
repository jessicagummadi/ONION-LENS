from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.app.schemas.analysis import DefectSummary, OnionBulbItem

class InspectionCreate(BaseModel):
    id: Optional[str] = None
    lot_id: str
    inspector_id: Optional[str] = "INSP-APMC-8492"
    quantity_kg: Optional[str] = "500 kg"
    variety: Optional[str] = "Nashik Red"
    grade: str
    grade_name: str
    quality_score: int
    total_onions: int
    healthy_onions: int
    defective_onions: int
    avg_diameter: str
    color_uniformity: str
    defects: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    image_data_url: Optional[str] = None

class InspectionListItem(BaseModel):
    id: str
    lot_id: str
    inspector_id: str
    timestamp: str
    quantity_kg: str
    variety: str
    grade: str
    grade_name: str
    quality_score: int
    total_onions: int
    healthy_onions: int
    defective_onions: int
    avg_diameter: str
    color_uniformity: str
    defects: Dict[str, Any]
    recommendations: List[str]
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class InspectionDetailResponse(InspectionListItem):
    detections: List[OnionBulbItem] = []
