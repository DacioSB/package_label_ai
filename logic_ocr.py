import cv2
import pytesseract
import re
import os


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return None

    # Moderate upscale
    img = cv2.resize(
        img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return thresh


def extract_text(image_path: str) -> str:
    if not os.path.exists(image_path):
        return ""

    processed = preprocess_image(image_path)
    if processed is None:
        return ""

    try:
        return pytesseract.image_to_string(
            processed,
            lang="eng",
            config="--psm 4"
        ).strip()
    except Exception:
        return ""


# =========================================================
# HELPERS
# =========================================================

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def looks_like_name(text: str) -> bool:
    if not text or len(text) < 3 or len(text) > 40:
        return False

    upper = text.upper()

    blacklist = [
        "AGENCIA", "XPRESS", "SEDEX", "CODIGO", "USO",
        "RUA", "AV", "AVENIDA", "CEP", "CONTRATO",
        "PEDIDO", "AMAZON", "SHOPEE", "BR", "OF"
    ]

    if any(word in upper for word in blacklist):
        return False

    digit_ratio = sum(c.isdigit() for c in text) / len(text)
    if digit_ratio > 0.1:
        return False

    alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / len(text)
    return alpha_ratio > 0.7


# =========================================================
# MAIN PARSER
# =========================================================

def parse_fields_strategy_a(text: str) -> dict:
    data = {
        "tracking": "",
        "cep": "",
        "recipient": "",
        "sender": "",
        "carrier": "DESCONHECIDO"
    }

    clean_text = text.upper()
    lines = [
        normalize(l)
        for l in clean_text.split("\n")
        if len(l.strip()) > 2
    ]

    # =====================================================
    # 1. INITIAL CARRIER DETECTION (TEXTUAL)
    # =====================================================
    if "AMAZ" in clean_text or "VAREJO" in clean_text:
        data["carrier"] = "AMAZON"
    elif "SHOPEE" in clean_text or ("SHOP" in clean_text and "XPRESS" in clean_text):
        data["carrier"] = "SHOPEE"
    elif "MERCADO" in clean_text and "LIVRE" in clean_text:
        data["carrier"] = "MERCADO LIVRE"
    elif "MAGALU" in clean_text or "MAGAZINE" in clean_text:
        data["carrier"] = "MAGALU"
    elif "CORREIOS" in clean_text or "SEDEX" in clean_text:
        data["carrier"] = "CORREIOS"

    # =====================================================
    # 2. TRACKING CODE EXTRACTION
    # =====================================================
    text_nospace = clean_text.replace(" ", "")
    tracking_candidates = []

    for m in re.finditer(r"OF\d{9}[A-Z]{2}", text_nospace):
        tracking_candidates.append(("SHOPEE", m.group(0)))

    for m in re.finditer(r"T[BDR][A-Z0-9]\d{8,12}", text_nospace):
        tracking_candidates.append(("AMAZON", m.group(0)))

    for m in re.finditer(r"[A-Z]{2}\d{9}[A-Z]{2}", text_nospace):
        tracking_candidates.append(("CORREIOS", m.group(0)))

    # Prefer tracking matching detected carrier
    for typ, code in tracking_candidates:
        if typ == data["carrier"]:
            data["tracking"] = code
            break

    if not data["tracking"] and tracking_candidates:
        data["tracking"] = tracking_candidates[0][1]

    # =====================================================
    # 3. FORCE CARRIER BY TRACKING (CRITICAL FIX)
    # =====================================================
    if data["tracking"].startswith("OF"):
        data["carrier"] = "SHOPEE"
    elif data["tracking"].startswith(("TBA", "TBR", "TBM")):
        data["carrier"] = "AMAZON"

    # =====================================================
    # 4. RECIPIENT / SENDER / CEP EXTRACTION
    # =====================================================
    recipient_line = None
    cep_candidates = []

    for i, line in enumerate(lines):

        # ---------- RECIPIENT (DESTINATARIO) ----------
        if "DESTINAT" in line and not data["recipient"]:
            for j in range(1, 5):
                if i + j < len(lines):
                    candidate = lines[i + j]
                    if looks_like_name(candidate):
                        data["recipient"] = candidate
                        recipient_line = i + j
                        break

        # ---------- SENDER (REMETENTE) ----------
        if ("REMET" in line or "SENDER" in line) and not data["sender"]:
            for j in range(1, 5):
                if i + j < len(lines):
                    candidate = lines[i + j]
                    if looks_like_name(candidate):
                        data["sender"] = candidate
                        break

        # ---------- AMAZON SPECIAL: NAME ABOVE ADDRESS ----------
        if data["carrier"] == "AMAZON" and not data["recipient"]:
            if any(x in line for x in ["RUA", "AV", "AVENIDA"]):
                for back in range(1, 4):
                    if i - back >= 0:
                        candidate = lines[i - back]
                        if looks_like_name(candidate):
                            data["recipient"] = candidate
                            recipient_line = i - back
                            break

        # ---------- CEP ----------
        cep_match = re.search(r"\b\d{5}[- ]?\d{3}\b", line)
        if cep_match:
            cep_candidates.append(
                (i, cep_match.group(0).replace("-", "").replace(" ", ""))
            )

    # =====================================================
    # 5. SHOPEE FALLBACK RECIPIENT (NO DESTINATARIO)
    # =====================================================
    if data["carrier"] == "SHOPEE" and not data["recipient"]:
        for i, line in enumerate(lines):
            if looks_like_name(line):
                data["recipient"] = line
                recipient_line = i
                break

    # =====================================================
    # 6. CEP SELECTION (CARRIER-AWARE)
    # =====================================================
    if cep_candidates:
        if data["carrier"] == "AMAZON":
            # Amazon: last CEP is almost always recipient
            data["cep"] = cep_candidates[-1][1]
        elif recipient_line is not None:
            data["cep"] = min(
                cep_candidates,
                key=lambda x: abs(x[0] - recipient_line)
            )[1]
        else:
            data["cep"] = cep_candidates[-1][1]

    return data
