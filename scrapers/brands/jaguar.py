"""
scrapers/brands/jaguar.py — Jaguar India scraper (official price-list PDF)
==========================================================================

Jaguar India (JLR) apni site pe official price-list PDF deta hai:
  https://www.findmeacar.in/pricing_pdf/jaguar-cars-price-in-india.pdf

Format (Land Rover jaisa):
  "Jaguar F-PACE** (25MY) Price in India"          <- model header
  "2.0 l Petrol R-Dynamic S 72.90"                 <- engine + fuel + variant + price(lakh)

Abhi Jaguar India me sirf F-PACE hai (lineup chhoti). PDF se model+variant+price.
"""

import re
import io
import urllib.request

PDF_URL = "https://www.findmeacar.in/pricing_pdf/jaguar-cars-price-in-india.pdf"

MODELS = ["F-PACE", "F-TYPE", "XF", "XE", "I-PACE", "F PACE", "F TYPE"]

FOOTER_HINTS = ["Visit ", "Prices ", "Ex-Showroom Price", "on-road", "Retailer",
                "Conditions", "TCS", "Locally", "PRICE LIST", "Variant",
                "GST", "Insurance", "findmeacar", "in Lakh"]


def _find_model(line):
    for m in MODELS:
        if m.lower() in line.lower():
            # normalize
            return "F-PACE" if "pace" in m.lower() else m
    return None


def _detect_fuel(line):
    if re.search(r"\bDiesel\b", line, re.I):
        return "Diesel"
    if re.search(r"\bPetrol\b", line, re.I):
        return "Petrol"
    if re.search(r"\bElectric\b", line, re.I) or "i-pace" in line.lower():
        return "Electric"
    if re.search(r"\d\.\dD\b", line):
        return "Diesel"
    return "Petrol"


def _clean_variant(line, model):
    v = line
    if model:
        v = re.sub(re.escape(model), "", v, flags=re.I)
    v = re.sub(r"(?i)jaguar", "", v)
    v = re.sub(r"\*+", "", v)
    v = re.sub(r"\(\d+\.?\d*MY\)", "", v)
    v = re.sub(r"Price in India", "", v, flags=re.I)
    v = re.sub(r"\d+\.\d{2}\s*$", "", v)     # price
    v = re.sub(r"\d\.\d\s*l\b", "", v)       # "2.0 l"
    v = re.sub(r"(Petrol|Diesel|Electric)", "", v, flags=re.I)
    v = re.sub(r"\s+", " ", v).strip()
    return v


def _get_pdf_text():
    req = urllib.request.Request(PDF_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        data = r.read()
    import pdfplumber
    text = ""
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for pg in pdf.pages:
            text += (pg.extract_text() or "") + "\n"
    return text


def scrape_jaguar():
    results = []
    seen = set()
    try:
        text = _get_pdf_text()
    except Exception as e:
        print(f"  [Jaguar] PDF fail: {str(e)[:60]}")
        return results

    current_model = None
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        has_price = re.search(r"(\d+\.\d{2})\s*$", line)
        if any(h in line for h in FOOTER_HINTS) and not has_price:
            # model header bhi footer-word ke saath ho sakta ("Price in India")
            m0 = _find_model(line)
            if m0:
                current_model = m0
            continue
        m = _find_model(line)
        if m:
            current_model = m
        if not has_price:
            continue
        price = int(float(has_price.group(1)) * 100000)
        if not (2000000 < price < 90000000):
            continue
        variant = _clean_variant(line, current_model)
        fuel = _detect_fuel(line)
        if not current_model or not variant:
            continue
        key = (current_model, variant, fuel, price)
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "model": current_model,
            "variant": variant,
            "fuel_type": fuel,
            "ex_showroom_price": price,
        })

    by = {}
    for r in results:
        by.setdefault(r["model"], 0)
        by[r["model"]] += 1
    for mn, c in by.items():
        print(f"  [Jaguar] {mn}: {c} variant(s)")
    if not results:
        print("  [Jaguar] koi variant nahi mila")
    return results


if __name__ == "__main__":
    cars = scrape_jaguar()
    print(f"\nTOTAL: {len(cars)}")
    for c in cars:
        print(c)