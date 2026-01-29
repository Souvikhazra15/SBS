"""
Document Extractor Service - Extract specific fields from Indian identity documents

Supports:
- Aadhaar Card (12-digit number, name, DOB)
- PAN Card (10-character alphanumeric, name, DOB)
- Driving License (DL number, name, DOB)
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """Extract structured data from OCR text for Indian identity documents"""
    
    # Regex patterns for Indian documents
    # Enhanced Aadhaar patterns - EXACT format first (most reliable)
    AADHAAR_EXACT_PATTERN = r'\b\d{4}\s\d{4}\s\d{4}\b'  # XXXX XXXX XXXX (exact)
    AADHAAR_PATTERN = r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'  # With separators
    AADHAAR_CONTINUOUS = r'\b(\d{12})\b'  # Continuous 12 digits
    # Alternative Aadhaar patterns
    AADHAAR_ALT_PATTERN = r'(?:BSOPH)?(\d{4})[\s\-]?(\d{4})[\s\-]?(\d{4})'
    
    PAN_PATTERN = r'\b[A-Z]{5}\d{4}[A-Z]\b'
    # Enhanced PAN with word boundaries to avoid false matches
    PAN_STRICT_PATTERN = r'(?<![A-Z0-9])[A-Z]{5}\d{4}[A-Z](?![A-Z0-9])'
    
    DL_PATTERN = r'\b[A-Z]{2}[-\s]?\d{2}[-\s]?\d{4}[-\s]?\d{7}\b'
    
    # VID Pattern (16 digits in XXXX XXXX XXXX XXXX format)
    VID_PATTERN = r'\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b'
    
    # Date patterns - enhanced for various formats
    DATE_PATTERNS = [
        r'\b(\d{2})[/-](\d{2})[/-](\d{4})\b',  # DD/MM/YYYY or DD-MM-YYYY
        r'\b(\d{2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b',  # DD Mon YYYY
        r'\b(\d{4})[/-](\d{2})[/-](\d{2})\b',  # YYYY/MM/DD or YYYY-MM-DD
        r'\b(\d{2})[/-](\d{2})[/-](\d{2})\b',  # DD/MM/YY
    ]
    
    # Name patterns - enhanced for Indian names
    NAME_PATTERNS = [
        r'(?:Name|NAME|नाम)\s*[:=]?\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,3})',
        r'^([A-Z][A-Z\s]{5,}?)(?=\n)',  # All caps name at start
        r'([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',  # Title case names
    ]
    
    # Father's name patterns
    FATHER_NAME_PATTERNS = [
        r"(?:Father'?s?\s+Name|FATHER'?S?\s+NAME|पिता का नाम)\s*[:=]?\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,3})",
        r'(?:S/O|s/o|Son of)\s*[:=]?\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,3})',
    ]
    
    def __init__(self):
        """Initialize document extractor"""
        self.month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
    
    def extract_aadhaar(self, text: str, ocr_data: List[Any]) -> Dict[str, Any]:
        """
        Extract Aadhaar card details - Enhanced for real card formats
        
        Args:
            text: Full OCR extracted text
            ocr_data: Raw OCR data with bounding boxes
            
        Returns:
            Dictionary with extracted fields
        """
        logger.info("[EXTRACTOR] Extracting Aadhaar details")
        
        result = {
            "documentType": "AADHAAR",
            "aadhaarNumber": None,
            "vidNumber": None,  # Virtual ID
            "name": None,
            "dateOfBirth": None,
            "gender": None,
            "address": None,
            "fatherName": None,
            "confidence": 0.0,
            "extractedFields": {},
            "rawText": text
        }
        
        try:
            # Clean text - remove extra spaces and normalize
            text_clean = ' '.join(text.split())
            text_clean = text_clean.replace('|', 'I').replace('O', '0')  # Common OCR mistakes
            
            # Extract Aadhaar number (12 digits) - Try multiple patterns in priority order
            aadhaar = None
            
            # Priority 1: Exact format with spaces (XXXX XXXX XXXX) - most reliable
            exact_match = re.search(self.AADHAAR_EXACT_PATTERN, text_clean)
            if exact_match:
                aadhaar = exact_match.group().replace(' ', '')
                logger.info(f"[EXTRACTOR] Aadhaar found (exact format): ****{aadhaar[-4:]}")
            
            # Priority 2: With separators (dashes or spaces)
            if not aadhaar:
                sep_match = re.search(self.AADHAAR_PATTERN, text_clean, re.IGNORECASE)
                if sep_match:
                    aadhaar = sep_match.group().replace(' ', '').replace('-', '')
                    logger.info(f"[EXTRACTOR] Aadhaar found (with separators): ****{aadhaar[-4:]}")
            
            # Priority 3: Alternative pattern (BSOPH prefix sometimes appears)
            if not aadhaar:
                alt_match = re.search(self.AADHAAR_ALT_PATTERN, text_clean, re.IGNORECASE)
                if alt_match:
                    aadhaar = alt_match.group(1) + alt_match.group(2) + alt_match.group(3)
                    logger.info(f"[EXTRACTOR] Aadhaar found (alternative pattern): ****{aadhaar[-4:]}")
            
            # Priority 4: Continuous 12 digits
            if not aadhaar:
                cont_match = re.search(self.AADHAAR_CONTINUOUS, text_clean)
                if cont_match:
                    aadhaar = cont_match.group(1)
                    logger.info(f"[EXTRACTOR] Aadhaar found (continuous digits): ****{aadhaar[-4:]}")
            
            # Validate and store if found
            if aadhaar and len(aadhaar) == 12 and aadhaar.isdigit():
                result["aadhaarNumber"] = aadhaar
                result["extractedFields"]["aadhaar"] = aadhaar
                logger.info(f"[EXTRACTOR] ✓ Valid Aadhaar number extracted: ****{aadhaar[-4:]}")
            else:
                logger.warning(f"[EXTRACTOR] ✗ No valid Aadhaar number found in text")
            
            # Extract VID (Virtual ID) - 16 digits in XXXX XXXX XXXX XXXX format
            vid_match = re.search(self.VID_PATTERN, text_clean)
            if vid_match:
                vid = vid_match.group().replace(' ', '')
                if len(vid) == 16 and vid.isdigit():
                    result["vidNumber"] = vid
                    result["extractedFields"]["vid"] = vid
                    logger.info(f"[EXTRACTOR] ✓ VID found: ****{vid[-4:]}")
            
            # Extract name - Try multiple patterns
            name_found = False
            for pattern in self.NAME_PATTERNS:
                name_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                if name_match:
                    name = name_match.group(1).strip()
                    # Validate name (at least 2 words, no digits, reasonable length)
                    if (len(name) > 5 and len(name) < 100 and 
                        not any(char.isdigit() for char in name) and
                        len(name.split()) >= 2):
                        result["name"] = name.title()
                        result["extractedFields"]["name"] = name.title()
                        logger.info(f"[EXTRACTOR] Name found: {name}")
                        name_found = True
                        break
            
            # Extract father's name
            for pattern in self.FATHER_NAME_PATTERNS:
                father_match = re.search(pattern, text, re.IGNORECASE)
                if father_match:
                    father_name = father_match.group(1).strip()
                    if len(father_name) > 5 and not any(char.isdigit() for char in father_name):
                        result["fatherName"] = father_name.title()
                        result["extractedFields"]["fatherName"] = father_name.title()
                        logger.info(f"[EXTRACTOR] Father's name found: {father_name}")
                        break
            
            # Extract DOB - Enhanced patterns
            dob_patterns = [
                r'(?:DOB|D\.O\.B|Date of Birth|Birth|जन्म तिथि)\s*[:=]?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
                r'(?:DOB|D\.O\.B|Date of Birth|Birth)\s*[:=]?\s*(\d{2}\s+[A-Za-z]+\s+\d{4})',
                r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b',  # Any date pattern
            ]
            
            for pattern in dob_patterns:
                dob_match = re.search(pattern, text, re.IGNORECASE)
                if dob_match:
                    dob = self._normalize_date(dob_match.group(1))
                    if dob and self._is_valid_dob(dob):
                        result["dateOfBirth"] = dob
                        result["extractedFields"]["dob"] = dob
                        logger.info(f"[EXTRACTOR] DOB found: {dob}")
                        break
            
            # Extract gender
            gender_match = re.search(r'\b(MALE|FEMALE|M|F|पुरुष|महिला)\b', text, re.IGNORECASE)
            if gender_match:
                gender = gender_match.group(1).upper()
                gender = 'MALE' if gender in ['MALE', 'M', 'पुरुष'] else 'FEMALE'
                result["gender"] = gender
                result["extractedFields"]["gender"] = gender
            
            # Calculate confidence based on extracted fields
            confidence = 0
            if result["aadhaarNumber"]:
                confidence += 50  # Most important
            if result["name"]:
                confidence += 25
            if result["dateOfBirth"]:
                confidence += 15
            if result["gender"]:
                confidence += 10
            
            result["confidence"] = confidence / 100.0
            logger.info(f"[EXTRACTOR] Aadhaar extraction confidence: {result['confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"[EXTRACTOR] Aadhaar extraction failed: {str(e)}")
        
        return result
    
    def extract_pan(self, text: str, ocr_data: List[Any]) -> Dict[str, Any]:
        """
        Extract PAN card details
        
        Args:
            text: Full OCR extracted text
            ocr_data: Raw OCR data with bounding boxes
            
        Returns:
            Dictionary with extracted fields
        """
        logger.info("[EXTRACTOR] Extracting PAN details")
        
        result = {
            "documentType": "PAN_CARD",
            "panNumber": None,
            "name": None,
            "fatherName": None,
            "dateOfBirth": None,
            "confidence": 0.0,
            "extractedFields": {},
            "rawText": text
        }
        
        try:
            # Extract PAN number (Format: ABCDE1234F)
            # Clean text first for better matching
            text_clean = ' '.join(text.split()).replace('|', 'I').replace('O', '0')
            text_upper = text_clean.upper()
            
            # Try strict pattern first (most reliable)
            pan_match = re.search(self.PAN_STRICT_PATTERN, text_upper)
            if not pan_match:
                # Fallback to regular pattern
                pan_match = re.search(self.PAN_PATTERN, text_upper)
            
            if pan_match:
                pan = pan_match.group().upper().strip()
                # Validate PAN format more strictly
                if (len(pan) == 10 and 
                    pan[:5].isalpha() and 
                    pan[5:9].isdigit() and 
                    pan[9].isalpha()):
                    result["panNumber"] = pan
                    result["extractedFields"]["pan"] = pan
                    logger.info(f"[EXTRACTOR] \u2713 PAN number found: {pan[:3]}**{pan[-1]}")
                else:
                    logger.warning(f"[EXTRACTOR] Invalid PAN format: {pan}")
            
            # Extract Card ID (visible on card, format like BSOPH1631)
            card_id_pattern = r'\b([A-Z]{5}\d{4})\b'
            card_id_match = re.search(card_id_pattern, text_clean)
            if card_id_match:
                card_id = card_id_match.group(1)
                # Make sure it's not the PAN number itself
                if card_id != result.get("panNumber"):
                    result["extractedFields"]["cardId"] = card_id
                    logger.info(f"[EXTRACTOR] Card ID found: {card_id}")
            
            # Extract name - Enhanced for PAN card format
            name_patterns = [
                r'(?:Name|NAME|नाम)\s*[:=]?\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,3})',
                r'([A-Z][A-Z\s]{5,}?)(?=\s*(?:Father|पिता|FATHER))',  # Name before "Father"
                r'([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)',  # Title case names
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                if name_match:
                    name = name_match.group(1).strip()
                    # Validate name - filter out common text on cards
                    if (len(name) > 5 and len(name) < 100 and 
                        not any(char.isdigit() for char in name) and
                        'INCOME TAX' not in name.upper() and
                        'PERMANENT' not in name.upper() and
                        'ACCOUNT' not in name.upper() and
                        len(name.split()) >= 2):
                        result["name"] = name.title()
                        result["extractedFields"]["name"] = name.title()
                        logger.info(f"[EXTRACTOR] Name found: {name}")
                        break
            
            # Extract father's name - Use enhanced patterns from class
            for pattern in self.FATHER_NAME_PATTERNS:
                father_match = re.search(pattern, text, re.IGNORECASE)
                if father_match:
                    father_name = father_match.group(1).strip()
                    if (len(father_name) > 5 and 
                        not any(char.isdigit() for char in father_name) and
                        father_name != result.get("name")):
                        result["fatherName"] = father_name.title()
                        result["extractedFields"]["fatherName"] = father_name.title()
                        logger.info(f"[EXTRACTOR] Father's name found: {father_name}")
                        break
            
            # Extract DOB - Enhanced patterns
            dob_patterns = [
                r'(?:DOB|D\.O\.B|Date of Birth|Birth|जन्म तिथि)\s*[:=]?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
                r'(?:DOB|D\.O\.B|Date of Birth|Birth)\s*[:=]?\s*(\d{2}\s+[A-Za-z]+\s+\d{4})',
                r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b',
            ]
            
            for pattern in dob_patterns:
                dob_match = re.search(pattern, text, re.IGNORECASE)
                if dob_match:
                    dob = self._normalize_date(dob_match.group(1))
                    if dob and self._is_valid_dob(dob):
                        result["dateOfBirth"] = dob
                        result["extractedFields"]["dob"] = dob
                        logger.info(f"[EXTRACTOR] DOB found: {dob}")
                        break
            
            # Calculate confidence
            confidence = 0
            if result["panNumber"]:
                confidence += 60  # Most important for PAN
            if result["name"]:
                confidence += 25
            if result["dateOfBirth"]:
                confidence += 10
            if result["fatherName"]:
                confidence += 5
            
            result["confidence"] = confidence / 100.0
            logger.info(f"[EXTRACTOR] PAN extraction confidence: {result['confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"[EXTRACTOR] PAN extraction failed: {str(e)}")
        
        return result
    
    def extract_driving_license(self, text: str, ocr_data: List[Any]) -> Dict[str, Any]:
        """
        Extract Driving License details
        
        Args:
            text: Full OCR extracted text
            ocr_data: Raw OCR data with bounding boxes
            
        Returns:
            Dictionary with extracted fields
        """
        logger.info("[EXTRACTOR] Extracting Driving License details")
        
        result = {
            "documentType": "DRIVERS_LICENSE",
            "licenseNumber": None,
            "name": None,
            "dateOfBirth": None,
            "issueDate": None,
            "expiryDate": None,
            "bloodGroup": None,
            "address": None,
            "confidence": 0.0,
            "extractedFields": {},
            "rawText": text
        }
        
        try:
            # Extract DL number (Format: XX-YYZZZZZZZZZZ or variations)
            dl_match = re.search(self.DL_PATTERN, text)
            if dl_match:
                dl_number = dl_match.group().replace(' ', '').replace('-', '')
                result["licenseNumber"] = dl_number
                result["extractedFields"]["licenseNumber"] = dl_number
                logger.info(f"[EXTRACTOR] DL number found: {dl_number}")
            
            # Extract name
            name_patterns = [
                r'(?:Name|NAME)\s*[:=]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, text)
                if name_match:
                    name = name_match.group(1).strip()
                    if len(name) > 3:
                        result["name"] = name
                        result["extractedFields"]["name"] = name
                        logger.info(f"[EXTRACTOR] Name found: {name}")
                        break
            
            # Extract DOB
            dob_patterns = [
                r'(?:DOB|Date of Birth|Birth)\s*[:=]?\s*(\d{2}[/-]\d{2}[/-]\d{4})',
            ]
            
            for pattern in dob_patterns:
                dob_match = re.search(pattern, text, re.IGNORECASE)
                if dob_match:
                    dob = self._normalize_date(dob_match.group(1))
                    if dob:
                        result["dateOfBirth"] = dob
                        result["extractedFields"]["dob"] = dob
                        logger.info(f"[EXTRACTOR] DOB found: {dob}")
                        break
            
            # Extract blood group
            blood_match = re.search(r'\b([ABO]|AB)[+-]\b', text)
            if blood_match:
                blood_group = blood_match.group()
                result["bloodGroup"] = blood_group
                result["extractedFields"]["bloodGroup"] = blood_group
            
            # Calculate confidence
            confidence = 0
            if result["licenseNumber"]:
                confidence += 50
            if result["name"]:
                confidence += 30
            if result["dateOfBirth"]:
                confidence += 20
            
            result["confidence"] = confidence / 100.0
            logger.info(f"[EXTRACTOR] DL extraction confidence: {result['confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"[EXTRACTOR] DL extraction failed: {str(e)}")
        
        return result
    
    def _is_valid_dob(self, date_str: str) -> bool:
        """
        Validate if date of birth is reasonable
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            True if valid DOB
        """
        try:
            from datetime import datetime
            dob = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.now()
            age = (today - dob).days // 365
            
            # Valid age range: 0-120 years
            return 0 <= age <= 120
        except:
            return False
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date to YYYY-MM-DD format
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Normalized date string or None
        """
        try:
            # Try DD/MM/YYYY or DD-MM-YYYY
            match = re.match(r'(\d{2})[/-](\d{2})[/-](\d{4})', date_str)
            if match:
                day, month, year = match.groups()
                return f"{year}-{month}-{day}"
            
            # Try DD Mon YYYY
            match = re.match(r'(\d{2})\s+([A-Za-z]+)\s+(\d{4})', date_str)
            if match:
                day, month_name, year = match.groups()
                month = self.month_map.get(month_name[:3].lower())
                if month:
                    return f"{year}-{month}-{day}"
            
            # Try YYYY/MM/DD or YYYY-MM-DD
            match = re.match(r'(\d{4})[/-](\d{2})[/-](\d{2})', date_str)
            if match:
                year, month, day = match.groups()
                return f"{year}-{month}-{day}"
            
        except Exception as e:
            logger.error(f"[EXTRACTOR] Date normalization failed: {str(e)}")
        
        return None
    
    def extract(self, document_type: str, text: str, ocr_data: List[Any]) -> Dict[str, Any]:
        """
        Extract document details based on document type
        
        Args:
            document_type: Type of document (AADHAAR, PAN_CARD, DRIVERS_LICENSE, PASSPORT, NATIONAL_ID, VOTER_ID)
            text: Full OCR extracted text
            ocr_data: Raw OCR data with bounding boxes
            
        Returns:
            Dictionary with extracted fields
        """
        logger.info(f"[EXTRACTOR] Processing document type: {document_type}")
        
        if document_type == "AADHAAR":
            return self.extract_aadhaar(text, ocr_data)
        elif document_type == "PAN_CARD":
            return self.extract_pan(text, ocr_data)
        elif document_type == "DRIVERS_LICENSE":
            return self.extract_driving_license(text, ocr_data)
        elif document_type in ["PASSPORT", "NATIONAL_ID", "VOTER_ID"]:
            return self.extract_generic_id(document_type, text, ocr_data)
        else:
            logger.warning(f"[EXTRACTOR] Unknown document type: {document_type}, using generic extraction")
            return self.extract_generic_id(document_type, text, ocr_data)
    
    def extract_generic_id(self, document_type: str, text: str, ocr_data: List[Any]) -> Dict[str, Any]:
        """
        Extract generic identity document details (Passport, National ID, Voter ID, etc.)
        
        Args:
            document_type: Type of document
            text: Full OCR extracted text
            ocr_data: Raw OCR data with bounding boxes
            
        Returns:
            Dictionary with extracted fields
        """
        logger.info(f"[EXTRACTOR] Extracting generic ID: {document_type}")
        
        result = {
            "documentType": document_type,
            "documentNumber": None,
            "name": None,
            "dateOfBirth": None,
            "confidence": 0.0,
            "extractedFields": {},
            "rawText": text
        }
        
        try:
            text_clean = ' '.join(text.split())
            
            # Generic document number patterns
            doc_patterns = [
                r'\b([A-Z]\d{7,8})\b',  # Passport format (A1234567)
                r'\b([A-Z]{2}\d{6,8})\b',  # Various ID formats
                r'\b([A-Z]{3}\d{7})\b',  # Voter ID format (ABC1234567)
                r'\b(\d{8,16})\b',  # Generic numeric IDs
                r'\b([A-Z0-9]{8,20})\b',  # Alphanumeric IDs
            ]
            
            for pattern in doc_patterns:
                match = re.search(pattern, text_clean)
                if match:
                    doc_num = match.group(1)
                    # Filter out common false positives
                    if doc_num not in ['REPUBLIC', 'GOVERNMENT', 'DOCUMENT']:
                        result["documentNumber"] = doc_num
                        result["extractedFields"]["documentNumber"] = doc_num
                        result["extractedFields"]["number"] = doc_num
                        logger.info(f"[EXTRACTOR] Document number found: {doc_num}")
                        break
            
            # Extract name - use existing patterns
            for pattern in self.NAME_PATTERNS:
                name_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
                if name_match:
                    name = name_match.group(1).strip()
                    if (len(name) > 5 and len(name) < 100 and 
                        not any(char.isdigit() for char in name) and
                        len(name.split()) >= 2):
                        result["name"] = name.title()
                        result["extractedFields"]["name"] = name.title()
                        logger.info(f"[EXTRACTOR] Name found: {name}")
                        break
            
            # Extract DOB
            for pattern in self.DATE_PATTERNS:
                dob_match = re.search(pattern, text, re.IGNORECASE)
                if dob_match:
                    date_text = dob_match.group()
                    dob = self._normalize_date(date_text)
                    if dob and self._is_valid_dob(dob):
                        result["dateOfBirth"] = dob
                        result["extractedFields"]["dob"] = dob
                        logger.info(f"[EXTRACTOR] DOB found: {dob}")
                        break
            
            # Calculate confidence
            confidence = 0
            if result["documentNumber"]:
                confidence += 50
            if result["name"]:
                confidence += 30
            if result["dateOfBirth"]:
                confidence += 20
            
            result["confidence"] = confidence / 100.0
            logger.info(f"[EXTRACTOR] {document_type} extraction confidence: {result['confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"[EXTRACTOR] Generic ID extraction failed: {str(e)}")
        
        return result
