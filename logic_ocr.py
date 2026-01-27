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

    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    return thresh

def extract_test(image_path):
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
        text: str = pytesseract.image_to_string(image, lang="por")
        return text.strip()
    except Exception as e:
        print(f"[OCR] Error: {e}")
        return ""