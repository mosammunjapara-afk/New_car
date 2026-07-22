"""
debug_skoda_pdf.py — Skoda price PDF + fresh site try
======================================================
Skoda site variant-price nahi deti thi. Try:
  1. Skoda price PDF (findmeacar/findmeasuv-style)
  2. Skoda ki nayi price page / buildyourown API

CHALAO:
    python debug_skoda_pdf.py
Phir skoda_pdf.txt UPLOAD kar do.
"""

import re, urllib.request

out = []
def log(s=""):
    print(s); out.append(str(s))


# 1. PDF try
log("=== PDF try ===")
PDFS = [
    "https://www.findmeacar.in/pricing_pdf/skoda-cars-price-in-india.pdf",
    "https://www.findmeasuv.in/pricing_pdf/skoda-cars-price-in-india.pdf",
    "https://www.findmeacar.in/pricing_pdf/skoda-vehicles-price-in-india.pdf",
]
found = None
for url in PDFS:
    log(f"try: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        if data[:4] == b"%PDF":
            log(f"  MILA! {len(data)} bytes")
            with open("skoda_pricelist.pdf", "wb") as f:
                f.write(data)
            found = data
            break
    except Exception as e:
        log(f"    ({str(e)[:40]})")

if found:
    try:
        import pdfplumber, io
        text = ""
        with pdfplumber.open(io.BytesIO(found)) as pdf:
            for pg in pdf.pages:
                text += (pg.extract_text() or "") + "\n"
        log(f"\ntext: {len(text)} chars")
        for l in text.split("\n"):
            if l.strip():
                log(f"  {l.strip()[:90]}")
    except Exception as e:
        log(f"  parse fail: {e}")

# 2. Skoda site API (playwright)
if not found:
    log("\n=== Skoda site try (buildyourown/price API) ===")
    from playwright.sync_api import sync_playwright
    def rp(b):
        return sorted(set(int(n) for n in re.findall(r'\b(\d{6,8})\b', b) if 500000 <= int(n) <= 9999999))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page.set_default_timeout(35000)
        apis = []
        def on_resp(resp):
            u = resp.url.lower()
            if any(s in u for s in ["google","gtm","facebook","font",".css",".png","analytics"]):
                return
            ct = resp.headers.get("content-type","")
            if "json" in ct:
                try: b = resp.text()
                except: return
                if rp(b) and any(k in b.lower() for k in ["variant","price","model","trim"]):
                    apis.append((resp.url, b))
        page.on("response", on_resp)
        # Skoda price/buildyourown pages
        for url in ["https://www.skoda-auto.co.in/build-your-own",
                    "https://www.skoda-auto.co.in/price-lists",
                    "https://www.skoda-auto.co.in/models/kylaq/price"]:
            apis.clear()
            log(f"\nPAGE: {url}")
            try:
                r = page.goto(url, wait_until="domcontentloaded", timeout=35000)
                log(f"  status: {r.status if r else '?'}")
                page.wait_for_timeout(6000)
                for _ in range(6):
                    page.mouse.wheel(0,1000); page.wait_for_timeout(500)
                if apis:
                    for u,b in apis[:3]:
                        log(f"  API: {u[:90]}")
                        log(f"    prices: {rp(b)[:12]}")
                txt = page.inner_text("body")
                pl = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d{5,}",l)]
                for l in pl[:8]:
                    log(f"  ₹: {l[:50]}")
            except Exception as e:
                log(f"  fail: {str(e)[:40]}")
        browser.close()

with open("skoda_pdf.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\nHO GAYA. skoda_pdf.txt UPLOAD kar do.")