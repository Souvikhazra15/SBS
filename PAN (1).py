import cv2
import re
import numpy as np
import easyocr
import os
from pyzbar.pyzbar import decode

# ---------------- OCR ----------------
reader = easyocr.Reader(['en'], gpu=False)

def extract_ocr(image):
    results = reader.readtext(image)
    data = []
    for bbox, text, conf in results:
        x = [int(p[0]) for p in bbox]
        y = [int(p[1]) for p in bbox]
        # Clean and normalize text
        cleaned_text = text.strip()
        data.append({
            "text": cleaned_text,
            "bbox": [min(x), min(y), max(x), max(y)],
            "conf": conf
        })
    return data

# ---------------- PAN FORMAT ----------------
def is_valid_pan(pan):
    return re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan) is not None

def correct_pan_ocr_errors(text):
    """
    Fix common OCR mistakes in PAN numbers.
    Common errors: 5->S, 7->T, 0->O, 1->I, 8->B, etc.
    """
    if len(text) != 10:
        return None
    
    # Expected format: 5 letters, 4 digits, 1 letter
    corrected = text.upper()
    
    # For positions 5-8 (0-indexed: 5,6,7,8), replace letters with similar digits
    digit_replacements = {
        'S': '5', 'T': '7', 'O': '0', 'I': '1', 'B': '8', 
        'Z': '2', 'G': '6', 'L': '1', 'Q': '0', 'A': '4'
    }
    
    # Convert to list for easier manipulation
    chars = list(corrected)
    
    # Fix digit positions (indices 5-8) - replace letters with likely digits
    for i in range(5, 9):
        if chars[i].isalpha() and chars[i] in digit_replacements:
            chars[i] = digit_replacements[chars[i]]
    
    # Fix letter positions that might have digits (indices 0-4 and 9)
    letter_replacements = {'5': 'S', '7': 'T', '0': 'O', '1': 'I', '8': 'B', '2': 'Z', '4': 'A'}
    for i in list(range(0, 5)) + [9]:
        if chars[i].isdigit() and chars[i] in letter_replacements:
            chars[i] = letter_replacements[chars[i]]
    
    result = ''.join(chars)
    return result if is_valid_pan(result) else None

# ---------------- REGIONS ----------------
def define_regions(h):
    return {
        "header": (0.00*h, 0.18*h),
        "pan": (0.18*h, 0.35*h),
        "name": (0.35*h, 0.50*h),
        "father": (0.50*h, 0.65*h),
        "dob": (0.65*h, 0.80*h)
    }

def in_region(bbox, region):
    _, y1, _, y2 = bbox
    center = (y1 + y2) / 2
    return region[0] <= center <= region[1]

# ---------------- FIELD DETECTORS ----------------
def is_name(text):
    return text.isupper() and len(text.split()) >= 2

def is_dob(text):
    return re.fullmatch(r"\d{2}/\d{2}/\d{4}", text) is not None

# More strict person-name detector to avoid headers like 'INCOME TAX DEPARTMENT'
BANNED_NAME_PHRASES = {
    "INCOME TAX DEPARTMENT",
    "GOVERNMENT OF INDIA",
    "GOVT OF INDIA",
    "PERMANENT ACCOUNT NUMBER",
    "ACCOUNT NUMBER",
    "INCOME TAX",
    "DEPARTMENT",
    "INDIA",
    "DATE OF BIRTH",
    "DOB",
    "FATHER'S NAME",
    "FATHER NAME"
}

BANNED_NAME_TOKENS = {
    "DATE", "BIRTH", "GOVERNMENT", "GOVT", "DEPARTMENT", "INCOME", "TAX",
    "ACCOUNT", "NUMBER", "PAN", "OF", "NAME", "FATHER", "SON", "DAUGHTER",
    "S/O", "D/O"
}

def is_person_name(text):
    t = text.strip().upper()
    words = [w for w in t.split() if w]
    # Must be alphabetic words
    if not words or any(not w.isalpha() for w in words):
        return False
    # Must have at least two words
    if len(words) < 2:
        return False
    # Disallow known label phrases and tokens
    if any(phrase in t for phrase in BANNED_NAME_PHRASES):
        return False
    if any(w in BANNED_NAME_TOKENS for w in words):
        return False
    return True

# ---------------- LABEL-BASED EXTRACTION ----------------
# Common PAN card labels and synonyms
LABEL_PATTERNS = {
    "pan": [
        r"\bPERMANENT\s+ACCOUNT\s+NUMBER\b",
        r"\bPAN\b",
        r"\bAccount\s+Number\b",
        r"\bस्थायी\s+खाता\b"
    ],
    "name": [r"\bNAME\b", r"\bनाम\b"],
    "father": [
        r"\bFATHER'?S\s+NAME\b",
        r"\bFATHER\s+NAME\b",
        r"\bFATHER\b",
        r"\bS/O\b",
        r"\bD/O\b",
        r"\bSON\s+OF\b",
        r"\bDAUGHTER\s+OF\b",
        r"\bपिता\s+का\s+नाम\b"
    ],
    "dob": [
        r"\bDATE\s+OF\s+BIRTH\b",
        r"\bDOB\b",
        r"\bजन्म\s+की\s+तारीख\b",
        r"\bDate\s+of\s+Birth\b"
    ]
}

def _match_label_type(text):
    t = text.strip().upper()
    for key, patterns in LABEL_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, t):
                return key
    return None

def _center(b):
    return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)

def _distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5

def _is_right_of(label_bbox, value_bbox):
    return value_bbox[0] >= label_bbox[2] - 5  # small tolerance

def _is_below(label_bbox, value_bbox):
    return value_bbox[1] >= label_bbox[3] - 5

def _on_same_line(label_bbox, value_bbox, tolerance=20):
    """Check if value is roughly on same horizontal line as label"""
    label_center_y = (label_bbox[1] + label_bbox[3]) / 2
    value_center_y = (value_bbox[1] + value_bbox[3]) / 2
    return abs(label_center_y - value_center_y) < tolerance

def _candidate_ok(label_type, text):
    if label_type == "pan":
        return is_valid_pan(text)
    if label_type == "dob":
        return is_dob(text)
    if label_type in ("name", "father"):
        return is_person_name(text)
    return False

def _score_candidate(label_bbox, value_bbox):
    lc = _center(label_bbox)
    vc = _center(value_bbox)
    # Prioritize vertical proximity (value must be below the label)
    dy = max(0, value_bbox[1] - label_bbox[3])
    dx = abs(vc[0] - lc[0])
    return dy + 0.5 * dx

def label_based_extract(ocr, h):
    """
    Identify fields by detecting explicit labels and picking nearby values.
    Returns a dict with keys pan,name,father,dob and font sizes list.
    """
    result = {"pan": None, "name": None, "father": None, "dob": None}
    font_sizes = []

    # index OCR items
    items = [
        {"text": it["text"], "bbox": it["bbox"], "size": it["bbox"][3] - it["bbox"][1]}
        for it in ocr
    ]
    for it in items:
        font_sizes.append((it["text"], it["size"]))

    # EARLY FALLBACK: scan for PAN and DOB first using simple patterns
    if not result.get("pan"):
        for it in items:
            text = it["text"].strip()
            # Try direct match
            if is_valid_pan(text):
                result["pan"] = text
                break
            # Try OCR error correction
            corrected = correct_pan_ocr_errors(text)
            if corrected:
                result["pan"] = corrected
                break
    
    if not result.get("dob"):
        for it in items:
            text = it["text"].strip()
            if is_dob(text):
                result["dob"] = text
                break

    # Collect all labels
    labels = []  # (type, bbox, text)
    for it in items:
        lt = _match_label_type(it["text"])
        if lt:
            labels.append((lt, it["bbox"], it["text"]))

    # Helper to get nearest label of a given type vertically relative to a bbox
    def nearest_label_above(label_type, bbox):
        ty = None
        min_dy = float("inf")
        for lt, lb, _ in labels:
            if lt != label_type:
                continue
            if lb[3] <= bbox[1]:  # label bottom above value top
                dy = bbox[1] - lb[3]
                if dy < min_dy:
                    min_dy = dy
                    ty = lb
        return ty

    def nearest_label_below(label_type, bbox):
        ty = None
        min_dy = float("inf")
        for lt, lb, _ in labels:
            if lt != label_type:
                continue
            if lb[1] >= bbox[3]:  # label top below value bottom
                dy = lb[1] - bbox[3]
                if dy < min_dy:
                    min_dy = dy
                    ty = lb
        return ty

    # For each label occurrence, choose best candidate below with extra constraints
    chosen_values = {"pan": None, "name": None, "father": None, "dob": None}
    chosen_scores = {k: float("inf") for k in chosen_values}

    # Cache label bboxes by type
    label_bboxes = {
        "name": [lb for lt, lb, _ in labels if lt == "name"],
        "father": [lb for lt, lb, _ in labels if lt == "father"],
        "pan": [lb for lt, lb, _ in labels if lt == "pan"],
        "dob": [lb for lt, lb, _ in labels if lt == "dob"],
    }

    max_gap = max(20, int(0.20 * h))  # value must be close under the label (widened)
    for lt, label_bbox, _text in labels:
        # build candidates below or right-of (for PAN/DOB which may be inline)
        candidates = []
        for jt in items:
            val_text, val_bbox = jt["text"], jt["bbox"]
            if not _candidate_ok(lt, val_text):
                continue
            
            # For PAN and DOB, also allow right-of (inline) positioning
            is_inline = False
            if lt in ("pan", "dob"):
                if _is_right_of(label_bbox, val_bbox) and _on_same_line(label_bbox, val_bbox):
                    is_inline = True
            
            # Check if below or inline
            is_below_label = _is_below(label_bbox, val_bbox)
            if not (is_below_label or is_inline):
                continue
            
            # enforce vertical proximity band for below positioning
            if is_below_label:
                dy = val_bbox[1] - label_bbox[3]
                if dy < 0 or dy > max_gap:
                    continue

            # Additional constraint: if extracting name and a father label exists, restrict to above father label
            if lt == "name" and label_bboxes["father"]:
                # find nearest father label below the current name label
                nearest_father = None
                min_gap = float("inf")
                for fb in label_bboxes["father"]:
                    if fb[1] >= label_bbox[3]:  # father label below name label
                        gap = fb[1] - label_bbox[3]
                        if gap < min_gap:
                            min_gap = gap
                            nearest_father = fb
                if nearest_father is not None:
                    # candidate must lie above father label top
                    if val_bbox[1] >= nearest_father[1]:
                        continue

            # If extracting father and a name label exists, restrict to below name label
            if lt == "father" and label_bboxes["name"]:
                # find nearest name label above current father label
                nearest_name = None
                min_gap_n = float("inf")
                for nb in label_bboxes["name"]:
                    if nb[3] <= label_bbox[1]:  # name label above father label
                        gap = label_bbox[1] - nb[3]
                        if gap < min_gap_n:
                            min_gap_n = gap
                            nearest_name = nb
                if nearest_name is not None:
                    # candidate must lie below name label bottom
                    if val_bbox[3] <= nearest_name[3]:
                        continue

            score = _score_candidate(label_bbox, val_bbox)
            candidates.append((score, val_text, val_bbox))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            score, val_text, val_bbox = candidates[0]
            if score < chosen_scores[lt]:
                chosen_scores[lt] = score
                chosen_values[lt] = val_text

    # finalize - merge label-based results, but preserve early-detected PAN/DOB
    for key, value in chosen_values.items():
        if value is not None:
            result[key] = value

    # Fallback: comprehensive scan for PAN in all OCR text
    if not result.get("pan"):
        for it in items:
            text = it["text"]
            # Try multiple cleaning strategies
            variants = [
                text.strip(),
                text.strip().replace(" ", ""),
                text.strip().replace("\n", ""),
                text.strip().replace(" ", "").replace("\n", "").upper()
            ]
            for variant in variants:
                if is_valid_pan(variant):
                    result["pan"] = variant
                    break
                # Regex search within text
                pan_match = re.search(r'([A-Z]{5}[0-9]{4}[A-Z])', variant)
                if pan_match:
                    candidate = pan_match.group(1)
                    if is_valid_pan(candidate):
                        result["pan"] = candidate
                        break
            if result.get("pan"):
                break
    
    if not result.get("dob"):
        for it in items:
            if is_dob(it["text"]):
                result["dob"] = it["text"]
                break
            # Also check if date appears after colon
            if ":" in it["text"]:
                parts = it["text"].split(":")
                for part in parts:
                    clean = part.strip()
                    if is_dob(clean):
                        result["dob"] = clean
                        break

    # Avoid duplicates: if name equals father, unset father
    if result.get("name") and result.get("father") and result["name"].strip() == result["father"].strip():
        result["father"] = None

    # Fallback ordering: use vertical order (topmost = Name, next = Father)
    # Always collect all person names and override if label matching was unreliable
    person_items = [(it["text"], it["bbox"]) for it in items if is_person_name(it["text"])]
    if person_items:
        # sort by top y (vertical position, top to bottom)
        person_items.sort(key=lambda x: x[1][1])
        
        # Override name with topmost person name if it exists
        if len(person_items) >= 1:
            result["name"] = person_items[0][0]
        
        # Override father with second person name if it exists
        if len(person_items) >= 2 and person_items[1][0] != result.get("name"):
            result["father"] = person_items[1][0]
        else:
            # No second name found
            if result.get("father") == result.get("name"):
                result["father"] = None

    return result, font_sizes

# ---------------- LAYOUT & EXTRACTION ----------------
def layout_and_extract(ocr, h):
    regions = define_regions(h)
    result = {
        "pan": None,
        "name": None,
        "father": None,
        "dob": None
    }
    font_sizes = []

    name_candidates = []  # (text, size, bbox)
    name_bbox = None
    father_bbox = None

    for item in ocr:
        text, bbox = item["text"], item["bbox"]
        size = bbox[3] - bbox[1]
        font_sizes.append((text, size))

        if is_valid_pan(text) and in_region(bbox, regions["pan"]):
            result["pan"] = text

        # Collect uppercase multi-word candidates for name/father
        if is_person_name(text):
            name_candidates.append((text, size, bbox))

        if is_person_name(text) and in_region(bbox, regions["name"]):
            result["name"] = text
            name_bbox = bbox

        elif is_person_name(text) and in_region(bbox, regions["father"]):
            result["father"] = text
            father_bbox = bbox

        elif is_dob(text) and in_region(bbox, regions["dob"]):
            result["dob"] = text

    # Heuristic fallback: use font size to disambiguate name vs father's name
    if name_candidates:
        # Sort candidates by size (largest first)
        name_candidates.sort(key=lambda x: x[1], reverse=True)

        # If name is missing, take the largest candidate
        if result["name"] is None:
            result["name"] = name_candidates[0][0]
            name_bbox = name_candidates[0][2]

        # If father is missing, choose the next suitable candidate
        if result["father"] is None:
            # Prefer a candidate below the name (vertical position)
            father_text = None
            if name_bbox is not None:
                name_center_y = (name_bbox[1] + name_bbox[3]) / 2
                for text, size, bbox in name_candidates[1:]:
                    if text != result["name"]:
                        center_y = (bbox[1] + bbox[3]) / 2
                        if center_y > name_center_y:
                            father_text = text
                            father_bbox = bbox
                            break
            # Fallback: second largest distinct candidate
            if father_text is None:
                for text, size, bbox in name_candidates:
                    if text != result["name"]:
                        father_text = text
                        father_bbox = bbox
                        break
            result["father"] = father_text

        # Correction: if only father got set and it's the largest candidate, swap
        if result["name"] is None and result["father"] is not None:
            largest_text = name_candidates[0][0]
            if result["father"] == largest_text:
                result["name"] = result["father"]
                # choose another for father
                for text, size, bbox in name_candidates[1:]:
                    if text != result["name"]:
                        result["father"] = text
                        father_bbox = bbox
                        break

    # Avoid duplicate assignment
    if result["father"] == result["name"]:
        result["father"] = None

    return result, font_sizes

# ---------------- FONT HIERARCHY ----------------
def font_hierarchy(fonts):
    if len(fonts) < 2:
        return False
    largest = max(fonts, key=lambda x: x[1])[1]
    smallest = min(fonts, key=lambda x: x[1])[1]
    return largest > smallest * 1.4

# ---------------- QR CHECK ----------------
def qr_check(image, pan):
    qr = decode(image)
    if not qr:
        return False
    qr_text = qr[0].data.decode("utf-8")
    return pan.replace(" ", "") in qr_text

# ---------------- TAMPERING CHECK ----------------
def tampering_check(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    return lap > 80

# ---------------- PHOTO EXTRACTION ----------------
def extract_face_photo(image, image_path):
    """
    Extract a face photo from the PAN card image.
    1. Detect face using Haar Cascade.
    2. If none found, fallback to a reasonable left-side crop.
    3. Save as <base>_photo.jpg adjacent to the input image.
    """
    try:
        h, w, _ = image.shape
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(50, 50)
        )

        if len(faces) == 0:
            # Fallback: crop a typical photo area (left/top quadrant)
            x1, y1 = int(0.03 * w), int(0.15 * h)
            x2, y2 = int(0.35 * w), int(0.65 * h)
            photo_region = image[y1:y2, x1:x2]
        else:
            # Choose largest detected face
            x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
            pad_x, pad_y = int(fw * 0.15), int(fh * 0.20)
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(w, x + fw + pad_x)
            y2 = min(h, y + fh + pad_y)
            photo_region = image[y1:y2, x1:x2]

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        photo_filename = f"{base_name}_photo.jpg"
        out_dir = os.path.dirname(image_path) or os.getcwd()
        os.makedirs(out_dir, exist_ok=True)
        photo_path = os.path.join(out_dir, photo_filename)
        cv2.imwrite(photo_path, photo_region)
        return True, photo_path
    except Exception:
        return False, None


# ---------------- FINAL VERIFICATION ----------------
def verify_pan_card(image_path):
    image = cv2.imread(image_path)
    h, w, _ = image.shape

    ocr = extract_ocr(image)
    # First try label-based extraction; fallback to layout heuristics
    extracted, fonts = label_based_extract(ocr, h)
    if not any(extracted.values()):
        extracted, fonts = layout_and_extract(ocr, h)

    pan_ok = extracted["pan"] is not None
    name_ok = extracted["name"] is not None
    father_ok = extracted["father"] is not None
    dob_ok = extracted["dob"] is not None
    font_ok = font_hierarchy(fonts)
    qr_ok = qr_check(image, extracted["pan"]) if pan_ok else False
    tamper_ok = tampering_check(image)

    score = 0
    score += 30 if pan_ok else 0
    score += 15 if name_ok else 0
    score += 15 if father_ok else 0
    score += 10 if dob_ok else 0
    score += 15 if qr_ok else 0
    score += 15 if font_ok and tamper_ok else 0

    if score >= 80:
        status = "Likely Original"
    elif score >= 50:
        status = "Suspicious"
    else:
        status = "Likely Edited / Fake"

    photo_ok, photo_path = extract_face_photo(image, image_path)

    return {
        "PAN": extracted["pan"],
        "Name": extracted["name"],
        "Father": extracted["father"],
        "DOB": extracted["dob"],
        "Score": score,
        "Status": status,
        "PhotoExtracted": photo_ok,
        "PhotoPath": photo_path
    }

# ---------------- RUN ----------------
if __name__ == "__main__":
    # Input image
    image_file = "pancard.jpeg"

    result = verify_pan_card(image_file)
    print(result)
