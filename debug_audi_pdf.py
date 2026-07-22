"""
debug_audi_pdf.py — Audi price-list PDF dhoondo (findmeacar-style)
===================================================================
Audi site 503 (bot-block). Par Land Rover/Jaguar jaisa PDF ho sakta hai jo
third-party host karte hain. Ye script kuch sambhavit PDF URLs try karta hai.

CHALAO:
    python debug_audi_pdf.py
Phir audi_pdf.txt (+ audi_pricelist.pdf agar mile) UPLOAD karo.
"""

import re
import urllib.request

out = []
def log(s=""):
    print(s); out.append(str(s))

# sambhavit PDF URLs (findmeacar/findmeasuv pattern + audi India)
CANDIDATES = [
    "https://www.findmeacar.in/pricing_pdf/audi-cars-price-in-india.pdf",
    "https://www.findmeasuv.in/pricing_pdf/audi-cars-price-in-india.pdf",
    "https://www.findmeacar.in/pricing_pdf/audi-vehicles-price-in-india.pdf",
    "https://www.audi.in/content/dam/nemo/india/price-list.pdf",
]

def try_pdf(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        if data[:4] == b"%PDF":
            return data
    except Exception as e:
        log(f"    ({str(e)[:40]})")
    return None

found = None
for url in CANDIDATES:
    log(f"try: {url}")
    data = try_pdf(url)
    if data:
        log(f"  ✓ MILA! {len(data)} bytes")
        with open("audi_pricelist.pdf", "wb") as f:
            f.write(data)
        found = data
        break

if found:
    try:
        import pdfplumber, io
        text = ""
        with pdfplumber.open(io.BytesIO(found)) as pdf:
            for pg in pdf.pages:
                text += (pg.extract_text() or "") + "\n"
        log(f"\ntext: {len(text)} chars")
        log("=== lines ===")
        for l in text.split("\n"):
            if l.strip():
                log(f"  {l.strip()[:90]}")
    except Exception as e:
        log(f"parse fail: {e}")
else:
    log("\nkoi PDF nahi mila in candidates me.")
    log("Audi ke liye alag source chahiye (ya carwale/cardekho jaisa aggregator).")

with open("audi_pdf.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\nHO GAYA. audi_pdf.txt UPLOAD kar do.")