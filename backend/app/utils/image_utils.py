import base64
import re
import uuid
from pathlib import Path
from typing import Tuple, Optional
import cv2
import numpy as np
from backend.app.config import UPLOADS_DIR

def decode_image(image_input: str | bytes) -> Optional[np.ndarray]:
    """
    Decodes an image from raw bytes, base64 data URL, or plain base64 string.
    Returns a BGR OpenCV numpy array.
    """
    try:
        if isinstance(image_input, str):
            # Check if data URL like 'data:image/jpeg;base64,...'
            if "," in image_input:
                image_input = image_input.split(",", 1)[1]
            image_bytes = base64.b64decode(image_input)
        else:
            image_bytes = image_input

        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"[IMAGE DECODE ERROR] {e}")
        return None

def apply_clahe_preprocessing(img: np.ndarray) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)
    to the Luminance channel in LAB color space to normalize lighting.
    """
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l_channel)
    lab_eq = cv2.merge((l_eq, a_channel, b_channel))
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)

def save_uploaded_image(img: np.ndarray, prefix: str = "insp") -> Tuple[str, str]:
    """
    Saves image to uploads directory.
    Returns (relative_url, absolute_filepath).
    """
    filename = f"{prefix}_{uuid.uuid4().hex[:12]}.jpg"
    filepath = UPLOADS_DIR / filename
    cv2.imwrite(str(filepath), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return f"/uploads/{filename}", str(filepath)
