"""
Face Matching Service using OpenCV with Advanced Feature Extraction
Performs face detection and multi-method comparison for better accuracy
"""
import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

class FaceMatchingService:
    """Service for face detection and matching using OpenCV with multiple algorithms"""
    
    # Decision thresholds
    MATCH_THRESHOLD = 0.60  # Combined similarity threshold for face match
    
    # Decision constants
    DECISION_MATCH = "MATCH"
    DECISION_NO_MATCH = "NO_MATCH"
    DECISION_FACE_NOT_DETECTED = "FACE_NOT_DETECTED"
    DECISION_MULTIPLE_FACES = "MULTIPLE_FACES"
    DECISION_ERROR = "ERROR"
    
    def __init__(self):
        """Initialize face detection and feature extractors"""
        self.model_name = "opencv_multi_algorithm"
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Feature extractors for better matching
        self.orb = cv2.ORB_create(nfeatures=500)  # For keypoint matching
        
        self.initialized = True
        logger.info(f"[FACE] Enhanced face matching service initialized with multiple algorithms")
        
    def _load_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Load image from bytes"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                logger.error("[FACE] Failed to decode image")
                return None
            return img
        except Exception as e:
            logger.error(f"[FACE] Error loading image: {e}")
            return None
    
    def _detect_faces(self, img: np.ndarray) -> list:
        """Detect faces in image using Haar Cascade with eye verification"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Increase minNeighbors and minSize to reduce false positives
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=8,
                minSize=(80, 80),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Filter faces by detecting eyes (more reliable face confirmation)
            valid_faces = []
            for (x, y, w, h) in faces:
                face_region = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(face_region, scaleFactor=1.1, minNeighbors=3)
                # If at least 1 eye detected, it's likely a real face
                if len(eyes) >= 1:
                    valid_faces.append((x, y, w, h))
            
            # If eye detection filtered out all faces, fall back to original detections
            if len(valid_faces) == 0 and len(faces) > 0:
                logger.warning("[FACE] Eye detection filtered all faces, using original detections")
                valid_faces = list(faces)
            
            # If multiple faces detected, keep only the largest one
            if len(valid_faces) > 1:
                logger.warning(f"[FACE] Multiple faces detected ({len(valid_faces)}), selecting largest")
                valid_faces = sorted(valid_faces, key=lambda f: f[2] * f[3], reverse=True)
                valid_faces = [valid_faces[0]]
            
            return valid_faces
        except Exception as e:
            logger.error(f"[FACE] Error detecting faces: {e}")
            return []
    
    def _preprocess_face(self, face_img: np.ndarray) -> np.ndarray:
        """Preprocess face image for better matching"""
        # Histogram equalization for better contrast
        if len(face_img.shape) == 3:
            # Convert to YUV and equalize Y channel
            yuv = cv2.cvtColor(face_img, cv2.COLOR_BGR2YUV)
            yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
            face_img = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        else:
            face_img = cv2.equalizeHist(face_img)
        
        # Denoise
        face_img = cv2.fastNlMeansDenoisingColored(face_img, None, 10, 10, 7, 21)
        
        return face_img
    
    def _extract_face_region(self, img: np.ndarray, face_bbox: tuple) -> np.ndarray:
        """Extract and preprocess face region from image"""
        x, y, w, h = face_bbox
        face_img = img[y:y+h, x:x+w]
        
        # Preprocess
        face_img = self._preprocess_face(face_img)
        
        # Resize to standard size for comparison
        face_img = cv2.resize(face_img, (128, 128))
        return face_img
    
    def _compute_histogram_similarity(self, face1: np.ndarray, face2: np.ndarray) -> float:
        """Compute similarity using histogram comparison"""
        # Convert to HSV for better color comparison
        hsv1 = cv2.cvtColor(face1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(face2, cv2.COLOR_BGR2HSV)
        
        # Compute histograms
        hist1 = cv2.calcHist([hsv1], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        
        # Normalize
        cv2.normalize(hist1, hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        
        # Compare
        similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        return float(similarity)
    
    def _compute_orb_similarity(self, face1: np.ndarray, face2: np.ndarray) -> float:
        """Compute similarity using ORB keypoint matching"""
        try:
            gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)
            
            # Detect and compute ORB features
            kp1, des1 = self.orb.detectAndCompute(gray1, None)
            kp2, des2 = self.orb.detectAndCompute(gray2, None)
            
            if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
                logger.warning("[FACE] Insufficient keypoints detected")
                return 0.5  # Neutral score
            
            # Match features using BFMatcher
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            
            # Sort matches by distance
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Calculate similarity based on good matches
            good_matches = [m for m in matches if m.distance < 50]
            similarity = len(good_matches) / max(len(kp1), len(kp2))
            
            # Normalize to 0-1 range
            similarity = min(1.0, similarity * 2)  # Scale up for better range
            
            return float(similarity)
        except Exception as e:
            logger.error(f"[FACE] Error in ORB matching: {e}")
            return 0.5
    
    def _compute_ssim_similarity(self, face1: np.ndarray, face2: np.ndarray) -> float:
        """Compute structural similarity (simplified SSIM)"""
        gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)
        
        # Compute mean and variance
        mean1, stddev1 = cv2.meanStdDev(gray1)
        mean2, stddev2 = cv2.meanStdDev(gray2)
        
        # Compute correlation
        correlation = np.corrcoef(gray1.flatten(), gray2.flatten())[0, 1]
        
        # Simple SSIM approximation
        similarity = (2 * mean1 * mean2 + 0.01) / (mean1**2 + mean2**2 + 0.01)
        similarity = similarity[0][0] * abs(correlation)
        
        return float(max(0, min(1, similarity)))
    
    def _compute_combined_similarity(self, face1: np.ndarray, face2: np.ndarray) -> Dict[str, float]:
        """Compute combined similarity using multiple methods"""
        # Histogram similarity (color/texture)
        hist_sim = self._compute_histogram_similarity(face1, face2)
        
        # ORB keypoint similarity (structural features)
        orb_sim = self._compute_orb_similarity(face1, face2)
        
        # SSIM-like similarity (overall structure)
        ssim_sim = self._compute_ssim_similarity(face1, face2)
        
        # Weighted combination (histogram is most reliable with our setup)
        combined = (hist_sim * 0.5) + (orb_sim * 0.3) + (ssim_sim * 0.2)
        
        return {
            'histogram': hist_sim,
            'orb_features': orb_sim,
            'structural': ssim_sim,
            'combined': combined
        }
    
    def match_faces(
        self,
        id_image_bytes: bytes,
        selfie_image_bytes: bytes
    ) -> Dict[str, Any]:
        """
        Match faces from ID document and selfie
        
        Args:
            id_image_bytes: Bytes of ID card image
            selfie_image_bytes: Bytes of selfie image
            
        Returns:
            Dictionary containing:
                - decision: MATCH, NO_MATCH, FACE_NOT_DETECTED, MULTIPLE_FACES, ERROR
                - similarity_score: Similarity score (0.0 - 1.0)
                - id_face_detected: Boolean
                - selfie_face_detected: Boolean
                - id_face_count: Number of faces in ID
                - selfie_face_count: Number of faces in selfie
                - processing_time: Processing time in milliseconds
                - threshold: Threshold used for decision
                - error: Error message if any
        """
        start_time = time.time()
        
        result = {
            "decision": self.DECISION_ERROR,
            "similarity_score": 0.0,
            "id_face_detected": False,
            "selfie_face_detected": False,
            "id_face_count": 0,
            "selfie_face_count": 0,
            "processing_time": 0,
            "threshold": self.MATCH_THRESHOLD,
            "error": None
        }
        
        try:
            # Load images
            logger.info("[FACE] Loading ID image...")
            id_img = self._load_image(id_image_bytes)
            if id_img is None:
                result["error"] = "Failed to load ID image"
                result["decision"] = self.DECISION_ERROR
                return result
            
            logger.info("[FACE] Loading selfie image...")
            selfie_img = self._load_image(selfie_image_bytes)
            if selfie_img is None:
                result["error"] = "Failed to load selfie image"
                result["decision"] = self.DECISION_ERROR
                return result
            
            # Detect faces in ID image
            logger.info("[FACE] Detecting face in ID image...")
            id_faces = self._detect_faces(id_img)
            result["id_face_count"] = len(id_faces)
            result["id_face_detected"] = len(id_faces) > 0
            
            if len(id_faces) == 0:
                logger.warning("[FACE] No face detected in ID image")
                result["decision"] = self.DECISION_FACE_NOT_DETECTED
                result["error"] = "No face detected in ID image"
                return result
            
            if len(id_faces) > 1:
                logger.warning(f"[FACE] Multiple faces ({len(id_faces)}) detected in ID image")
                result["decision"] = self.DECISION_MULTIPLE_FACES
                result["error"] = f"Multiple faces ({len(id_faces)}) detected in ID image"
                return result
            
            logger.info("[FACE] ✓ ID face detected")
            
            # Detect faces in selfie image
            logger.info("[FACE] Detecting face in selfie image...")
            selfie_faces = self._detect_faces(selfie_img)
            result["selfie_face_count"] = len(selfie_faces)
            result["selfie_face_detected"] = len(selfie_faces) > 0
            
            if len(selfie_faces) == 0:
                logger.warning("[FACE] No face detected in selfie image")
                result["decision"] = self.DECISION_FACE_NOT_DETECTED
                result["error"] = "No face detected in selfie image"
                return result
            
            if len(selfie_faces) > 1:
                logger.warning(f"[FACE] Multiple faces ({len(selfie_faces)}) detected in selfie image")
                result["decision"] = self.DECISION_MULTIPLE_FACES
                result["error"] = f"Multiple faces ({len(selfie_faces)}) detected in selfie image"
                return result
            
            logger.info("[FACE] ✓ Selfie face detected")
            
            # Extract face regions
            logger.info("[FACE] Extracting and preprocessing face regions...")
            id_face = self._extract_face_region(id_img, id_faces[0])
            selfie_face = self._extract_face_region(selfie_img, selfie_faces[0])
            
            # Calculate similarity using multiple methods
            logger.info("[FACE] Computing multi-algorithm face similarity...")
            similarities = self._compute_combined_similarity(id_face, selfie_face)
            
            # Use combined score
            similarity = similarities['combined']
            result["similarity_score"] = similarity
            
            # Log individual scores
            logger.info(f"[FACE] Histogram similarity: {similarities['histogram']:.4f}")
            logger.info(f"[FACE] ORB features similarity: {similarities['orb_features']:.4f}")
            logger.info(f"[FACE] Structural similarity: {similarities['structural']:.4f}")
            logger.info(f"[FACE] Combined similarity score: {similarity:.4f}")
            
            # Make decision
            if similarity >= self.MATCH_THRESHOLD:
                result["decision"] = self.DECISION_MATCH
                logger.info(f"[FACE] ✓ Decision: MATCH (similarity={similarity:.4f} >= threshold={self.MATCH_THRESHOLD})")
            else:
                result["decision"] = self.DECISION_NO_MATCH
                logger.warning(f"[FACE] ✗ Decision: NO_MATCH (similarity={similarity:.4f} < threshold={self.MATCH_THRESHOLD})")
            
        except Exception as e:
            logger.error(f"[FACE] Error in face matching: {e}", exc_info=True)
            result["error"] = str(e)
            result["decision"] = self.DECISION_ERROR
        
        finally:
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            result["processing_time"] = processing_time
            logger.info(f"[FACE] Processing completed in {processing_time}ms")
        
        return result


# Global singleton instance
_face_matching_service = None

def get_face_matching_service() -> FaceMatchingService:
    """Get or create the global face matching service instance"""
    global _face_matching_service
    if _face_matching_service is None:
        _face_matching_service = FaceMatchingService()
    return _face_matching_service
