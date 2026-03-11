import cv2
import pytesseract
import re
import os
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = str(
    Path("C:/Users/dacio.bezerra/AppData/Local/Programs/Tesseract-OCR/tesseract.exe")
)

# =========================================================
# IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return None

    # Upscale for better text resolution
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # Adaptive thresholding to handle uneven lighting on crumpled packages
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
    )

    return thresh

def extract_text(image_path: str) -> str:
    if not os.path.exists(image_path):
        return ""

    processed = preprocess_image(image_path)
    if processed is None:
        return ""

    try:
        # psm 4 assumes a single column of text of variable sizes (good for labels)
        text = pytesseract.image_to_string(processed, lang="eng", config="--psm 6")
        return text.strip()
    except Exception:
        return ""

# =========================================================
# HELPERS
# =========================================================

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def looks_like_name(text: str) -> bool:
    if not text or len(text) < 3 or len(text) > 60:
        return False

    upper = text.upper()
    
    # Avoid picking up generic label terms as names
    blacklist = {
        "AGENCIA", "XPRESS", "SEDEX", "CODIGO", "USO",
        "RUA", "AVENIDA", "CEP", "CONTRATO", "DADOS",
        "PEDIDO", "CNPJ", "CPF", "BAIRRO", "CIDADE",
        "ESTADO", "NUMERO", "COMPLEMENTO", "ANDAR",
        "BLOCO", "APTO", "GALPAO", "TELEFONE", "CELULAR",
        "EMAIL", "WWW", "HTTP", "HTTPS", "SAC", "LOG",
        "PESO", "KILOS", "DECLARACAO", "CONTEUDO",
        "ASSINATURA", "DOCUMENTO", "DATA", "HORA", "TERMO",
        "VALOR", "FRETE", "GRATIS", "TOTAL", "CENTRO"
    }
    
    words = set(re.findall(r'[A-Z]+', upper))
    if words.intersection(blacklist):
        return False

    # Must contain letters
    if not any(c.isalpha() for c in text):
        return False

    digit_ratio = sum(c.isdigit() for c in text) / len(text)
    if digit_ratio > 0.2:
        return False

    return True

# =========================================================
# MAIN PARSER
# =========================================================

def parse_fields_strategy_a(text: str) -> dict:
    data = {
        "tracking": "DESCONHECIDO",
        "cep": "DESCONHECIDO",
        "recipient": "DESCONHECIDO",
        "sender": "DESCONHECIDO",
        "carrier": "DESCONHECIDO"
    }

    if not text:
        return data

    clean_text = text.upper()
    lines = [normalize(l) for l in clean_text.split("\n") if len(l.strip()) > 2]

    # =====================================================
    # 1. INITIAL CARRIER DETECTION (TEXTUAL)
    # =====================================================
    if any(x in clean_text for x in ["SHOPEE", "SHPS", "SHQP", "SPX"]):
        data["carrier"] = "SHOPEE"
    elif any(x in clean_text for x in ["AMAZON", "VAREJO"]):
        data["carrier"] = "AMAZON"
    elif any(x in clean_text for x in ["MERCADO LIVRE", "MERCADOLIVRE"]):
        data["carrier"] = "MERCADO LIVRE"
    elif any(x in clean_text for x in ["MAGALU", "MAGAZINE"]):
        data["carrier"] = "MAGALU"
    elif any(x in clean_text for x in ["CORREIOS", "SEDEX", "PAC "]):
        data["carrier"] = "CORREIOS"

    # =====================================================
    # 2. TRACKING CODE EXTRACTION
    # =====================================================
    tracking_candidates = []
    
    # Tokenize aggressively to find tracking codes, ignoring punctuation except what's needed
    tokens = re.split(r'[\s\n:,]+', clean_text)
    
    for token in tokens:
        # Strip generic non-alphanumeric around the token
        t_clean = re.sub(r'^[^A-Z0-9]+|[^A-Z0-9]+$', '', token)
        if len(t_clean) < 8:
            continue
            
        # SHOPEE (BR followed by 12-15 digits and optional letter)
        # OCR might read BR as 8R, O as 0, etc.
        if re.match(r'^[B8]R[O0-9]{11,15}[A-Z]?$', t_clean):
            fixed = "BR" + t_clean[2:].replace('O', '0').replace('S', '5').replace('I', '1')
            tracking_candidates.append(("SHOPEE", fixed))
            
        # SHOPEE (OF followed by 9 digits and 2 letters)
        elif re.match(r'^OF[O0-9]{9}[A-Z]{2}$', t_clean):
            fixed = "OF" + t_clean[2:11].replace('O', '0') + t_clean[11:]
            tracking_candidates.append(("SHOPEE", fixed))

        # AMAZON (TBA, TBR, TBM followed by digits)
        elif re.match(r'^T[BDR8][A-Z0-9][O0-9]{8,15}$', t_clean):
            fixed = t_clean.replace('O', '0')
            tracking_candidates.append(("AMAZON", fixed))
            
        # CORREIOS (2 Letters + 9 Digits + 2 Letters)
        elif re.match(r'^[A-Z]{2}[O0-9]{9}[A-Z]{2}$', t_clean):
            fixed = t_clean[:2] + t_clean[2:11].replace('O', '0') + t_clean[11:]
            tracking_candidates.append(("CORREIOS", fixed))
            
        # OTHER ALPHANUMERIC (General fallback)
        elif re.match(r'^[A-Z]{2,5}\d{8,14}[A-Z]*$', t_clean):
            tracking_candidates.append(("OTHER", t_clean))
            
        # NUMERIC ONLY (Like Centauro: 9923401130101)
        elif re.match(r'^\d{11,15}$', t_clean):
            tracking_candidates.append(("OTHER", t_clean))

    # Fallback to search inside lines if tokenization split them weirdly
    text_nospace = clean_text.replace(" ", "")
    if not tracking_candidates:
        for m in re.finditer(r"BR\d{11,15}[A-Z]?", text_nospace):
            tracking_candidates.append(("SHOPEE", m.group(0)))
        for m in re.finditer(r"T[BDR][A-Z0-9]\d{8,15}", text_nospace):
            tracking_candidates.append(("AMAZON", m.group(0)))
        for m in re.finditer(r"[A-Z]{2}\d{9}[A-Z]{2}", text_nospace):
            tracking_candidates.append(("CORREIOS", m.group(0)))

    if tracking_candidates:
        # Pick the one that matches our detected carrier first
        matched = False
        for typ, code in tracking_candidates:
            if typ == data["carrier"]:
                data["tracking"] = code
                matched = True
                break
        
        # Next, pick the first standard recognized format
        if not matched:
            for typ, code in tracking_candidates:
                if typ in ["SHOPEE", "AMAZON", "CORREIOS"]:
                    data["tracking"] = code
                    data["carrier"] = typ
                    matched = True
                    break
                    
        # Otherwise, just pick the first candidate
        if not matched:
            data["tracking"] = tracking_candidates[0][1]

    # Force Carrier update based on tracking if it was DESCONHECIDO
    if data["tracking"] != "DESCONHECIDO":
        if data["tracking"].startswith(("BR", "OF")) and len(data["tracking"]) >= 13 and not data["tracking"].endswith("BR"):
            data["carrier"] = "SHOPEE"
        elif data["tracking"].startswith(("TBA", "TBR", "TBM")):
            data["carrier"] = "AMAZON"

    # =====================================================
    # 3. RECIPIENT / SENDER / CEP EXTRACTION
    # =====================================================
    recipient_line = None
    cep_candidates = []

    for i, line in enumerate(lines):
        # ---------- RECIPIENT ----------
        if any(kw in line for kw in ["DESTINAT", "ENTREGA PARA", "RECEBEDOR", "DEST.", "CLIENTE"]) and data["recipient"] == "DESCONHECIDO":
            # Check same line
            match = re.search(r"(?:DESTINAT[A-Z]*|ENTREGA PARA|RECEBEDOR|DEST\.|CLIENTE)\s*[:\-]?\s*(.*)", line)
            if match and len(match.group(1).strip()) > 2:
                candidate = match.group(1).strip()
                # Exclude strings that are just "DADOS DO DESTINATARIO"
                if not candidate.startswith("DADOS DO") and looks_like_name(candidate):
                    data["recipient"] = candidate
                    recipient_line = i
                    continue
            
            # Check next lines
            if data["recipient"] == "DESCONHECIDO":
                for j in range(1, 4):
                    if i + j < len(lines):
                        candidate = lines[i + j]
                        if looks_like_name(candidate):
                            data["recipient"] = candidate
                            recipient_line = i + j
                            break

        # ---------- SENDER ----------
        if any(kw in line for kw in ["REMET", "SENDER", "EMITENT", "FROM"]) and data["sender"] == "DESCONHECIDO":
            # Check same line
            match = re.search(r"(?:REMET[A-Z]*|SENDER|EMITENT[A-Z]*|FROM)\s*[:\-]?\s*(.*)", line)
            if match and len(match.group(1).strip()) > 2:
                candidate = match.group(1).strip()
                if not candidate.startswith("DADOS DO"):
                    data["sender"] = candidate
                    continue
            
            # Check next lines
            if data["sender"] == "DESCONHECIDO":
                for j in range(1, 4):
                    if i + j < len(lines):
                        candidate = lines[i + j]
                        # For sender, companies often have "COMERCIO", "LTDA", etc., so we bypass looks_like_name for immediate next line
                        if len(candidate) > 2 and not any(kw in candidate for kw in ["CPF", "CNPJ", "ENDERE", "RUA", "AV ", "CEP"]):
                            data["sender"] = candidate
                            break

        # ---------- CEP ----------
        # Replace O with 0 for CEP regex
        line_fixed = line.replace('O', '0')
        for m in re.finditer(r"\b\d{5}[-\s]?\d{3}\b", line_fixed):
            cep_str = m.group(0).replace("-", "").replace(" ", "")
            # Boost priority if "ENTREGA" or "DESTINAT" is in the same line
            priority = 1 if any(kw in line for kw in ["ENTREGA", "DESTINAT"]) else 0
            cep_candidates.append((i, cep_str, priority))

    # =====================================================
    # 4. AMAZON SPECIAL FALLBACK
    # =====================================================
    if data["carrier"] == "AMAZON" and data["recipient"] == "DESCONHECIDO":
        for i, line in enumerate(lines):
            if any(x in line for x in ["RUA ", "AV ", "AVENIDA ", "ROD ", "RODOVIA ", "TRAVESSA "]):
                for back in range(1, 4):
                    if i - back >= 0:
                        candidate = lines[i - back]
                        if looks_like_name(candidate):
                            data["recipient"] = candidate
                            recipient_line = i - back
                            break
                if data["recipient"] != "DESCONHECIDO":
                    break

    # =====================================================
    # 5. SHOPEE FALLBACK RECIPIENT
    # =====================================================
    if data["carrier"] == "SHOPEE" and data["recipient"] == "DESCONHECIDO":
        for i, line in enumerate(lines):
            if looks_like_name(line):
                data["recipient"] = line
                recipient_line = i
                break

    # =====================================================
    # 6. CEP SELECTION
    # =====================================================
    if cep_candidates:
        if recipient_line is not None:
            # Sort by highest priority first, then closest distance to recipient line
            best_cep = min(cep_candidates, key=lambda x: (-x[2], abs(x[0] - recipient_line)))
            data["cep"] = best_cep[1]
        else:
            # Sort by highest priority, then last appeared
            best_cep = max(cep_candidates, key=lambda x: (x[2], x[0]))
            data["cep"] = best_cep[1]

    # Clean up outputs slightly to make test comparisons cleaner
    if data["recipient"] != "DESCONHECIDO":
        data["recipient"] = re.sub(r'[^A-Z0-9\s]', '', data["recipient"]).strip()
    if data["sender"] != "DESCONHECIDO":
        data["sender"] = re.sub(r'[^A-Z0-9\s]', '', data["sender"]).strip()

    return data