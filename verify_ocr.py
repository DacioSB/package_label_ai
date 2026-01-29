import logic_ocr
import json
import os
import cv2

test_images = [
    "images/package.png",
    "images/package2.png",
    "images/real_shopee.png"
]

print("========================================")
print("🔎 OCR LOGIC VERIFICATION TOOL")
print("========================================")

for image_path in test_images:
    print(f"\nProcessing: {image_path}...")
    if not os.path.exists(image_path):
        print(f"❌ Error: File {image_path} not found.")
        continue

    # 1. Run Extraction
    raw_text = logic_ocr.extract_text(image_path)
    # 2. Run Parsing
    parsed_data = logic_ocr.parse_fields_strategy_a(raw_text)
    # 3. Print Results
    print("-" * 40)
    print("📄 RAW TEXT (First 300 chars):")
    print(f"{raw_text[:300]}...") # Truncate to keep console clean
    print("-" * 40)
    print("🧠 PARSED DATA:")
    print(json.dumps(parsed_data, indent=4, ensure_ascii=False))

    # 4. Specific Checks for the REAL Shopee Label
    if "package2" in image_path:
        print("-" * 40)
        print("🎯 SPECIFIC VALIDATION (Real Label):")
        
        # Check Tracking (Should be OF666611769BR, NOT the bottom BR...DU code)
        if parsed_data["tracking"] == "OF666611769BR":
            print("✅ Tracking: CORRECT (OF666611769BR)")
        else:
            print(f"❌ Tracking: FAIL (Got '{parsed_data['tracking']}')")
            
        # Check Recipient (Should be Yara)
        if "Yara" in parsed_data["recipient"]:
            print("✅ Recipient: CORRECT (Found 'Yara')")
        else:
            print(f"❌ Recipient: FAIL (Got '{parsed_data['recipient']}')")

        # Check Sender (Should be Leoshop)
        if "Leoshop" in parsed_data["sender"]:
            print("✅ Sender: CORRECT (Found 'Leoshop')")
        else:
            print(f"❌ Sender: FAIL (Got '{parsed_data['sender']}')")
            
    print("========================================")