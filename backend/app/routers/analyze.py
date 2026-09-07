import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.analysis import AnalysisResponse
from backend.app.services.cv_pipeline import ComputerVisionPipeline
from backend.app.utils.image_utils import decode_image, save_uploaded_image
from backend.app.models.inspection import Inspection, OnionDetection, OnionDefect

router = APIRouter(prefix="/api", tags=["analyze"])
pipeline = ComputerVisionPipeline()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_onion_lot(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Real Computer Vision analysis endpoint:
    - Accepts both application/json and multipart/form-data.
    - Segments individual onion bulbs using OpenCV Watershed.
    - Classifies individual bulb defects (sprouting, mold/rot, damage, peeling).
    - Counts individual bulbs affected (rule: individual onion counts first!).
    - Calculates deterministic AGMARK grade and quality score.
    - Persists inspection, detections, and defect records to SQLite database.
    """
    raw_image = None
    lot_id = None
    variety = "Nashik Red"
    quantity_kg = "500 kg"
    inspector_id = "INSP-APMC-8492"

    content_type = request.headers.get("content-type", "")

    try:
        if "multipart/form-data" in content_type:
            form = await request.form()
            file = form.get("file")
            image_data = form.get("image_data") or form.get("image")
            lot_id = form.get("lot_id") or form.get("lotId")
            variety = form.get("variety") or "Nashik Red"
            quantity_kg = form.get("quantity_kg") or form.get("quantityKg") or "500 kg"
            inspector_id = form.get("inspector_id") or form.get("inspector") or "INSP-APMC-8492"

            if file and hasattr(file, "read"):
                file_bytes = await file.read()
                raw_image = decode_image(file_bytes)
            elif image_data:
                raw_image = decode_image(str(image_data))
        else:
            # application/json
            body = await request.json()
            image_data = body.get("image") or body.get("image_data")
            lot_id = body.get("lot_id") or body.get("lotId")
            variety = body.get("variety") or "Nashik Red"
            quantity_kg = body.get("quantity_kg") or body.get("quantityKg") or "500 kg"
            inspector_id = body.get("inspector_id") or body.get("inspector") or "INSP-APMC-8492"

            if image_data:
                raw_image = decode_image(str(image_data))
    except Exception as parse_err:
        print(f"[REQUEST PARSE ERROR] {parse_err}")
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse request: {str(parse_err)}"
        )

    if raw_image is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid image input. Provide a valid JPEG/PNG file or base64 data."
        )

    # Save image to uploads folder
    rel_url, abs_path = save_uploaded_image(raw_image, prefix="lot")

    # Generate lot ID if not provided
    now = datetime.now()
    if not lot_id or lot_id == "auto":
        lot_id = f"LOT-{now.year}-{int(now.timestamp()) % 10000:04d}"

    lot_details = {
        "lot_id": lot_id,
        "variety": variety,
        "quantity_kg": quantity_kg,
        "inspector_id": inspector_id
    }

    # Run real computer vision inference pipeline
    analysis = pipeline.analyze(raw_image, lot_details)
    analysis["lot_id"] = lot_id
    analysis["timestamp"] = now.isoformat()
    analysis["image_url"] = rel_url

    inspection_id = f"INSP-{int(now.timestamp() * 1000)}"
    analysis["inspection_id"] = inspection_id

    # Persist results to relational database if onions were detected
    if analysis.get("is_onion"):
        try:
            inspection = Inspection(
                id=inspection_id,
                lot_id=lot_id,
                inspector_id=inspector_id,
                timestamp=analysis["timestamp"],
                quantity_kg=quantity_kg,
                variety=variety,
                total_onions=analysis["total_onions"],
                healthy_onions=analysis["healthy_onions"],
                defective_onions=analysis["defective_onions"],
                quality_score=analysis["quality_score"],
                grade=analysis["grade"],
                grade_name=analysis["grade_name"],
                avg_diameter=analysis["avg_diameter"],
                color_uniformity=analysis["color_uniformity"],
                defects_json=json.dumps(analysis.get("defect_percentages", {})),
                recommendations_json=json.dumps(analysis.get("recommendations", [])),
                image_path=rel_url
            )
            db.add(inspection)
            db.flush()

            # Insert individual onion detections & defects
            for bulb in analysis.get("individual_bulbs", []):
                detection = OnionDetection(
                    inspection_id=inspection_id,
                    onion_id=bulb["onion_id"],
                    confidence=bulb["confidence"],
                    is_healthy=bulb["is_healthy"],
                    bbox_x=bulb["bbox"][0] if bulb.get("bbox") else 0.0,
                    bbox_y=bulb["bbox"][1] if bulb.get("bbox") else 0.0,
                    bbox_width=bulb["bbox"][2] if bulb.get("bbox") else 0.0,
                    bbox_height=bulb["bbox"][3] if bulb.get("bbox") else 0.0,
                    center_x_pct=bulb["center_x_pct"],
                    center_y_pct=bulb["center_y_pct"],
                    diameter_mm=bulb["diameter_mm"]
                )
                db.add(detection)
                db.flush()

                for defect in bulb.get("defects", []):
                    d_record = OnionDefect(
                        inspection_id=inspection_id,
                        onion_detection_id=detection.id,
                        defect_type=defect["type"],
                        confidence=defect["confidence"],
                        severity=defect.get("severity", "medium"),
                        affected_area_pct=defect.get("affected_area_pct", 0.0)
                    )
                    db.add(d_record)

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[DATABASE SAVE ERROR] {e}")

    return analysis
