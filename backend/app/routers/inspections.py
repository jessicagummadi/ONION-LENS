import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models.inspection import Inspection, OnionDetection, OnionDefect
from backend.app.schemas.inspection import InspectionCreate, InspectionListItem, InspectionDetailResponse

router = APIRouter(prefix="/api/inspections", tags=["inspections"])

@router.get("", response_model=dict)
def get_inspections(
    filter_grade: Optional[str] = Query("all", alias="filter"),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Inspection)

    if filter_grade and filter_grade != "all":
        grade_map = {
            "grade-a": "GRADE_A",
            "urs": "URS",
            "not-eligible": "NOT_ELIGIBLE"
        }
        target_grade = grade_map.get(filter_grade.lower(), filter_grade.upper())
        query = query.filter(Inspection.grade == target_grade)

    if search:
        search_str = f"%{search.strip().lower()}%"
        query = query.filter(Inspection.lot_id.ilike(search_str))

    records = query.order_by(desc(Inspection.created_at)).limit(limit).all()

    items = []
    for r in records:
        defects_dict = {}
        try:
            defects_dict = json.loads(r.defects_json) if r.defects_json else {}
        except Exception:
            pass

        recs_list = []
        try:
            recs_list = json.loads(r.recommendations_json) if r.recommendations_json else []
        except Exception:
            pass

        items.append({
            "id": r.id,
            "lotId": r.lot_id,
            "inspectorId": r.inspector_id,
            "timestamp": r.timestamp,
            "quantityKg": r.quantity_kg,
            "variety": r.variety,
            "grade": r.grade,
            "gradeName": r.grade_name,
            "qualityScore": r.quality_score,
            "totalOnions": r.total_onions,
            "healthyOnions": r.healthy_onions,
            "defectiveOnions": r.defective_onions,
            "bulbCount": r.total_onions,
            "avgDiameter": r.avg_diameter,
            "colorUniformity": r.color_uniformity,
            "defects": defects_dict,
            "recommendations": recs_list,
            "image": r.image_path or "/static/images/samples/sample-lot-grade-a.jpg"
        })

    return {"success": True, "inspections": items}

@router.get("/{inspection_id}")
def get_inspection_detail(inspection_id: str, db: Session = Depends(get_db)):
    record = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inspection record not found")

    defects_dict = {}
    try:
        defects_dict = json.loads(record.defects_json) if record.defects_json else {}
    except Exception:
        pass

    recs_list = []
    try:
        recs_list = json.loads(record.recommendations_json) if record.recommendations_json else []
    except Exception:
        pass

    detections = []
    for d in record.detections:
        defect_items = []
        for df in d.defects:
            defect_items.append({
                "type": df.defect_type,
                "confidence": df.confidence,
                "severity": df.severity,
                "affected_area_pct": df.affected_area_pct
            })

        detections.append({
            "onion_id": d.onion_id,
            "confidence": d.confidence,
            "is_healthy": d.is_healthy,
            "diameter_mm": d.diameter_mm,
            "bbox": [d.bbox_x, d.bbox_y, d.bbox_width, d.bbox_height],
            "center_x_pct": d.center_x_pct,
            "center_y_pct": d.center_y_pct,
            "grade": "GRADE_A" if d.is_healthy else "NOT_ELIGIBLE",
            "grade_name": "Grade A" if d.is_healthy else "Not Eligible",
            "issues": "Healthy" if d.is_healthy else ", ".join([x["type"] for x in defect_items]),
            "defects": defect_items
        })

    return {
        "success": True,
        "inspection": {
            "id": record.id,
            "lotId": record.lot_id,
            "inspectorId": record.inspector_id,
            "timestamp": record.timestamp,
            "quantityKg": record.quantity_kg,
            "variety": record.variety,
            "grade": record.grade,
            "gradeName": record.grade_name,
            "qualityScore": record.quality_score,
            "totalOnions": record.total_onions,
            "healthyOnions": record.healthy_onions,
            "defectiveOnions": record.defective_onions,
            "bulbCount": record.total_onions,
            "avgDiameter": record.avg_diameter,
            "colorUniformity": record.color_uniformity,
            "defects": defects_dict,
            "recommendations": recs_list,
            "image": record.image_path,
            "individualBulbs": detections
        }
    }

@router.delete("/{inspection_id}")
def delete_inspection(inspection_id: str, db: Session = Depends(get_db)):
    record = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inspection not found")
    db.delete(record)
    db.commit()
    return {"success": True, "message": f"Inspection {inspection_id} deleted successfully"}
