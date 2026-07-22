"""
debug_aggregator.py — blocked brands ke liye AUTOMATIC aggregator source
=========================================================================
Mahindra-new/Audi/Volvo/Skoda apni site se automatic nahi dete. Ye script
alag aggregators try karta hai (Scorpio N test) — kaunsa clean variant+price
deta hai aur auto-scrape ho sakta hai.
CHALAO: python debug_aggregator.py  -> aggregator.txt UPLOAD
"""
from playwright.sync_api import sync_playwright
import re
out=[]
def log(s=""):
    print(s); out.append(str(s))

TARGETS=[
    ("CarDekho","https://www.cardekho.com/mahindra/scorpio-n/price-in-new-delhi"),
    ("CarWale","https://www.carwale.com/mahindra-cars/scorpio-n/"),
    ("Zigwheels","https://www.zigwheels.com/newcars/mahindra/scorpio-n"),
    ("Spinny","https://www.spinny.com/new-cars/mahindra-scorpio-n/"),
]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
    context=browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="en-IN")
    context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    page=context.new_page()
    page.set_default_timeout(35000)
    for name,url in TARGETS:
        log("\n"+"="*60); log(f"{name}: {url}"); log("="*60)
        try:
            r=page.goto(url,wait_until="domcontentloaded",timeout=35000)
            st=r.status if r else "?"
            log(f"  status: {st}")
            if st!=200: continue
            page.wait_for_timeout(5000)
            for _ in range(8):
                page.mouse.wheel(0,1000); page.wait_for_timeout(500)
            page.wait_for_timeout(2000)
            txt=page.inner_text("body")
            lines=[l.strip() for l in txt.split("\n") if l.strip()]
            plines=[(i,l) for i,l in enumerate(lines) if "₹" in l and re.search(r"\d",l)]
            log(f"  Rs lines: {len(plines)}")
            for i,l in plines[:12]:
                prev=lines[i-1] if i>0 else ""
                log(f"    [{prev[:22]}] {l[:35]}")
            trims=[t for t in ["Z2","Z4","Z6","Z8"] if t in txt]
            if trims: log(f"  Scorpio trims: {trims}")
        except Exception as e:
            log(f"  fail: {str(e)[:45]}")
    browser.close()
with open("aggregator.txt","w",encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n\nHO GAYA. aggregator.txt UPLOAD kar do.")