"""
debug_landrover_pdf.py — Land Rover official price-list PDF parse
=================================================================
LR India apni site pe official price-list PDF deta hai:
  https://www.findmeasuv.in/pricing_pdf/land-rover-vehicles-price-in-india.pdf

Isme saare LR models + variants + prices hote hain. Ye script PDF download
karke text nikaalta hai (model + variant + ₹ price).

CHALAO:
    python debug_landrover_pdf.py

Agar pdfplumber nahi hai: pip install pdfplumber
Phir landrover_pdf.txt UPLOAD kar dena.
"""

import re
import urllib.request

out = []
def log(s=""):
    print(s)
    out.append(str(s))

PDF_URL = "https://www.findmeasuv.in/pricing_pdf/land-rover-vehicles-price-in-india.pdf"

# 1. download
log("PDF download kar rahe hain...")
try:
    req = urllib.request.Request(PDF_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
    with open("lr_pricelist.pdf", "wb") as f:
        f.write(data)
    log(f"  downloaded: {len(data)} bytes")
except Exception as e:
    log(f"  download fail: {e}")
    data = None

# 2. parse text
if data:
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open("lr_pricelist.pdf") as pdf:
            for pg in pdf.pages:
                t = pg.extract_text() or ""
                text += t + "\n"
        log(f"  pdfplumber: {len(text)} chars")
    except ImportError:
        log("  pdfplumber nahi hai — pip install pdfplumber karke dobara chalao")
        try:
            from pypdf import PdfReader
            reader = PdfReader("lr_pricelist.pdf")
            for pg in reader.pages:
                text += (pg.extract_text() or "") + "\n"
            log(f"  pypdf: {len(text)} chars")
        except Exception:
            pass
    except Exception as e:
        log(f"  parse fail: {str(e)[:50]}")

    if text:
        log("\n=== PDF TEXT (price-jaisi lines) ===")
        for line in text.split("\n"):
            # line jisme model/variant naam + price
            if re.search(r"[\d,]{7,}", line) or re.search(r"(Range Rover|Defender|Discovery|Velar|Evoque)", line, re.I):
                log(f"  {line.strip()[:90]}")

with open("landrover_pdf.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. landrover_pdf.txt UPLOAD kar do (aur lr_pricelist.pdf bhi agar ho).")
print("=" * 60)