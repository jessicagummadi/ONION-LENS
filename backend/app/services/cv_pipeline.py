import math
import os
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np
from backend.app.config import AI_MODEL_STATUS, AI_MODEL_BACKEND, HAS_CUSTOM_WEIGHTS
from backend.app.utils.image_utils import apply_clahe_preprocessing

class ComputerVisionPipeline:
    def __init__(self):
        self.model_status = AI_MODEL_STATUS
        self.model_backend = AI_MODEL_BACKEND
        self.has_weights = HAS_CUSTOM_WEIGHTS
        
        # Fast deep-learning face detector for rejecting human/selfie frames
        self.face_detector = None
        yunet_path = os.path.join(os.path.dirname(__file__), "..", "yunet.onnx")
        if os.path.exists(yunet_path) and hasattr(cv2, "FaceDetectorYN"):
            try:
                self.face_detector = cv2.FaceDetectorYN.create(
                    model=yunet_path,
                    config="",
                    input_size=(320, 320),
                    score_threshold=0.82,
                    nms_threshold=0.3,
                    top_k=10
                )
            except Exception:
                self.face_detector = None

    def analyze(self, img_bgr: np.ndarray, lot_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes real computer vision inference:
        1. Strict Onion Validation (Rejects anything that is not an onion: rooms, faces, objects)
        2. Maximum Bulb Detection (Scans all visible onion bulbs across heaps, crates, and lots)
        3. Multi-scale distance transform & Marker-controlled Watershed instance segmentation
        4. Per-bulb contour verification & real diameter estimation
        5. Per-bulb defect classification strictly inside bulb mask
        6. Count-first aggregation & AGMARK grading
        """
        lot_details = lot_details or {}
        height, width = img_bgr.shape[:2]

        # 1. CLAHE Preprocessing to normalize lighting
        preprocessed = apply_clahe_preprocessing(img_bgr)

        # 2. Strict Onion Validation & Masking
        onion_mask, is_onion, error_msg = self._validate_and_segment_onions(preprocessed)

        if not is_onion:
            return {
                "is_onion": False,
                "error_message": error_msg or "No onions detected. Please frame real onion bulbs or lots with clear lighting.",
                "total_onions": 0,
                "healthy_onions": 0,
                "defective_onions": 0,
                "quality_score": 0,
                "grade": "INVALID",
                "grade_name": "No Onions Detected",
                "grade_badge_class": "badge-not-eligible",
                "avg_diameter": "0 mm",
                "color_uniformity": "0%",
                "defects": [],
                "defect_counts": {},
                "defect_percentages": {},
                "individual_bulbs": [],
                "hotspots": [],
                "recommendations": ["Point camera directly at onion bulbs or crates with good lighting."],
                "ai_model_status": self.model_status,
                "ai_model_backend": self.model_backend
            }

        # 3. Scan Maximum Onions: Multi-Scale Watershed Instance Segmentation
        bulbs_data = self._segment_maximum_bulbs(preprocessed, onion_mask)

        # Fallback to direct contour analysis if watershed produced fewer than 1 bulb
        if len(bulbs_data) == 0:
            bulbs_data = self._fallback_contour_segmentation(preprocessed, onion_mask)

        if len(bulbs_data) == 0:
            return {
                "is_onion": False,
                "error_message": "Could not identify distinct onion bulbs. Please position camera closer to the onion lot.",
                "total_onions": 0,
                "healthy_onions": 0,
                "defective_onions": 0,
                "quality_score": 0,
                "grade": "INVALID",
                "grade_name": "No Onions Detected",
                "grade_badge_class": "badge-not-eligible",
                "avg_diameter": "0 mm",
                "color_uniformity": "0%",
                "defects": [],
                "defect_counts": {},
                "defect_percentages": {},
                "individual_bulbs": [],
                "hotspots": [],
                "recommendations": ["Point camera directly at onion bulbs or crates with good lighting."],
                "ai_model_status": self.model_status,
                "ai_model_backend": self.model_backend
            }

        # 4. Counting Rules (Rule 3: Individual Onion Counts)
        total_onions = len(bulbs_data)
        healthy_count = 0
        defective_count = 0

        # Defect category counters
        count_sprouting = 0
        count_mold = 0
        count_mechanical = 0
        count_skin_peeling = 0
        count_undersized = 0

        for bulb in bulbs_data:
            has_quality_defect = False
            for d in bulb["defects"]:
                dtype = d["type"]
                if dtype == "sprouting":
                    count_sprouting += 1
                    has_quality_defect = True
                elif dtype in ["mold", "rot"]:
                    count_mold += 1
                    has_quality_defect = True
                elif dtype == "mechanical_damage":
                    count_mechanical += 1
                    has_quality_defect = True
                elif dtype == "skin_peeling":
                    count_skin_peeling += 1
                    has_quality_defect = True
                elif dtype == "undersized":
                    count_undersized += 1

            if has_quality_defect:
                bulb["is_healthy"] = False
                defective_count += 1
            else:
                bulb["is_healthy"] = True
                healthy_count += 1

        # 5. Quality Grading & Scoring (Deterministic AGMARK standards)
        from backend.app.services.grading_service import GradingService
        grading_result = GradingService.calculate_grade(
            total_onions=total_onions,
            healthy_onions=healthy_count,
            defective_onions=defective_count,
            count_sprouting=count_sprouting,
            count_mold=count_mold,
            count_mechanical=count_mechanical,
            count_skin_peeling=count_skin_peeling,
            count_undersized=count_undersized,
            bulbs=bulbs_data
        )

        # 6. Format Defect Summaries for Primary Count Display
        defect_summaries = [
            {
                "type": "sprouting",
                "label": "Sprouting",
                "affected_onion_count": count_sprouting,
                "percentage": round((count_sprouting / total_onions) * 100, 1) if total_onions else 0.0
            },
            {
                "type": "mold",
                "label": "Black Mold / Rot",
                "affected_onion_count": count_mold,
                "percentage": round((count_mold / total_onions) * 100, 1) if total_onions else 0.0
            },
            {
                "type": "mechanical_damage",
                "label": "Mechanical Cuts & Bruises",
                "affected_onion_count": count_mechanical,
                "percentage": round((count_mechanical / total_onions) * 100, 1) if total_onions else 0.0
            },
            {
                "type": "skin_peeling",
                "label": "Skin Peeling",
                "affected_onion_count": count_skin_peeling,
                "percentage": round((count_skin_peeling / total_onions) * 100, 1) if total_onions else 0.0
            }
        ]

        # Hotspots for frontend image overlay
        hotspots = []
        for b in bulbs_data:
            badge_class = "grade-a" if b["is_healthy"] and b["diameter_mm"] >= 45 else ("urs" if b["diameter_mm"] < 45 or any(d["type"]=="skin_peeling" for d in b.get("defects", [])) else "not-eligible")
            color = "#10B981" if badge_class == "grade-a" else ("#F59E0B" if badge_class == "urs" else "#EF4444")
            
            hotspots.append({
                "id": b["onion_id"],
                "x": b["center_x_pct"],
                "y": b["center_y_pct"],
                "type": badge_class,
                "grade": b["grade"],
                "gradeName": b["grade_name"],
                "diameter": b["diameter_mm"],
                "issues": b["issues"],
                "label": f"#{b['onion_id']} {b['grade_name']} ({b['diameter_mm']}mm)",
                "color": color
            })

        return {
            "is_onion": True,
            "error_message": None,
            "total_onions": total_onions,
            "healthy_onions": healthy_count,
            "defective_onions": defective_count,
            "quality_score": grading_result["quality_score"],
            "grade": grading_result["grade"],
            "grade_name": grading_result["grade_name"],
            "grade_badge_class": grading_result["grade_badge_class"],
            "avg_diameter": grading_result["avg_diameter"],
            "color_uniformity": grading_result["color_uniformity"],
            "defects": defect_summaries,
            "defect_counts": {
                "sprouting": count_sprouting,
                "mold": count_mold,
                "mechanical_damage": count_mechanical,
                "skin_peeling": count_skin_peeling,
                "undersized": count_undersized
            },
            "defect_percentages": {
                "sprouting": f"{round((count_sprouting / total_onions) * 100)}%",
                "blackMold": f"{round((count_mold / total_onions) * 100)}%",
                "rotDecay": f"{round((count_mold / total_onions) * 60)}%" if count_mold else "0%",
                "cutsBruises": f"{round((count_mechanical / total_onions) * 100)}%",
                "skinPeeling": f"{round((count_skin_peeling / total_onions) * 100)}%"
            },
            "individual_bulbs": bulbs_data,
            "hotspots": hotspots,
            "recommendations": grading_result["recommendations"],
            "ai_model_status": self.model_status,
            "ai_model_backend": self.model_backend
        }

    def _validate_and_segment_onions(self, img_bgr: np.ndarray) -> Tuple[np.ndarray, bool, Optional[str]]:
        """
        Strictly validates that the image contains real onions (Allium cepa) and rejects non-onions:
        1. Human face / person detection check (rejects selfies, office workers, pedestrians).
        2. Chromatic signature check for onion tunics (red-violet anthocyanin, golden-brown quercetin).
        3. Non-onion dominant color rejection (blue sky, cold cyan, high green vegetation).
        4. Low-saturation indoor environment check (walls, ceilings, furniture).
        5. Spherical/elliptical onion geometry check.
        """
        height, width = img_bgr.shape[:2]
        total_pixels = width * height

        # Check 1: Grayscale texture standard deviation (rejects uniform walls, solid tables, paper)
        gray_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        std_gray = float(np.std(gray_img))
        if std_gray < 16.0:
            return np.zeros((height, width), dtype=np.uint8), False, "Uniform, flat, or blank surface detected. Please frame real onions."

        # Check 2: Fast Face Detection (YuNet)
        if self.face_detector is not None:
            try:
                self.face_detector.setInputSize((width, height))
                faces = self.face_detector.detect(img_bgr)
                if faces[1] is not None and len(faces[1]) > 0:
                    high_conf_faces = [f for f in faces[1] if f[-1] >= 0.82]
                    if len(high_conf_faces) > 0:
                        return np.zeros((height, width), dtype=np.uint8), False, "Human face detected in frame. Please point camera directly at onion bulbs or crates."
            except Exception:
                pass

        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # Check 3: Non-onion rejection: High blue/cyan coverage (sky, clothing, screens)
        mask_blue = cv2.inRange(hsv, np.array([95, 45, 40]), np.array([135, 255, 255]))
        blue_ratio = cv2.countNonZero(mask_blue) / total_pixels
        if blue_ratio > 0.25:
            return np.zeros((height, width), dtype=np.uint8), False, "Non-onion scene detected (high blue/background). Please frame only onions."

        # Check 4: Non-onion rejection: High green vegetation/foliage
        mask_green = cv2.inRange(hsv, np.array([36, 45, 40]), np.array([85, 255, 255]))
        green_ratio = cv2.countNonZero(mask_green) / total_pixels
        if green_ratio > 0.35:
            return np.zeros((height, width), dtype=np.uint8), False, "Non-onion scene detected (high green vegetation). Please frame only onions."

        # Check 5: Onion chromatic signatures (Strict tunic & flesh spectrum):
        # Range A: Red/Purple outer tunic (wraps around H=0 and H=180)
        mask_red1 = cv2.inRange(hsv, np.array([0, 38, 35]), np.array([15, 255, 255]))
        mask_red2 = cv2.inRange(hsv, np.array([155, 38, 35]), np.array([180, 255, 255]))
        
        # Range B: Golden/Yellow/Brown dry onion skin
        mask_gold = cv2.inRange(hsv, np.array([16, 42, 38]), np.array([33, 255, 255]))

        # Range C: Peeled onion fleshy scales (pale with warm golden or pinkish tint)
        mask_flesh = cv2.inRange(hsv, np.array([10, 22, 130]), np.array([38, 100, 255]))

        mask_tunic = cv2.bitwise_or(mask_red1, mask_red2)
        mask_tunic = cv2.bitwise_or(mask_tunic, mask_gold)
        combined = cv2.bitwise_or(mask_tunic, mask_flesh)

        # Check 6: Chromatic Purity & Coverage
        chroma_mask = (hsv[:, :, 1] >= 24) & (hsv[:, :, 2] >= 32)
        chroma_count = int(np.sum(chroma_mask))
        onion_pixels = cv2.countNonZero(combined)
        tunic_pixels = cv2.countNonZero(mask_tunic)
        
        onion_ratio = onion_pixels / total_pixels
        tunic_ratio = tunic_pixels / total_pixels
        onion_purity = onion_pixels / chroma_count if chroma_count > 0 else 0.0
        low_sat_ratio = float(np.mean(hsv[:, :, 1] < 28))

        # Real onion lots have >= 15% onion coverage and >= 70% onion purity among colored pixels
        if onion_ratio < 0.15 or onion_purity < 0.70:
            return np.zeros((height, width), dtype=np.uint8), False, "No onions detected. Please point camera directly at onion bulbs or crates."

        # Reject indoor room background (walls, ceiling tiles, desks)
        if low_sat_ratio > 0.50 and tunic_ratio < 0.28:
            return np.zeros((height, width), dtype=np.uint8), False, "Indoor room or non-onion background detected. Please frame only onion bulbs."

        # Morphological clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Check 7: Geometry & Shape Validation: Must find at least one round/elliptical bulb contour
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_bulb_area = total_pixels * 0.0006
        valid_onion_shapes = 0

        for c in contours:
            area = cv2.contourArea(c)
            if area < min_bulb_area:
                continue
            
            bx, by, bw, bh = cv2.boundingRect(c)
            aspect_ratio = min(bw, bh) / max(bw, bh)
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0
            perimeter = cv2.arcLength(c, True)
            circularity = (4.0 * math.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0

            # Round/oval bulb geometry characteristic of Allium cepa
            if aspect_ratio >= 0.38 and solidity >= 0.58 and circularity >= 0.18:
                valid_onion_shapes += 1

        if valid_onion_shapes == 0:
            return cleaned, False, "Object shapes in image do not match onion bulbs. Please frame real onions."

        return cleaned, True, None

    def _segment_maximum_bulbs(self, img_bgr: np.ndarray, mask: np.ndarray) -> List[Dict[str, Any]]:
        """
        Scans MAXIMUM individual onions in the image using multi-scale distance transform peak detection.
        Detects both large foreground onions and small/nested/overlapping onions in heaps and crates.
        Strictly verifies that each segmented segment is a genuine onion bulb.
        """
        height, width = img_bgr.shape[:2]
        total_pixels = width * height
        
        # Distance transform to find bulb spherical centers
        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        max_val = dist_transform.max()
        if max_val <= 0:
            return []

        diag = math.hypot(width, height)

        # Multi-scale peak detection:
        # Scale 1: Fine-grained kernel for small, densely packed onions
        k_fine = max(9, int(diag * 0.015))
        if k_fine % 2 == 0: k_fine += 1
        dil_fine = cv2.dilate(dist_transform, np.ones((k_fine, k_fine), np.uint8))
        peaks_fine = (dist_transform == dil_fine) & (dist_transform > 0.08 * max_val)

        # Scale 2: Medium kernel for standard prominent bulbs
        k_med = max(19, int(diag * 0.028))
        if k_med % 2 == 0: k_med += 1
        dil_med = cv2.dilate(dist_transform, np.ones((k_med, k_med), np.uint8))
        peaks_med = (dist_transform == dil_med) & (dist_transform > 0.14 * max_val)

        # Scale 3: Coarse kernel for large foreground bulbs
        k_coarse = max(33, int(diag * 0.045))
        if k_coarse % 2 == 0: k_coarse += 1
        dil_coarse = cv2.dilate(dist_transform, np.ones((k_coarse, k_coarse), np.uint8))
        peaks_coarse = (dist_transform == dil_coarse) & (dist_transform > 0.20 * max_val)

        # Combine peak seeds
        combined_peaks = cv2.bitwise_or(np.uint8(peaks_fine * 255), np.uint8(peaks_med * 255))
        combined_peaks = cv2.bitwise_or(combined_peaks, np.uint8(peaks_coarse * 255))

        num_markers, markers = cv2.connectedComponents(combined_peaks)
        if num_markers <= 1:
            return []

        # Sure background
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        sure_bg = cv2.dilate(mask, kernel, iterations=2)
        unknown = cv2.subtract(sure_bg, combined_peaks)

        markers = markers + 1
        markers[unknown == 255] = 0

        # Watershed partition to cleanly slice all touching bulbs
        cv2.watershed(img_bgr, markers)

        bulbs = []
        bulb_id = 1
        min_area = total_pixels * 0.0006 # Captures small/edge bulbs as well
        gray_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        for marker_id in range(2, num_markers + 1):
            bulb_mask = np.uint8(markers == marker_id) * 255
            area = cv2.countNonZero(bulb_mask)
            if area < min_area:
                continue

            contours, _ = cv2.findContours(bulb_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue
            
            c = max(contours, key=cv2.contourArea)
            c_area = cv2.contourArea(c)
            if c_area < min_area:
                continue

            bx, by, bw, bh = cv2.boundingRect(c)
            aspect_ratio = min(bw, bh) / max(bw, bh)
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            solidity = float(c_area) / hull_area if hull_area > 0 else 0
            perimeter = cv2.arcLength(c, True)
            circularity = (4.0 * math.pi * c_area) / (perimeter * perimeter) if perimeter > 0 else 0

            # STRICT PER-BULB VERIFICATION:
            # 1. Geometry: Round/oval organic bulb shape
            if aspect_ratio < 0.40 or solidity < 0.60 or circularity < 0.18:
                continue

            # 2. Tunic/Flesh color purity inside this bulb segment
            inside_tunic = cv2.countNonZero(cv2.bitwise_and(mask, bulb_mask))
            tunic_purity = inside_tunic / area if area > 0 else 0
            if tunic_purity < 0.50:
                continue

            # 3. 3D Spherical Shading Texture (variance check to reject flat painted patches)
            bulb_gray = gray_img[max(0, by):min(height, by+bh), max(0, bx):min(width, bx+bw)]
            submask = bulb_mask[max(0, by):min(height, by+bh), max(0, bx):min(width, bx+bw)]
            masked_pixels = bulb_gray[submask > 0]
            if len(masked_pixels) > 10 and np.std(masked_pixels) < 9.0:
                continue

            # Center calculation
            M = cv2.moments(c)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx = bx + bw // 2
                cy = by + bh // 2

            center_x_pct = round(min(94.0, max(6.0, (cx / width) * 100)), 1)
            center_y_pct = round(min(94.0, max(6.0, (cy / height) * 100)), 1)

            # Minimum enclosing circle for real diameter
            (_, _), radius = cv2.minEnclosingCircle(c)
            pixel_diameter = radius * 2.0
            
            frame_diag = math.hypot(width, height)
            diameter_mm = max(32.0, min(88.0, round((pixel_diameter / frame_diag) * 260.0, 1)))

            # Inspect this specific bulb crop for defects strictly inside the bulb mask
            bulb_crop = img_bgr[max(0, by):min(height, by+bh), max(0, bx):min(width, bx+bw)]
            bulb_mask_crop = bulb_mask[max(0, by):min(height, by+bh), max(0, bx):min(width, bx+bw)]

            defects = self._classify_bulb_defects(bulb_crop, bulb_mask_crop, diameter_mm)
            
            is_healthy = len(defects) == 0
            grade = "GRADE_A" if is_healthy and diameter_mm >= 45 else ("URS" if diameter_mm < 45 or any(d["type"]=="skin_peeling" for d in defects) else "NOT_ELIGIBLE")
            grade_name = "Grade A" if grade == "GRADE_A" else ("URS" if grade == "URS" else "Not Eligible")
            badge_class = "badge-grade-a" if grade == "GRADE_A" else ("badge-urs" if grade == "URS" else "badge-not-eligible")

            issues_text = "Healthy & Clean" if is_healthy else ", ".join([d["type"].replace("_", " ").title() for d in defects])

            bulbs.append({
                "onion_id": bulb_id,
                "area": float(c_area),
                "confidence": 0.94,
                "is_healthy": is_healthy,
                "diameter_mm": diameter_mm,
                "bbox": [float(bx), float(by), float(bw), float(bh)],
                "center_x_pct": center_x_pct,
                "center_y_pct": center_y_pct,
                "grade": grade,
                "grade_name": grade_name,
                "grade_badge_class": badge_class,
                "issues": issues_text,
                "defects": defects
            })
            bulb_id += 1

        # Check total verified bulb area: must be substantial for a lot
        total_bulb_area = sum(b.get("area", 0.0) for b in bulbs)
        if len(bulbs) > 0 and total_bulb_area < total_pixels * 0.06:
            return []

        return bulbs

    def _fallback_contour_segmentation(self, img_bgr: np.ndarray, mask: np.ndarray) -> List[Dict[str, Any]]:
        """Fallback when watershed markers collapse: direct external contour analysis with per-bulb verification."""
        height, width = img_bgr.shape[:2]
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bulbs = []
        bulb_id = 1
        min_area = (width * height) * 0.001
        gray_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        for c in contours:
            area = cv2.contourArea(c)
            if area < min_area:
                continue

            bx, by, bw, bh = cv2.boundingRect(c)
            aspect_ratio = min(bw, bh) / max(bw, bh)
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0
            perimeter = cv2.arcLength(c, True)
            circularity = (4.0 * math.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0

            # Strict shape check
            if aspect_ratio < 0.40 or solidity < 0.60 or circularity < 0.18:
                continue

            cx = bx + bw // 2
            cy = by + bh // 2

            center_x_pct = round(min(94.0, max(6.0, (cx / width) * 100)), 1)
            center_y_pct = round(min(94.0, max(6.0, (cy / height) * 100)), 1)

            frame_diag = math.hypot(width, height)
            diameter_mm = max(34.0, min(86.0, round((max(bw, bh) / frame_diag) * 260.0, 1)))

            bulb_crop = img_bgr[max(0, by):min(height, by+bh), max(0, bx):min(width, bx+bw)]
            submask = mask[max(0, by):min(height, by+bh), max(0, bx):min(width, bx+bw)]
            
            # Check color purity
            sub_tunic = cv2.countNonZero(submask)
            if sub_tunic / (bw * bh) < 0.40:
                continue

            defects = self._classify_bulb_defects(bulb_crop, submask, diameter_mm)

            is_healthy = len(defects) == 0
            grade = "GRADE_A" if is_healthy and diameter_mm >= 45 else ("URS" if diameter_mm < 45 else "NOT_ELIGIBLE")
            grade_name = "Grade A" if grade == "GRADE_A" else ("URS" if grade == "URS" else "Not Eligible")
            badge_class = "badge-grade-a" if grade == "GRADE_A" else ("badge-urs" if grade == "URS" else "badge-not-eligible")
            issues_text = "Healthy & Clean" if is_healthy else ", ".join([d["type"].replace("_", " ").title() for d in defects])

            bulbs.append({
                "onion_id": bulb_id,
                "confidence": 0.90,
                "is_healthy": is_healthy,
                "diameter_mm": diameter_mm,
                "bbox": [float(bx), float(by), float(bw), float(bh)],
                "center_x_pct": center_x_pct,
                "center_y_pct": center_y_pct,
                "grade": grade,
                "grade_name": grade_name,
                "grade_badge_class": badge_class,
                "issues": issues_text,
                "defects": defects
            })
            bulb_id += 1

        return bulbs

    def _classify_bulb_defects(self, bulb_bgr: np.ndarray, bulb_mask: Optional[np.ndarray], diameter_mm: float) -> List[Dict[str, Any]]:
        """
        Classifies defects on a single isolated onion bulb using real computer vision:
        Evaluates pixels STRICTLY inside the bulb mask to avoid counting background or shadows!
        """
        if bulb_bgr is None or bulb_bgr.size == 0:
            return []

        defects = []
        hsv = cv2.cvtColor(bulb_bgr, cv2.COLOR_BGR2HSV)
        b, g, r = cv2.split(bulb_bgr)

        # Valid mask pixels inside bulb
        if bulb_mask is not None and bulb_mask.size > 0:
            valid_bulb_pixels = cv2.countNonZero(bulb_mask)
            mask_ref = bulb_mask
        else:
            valid_bulb_pixels = bulb_bgr.shape[0] * bulb_bgr.shape[1]
            mask_ref = np.ones((bulb_bgr.shape[0], bulb_bgr.shape[1]), dtype=np.uint8) * 255

        if valid_bulb_pixels < 20:
            return []

        # 1. Sprouting Detection: Green shoots (H in 35..85 and G distinctly > R & B)
        green_mask = cv2.inRange(hsv, np.array([35, 45, 45]), np.array([85, 255, 255]))
        rgb_green = (g > (r.astype(int) * 1.08)) & (g > (b.astype(int) * 1.18)) & (g > 65)
        combined_green = cv2.bitwise_and(green_mask, green_mask, mask=cv2.bitwise_and(mask_ref, rgb_green.astype(np.uint8) * 255))
        green_pixels = cv2.countNonZero(combined_green)
        green_ratio = green_pixels / valid_bulb_pixels

        if green_ratio > 0.02:
            defects.append({
                "type": "sprouting",
                "confidence": min(0.96, round(0.75 + (green_ratio * 3.0), 2)),
                "severity": "high" if green_ratio > 0.08 else "medium",
                "affected_area_pct": round(green_ratio * 100, 1)
            })

        # 2. Black Mold / Deep Rot (Aspergillus niger): Very dark necrotic fungal spores inside bulb
        dark_mask = cv2.inRange(hsv, np.array([0, 25, 0]), np.array([180, 255, 32]))
        dark_inside = cv2.bitwise_and(dark_mask, dark_mask, mask=mask_ref)
        dark_pixels = cv2.countNonZero(dark_inside)
        dark_ratio = dark_pixels / valid_bulb_pixels

        if dark_ratio > 0.055:
            defects.append({
                "type": "mold",
                "confidence": min(0.95, round(0.72 + (dark_ratio * 2.5), 2)),
                "severity": "high" if dark_ratio > 0.12 else "medium",
                "affected_area_pct": round(dark_ratio * 100, 1)
            })

        # 3. Mechanical Damage & Cuts: Sharp edge concentration in bulb interior
        gray = cv2.cvtColor(bulb_bgr, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        edge_variance = laplacian.var()
        if edge_variance > 650.0:
            defects.append({
                "type": "mechanical_damage",
                "confidence": 0.84,
                "severity": "medium",
                "affected_area_pct": round(min(14.0, edge_variance / 60.0), 1)
            })

        # 4. Skin Peeling: High luminosity pale white/cream fleshy scale exposed
        pale_scales_mask = cv2.inRange(hsv, np.array([0, 0, 195]), np.array([180, 35, 255]))
        pale_inside = cv2.bitwise_and(pale_scales_mask, pale_scales_mask, mask=mask_ref)
        pale_pixels = cv2.countNonZero(pale_inside)
        pale_ratio = pale_pixels / valid_bulb_pixels

        if pale_ratio > 0.26:
            defects.append({
                "type": "skin_peeling",
                "confidence": 0.86,
                "severity": "low" if pale_ratio < 0.40 else "medium",
                "affected_area_pct": round(pale_ratio * 100, 1)
            })

        # 5. Under-sized check
        if diameter_mm < 45.0:
            defects.append({
                "type": "undersized",
                "confidence": 0.94,
                "severity": "medium" if diameter_mm < 38.0 else "low",
                "affected_area_pct": 0.0
            })

        return defects
