import logic_ocr as logic_ocr
import json

# Test cases with expected values
test_cases = [
    {
        "file": "images/package_amazon.jpeg",
        "name": "package_amazon.jpeg",
        "expected": {
            "tracking": "TBR300059176",
            "carrier": "AMAZON",
            "recipient": "Mayara",
            "sender": "DESCONHECIDO",
            "cep": "68415392" or "58415392"
        }
    },
    {
        "file": "images/adel_perfumes.jpg",
        "name": "adel_perfumes.jpg",
        "expected": {
            "tracking": "UADEL772847983",
            "carrier": "DESCONHECIDO",
            "recipient": "Dacio Bezerra",
            "sender": "Adel perfumes",
            "cep": "58013240"
        }
    },
    {
        "file": "images/centauro.jpg",
        "name": "centauro.jpg",
        "expected": {
            "tracking": "9923401130101" or "99234011301" or "58475000" or "68475000",
            "carrier": "DESCONHECIDO",
            "recipient": "Dacio Bezerra",
            "sender": "SBF COMERCIO DE PRODUTOS ESPORTIVOS LTDA",
            "cep": "58013240"
        }
    },
    {
        "file": "images/dafiti.jpg",
        "name": "dafiti.jpg",
        "expected": {
            "tracking": "NR163351686BR",
            "carrier": "DESCONHECIDO",
            "recipient": "DACIO BEZERRA",
            "sender": "Dafiti CD Extrema" or "GFG COMERCIO DIGITAL LTDA",
            "cep": "58013-240"
        }
    },
    {
        "file": "images/new_shopee2.jpg",
        "name": "new_shopee2.jpg",
        "expected": {
            "tracking": "BR267104392699Y",
            "carrier": "SHOPEE",
            "recipient": "Dacio Silva Bezerra",
            "sender": "Can You Hear?",
            "cep": "58013-240"
        }
    },
    {
        "file": "images/new_shopee3.jpg",
        "name": "new_shopee3.jpg",
        "expected": {
            "tracking": "BR2608036412367",
            "carrier": "SHOPEE",
            "recipient": "Dacio Silva Bezerra",
            "sender": "customst",
            "cep": "58013-240"
        }
    }
]

def check_match(expected, actual, field_name):
    """Check if actual value matches expected value (fuzzy for names)"""
    if expected is None:
        return None  # Don't count this field
    
    if not actual or actual == "DESCONHECIDO":
        return False
    
    # Exact match for tracking codes and carriers
    if field_name in ["tracking", "carrier"]:
        return expected.upper() == actual.upper()
    
    # CEP can have different formats
    if field_name == "cep":
        expected_clean = expected.replace("-", "").replace(" ", "")
        actual_clean = actual.replace("-", "").replace(" ", "")
        return expected_clean in actual_clean or actual_clean in expected_clean
    
    # Fuzzy match for names (partial match OK)
    if field_name in ["recipient", "sender"]:
        return expected.upper() in actual.upper() or actual.upper() in expected.upper()
    
    return False

print("=" * 60)
print("📊 OCR EXTRACTION SUCCESS RATE CALCULATOR")
print("=" * 60)

total_fields = 0
successful_fields = 0
skipped_fields = 0

for test in test_cases:
    print(f"\n📦 {test['name']}")
    print("-" * 60)
    
    # Extract text and parse
    raw_text = logic_ocr.extract_text(test["file"])
    parsed = logic_ocr.parse_fields_strategy_a(raw_text)
    
    fields_to_check = ["tracking", "carrier", "recipient", "sender", "cep"]
    
    for field in fields_to_check:
        expected = test["expected"].get(field)
        actual = parsed.get(field, "")
        
        result = check_match(expected, actual, field)
        
        if result is None:
            icon = "⚪"
            status = "N/A"
            skipped_fields += 1
        elif result:
            icon = "✅"
            status = "CORRECT"
            successful_fields += 1
            total_fields += 1
        else:
            icon = "❌"
            status = "WRONG"
            total_fields += 1
        
        # Format output
        field_display = field.ljust(10)
        expected_display = str(expected)[:20].ljust(20) if expected else "N/A".ljust(20)
        actual_display = str(actual)[:20].ljust(20) if actual else "''".ljust(20)
        
        print(f"{icon} {field_display} | Expected: {expected_display} | Got: {actual_display} | {status}")

print("\n" + "=" * 60)
print("📈 FINAL RESULTS")
print("=" * 60)

if total_fields > 0:
    success_rate = (successful_fields / total_fields) * 100
    print(f"✅ Successful: {successful_fields}/{total_fields} fields")
    print(f"❌ Failed: {total_fields - successful_fields}/{total_fields} fields")
    print(f"⚪ Skipped (N/A): {skipped_fields} fields")
    print(f"\n🎯 SUCCESS RATE: {success_rate:.1f}%")
    
    if success_rate >= 60:
        print("\n🎉 TARGET MET! (≥60%)")
    else:
        print(f"\n⚠️  Below target. Need {60 - success_rate:.1f}% more.")
else:
    print("No fields to evaluate")