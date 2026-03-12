import cv2
import pytesseract
import PIL
import customtkinter
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = str(
    Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
)

print("--- DIAGNOSTIC START (LINUX) ---")
print(f"✅ OpenCV Version: {cv2.__version__}")
print(f"✅ Pillow Version: {PIL.__version__}")
print(f"✅ CustomTkinter Version: {customtkinter.__version__}")

if "tesseract" in pytesseract.pytesseract.tesseract_cmd:
    tesseract_path = pytesseract.pytesseract.tesseract_cmd
    print(f"✅ Tesseract Binary Found at: {tesseract_path}")
    try:
        langs = pytesseract.get_languages(config="")
        print(f"✅ Tesseract Languages: {langs}")
        if "por" in langs:
            print("✅ Portuguese (por) language pack detected!")
            print("🚀 SYSTEM READY FOR TASK 2!")
        else:
            print("⚠️ Tesseract found, but 'por' is missing. Check Step 1.")
    except Exception as e:
        print(f"❌ Tesseract Error: {e}")
else:
    print("❌ Tesseract NOT found in PATH. Did you run sudo apt install...?")

print("--- DIAGNOSTIC END ---")