"""
debug_ck_urls.py — 0-waale models ke sahi CarDekho URL dhoondo
===============================================================
Kuch models 0 aaye (galat slug). Ye script har model ke liye 2-3 URL-variations
try karta hai aur dekhta hai kaunsa 200 + variants deta hai.
CHALAO: python debug_ck_urls.py -> ck_urls.txt UPLOAD
"""
from playwright.sync_api import sync_playwright
import re
out=[]
def log(s=""):
    print(s); out.append(str(s))

# (brand, model, [url candidates])
TESTS=[
    ("Audi","e-tron GT",["https://www.cardekho.com/audi/e-tron-gt","https://www.cardekho.com/audi/rs-e-tron-gt","https://www.cardekho.com/audi/e-tron"]),
    ("Volvo","XC40",["https://www.cardekho.com/volvo/xc40","https://www.cardekho.com/volvo/xc40-recharge","https://www.cardekho.com/volvo/ex40"]),
    ("Volvo","S90",["https://www.cardekho.com/volvo/s90","https://www.cardekho.com/volvo-cars/s90"]),
    ("Volvo","XC90",["https://www.cardekho.com/volvo/xc90"]),
    ("Mahindra","Thar",["https://www.cardekho.com/mahindra/thar"]),
    ("Mahindra","Thar Roxx",["https://www.cardekho.com/mahindra/thar-roxx","https://www.cardekho.com/mahindra/thar-5-door"]),
    ("Mahindra","XUV 3XO",["https://www.cardekho.com/mahindra/xuv-3xo","https://www.cardekho.com/mahindra/xuv3xo"]),
    ("Mahindra","Bolero",["https://www.cardekho.com/mahindra/bolero","https://www.cardekho.com/mahindra/bolero-neo"]),
    ("Mahindra","Scorpio Classic",["https://www.cardekho.com/mahindra/scorpio-classic","https://www.cardekho.com/mahindra/scorpio"]),
]
def rp(b):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,8})\b',b) if 500000<=int(n)<=9999999))
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
    context=browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",locale="en-IN")
    context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    page=context.new_page(); page.set_default_timeout(25000)
    for brand,model,urls in TESTS:
        log(f"\n{brand} {model}:")
        for url in urls:
            try:
                r=page.goto(url,wait_until="domcontentloaded",timeout=25000)
                st=r.status if r else "?"
                if st==200:
                    page.wait_for_timeout(3000)
                    html=page.content()
                    # variant count (Product name+price blocks)
                    blocks=re.findall(r'"name":"('+re.escape(brand)+r'[^"]*)".*?"price":"(\d{6,8})"',html)
                    log(f"  [200] {url}  -> {len(blocks)} variants")
                else:
                    log(f"  [{st}] {url}")
            except Exception as e:
                log(f"  [err] {url} ({str(e)[:25]})")
    browser.close()
with open("ck_urls.txt","w",encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n\nHO GAYA. ck_urls.txt UPLOAD kar do.")