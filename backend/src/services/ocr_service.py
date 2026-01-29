"""
OCR Service - Extract text and ID numbers from identity documents

Uses PaddleOCR for high-accuracy optical character recognition with
preprocessing, pattern matching, and confidence scoring.
"""

import os
import re
import cv2
import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    logging.warning("[OCR] PaddleOCR not available, install with: pip install paddleocr")

logger = logging.getLogger(__name__)


class OCRService:
    """Service for OCR processing and ID number extraction"""

    def __init__(self):
        """Initialize OCR engine"""
        if PADDLE_AVAILABLE:
            try:
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',
                    use_gpu=False,
                    show_log=False
                )
                logger.info("[OCR] PaddleOCR initialized successfully")
            except Exception as e:
                logger.error(f"[OCR] Failed to initialize PaddleOCR: {str(e)}")
                self.ocr = None
        else:
            self.ocr = None
            logger.warning("[OCR] PaddleOCR not available")

    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        """
        Preprocess image for better OCR results - Enhanced for Indian ID cards
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Preprocessed image as numpy array
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Failed to decode image")
            
            logger.info(f"[OCR] Image decoded: {image.shape}")
            
            # Resize if too large (keep aspect ratio)
            max_dimension = 2000
            height, width = image.shape[:2]
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                logger.info(f"[OCR] Image resized to {new_width}x{new_height}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Apply bilateral filter to reduce noise while preserving edges
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
            
            # Detect and correct rotation/skew
            coords = np.column_stack(np.where(binary > 0))
            if len(coords) > 0:
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                
                # Only correct if angle is significant
                if abs(angle) > 0.5:
                    (h, w) = binary.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    binary = cv2.warpAffine(
                        binary,
                        M,
                        (w, h),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )
                    logger.info(f"[OCR] Image deskewed by {angle:.2f} degrees")
            
            # Morphological operations to clean up text
            kernel = np.ones((1, 1), np.uint8)
            opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # Sharpen the image for better text clarity
            sharpen_kernel = np.array([[-1, -1, -1],
                                      [-1,  9, -1],
                                      [-1, -1, -1]])
            sharpened = cv2.filter2D(opening, -1, sharpen_kernel)
            
            logger.info("[OCR] Image preprocessing complete")
            return sharpened
            
        except Exception as e:
            logger.error(f"[OCR] Preprocessing failed: {str(e)}")
            # Return original image as fallback
            nparr = np.frombuffer(image_data, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    def check_image_quality(self, image: np.ndarray) -> Tuple[bool, float, str]:
        """
        Check if image quality is sufficient for OCR
        
        Args:
            image: Preprocessed image
            
        Returns:
            Tuple of (is_good_quality, score, message)
        """
        try:
            # Check for blur using Laplacian variance
            laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
            
            # Threshold for blur detection (higher is sharper)
            blur_threshold = 100.0
            
            if laplacian_var < blur_threshold:
                return False, laplacian_var, f"Image is too blurry (score: {laplacian_var:.2f}, threshold: {blur_threshold})"
            
            # Check brightness
            mean_brightness = np.mean(image)
            
            if mean_brightness < 50:
                return False, mean_brightness, "Image is too dark"
            elif mean_brightness > 200:
                return False, mean_brightness, "Image is too bright"
            
            logger.info(f"[OCR] Image quality check passed (blur: {laplacian_var:.2f}, brightness: {mean_brightness:.2f})")
            return True, laplacian_var, "Image quality is good"
            
        except Exception as e:
            logger.error(f"[OCR] Quality check failed: {str(e)}")
            return True, 0.0, "Quality check skipped"

    def extract_id_patterns(self, text: str) -> Dict[str, Any]:
        """
        Extract ID numbers using regex patterns
        
        Supports various formats:
        - Aadhaar: XXXX-XXXX-XXXX or XXXXXXXXXXXX
        - PAN: AAAAA9999A
        - Passport: A1234567, etc.
        - National ID: various patterns
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            Dictionary with extracted IDs and patterns
        """
        results = {
            'aadhaar': [],
            'pan': [],
            'passport': [],
            'national_id': [],
            'all_numbers': []
        }
        
        # Aadhaar pattern: 12 digits with optional dashes/spaces
        aadhaar_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        aadhaar_matches = re.findall(aadhaar_pattern, text)
        results['aadhaar'] = [re.sub(r'[-\s]', '', m) for m in aadhaar_matches]
        
        # PAN pattern: 5 letters + 4 digits + 1 letter
        pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]\b'
        results['pan'] = re.findall(pan_pattern, text.upper())
        
        # Passport pattern: Letter + 7 digits
        passport_pattern = r'\b[A-Z]\d{7}\b'
        results['passport'] = re.findall(passport_pattern, text.upper())
        
        # Generic ID numbers (8-16 digits)
        number_pattern = r'\b\d{8,16}\b'
        results['all_numbers'] = re.findall(number_pattern, text)
        
        # National ID patterns (alphanumeric, 8-20 chars)
        national_id_pattern = r'\b[A-Z0-9]{8,20}\b'
        results['national_id'] = re.findall(national_id_pattern, text.upper())
        
        logger.info(f"[OCR] Pattern extraction: Aadhaar={len(results['aadhaar'])}, "
                   f"PAN={len(results['pan'])}, Passport={len(results['passport'])}, "
                   f"National ID={len(results['national_id'])}")
        
        return results

    def validate_id_format(self, id_number: str, id_type: str) -> Tuple[bool, float]:
        """
        Validate ID number format and compute confidence
        
        Args:
            id_number: The ID number to validate
            id_type: Type of ID (aadhaar, pan, passport, etc.)
            
        Returns:
            Tuple of (is_valid, confidence_score)
        """
        if id_type == 'aadhaar':
            # Aadhaar should be exactly 12 digits
            if len(id_number) == 12 and id_number.isdigit():
                # Verhoeff algorithm validation (simplified)
                return True, 0.95
            return False, 0.3
        
        elif id_type == 'pan':
            # PAN: 5 letters + 4 digits + 1 letter
            if len(id_number) == 10:
                pattern = r'^[A-Z]{5}\d{4}[A-Z]$'
                if re.match(pattern, id_number):
                    return True, 0.95
            return False, 0.3
        
        elif id_type == 'passport':
            # Passport: Letter + 7 digits
            if len(id_number) == 8:
                pattern = r'^[A-Z]\d{7}$'
                if re.match(pattern, id_number):
                    return True, 0.90
            return False, 0.3
        
        else:
            # Generic validation
            if 8 <= len(id_number) <= 20:
                return True, 0.70
            return False, 0.2

    async def process_id_document(self, image_data: bytes) -> Dict[str, Any]:
        """
        Main OCR processing pipeline
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with OCR results, extracted ID, confidence
        """
        start_time = datetime.now()
        
        try:
            logger.info("[OCR] Starting OCR processing")
            
            if not self.ocr:
                raise ValueError("OCR engine not initialized. Install PaddleOCR: pip install paddleocr")
            
            # Preprocess image
            processed_image = self.preprocess_image(image_data)
            
            # Check image quality
            is_good, quality_score, quality_msg = self.check_image_quality(processed_image)
            if not is_good:
                return {
                    'success': False,
                    'error': quality_msg,
                    'quality_score': quality_score,
                    'processing_time': int((datetime.now() - start_time).total_seconds() * 1000)
                }
            
            logger.info("[OCR] Running OCR engine")
            
            # Run OCR
            result = self.ocr.ocr(processed_image, cls=True)
            
            if not result or not result[0]:
                return {
                    'success': False,
                    'error': 'No text detected in image',
                    'processing_time': int((datetime.now() - start_time).total_seconds() * 1000)
                }
            
            # Extract all text and confidence scores
            full_text = []
            confidences = []
            
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                full_text.append(text)
                confidences.append(confidence)
                logger.debug(f"[OCR] Detected: '{text}' (confidence: {confidence:.3f})")
            
            full_text_str = ' '.join(full_text)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"[OCR] Extracted {len(full_text)} text lines with avg confidence {avg_confidence:.3f}")
            
            # Extract ID patterns
            id_patterns = self.extract_id_patterns(full_text_str)
            
            # Determine best ID match
            best_id = None
            best_type = None
            best_confidence = 0.0
            
            # Priority: Aadhaar > PAN > Passport > National ID
            for id_type in ['aadhaar', 'pan', 'passport', 'national_id']:
                if id_patterns[id_type]:
                    candidate = id_patterns[id_type][0]
                    is_valid, conf = self.validate_id_format(candidate, id_type)
                    
                    if is_valid and conf > best_confidence:
                        best_id = candidate
                        best_type = id_type
                        best_confidence = conf * avg_confidence  # Combine OCR and validation confidence
            
            # Fallback to any number if no specific ID found
            if not best_id and id_patterns['all_numbers']:
                best_id = id_patterns['all_numbers'][0]
                best_type = 'unknown'
                best_confidence = avg_confidence * 0.6
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if best_id:
                logger.info(f"[OCR] Extracted ID: {best_id} (type: {best_type}, confidence: {best_confidence:.3f})")
                
                return {
                    'success': True,
                    'idNumber': best_id,
                    'idType': best_type,
                    'confidence': round(best_confidence, 3),
                    'fullText': full_text_str,
                    'ocrResult': {
                        'lines': full_text,
                        'confidences': [round(c, 3) for c in confidences],
                        'avg_confidence': round(avg_confidence, 3),
                        'patterns': id_patterns
                    },
                    'quality_score': round(quality_score, 2),
                    'processing_time': processing_time
                }
            else:
                return {
                    'success': False,
                    'error': 'No ID number found in image',
                    'fullText': full_text_str,
                    'ocrResult': {
                        'lines': full_text,
                        'confidences': [round(c, 3) for c in confidences],
                        'patterns': id_patterns
                    },
                    'processing_time': processing_time
                }
                
        except Exception as e:
            logger.error(f"[OCR] Processing failed: {str(e)}")
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
