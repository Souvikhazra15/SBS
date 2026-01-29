import cv2
import re
import numpy as np
from pyzbar.pyzbar import decode
import easyocr
import pytesseract
import os

# Try to use Tesseract for better Indian language support
try:
    # Set this path - Uncomment after installing Tesseract
    pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_AVAILABLE = True
except:
    TESSERACT_AVAILABLE = False

# Initialize OCR readers
reader_easy = easyocr.Reader(['en', 'hi'], gpu=False)
READER = reader_easy  # Default

def extract_ocr(image):
    """Extract text using Tesseract (supports Gujarati) or fallback to easyOCR"""
    
    # Try Tesseract first if available (better Gujarati support)
    if TESSERACT_AVAILABLE:
        try:
            # Tesseract with multiple languages including Gujarati
            text_data_tesseract = pytesseract.image_to_data(
                image, 
                lang='eng+hin+guj',  # English, Hindi, Gujarati
                output_type=pytesseract.Output.DICT
            )
            
            ocr_data = []
            for i, conf in enumerate(text_data_tesseract['conf']):
                if int(conf) > 0:  # Only include detected text
                    x, y, w, h = (
                        text_data_tesseract['left'][i],
                        text_data_tesseract['top'][i],
                        text_data_tesseract['width'][i],
                        text_data_tesseract['height'][i]
                    )
                    text = text_data_tesseract['text'][i].strip()
                    if text:
                        ocr_data.append({
                            "text": text,
                            "bbox": [x, y, x + w, y + h],
                            "conf": int(conf) / 100.0
                        })
            
            if ocr_data:
                print("[Using Tesseract OCR - Gujarati supported]")
                return ocr_data
        except Exception as e:
            print(f"Tesseract failed: {e}, falling back to easyOCR")
    
    # Fallback to easyOCR
    print("[Using easyOCR - Hindi/English only]")
    results = READER.readtext(image)
    ocr_data = []
    for bbox, text, conf in results:
        x_coords = [int(p[0]) for p in bbox]
        y_coords = [int(p[1]) for p in bbox]
        ocr_data.append({
            "text": text.strip(),
            "bbox": [min(x_coords), min(y_coords), max(x_coords), max(y_coords)],
            "conf": conf
        })
    return ocr_data

# ------------------ REGIONS ------------------
def define_regions(h, w):
    """
    Define regions based on Gujarati Aadhar card layout:
    - Top: Name (Local/Gujarati language)
    - Below: Name (English)
    - Below: DOB (with label: તારીખ/DOB : DD/MM/YYYY)
    - Below: Gender (direct text: MALE/FEMALE/પુરુષ/સ્ત્રી)
    - Footer:
      - Aadhar: XXXX XXXX XXXX (12 digits)
      - VID: XXXX XXXX XXXX XXXX (16 digits)
    """
    return {
        "name_local": (0.05*h, 0.30*h),      # Top - Gujarati name
        "name_english": (0.15*h, 0.40*h),    # English name (below Gujarati)
        "dob": (0.25*h, 0.50*h),             # DOB section
        "gender": (0.35*h, 0.65*h),          # Gender (direct text, no label)
        "aadhaar": (0.65*h, 0.85*h),         # Aadhar: XXXX XXXX XXXX
        "vid": (0.80*h, 1.0*h),              # VID: XXXX XXXX XXXX XXXX below Aadhar
        "address": (0.40*h, 1.0*h)           # Address at bottom
    }

def in_region(bbox, region):
    _, y1, _, y2 = bbox
    y = (y1 + y2) / 2
    return region[0] <= y <= region[1]

# ------------------ VALIDATORS ------------------
def is_aadhaar(text):
    """
    Match 12-digit Aadhar in format: XXXX XXXX XXXX
    Exactly 12 digits in 3 groups of 4
    """
    # Check for exact format: 4 digits, space, 4 digits, space, 4 digits
    if re.match(r"^\d{4}\s\d{4}\s\d{4}$", text.strip()):
        return True
    return False

def is_name(text):
    """
    Match English name - typically proper nouns (First Last names)
    Names have clear capital letters for each word
    """
    words = text.split()
    if len(text) < 3:
        return False
    
    # Check for English names: "Vishvarajsinh Krushnpalsinh Zala"
    # All words start with capital letter
    if len(words) >= 2:
        proper_words = sum(1 for w in words if w and w[0].isupper())
        if proper_words >= 2:
            return True
    
    # Also accept all caps names
    if text.isupper() and len(words) >= 2:
        return True
    
    return False

def is_dob(text):
    """
    Match Date of Birth format: DD/MM/YYYY
    May include label like "DOB:" or local language prefix
    Format: DOB: 07/02/2006 or તારીખ: 07/02/2006
    """
    # Must have date in DD/MM/YYYY format
    if re.search(r"\d{1,2}/\d{1,2}/\d{4}", text):
        return True
    return False

def is_gender(text):
    """Match gender: MALE, FEMALE, M, F, પુરુષ, સ્ત્રી, etc (Gujarati & Hindi)"""
    text_upper = text.upper().strip()
    # Check if any gender keyword is present in the text
    # Gender appears without label, just the word itself
    return bool(re.search(r"\b(MALE|FEMALE|M|F|પુરુષ|સ્ત્રી|पुरुष|महिला)\b", text_upper))

def is_vid(text):
    """
    Match VID (Virtual ID) - 16 digits in format: XXXX XXXX XXXX XXXX
    4 groups of 4 digits each
    """
    return "VID" in text.upper() and re.search(r"\d{4}\s\d{4}\s\d{4}\s\d{4}", text) is not None

# ------------------ LAYOUT CHECK ------------------
def layout_check(ocr, h, w):
    regions = define_regions(h, w)
    flags = {
        "name_local": False, 
        "name_english": False, 
        "dob": False, 
        "gender": False,
        "aadhaar": False, 
        "vid": False,
        "address": False
    }
    sizes = []
    detailed_findings = []

    for item in ocr:
        text, bbox = item["text"], item["bbox"]
        size = bbox[3] - bbox[1]
        y_mid = (bbox[1] + bbox[3]) / 2
        sizes.append((text, size))

        # Check in priority order to avoid mis-matches
        
        # 1. VID FIRST (must check before Aadhar since VID contains 12-digit number)
        if is_vid(text) and in_region(bbox, regions["vid"]):
            flags["vid"] = True
            detailed_findings.append(f"✓ VID: {text}")
        
        # 2. Aadhar number (12 digits - very distinctive)
        elif is_aadhaar(text) and in_region(bbox, regions["aadhaar"]):
            flags["aadhaar"] = True
            detailed_findings.append(f"✓ Aadhaar Number: {text}")
        
        # 3. DOB (has date format)
        elif is_dob(text) and in_region(bbox, regions["dob"]):
            flags["dob"] = True
            detailed_findings.append(f"✓ DOB: {text}")
        
        # 4. Gender (specific keywords)
        elif is_gender(text) and in_region(bbox, regions["gender"]):
            flags["gender"] = True
            detailed_findings.append(f"✓ Gender: {text}")
        
        # 5. English Name (proper nouns)
        elif is_name(text) and in_region(bbox, regions["name_english"]):
            flags["name_english"] = True
            detailed_findings.append(f"✓ Name (English): {text}")
        
        # 6. Local language name (anything else at top)
        elif in_region(bbox, regions["name_local"]):
            flags["name_local"] = True
            detailed_findings.append(f"✓ Name (Local): {text}")

    return flags, sizes, detailed_findings

# ------------------ FONT HEURISTIC ------------------
def font_hierarchy(sizes):
    if not sizes:
        return False
    sizes_sorted = sorted(sizes, key=lambda x: x[1], reverse=True)
    return sizes_sorted[0][1] > sizes_sorted[-1][1]

# ------------------ QR CHECK ------------------
def qr_check(image, ocr):
    try:
        qr_data = decode(image)
        if not qr_data:
            return False, "QR missing"

        qr_text = qr_data[0].data.decode("utf-8")
        
        # Find Aadhar number in OCR results
        for item in ocr:
            if is_aadhaar(item["text"]):
                aadhaar_num = item["text"].replace(" ", "")
                # Check if Aadhar number appears in QR data
                if aadhaar_num in qr_text:
                    return True, "QR valid - Aadhar matched"
                else:
                    return False, "QR mismatch - Aadhar not found in QR"
        
        return True, "QR present but Aadhar not verified"
    except Exception as e:
        return False, f"QR error: {str(e)}"

# ------------------ LOGO CHECK ------------------
def logo_presence(image):
    """Check for presence of Aadhar logo using edge detection"""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_sum = np.sum(edges)
        # Aadhar cards have significant edge patterns
        return edge_sum > 50000  # Adjusted threshold
    except Exception as e:
        print(f"Logo check error: {e}")
        return False

# ------------------ TAMPERING CHECK ------------------
def tampering_check(image):
    """Detect tampering/blurring using Laplacian variance (focus measure)"""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F).var()
        # High variance = sharp/clear, Low variance = blurred/edited
        is_clear = lap > 80
        return is_clear, lap
    except Exception as e:
        print(f"Tampering check error: {e}")
        return False, 0

# ------------------ PHOTO EXTRACTION ------------------
def extract_photo(image, image_path):
    """
    Extract the photo from Aadhar card by detecting human face first
    1. Detect face in the image using Haar Cascade
    2. Extract the face region with padding
    3. Save as separate JPG file
    """
    try:
        h, w, _ = image.shape
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Load Haar Cascade classifier for face detection
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Detect faces in the image
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(50, 50)
        )
        
        if len(faces) == 0:
            print("⚠ No face detected in image - using coordinate-based extraction")
            # Fallback to coordinate-based extraction if no face found
            photo_region = image[
                int(0.15*h):int(0.70*h),  # Height: 15% to 70%
                int(0.02*w):int(0.35*w)   # Width: 2% to 35% (left side)
            ]
        else:
            # Get the largest face detected (usually the main photo)
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, fw, fh = largest_face
            
            # Add padding around the face for complete photo extraction
            padding_x = int(fw * 0.15)  # 15% padding on sides
            padding_y = int(fh * 0.20)  # 20% padding on top/bottom
            
            # Calculate extraction boundaries
            x1 = max(0, x - padding_x)
            y1 = max(0, y - padding_y)
            x2 = min(w, x + fw + padding_x)
            y2 = min(h, y + fh + padding_y)
            
            # Extract photo region
            photo_region = image[y1:y2, x1:x2]
            
            print(f"✓ Face detected at position: ({x}, {y}), Size: {fw}x{fh}")
            print(f"✓ Extracting with padding: {padding_x}px (sides), {padding_y}px (top/bottom)")
        
        # Save extracted photo
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        photo_filename = f"{base_name}_photo.jpg"
        photo_dir = os.path.dirname(image_path)
        
        # If no directory specified, use current directory
        if not photo_dir:
            photo_dir = os.getcwd()
        
        photo_path = os.path.join(photo_dir, photo_filename)
        
        # Ensure output directory exists
        os.makedirs(photo_dir, exist_ok=True)
        
        # Save the extracted photo
        cv2.imwrite(photo_path, photo_region)
        print(f"✓ Photo extracted and saved: {photo_filename}")
        
        return True, photo_path
    
    except Exception as e:
        print(f"⚠ Photo extraction error: {e}")
        return False, None


# ------------------ FINAL VERIFICATION ------------------
def verify_aadhaar(image_path):
    """
    Comprehensive Aadhar card verification
    Checks: Layout, QR, Font hierarchy, Logo, Tampering
    Returns: Score (0-100), Status, Details
    """
    
    # Check if image exists
    if not os.path.exists(image_path):
        return {
            "score": 0,
            "status": "Error - Image not found",
            "error": f"File not found: {image_path}",
            "layout": {},
            "qr": "Not checked"
        }
    
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return {
                "score": 0,
                "status": "Error - Invalid image",
                "error": "Unable to read image file",
                "layout": {},
                "qr": "Not checked"
            }
        
        h, w, _ = image.shape
        
        # Extract OCR data
        print("Extracting text from image...")
        ocr = extract_ocr(image)
        
        if not ocr:
            return {
                "score": 0,
                "status": "Error - No text detected",
                "error": "OCR returned no results",
                "layout": {},
                "qr": "Not checked"
            }
        
        print(f"Found {len(ocr)} text elements")
        
        # Perform all checks
        layout_flags, sizes, layout_findings = layout_check(ocr, h, w)
        font_ok = font_hierarchy(sizes)
        qr_ok, qr_msg = qr_check(image, ocr)
        logo_ok = logo_presence(image)
        tamper_ok, lap_var = tampering_check(image)
        
        # Extract photo from Aadhar card
        photo_extracted, photo_path = extract_photo(image, image_path)
        
        # Calculate score (0-100)
        score = 0
        checks_passed = 0
        total_checks = 5
        
        # 1. Layout check - count how many key fields found
        # CRITICAL fields for valid Aadhar: Name (English), DOB, Aadhar number, Gender
        critical_fields = ["name_english", "dob", "aadhaar", "gender"]
        critical_count = sum(1 for field in critical_fields if layout_flags.get(field, False))
        
        if critical_count == 4:  # All critical fields found
            score += 35  # All critical fields found
            checks_passed += 1
        elif critical_count == 3:
            score += 25  # Most fields found
        elif critical_count >= 2:
            score += 15  # Some fields found
        
        # 2. QR check (20 points)
        if qr_ok:
            score += 20
            checks_passed += 1
        
        # 3. Font hierarchy (15 points)
        if font_ok:
            score += 15
            checks_passed += 1
        
        # 4. Logo presence (20 points)
        if logo_ok:
            score += 20
            checks_passed += 1
        
        # 5. Tampering check (20 points)
        if tamper_ok:
            score += 20
            checks_passed += 1
        
        # Determine status based on critical field validation
        if critical_count == 4:  # All 4 critical fields present
            if score >= 90:
                status = "✓ VERIFIED - Original Aadhar Card"
            elif score >= 80:
                status = "✓ Likely Original"
            else:
                status = "⚠ Valid Structure but Warnings"
        elif critical_count >= 3:
            status = "⚠ Suspicious - Missing Field(s)"
        elif critical_count >= 2:
            status = "⚠ Highly Suspicious - Multiple Fields Missing"
        else:
            status = "✗ Invalid Aadhar Card"
        
        # Prepare OCR details
        ocr_details = []
        for item in ocr:
            ocr_details.append({
                "text": item["text"],
                "confidence": round(item["conf"], 3)
            })
        
        return {
            "score": score,
            "status": status,
            "checks_passed": f"{checks_passed}/{total_checks}",
            "photo_extracted": photo_extracted,
            "photo_path": photo_path if photo_extracted else None,
            "details": {
                "layout": layout_flags,
                "layout_findings": layout_findings,
                "font_hierarchy": font_ok,
                "qr_validation": qr_msg,
                "logo_detected": logo_ok,
                "tampering_check": {
                    "clear": tamper_ok,
                    "focus_variance": round(lap_var, 2)
                }
            },
            "ocr_results": ocr_details,
            "image_dimensions": f"{w}x{h}"
        }
    
    except Exception as e:
        return {
            "score": 0,
            "status": "Error - Verification failed",
            "error": str(e),
            "layout": {},
            "qr": "Not checked"
        }

# ------------------ RUN ------------------
if __name__ == "__main__":
    import json
    import sys
    
    # Fix Unicode encoding for Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Check if image file exists in current directory
    image_file = r"C:\SBS\image copy.png"  # Raw string to handle backslashes
    
    if not os.path.exists(image_file):
        print(f"[!] Image file '{image_file}' not found in {os.getcwd()}")
        print("\nAvailable images:")
        for file in os.listdir("."):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                print(f"  - {file}")
        print("\nUsage: python Aadhar.py <image_path>")
        print("Or modify the image_file variable in the script")
    else:
        print(f"Verifying Aadhar card: {image_file}\n")
        result = verify_aadhaar(image_file)
        
        print("=" * 60)
        print("AADHAR CARD VERIFICATION REPORT")
        print("=" * 60)
        print(f"Status: {result['status']}")
        print(f"Score: {result['score']}/100")
        
        if 'checks_passed' in result:
            print(f"Checks Passed: {result['checks_passed']}")
        
        if result.get('photo_extracted'):
            print(f"\n📷 Photo Extracted: {result.get('photo_path')}")
        
        if 'error' not in result or result['error'] is None:
            print("\n--- Verification Details ---")
            if 'details' in result:
                details = result['details']
                print(f"\nLayout Check:")
                print(f"  Name (Local): {'✓ Found' if details['layout'].get('name_local') else '✗ Not Found'}")
                print(f"  Name (English): {'✓ Found' if details['layout'].get('name_english') else '✗ Not Found'}")
                print(f"  DOB: {'✓ Found' if details['layout'].get('dob') else '✗ Not Found'}")
                print(f"  Gender: {'✓ Found' if details['layout'].get('gender') else '✗ Not Found'}")
                print(f"  Aadhaar Number: {'✓ Found' if details['layout'].get('aadhaar') else '✗ Not Found'}")
                print(f"  VID: {'✓ Found' if details['layout'].get('vid') else '✗ Not Found'}")
                
                if details.get('layout_findings'):
                    print(f"\nDetected Elements:")
                    for finding in details['layout_findings']:
                        print(f"  {finding}")
                
                print(f"\nAuthenticity Checks:")
                print(f"  Font Hierarchy: {'✓ PASS' if details['font_hierarchy'] else '✗ FAIL'}")
                print(f"  QR Code: {details['qr_validation']}")
                print(f"  Logo Detection: {'✓ YES' if details['logo_detected'] else '✗ NO'}")
                print(f"  Tampering Check: {'✓ CLEAR' if details['tampering_check']['clear'] else '⚠ BLURRED/EDITED'}")
                print(f"  Focus Variance: {details['tampering_check']['focus_variance']}")            
            # Final Verdict
            print("\n" + "=" * 60)
            print("FINAL VERDICT")
            print("=" * 60)
            
            critical_fields = details['layout']
            all_critical = all([
                critical_fields.get('name_english'),
                critical_fields.get('dob'),
                critical_fields.get('aadhaar'),
                critical_fields.get('gender')
            ])
            
            if all_critical and result['score'] >= 85:
                print("✓ AADHAR CARD IS ORIGINAL")
                print("  → All critical fields detected")
                print("  → Authenticity checks passed")
                print("  → Structure and format verified")
                print("\n  Status: GOOD TO GO ✓")
            elif all_critical and result['score'] >= 70:
                print("⚠ AADHAR CARD IS LIKELY ORIGINAL")
                print("  → All critical fields detected")
                print("  → Some authenticity warnings present")
                print("\n  Status: PROCEED WITH CAUTION ⚠")
            elif result['score'] >= 50:
                print("⚠ AADHAR CARD IS SUSPICIOUS")
                print("  → Some fields missing or unclear")
                print("  → Multiple authenticity concerns")
                print("\n  Status: REQUIRES MANUAL VERIFICATION ⚠")
            else:
                print("✗ AADHAR CARD IS LIKELY EDITED/FAKE")
                print("  → Critical fields missing")
                print("  → Failed authenticity checks")
                print("\n  Status: DO NOT ACCEPT ✗")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("=" * 60)
