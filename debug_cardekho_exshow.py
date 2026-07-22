"""
debug_cardekho_exshow.py — CarDekho variant-wise EX-SHOWROOM (new car)
======================================================================
Price-page pe on-road tha. Ex-showroom variant-wise CarDekho ke main model
page pe / variants page pe hota hai. Ye script:
  - /mahindra/scorpio-n (main) aur variants list page try karta hai
  - variant naam + ex-showroom price nikaalta hai
CHALAO: python debug_cardekho_exshow.py -> ck_exshow.txt + ck_scorpio2.html UPLOAD
"""
from playwright.sync_api import sync_playwright
import re
out=[]
def log(s=""):
    print(s); out.append(str(s))

URLS=[
    "https://www.cardekho.com/mahindra/scorpio-n",
    "https://www.cardekho.com/mahindra-scorpio-n/variants",
    "https://www.cardekho.com/mahindra/scorpio-n/specifications",
]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
    context=browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="en-IN")
    context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    page=context.new_page()
    page.set_default_timeout(35000)
    for url in URLS:
        log("\n"+"="*60); log(f"PAGE: {url}"); log("="*60)
        try:
            r=page.goto(url,wait_until="domcontentloaded",timeout=35000)
            log(f"  status: {r.status if r else '?'}")
            if not r or r.status!=200: continue
            page.wait_for_timeout(5000)
            for _ in range(10):
                page.mouse.wheel(0,1000); page.wait_for_timeout(400)
            page.wait_for_timeout(2000)
            html=page.content()
            # variant + ex-showroom: CarDekho variant list JSON
            # pattern: variant naam + "Rs X.XX Lakh" (ex-showroom)
            # JSON-LD offers (on-road) chhod ke, 'variantList'/'priceList' dhoondo
            # ₹ Lakh lines with variant
            txt=page.inner_text("body")
            lines=[l.strip() for l in txt.split("\n") if l.strip()]
            # variant naam (Z2/Z4/Z6/Z8...) + agli line me price
            found=[]
            for i,l in enumerate(lines):
                if re.match(r'^Z\d',l) and len(l)<40:
                    # aaspaas price
                    for j in range(i,min(i+3,len(lines))):
                        pm=re.search(r'₹\s*([\d.]+)\s*Lakh',lines[j])
                        if pm:
                            found.append((l,lines[j].strip()))
                            break
            log(f"  variant+price (text): {len(found)}")
            for v,pr in found[:20]:
                log(f"    {v[:28]:28} | {pr[:20]}")
            # embedded exShowroom numbers
            nums=sorted(set(int(n) for n in re.findall(r'\"(?:price|priceValue|exShowroomPrice)\":\s*\"?(\d{6,8})',html) if 1000000<=int(n)<=4000000))
            log(f"  ex-showroom-range nums: {nums[:20]}")
            # save biggest page
            if 'scorpio-n' in url and url.endswith('scorpio-n'):
                with open("ck_scorpio2.html","w",encoding="utf-8") as f: f.write(html)
                log("  saved ck_scorpio2.html")
        except Exception as e:
            log(f"  fail: {str(e)[:45]}")
    browser.close()
with open("ck_exshow.txt","w",encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n\nHO GAYA. ck_exshow.txt + ck_scorpio2.html UPLOAD kar do.")