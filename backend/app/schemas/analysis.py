from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DefectItem(BaseModel):
    type: str
    confidence: float
    severity: str = "medium"
    affected_area_pct: float = 0.0

class OnionBulbItem(BaseModel):
    onion_id: int
    confidence: float
    is_healthy: bool
    diameter_mm: float
    bbox: List[float] = Field(default_factory=list) # [x, y, w, h]
    center_x_pct: float
    center_y_pct: float
    grade: str # GRADE_A, URS, NOT_ELIGIBLE
    grade_name: str
    grade_badge_class: str
    issues: str
    defects: List[DefectItem] = Field(default_factory=list)

class DefectSummary(BaseModel):
    type: str
    label: str
    affected_onion_count: int
    percentage: float

class AnalysisResponse(BaseModel):
    inspection_id: str
    lot_id: str
    timestamp: str
    is_onion: bool
    error_message: Optional[str] = None
    
    # Core count metrics
    total_onions: int
    healthy_onions: int
    defective_onions: int # Unique count of defective onions!

    quality_score: int
    grade: str
    grade_name: str
    grade_badge_class: str
    avg_diameter: str
    color_uniformity: str

    defects: List[DefectSummary]
    defect_counts: Dict[str, int] # e.g. {"sprouting": 3, "mold": 2, ...}
    defect_percentages: Dict[str, str] # e.g. {"sprouting": "15%", ...}
    
    individual_bulbs: List[OnionBulbItem]
    hotspots: List[Dict[str, Any]]
    recommendations: List[str]
    
    image_url: Optional[str] = None
    ai_model_status: str
    ai_model_backend: str
