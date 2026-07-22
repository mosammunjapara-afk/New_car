"""
debug_cardekho_api.py — CarDekho ka variant-price JSON API capture
===================================================================
CarDekho khulta hai + trims dikhte hain, par prices JS me. Ye script CarDekho
ke Scorpio N page pe SAARI JSON API capture karta hai (variant+price wali).
CHALAO: python debug_cardekho_api.py -> cardekho_api.txt UPLOAD
"""
from playwright.sync_api import sync_playwright
import re, json
out=[]
def log(s=""):
    print(s); out.append(str(s))
def rp(b):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,8})\b',b) if 500000<=int(n)<=9999999))

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled"])
    context=browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="en-IN")
    context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    page=context.new_page()
    page.set_default_timeout(35000)
    hits=[]
    def on_resp(resp):
        u=resp.url.lower()
        if any(s in u for s in ["google","gtm","facebook",".css",".png",".jpg","font","analytics","doubleclick","adservice"]): return
        ct=resp.headers.get("content-type","")
        if "json" in ct:
            try: b=resp.text()
            except: return
            if rp(b) and any(k in b.lower() for k in ["variant","price","exshowroom","model"]):
                hits.append((resp.url,b))
    page.on("response",on_resp)
    URL="https://www.cardekho.com/mahindra/scorpio-n/price-in-new-delhi"
    log(f"PAGE: {URL}")
    try:
        page.goto(URL,wait_until="domcontentloaded",timeout=35000)
        page.wait_for_timeout(6000)
        for _ in range(12):
            page.mouse.wheel(0,1000); page.wait_for_timeout(500)
        page.wait_for_timeout(3000)
    except Exception as e:
        log(f"  fail: {str(e)[:40]}")
    log(f"\nprice-JSON APIs: {len(hits)}")
    seen=set()
    for u,b in hits[:8]:
        base=u.split('?')[0]
        if base in seen: continue
        seen.add(base)
        log(f"\n  {u[:110]}")
        log(f"    prices: {rp(b)[:15]}")
        names=re.findall(r'"(?:variantName|name|title|vname)"\s*:\s*"([^"]{2,35})"',b)
        if names: log(f"    names: {names[:12]}")
    # ek sabse achhi response save
    if hits:
        best=max(hits,key=lambda x:len(rp(x[1])))
        with open("cardekho_scorpion.json","w",encoding="utf-8") as f:
            f.write(best[1])
        log(f"\n  saved biggest -> cardekho_scorpion.json")
    browser.close()
with open("cardekho_api.txt","w",encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n\nHO GAYA. cardekho_api.txt (+cardekho_scorpion.json) UPLOAD kar do.")