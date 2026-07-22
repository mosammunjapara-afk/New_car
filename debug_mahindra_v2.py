"""
debug_mahindra_v2.py — Mahindra naye models (Thar/Scorpio/XUV3XO) dobara
=========================================================================
Pehle SSR platform pe the (0 mila). Ab try:
  1. Mahindra price PDF (findmeacar/findmeasuv-style)
  2. auto.mahindra.com pe API capture (price/variant JSON) with stealth

CHALAO:
    python debug_mahindra_v2.py
Phir mahindra_v2.txt UPLOAD kar do.
"""

import re, urllib.request

out = []
def log(s=""):
    print(s); out.append(str(s))


# 1. PDF try
log("=== Mahindra PDF try ===")
PDFS = [
    "https://www.findmeasuv.in/pricing_pdf/mahindra-vehicles-price-in-india.pdf",
    "https://www.findmeacar.in/pricing_pdf/mahindra-cars-price-in-india.pdf",
    "https://www.findmeasuv.in/pricing_pdf/mahindra-cars-price-in-india.pdf",
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
            with open("mahindra_pricelist.pdf", "wb") as f:
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

# 2. site API capture
if not found:
    log("\n=== auto.mahindra.com API capture ===")
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
            if any(s in u for s in ["google","gtm","facebook","font",".css",".png",".jpg","analytics","clarity"]):
                return
            ct = resp.headers.get("content-type","")
            if "json" in ct:
                try: b = resp.text()
                except: return
                if rp(b) and any(k in b.lower() for k in ["variant","price","model","trim"]):
                    apis.append((resp.url, b))
        page.on("response", on_resp)
        # naye Mahindra model pages
        PAGES = [
            "https://auto.mahindra.com/suv/thar-roxx",
            "https://auto.mahindra.com/suv/scorpio-n",
            "https://auto.mahindra.com/suv/xuv-3xo",
        ]
        for url in PAGES:
            apis.clear()
            log(f"\nPAGE: {url}")
            try:
                r = page.goto(url, wait_until="domcontentloaded", timeout=35000)
                log(f"  status: {r.status if r else '?'}")
                page.wait_for_timeout(6000)
                for _ in range(8):
                    page.mouse.wheel(0,1000); page.wait_for_timeout(500)
                page.wait_for_timeout(2000)
                if apis:
                    for u,b in apis[:3]:
                        log(f"  API: {u[:95]}")
                        log(f"    prices: {rp(b)[:12]}")
                        names = re.findall(r'"(?:name|variant|title|modelName)"\s*:\s*"([^"]{2,35})"', b)
                        if names: log(f"    names: {names[:8]}")
                txt = page.inner_text("body")
                pl = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d{5,}",l)]
                log(f"  ₹ lines: {len(pl)}")
                for l in pl[:8]:
                    log(f"    {l[:50]}")
            except Exception as e:
                log(f"  fail: {str(e)[:40]}")
        browser.close()

with open("mahindra_v2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\nHO GAYA. mahindra_v2.txt UPLOAD kar do.")