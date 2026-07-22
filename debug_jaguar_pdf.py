"""
debug_jaguar_pdf.py — Jaguar official price-list PDF parse
===========================================================
Jaguar bhi Land Rover jaisa PDF deta hai:
  https://www.findmeacar.in/pricing_pdf/jaguar-cars-price-in-india.pdf

Ye script PDF download karke text nikaalta hai (model + variant + price).

CHALAO:
    python debug_jaguar_pdf.py
Phir jaguar_pdf.txt + jaguar_pricelist.pdf UPLOAD kar do.
"""

import re
import urllib.request

out = []
def log(s=""):
    print(s); out.append(str(s))

PDF_URL = "https://www.findmeacar.in/pricing_pdf/jaguar-cars-price-in-india.pdf"

log("PDF download...")
try:
    req = urllib.request.Request(PDF_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        data = r.read()
    with open("jaguar_pricelist.pdf", "wb") as f:
        f.write(data)
    log(f"  downloaded: {len(data)} bytes")
except Exception as e:
    log(f"  fail: {e}")
    data = None

if data:
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open("jaguar_pricelist.pdf") as pdf:
            for pg in pdf.pages:
                text += (pg.extract_text() or "") + "\n"
        log(f"  text: {len(text)} chars")
    except Exception as e:
        log(f"  parse fail: {str(e)[:50]}")
    if text:
        log("\n=== PDF lines (raw) ===")
        for line in text.split("\n"):
            if line.strip():
                log(f"  {line.strip()[:95]}")

with open("jaguar_pdf.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\nHO GAYA. jaguar_pdf.txt UPLOAD kar do.")