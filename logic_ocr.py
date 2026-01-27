import re
import cv2
import pytesseract
import os

# NOTE: On Linux, we don't usually need to set tesseract_cmd if it's installed via apt.
# On Windows (later), we will uncomment this:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    """
    Loads an image, converts to grayscale, and applies thresholding
    to make text stand out against the background.
    """

    img = cv2.imread(image_path)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)

    return thresh

def extract_text(image_path: str):
    """
    Orchestrates the OCR process.
    Returns the raw string text found in the image.
    """

    if not os.path.exists(image_path):
        print(f"[OCR] Error: File {image_path} not found.")
        return ""

    image = preprocess_image(image_path)
    if image is None:
        print("[OCR] Error: Could not load image.")
        return ""
    
    try:
        text: str = pytesseract.image_to_string(image, lang="por", config="--psm 6")
        return text.strip()
    except Exception as e:
        print(f"[OCR] Error: {e}")
        return ""
    
def parse_fields_strategy_a(text: str):
    data = {
        "tracking": "",
        "cep": "",
        "recipient": "",
        "sender": "",
        "carrier": "DESCONHECIDO"
    }
    clean_text = text.upper()
    lines = clean_text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]
    
    # --- 1. CARRIER ---
    if "SHOPEE" in clean_text: data["carrier"] = "SHOPEE"
    elif "MERCADO" in clean_text: data["carrier"] = "MERCADO LIVRE"
    elif "AMAZON" in clean_text: data["carrier"] = "AMAZON"
    elif "MAGALU" in clean_text: data["carrier"] = "MAGALU"
    elif "CORREIOS" in clean_text or "SEDEX" in clean_text: data["carrier"] = "CORREIOS"

    correios_pattern = r'\b[A-Z]{2}\d{9}[A-Z]{2}\b'
    tracking_matches = re.findall(correios_pattern, clean_text)

    if tracking_matches:
        data["tracking"] = tracking_matches[0]
    else:
        long_match = re.search(r'\bBR\d{12,}[A-Z]{2}\b', clean_text)
        if long_match:
            data["tracking"] = long_match.group(0)
    
    for i, line in enumerate(lines):
        if "DESTINAT" in line:
            clean_line = re.sub(r'DESTINAT[AÁ]RIO[:\.]?', '', line).strip()
            if len(clean_line) > 3:
                data["recipient"] = clean_line
            elif i + 1 < len(lines):
                potential_name = lines[i + 1]
                if "RUA" not in potential_name and "CEP" not in potential_name:
                    data["recipient"] = potential_name
        
        if "REMETENTE" in line:
            clean_line = re.sub(r'REMETENTE[:\.]?', '', line).strip()
            if len(clean_line) > 3:
                data["sender"] = clean_line
            elif i + 1 < len(lines):
                data["sender"] = lines[i + 1]

        if "CEP" in line:
            cep_match = re.search(r'\d{5}-\d{3}', line)
            if cep_match:
                data["cep"] = cep_match.group(0)

    return data