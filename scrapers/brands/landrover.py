"""
scrapers/brands/landrover.py — Land Rover India scraper (official price-list PDF)
=================================================================================

Land Rover India apni site pe official price-list PDF deta hai (har model page
pe "price" link):
  https://www.findmeasuv.in/pricing_pdf/land-rover-vehicles-price-in-india.pdf

Ye PDF me saare LR models + variants + ex-showroom prices (Lakh me) hote hain.
Format (har line):
  "Range Rover (26MY) 4.4 l Petrol LWB SV 350.00"   <- model + engine + fuel + variant + price(lakh)
  "3.0 l Petrol LWB Autobiography 265.00"            <- same model ki agli variant
  "3.0D I6 (110) X-Dynamic HSE 135.90"               <- Defender format (D=diesel)

Hum PDF download karke (urllib), pdfplumber se text nikaal ke parse karte hain.
NOTE: PDF download ke liye requests/urllib chahiye; pdfplumber install hona chahiye.
"""

import re
import io
import urllib.request

PDF_URL = "https://www.findmeasuv.in/pricing_pdf/land-rover-vehicles-price-in-india.pdf"

# model headers (lambe naam pehle taaki "Range Rover Sport" pehle match ho "Range Rover" se)
MODELS = [
    "Range Rover Sport", "Range Rover Velar", "Range Rover Evoque",
    "Range Rover", "Defender", "Discovery Sport", "Discovery",
]

FOOTER_HINTS = ["Visit ", "Prices ", "Ex-Showroom Price", "on-road", "Retailer",
                "Conditions", "TCS", "Locally", "VEHICLES", "PRICE LIST",
                "Model Variant", "GST", "Insurance"]


def _find_model(line):
    for m in MODELS:
        if m.lower() in line.lower():
            return m
    return None


def _detect_fuel(line):
    # Defender/engine format: "3.0D I6" = diesel, "5.0 V8"/"2.0 Si4" = petrol
    if re.search(r"\bDiesel\b", line, re.I):
        return "Diesel"
    if re.search(r"\bPetrol\b", line, re.I):
        return "Petrol"
    # engine code: number + D (3.0D) = diesel
    if re.search(r"\d\.\dD\b", line):
        return "Diesel"
    if re.search(r"\bD\d", line):
        return "Diesel"
    # V8 / Si4 / petrol default
    return "Petrol"


def _clean_variant(line, model):
    v = line
    if model:
        v = re.sub(re.escape(model), "", v, flags=re.I)
    v = re.sub(r"\*+", "", v)
    v = re.sub(r"\(\d+\.?\d*MY\)", "", v)          # (26MY)
    v = re.sub(r"\d+\.\d{2}\s*$", "", v)           # price at end
    # engine (2.0 l / 3.0 l) ko chhota-form me rakho (2.0/3.0) taaki variant unique rahe
    v = re.sub(r"(\d\.\d)\s*l\b", r"\1", v)        # "2.0 l" -> "2.0"
    # fuel bhi variant me rakhna hai (Petrol/Diesel same-naam variants alag karta)
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


def scrape_landrover():
    results = []
    best = {}
    try:
        text = _get_pdf_text()
    except Exception as e:
        print(f"  [Land Rover] PDF fail: {str(e)[:60]}")
        return results

    current_model = None
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        has_price = re.search(r"(\d+\.\d{2})\s*$", line)
        # footer skip (par price-line ho to rakho)
        if any(h in line for h in FOOTER_HINTS) and not has_price:
            continue
        # model header update
        m = _find_model(line)
        if m:
            current_model = m
        if not has_price:
            continue
        price = int(float(has_price.group(1)) * 100000)
        if not (2000000 < price < 90000000):
            continue
        variant = _clean_variant(line, m)
        fuel = _detect_fuel(line)
        if not current_model or not variant:
            continue
        if len(variant) > 45:
            variant = variant[:45].strip()
        key = (current_model, variant, fuel)
        # same naam ke multiple MY/price — sabse kam (base) rakho, flip-flop khatam
        if key not in best or price < best[key]["ex_showroom_price"]:
            best[key] = {
                "model": current_model,
                "variant": variant,
                "fuel_type": fuel,
                "ex_showroom_price": price,
            }

    results = list(best.values())

    # summary
    by = {}
    for r in results:
        by.setdefault(r["model"], 0)
        by[r["model"]] += 1
    for mn, c in by.items():
        print(f"  [Land Rover] {mn}: {c} variant(s)")
    if not results:
        print("  [Land Rover] koi variant nahi mila")
    return results


if __name__ == "__main__":
    cars = scrape_landrover()
    print(f"\nTOTAL: {len(cars)}")
    for c in cars:
        print(c)