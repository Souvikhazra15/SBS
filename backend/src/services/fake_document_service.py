"""
Fake Document Detection Service

Advanced computer vision algorithms to detect fraudulent, expired, or altered documents.
Integrates comprehensive verification for Indian documents (Aadhaar, PAN) with
layout analysis, QR verification, tampering detection, and security feature validation.
"""

import base64
import io
import time
import logging
import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

logger = logging.getLogger(__name__)


class FakeDocumentService:
    """Service for detecting fake or altered documents with comprehensive verification."""
    
    def __init__(self):
        self.model_version = "v4.0.0"
        self.confidence_threshold = 0.85
        
        # Initialize easyOCR (English + Hindi for Indian documents)
        logger.info("[FAKE-DOC] Initializing easyOCR (English + Hindi)...")
        try:
            if EASYOCR_AVAILABLE:
                self.ocr_engine = easyocr.Reader(['en', 'hi'], gpu=False)
                logger.info("[FAKE-DOC] ✓ easyOCR loaded successfully")
            else:
                logger.warning("[FAKE-DOC] easyOCR not available")
                self.ocr_engine = None
        except Exception as e:
            logger.error(f"[FAKE-DOC] ✗ Failed to load easyOCR: {str(e)}")
            self.ocr_engine = None

        # Load Haar Cascade for face detection
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            logger.info("[FAKE-DOC] ✓ Face detection loaded")
        except Exception as e:
            logger.warning(f"[FAKE-DOC] Face detection unavailable: {e}")
            self.face_cascade = None
        
        # CNN model placeholder
        self.cnn_model = None
        self._load_cnn_model()
    
    def _load_cnn_model(self):
        """Load CNN model for security feature detection (graceful fallback)."""
        try:
            logger.info("[FAKE-DOC] CNN model not configured (optional)")
            self.cnn_model = None
        except Exception as e:
            logger.warning(f"[FAKE-DOC] CNN model unavailable: {str(e)}")
            self.cnn_model = None
        
    def analyze_document(self, document_image: str, document_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a document image for authenticity and tampering.
        
        Args:
            document_image: Base64 encoded image or file path
            document_type: Document type ('AADHAAR', 'PAN', or auto-detect)
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        start_time = time.time()
        
        try:
            # Decode and preprocess image
            image = self._decode_image(document_image)
            
            # Auto-detect document type if not specified
            if not document_type:
                document_type = self._detect_document_type(image)
                logger.info(f"[FAKE-DOC] Auto-detected document type: {document_type}")
            
            # Run document-specific verification
            if document_type == "AADHAAR":
                result = self._verify_aadhaar(image)
            elif document_type == "PAN":
                result = self._verify_pan(image)
            else:
                result = self._verify_generic(image)
            
            processing_time = int((time.time() - start_time) * 1000)
            result["processing_time_ms"] = processing_time
            result["model_version"] = self.model_version
            result["timestamp"] = datetime.utcnow().isoformat()
            result["document_type"] = document_type
            
            return result
            
        except Exception as e:
            logger.error(f"[FAKE-DOC] Analysis error: {str(e)}")
            return {
                "error": str(e),
                "forgery_score": 0.0,
                "is_authentic": False,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "document_type": document_type or "UNKNOWN"
            }
        except Exception as e:
            return {
                "error": str(e),
                "forgery_score": 0.0,
                "is_authentic": False,
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def _decode_image(self, image_data: str) -> np.ndarray:
        """Decode base64 image to numpy array."""
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        return np.array(image)
    
    def _detect_document_type(self, image: np.ndarray) -> str:
        """Auto-detect document type from image."""
        if not self.ocr_engine:
            return "UNKNOWN"
        
        try:
            # Extract text
            results = self.ocr_engine.readtext(image)
            text = " ".join([item[1].upper() for item in results])
            
            # Check for Aadhaar indicators
            if any(keyword in text for keyword in ["AADHAAR", "AADHAR", "आधार"]):
                return "AADHAAR"
            
            # Check for PAN indicators
            if "PERMANENT ACCOUNT NUMBER" in text or "INCOME TAX" in text:
                return "PAN"
            
            # Check for PAN pattern in text
            if re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text):
                return "PAN"
            
            # Check for Aadhaar pattern
            if re.search(r"\d{4}\s*\d{4}\s*\d{4}", text):
                return "AADHAAR"
                
            return "GENERIC"
        except Exception as e:
            logger.error(f"[FAKE-DOC] Document type detection error: {e}")
            return "UNKNOWN"
    
    def _verify_aadhaar(self, image: np.ndarray) -> Dict[str, Any]:
        """Comprehensive Aadhaar card verification with strict validation."""
        try:
            h, w = image.shape[:2] if len(image.shape) == 2 else image.shape[:2]
            
            # Extract OCR data
            ocr_data = self._extract_ocr(image)
            if not ocr_data:
                return {
                    "forgery_score": 0.0,
                    "is_authentic": False,
                    "error": "No text detected",
                    "checks": {}
                }
            
            # Perform comprehensive verification checks
            layout_check = self._check_aadhaar_layout(ocr_data, h, w)
            header_check = self._check_aadhaar_header(ocr_data)
            font_check = self._check_font_hierarchy([item["size"] for item in ocr_data])
            qr_check = self._check_qr_code(image, layout_check.get("aadhaar_number"))
            tampering_check = self._check_tampering(image)
            face_check = self._check_face_presence(image)
            color_check = self._check_aadhaar_color_scheme(image)
            hologram_check = self._check_hologram_presence(image)
            paper_check = self._check_paper_texture(image)
            
            # REALISTIC SCORING SYSTEM (Balanced for real-world documents)
            score = 0
            critical_issues = []
            
            # 1. QR Code presence (10 points) - Optional bonus, not critical
            if qr_check["detected"]:
                score += 10
                if qr_check["valid"]:
                    score += 5  # Extra bonus if we can validate data
            # QR not detected is NOT a critical issue (photos may not capture it)
            
            # 2. Government header (25 points) - Most important check
            if header_check["valid"]:
                score += 25
            else:
                critical_issues.append("Government header missing or incorrect")
            
            # 3. Critical fields present (30 points) - Very important
            critical_fields = layout_check.get("critical_fields_found", 0)
            if critical_fields >= 3:
                score += 30  # 3 or 4 fields is good enough
            elif critical_fields == 2:
                score += 20
                critical_issues.append("Only 2 critical fields found")
            else:
                critical_issues.append(f"Missing critical fields: {4 - critical_fields}")
            
            # 4. Color scheme (8 points) - Bonus only, photos may not capture colors
            if color_check["valid"]:
                score += 8
            
            # 5. Paper texture and quality (5 points) - Bonus only
            if paper_check["valid"]:
                score += 5
            
            # 6. Hologram presence (5 points) - Bonus only
            if hologram_check["detected"]:
                score += 5
            
            # 7. Tampering check (12 points) - Important but not critical
            if tampering_check["is_clear"]:
                score += 12
            # Blurry photos are common, not marking as critical issue
            
            # 8. Face photo presence (10 points) - Important indicator
            if face_check["face_detected"]:
                score += 10
            else:
                critical_issues.append("Face photo not clearly detected")
            
            # LENIENT THRESHOLD: Score >= 55 with max 2 critical issues = AUTHENTIC
            # This allows real documents with poor quality scans to pass
            is_authentic = (score >= 55 and len(critical_issues) <= 2) or (score >= 65)
            
            return {
                "forgery_score": round(score, 2),
                "is_authentic": is_authentic,
                "confidence_level": round(score / 100.0, 3),
                "critical_issues": critical_issues,
                "security_features": {
                    "qr_code_valid": qr_check["valid"],
                    "government_header_valid": header_check["valid"],
                    "layout_valid": critical_fields >= 3,
                    "color_scheme_valid": color_check["valid"],
                    "hologram_detected": hologram_check["detected"],
                    "paper_texture_valid": paper_check["valid"],
                    "tampering_detected": not tampering_check["is_clear"],
                    "face_photo_valid": face_check["face_detected"]
                },
                "details": {
                    "layout_analysis": layout_check,
                    "header_validation": header_check,
                    "qr_validation": qr_check,
                    "color_analysis": color_check,
                    "hologram_analysis": hologram_check,
                    "paper_analysis": paper_check,
                    "tampering_analysis": tampering_check,
                    "face_detection": face_check
                },
                "status": "AUTHENTIC" if is_authentic else "SUSPICIOUS" if score >= 40 else "FAKE"
            }
            
        except Exception as e:
            logger.error(f"[FAKE-DOC] Aadhaar verification error: {e}")
            return {
                "forgery_score": 0.0,
                "is_authentic": False,
                "error": str(e)
            }
    
    def _verify_pan(self, image: np.ndarray) -> Dict[str, Any]:
        """Comprehensive PAN card verification."""
        try:
            h, w = image.shape[:2] if len(image.shape) == 2 else image.shape[:2]
            
            # Extract OCR data
            ocr_data = self._extract_ocr(image)
            if not ocr_data:
                return {
                    "forgery_score": 0.0,
                    "is_authentic": False,
                    "error": "No text detected",
                    "checks": {}
                }
            
            # Perform PAN-specific verification
            pan_extraction = self._extract_pan_fields(ocr_data, h)
            qr_check = self._check_qr_code(image, pan_extraction.get("pan_number"))
            tampering_check = self._check_tampering(image)
            font_check = self._check_font_hierarchy([item["size"] for item in ocr_data])
            face_check = self._check_face_presence(image)
            
            # Calculate score
            score = 0
            
            # PAN number present and valid
            if pan_extraction.get("pan_valid"):
                score += 30
            
            # Name present
            if pan_extraction.get("name"):
                score += 15
            
            # Father's name present
            if pan_extraction.get("father_name"):
                score += 15
            
            # DOB present
            if pan_extraction.get("dob"):
                score += 10
            
            # QR code validation
            if qr_check["valid"]:
                score += 15
            
            # Font hierarchy and tampering
            if font_check and tampering_check["is_clear"]:
                score += 15
            
            is_authentic = score >= 70
            
            return {
                "forgery_score": round(score, 2),
                "is_authentic": is_authentic,
                "confidence_level": round(score / 100.0, 3),
                "security_features": {
                    "pan_format_valid": pan_extraction.get("pan_valid", False),
                    "qr_code_valid": qr_check["valid"],
                    "font_hierarchy_correct": font_check,
                    "tampering_detected": not tampering_check["is_clear"],
                    "face_photo_present": face_check["face_detected"]
                },
                "details": {
                    "pan_extraction": pan_extraction,
                    "qr_validation": qr_check,
                    "tampering_analysis": tampering_check,
                    "face_detection": face_check
                },
                "status": "AUTHENTIC" if is_authentic else "SUSPICIOUS" if score >= 50 else "FAKE"
            }
            
        except Exception as e:
            logger.error(f"[FAKE-DOC] PAN verification error: {e}")
            return {
                "forgery_score": 0.0,
                "is_authentic": False,
                "error": str(e)
            }
    
    def _verify_generic(self, image: np.ndarray) -> Dict[str, Any]:
        """Generic document verification for unsupported types."""
        try:
            # Basic checks
            tampering_check = self._check_tampering(image)
            face_check = self._check_face_presence(image)
            qr_check = self._check_qr_code(image, None)
            
            # Simple scoring
            score = 50  # Baseline
            if tampering_check["is_clear"]:
                score += 25
            if qr_check["valid"]:
                score += 15
            if face_check["face_detected"]:
                score += 10
            
            return {
                "forgery_score": round(score, 2),
                "is_authentic": score >= 70,
                "confidence_level": round(score / 100.0, 3),
                "security_features": {
                    "tampering_detected": not tampering_check["is_clear"],
                    "qr_code_present": qr_check["detected"],
                    "face_photo_present": face_check["face_detected"]
                },
                "status": "AUTHENTIC" if score >= 70 else "SUSPICIOUS"
            }
        except Exception as e:
            return {
                "forgery_score": 0.0,
                "is_authentic": False,
                "error": str(e)
            }
    
    def _extract_ocr(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Extract text using easyOCR."""
        if not self.ocr_engine:
            return []
        
        try:
            results = self.ocr_engine.readtext(image)
            ocr_data = []
            for bbox, text, conf in results:
                x_coords = [int(p[0]) for p in bbox]
                y_coords = [int(p[1]) for p in bbox]
                ocr_data.append({
                    "text": text.strip(),
                    "bbox": [min(x_coords), min(y_coords), max(x_coords), max(y_coords)],
                    "conf": conf,
                    "size": max(y_coords) - min(y_coords)
                })
            return ocr_data
        except Exception as e:
            logger.error(f"[FAKE-DOC] OCR extraction error: {e}")
            return []
    
    def _check_aadhaar_layout(self, ocr_data: List[Dict], h: int, w: int) -> Dict[str, Any]:
        """Check Aadhaar card layout and extract fields."""
        # Define regions (based on typical Aadhaar layout)
        regions = {
            "name": (0.15*h, 0.40*h),
            "dob": (0.25*h, 0.50*h),
            "gender": (0.35*h, 0.65*h),
            "aadhaar": (0.65*h, 0.85*h)
        }
        
        found_fields = {
            "name": False,
            "dob": False,
            "gender": False,
            "aadhaar": False
        }
        
        aadhaar_number = None
        
        for item in ocr_data:
            text = item["text"]
            bbox = item["bbox"]
            y_center = (bbox[1] + bbox[3]) / 2
            
            # Check for Aadhaar number (12 digits)
            if re.match(r"^\d{4}\s*\d{4}\s*\d{4}$", text.replace(" ", "")):
                if regions["aadhaar"][0] <= y_center <= regions["aadhaar"][1]:
                    found_fields["aadhaar"] = True
                    aadhaar_number = text.replace(" ", "")
            
            # Check for DOB
            if re.search(r"\d{1,2}/\d{1,2}/\d{4}", text):
                if regions["dob"][0] <= y_center <= regions["dob"][1]:
                    found_fields["dob"] = True
            
            # Check for gender
            if re.search(r"\b(MALE|FEMALE|પુરુષ|સ્ત્રી|पुरुष|महिला)\b", text.upper()):
                if regions["gender"][0] <= y_center <= regions["gender"][1]:
                    found_fields["gender"] = True
            
            # Check for name (capitalized words)
            if text.isupper() and len(text.split()) >= 2:
                if regions["name"][0] <= y_center <= regions["name"][1]:
                    found_fields["name"] = True
        
        critical_fields_found = sum(found_fields.values())
        
        return {
            "fields_found": found_fields,
            "critical_fields_found": critical_fields_found,
            "aadhaar_number": aadhaar_number,
            "layout_valid": critical_fields_found >= 3
        }
    
    def _extract_pan_fields(self, ocr_data: List[Dict], h: int) -> Dict[str, Any]:
        """Extract and validate PAN card fields."""
        result = {
            "pan_number": None,
            "pan_valid": False,
            "name": None,
            "father_name": None,
            "dob": None
        }
        
        for item in ocr_data:
            text = item["text"].strip().upper()
            
            # Check for PAN number
            pan_match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
            if pan_match:
                result["pan_number"] = pan_match.group()
                result["pan_valid"] = True
            
            # Check for DOB
            dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)
            if dob_match:
                result["dob"] = dob_match.group()
            
            # Check for name (capitalized, 2+ words, no banned tokens)
            banned_tokens = {"INCOME", "TAX", "DEPARTMENT", "GOVERNMENT", "ACCOUNT", "NUMBER", "PAN"}
            words = text.split()
            if len(words) >= 2 and all(w.isalpha() for w in words):
                if not any(token in words for token in banned_tokens):
                    if not result["name"]:
                        result["name"] = text
                    elif not result["father_name"]:
                        result["father_name"] = text
        
        return result
    
    def _check_font_hierarchy(self, font_sizes: List[int]) -> bool:
        """Check if document has proper font hierarchy."""
        if len(font_sizes) < 2:
            return False
        
        largest = max(font_sizes)
        smallest = min(font_sizes)
        return largest > smallest * 1.3
    
    def _check_qr_code(self, image: np.ndarray, expected_data: Optional[str]) -> Dict[str, Any]:
        """Check for QR code presence and validation."""
        try:
            qr_data = decode(image)
            if not qr_data:
                return {"detected": False, "valid": False, "message": "No QR code found"}
            
            qr_text = qr_data[0].data.decode("utf-8")
            
            if expected_data:
                valid = expected_data.replace(" ", "") in qr_text
                return {
                    "detected": True,
                    "valid": valid,
                    "message": "QR matched" if valid else "QR mismatch"
                }
            
            return {"detected": True, "valid": True, "message": "QR present"}
        except Exception as e:
            return {"detected": False, "valid": False, "message": f"QR check error: {str(e)}"}
    
    def _check_tampering(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect tampering using Laplacian variance (blur detection)."""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            is_clear = lap_var > 50  # Lowered threshold - many real photos are slightly blurry
            
            return {
                "is_clear": is_clear,
                "focus_variance": round(lap_var, 2),
                "tampering_detected": not is_clear
            }
        except Exception as e:
            return {
                "is_clear": False,
                "focus_variance": 0,
                "error": str(e)
            }
    
    def _check_face_presence(self, image: np.ndarray) -> Dict[str, Any]:
        """Check if document contains a face photo."""
        if not self.face_cascade:
            return {"face_detected": False, "message": "Face detection unavailable"}
        
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,  # More sensitive to smaller variations
                minNeighbors=3,     # Reduced from 4 - more lenient
                minSize=(40, 40)    # Smaller minimum size to catch smaller faces
            )
            
            return {
                "face_detected": len(faces) > 0,
                "face_count": len(faces),
                "message": f"{len(faces)} face(s) detected"
            }
        except Exception as e:
            return {
                "face_detected": False,
                "error": str(e)
            }
    
    def _check_aadhaar_header(self, ocr_data: List[Dict]) -> Dict[str, Any]:
        """Check for authentic Aadhaar government header."""
        try:
            # Must have "भारत सरकार" (Government of India) or "GOVERNMENT OF INDIA"
            all_text = " ".join([item["text"].upper() for item in ocr_data])
            
            has_govt_of_india = any(phrase in all_text for phrase in [
                "GOVERNMENT OF INDIA",
                "भारत सरकार",
                "GOVT OF INDIA"
            ])
            
            # Check for "AADHAAR" or "आधार" text
            has_aadhaar_text = any(word in all_text for word in ["AADHAAR", "AADHAR", "आधार"])
            
            valid = has_govt_of_india and has_aadhaar_text
            
            return {
                "valid": valid,
                "govt_header": has_govt_of_india,
                "aadhaar_text": has_aadhaar_text,
                "message": "Valid header" if valid else "Invalid or missing government header"
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _check_aadhaar_color_scheme(self, image: np.ndarray) -> Dict[str, Any]:
        """Check if document uses official Aadhaar color scheme (orange/red header)."""
        try:
            # Aadhaar cards have distinctive orange/red header
            # Check top 20% of image for orange/red colors
            h, w = image.shape[:2] if len(image.shape) == 2 else image.shape[:2]
            header_region = image[0:int(h*0.2), :]
            
            if len(header_region.shape) == 2:
                # Grayscale - cannot verify colors
                return {"valid": False, "message": "Cannot verify colors in grayscale"}
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(header_region, cv2.COLOR_BGR2HSV)
            
            # Orange/Red color range in HSV
            # Orange: H(0-25), S(100-255), V(100-255)
            lower_orange = np.array([0, 100, 100])
            upper_orange = np.array([25, 255, 255])
            
            mask = cv2.inRange(hsv, lower_orange, upper_orange)
            orange_percentage = (np.sum(mask > 0) / mask.size) * 100
            
            # Authentic Aadhaar should have at least 3% orange in header
            # Lowered from 5% - photos/scans may not capture colors perfectly
            valid = orange_percentage >= 3.0
            
            return {
                "valid": valid,
                "orange_percentage": round(orange_percentage, 2),
                "message": f"Orange coverage: {orange_percentage:.1f}%"
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _check_hologram_presence(self, image: np.ndarray) -> Dict[str, Any]:
        """Check for hologram-like reflective patterns (simplified check)."""
        try:
            # Real holograms show high-frequency patterns and edge density
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Real Aadhaar has distinctive edge patterns from hologram
            # Threshold: at least 3% edge density
            detected = edge_density >= 0.03
            
            return {
                "detected": detected,
                "edge_density": round(edge_density * 100, 2),
                "message": f"Edge density: {edge_density*100:.2f}%"
            }
        except Exception as e:
            return {"detected": False, "error": str(e)}
    
    def _check_paper_texture(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze paper texture and print quality."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Calculate texture using local binary patterns (simplified)
            # High variance = good paper texture, low variance = printed/fake
            variance = np.var(gray)
            
            # Check for uniform printing artifacts
            # Real documents have micro-variations in texture
            texture_score = variance / 1000.0  # Normalize
            
            # Valid if variance is reasonable (not too uniform, not too noisy)
            valid = 5.0 <= variance <= 5000.0
            
            return {
                "valid": valid,
                "texture_variance": round(variance, 2),
                "texture_score": round(min(texture_score, 100), 2),
                "message": "Good texture" if valid else "Suspicious texture"
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def get_supported_document_types(self) -> list:
        """Return list of supported document types."""
        return [
            "AADHAAR",
            "PAN",
            "PASSPORT",
            "DRIVERS_LICENSE",
            "VOTER_ID",
            "GENERIC"
        ]