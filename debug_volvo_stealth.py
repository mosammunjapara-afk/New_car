"""
debug_volvo_stealth.py — Volvo stealth + PDF try (403 bypass)
==============================================================
Volvo 403 tha. Ye script:
  1. stealth mode se volvocars.com/in try
  2. Volvo ka price PDF (findmeacar/findmeasuv-style) try

CHALAO:
    python debug_volvo_stealth.py
Phir volvo_stealth.txt UPLOAD kar do.
"""

from playwright.sync_api import sync_playwright
import re, urllib.request

out = []
def log(s=""):
    print(s); out.append(str(s))


def real_prices(body):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{7,8})\b', body) if 3000000 <= int(n) <= 90000000))


# 1. PDF try pehle (site se independent)
log("=== PDF try ===")
PDF_CANDIDATES = [
    "https://www.findmeacar.in/pricing_pdf/volvo-cars-price-in-india.pdf",
    "https://www.findmeasuv.in/pricing_pdf/volvo-cars-price-in-india.pdf",
    "https://www.findmeasuv.in/pricing_pdf/volvo-vehicles-price-in-india.pdf",
]
pdf_found = None
for url in PDF_CANDIDATES:
    log(f"try: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        if data[:4] == b"%PDF":
            log(f"  ✓ MILA! {len(data)} bytes")
            with open("volvo_pricelist.pdf", "wb") as f:
                f.write(data)
            pdf_found = data
            break
    except Exception as e:
        log(f"    ({str(e)[:40]})")

if pdf_found:
    try:
        import pdfplumber, io
        text = ""
        with pdfplumber.open(io.BytesIO(pdf_found)) as pdf:
            for pg in pdf.pages:
                text += (pg.extract_text() or "") + "\n"
        log(f"\nPDF text: {len(text)} chars")
        for l in text.split("\n"):
            if l.strip():
                log(f"  {l.strip()[:90]}")
    except Exception as e:
        log(f"  parse fail: {e}")

# 2. stealth site try
if not pdf_found:
    log("\n=== stealth site try ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-IN", timezone_id="Asia/Kolkata",
            viewport={"width": 1366, "height": 768},
            extra_http_headers={"Accept-Language": "en-IN,en;q=0.9"},
        )
        context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        page = context.new_page()
        page.set_default_timeout(35000)
        try:
            resp = page.goto("https://www.volvocars.com/in/cars/", wait_until="domcontentloaded", timeout=35000)
            st = resp.status if resp else "?"
            log(f"  [{st}] volvocars.com/in/cars/")
            if st == 200:
                page.wait_for_timeout(5000)
                for _ in range(6):
                    page.mouse.wheel(0,1000); page.wait_for_timeout(500)
                txt = page.inner_text("body")
                plines = [l.strip() for l in txt.split("\n") if ("₹" in l or "INR" in l) and re.search(r"\d{5,}",l)]
                log(f"  ₹ lines: {len(plines)}")
                for l in plines[:12]:
                    log(f"    {l[:50]}")
                hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
                ml = sorted(set(h for h in hrefs if any(m in h.lower() for m in ["xc40","xc60","xc90","ex40","ex90","c40"])))
                log(f"  model links: {ml[:10]}")
        except Exception as e:
            log(f"  fail: {str(e)[:45]}")
        browser.close()

with open("volvo_stealth.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\nHO GAYA. volvo_stealth.txt UPLOAD kar do.")