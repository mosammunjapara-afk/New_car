"""
debug_cardekho_html.py — CarDekho ka HTML/embedded-JSON se price
=================================================================
CarDekho ka alag API nahi (0). Data HTML/__NEXT_DATA__ me embedded hai.
Ye script poora HTML + embedded JSON scan karke variant+price dhoondta hai.
CHALAO: python debug_cardekho_html.py -> cardekho_html.txt + cardekho.html UPLOAD
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
    URL="https://www.cardekho.com/mahindra/scorpio-n/price-in-new-delhi"
    log(f"PAGE: {URL}")
    try:
        page.goto(URL,wait_until="domcontentloaded",timeout=35000)
        page.wait_for_timeout(6000)
        for _ in range(12):
            page.mouse.wheel(0,1000); page.wait_for_timeout(400)
        page.wait_for_timeout(3000)
        html=page.content()
        with open("cardekho.html","w",encoding="utf-8") as f:
            f.write(html)
        log(f"  HTML saved: {len(html)} chars")
        # __NEXT_DATA__ ya embedded JSON
        nd=page.evaluate("()=>{const s=document.getElementById('__NEXT_DATA__');return s?s.textContent:'';}")
        if nd:
            log(f"  __NEXT_DATA__: {len(nd)} chars, prices: {rp(nd)[:15]}")
        # variant + price: "variantName":"..." aur pass me price
        # CarDekho pattern: {"variantName":"Z2","price":...} type
        pairs=re.findall(r'"([A-Za-z0-9 .()+-]{2,30})"[^{}]{0,60}?"?(?:price|priceValue|minPrice)"?["\s:]+(\d{6,8})',html)
        if pairs:
            log(f"  variant-price pairs (HTML): {len(pairs)}")
            seen=set()
            for n,pr in pairs[:25]:
                if (n,pr) in seen: continue
                seen.add((n,pr))
                if 500000<=int(pr)<=9999999:
                    log(f"    {n[:26]:26} = {pr}")
        # ₹ table lines
        txt=page.inner_text("body")
        lines=[l.strip() for l in txt.split("\n") if l.strip()]
        pl=[(i,l) for i,l in enumerate(lines) if "₹" in l and re.search(r"\d{5,}",l)]
        log(f"\n  ₹ lines: {len(pl)}")
        for i,l in pl[:15]:
            prev=lines[i-1] if i>0 else ""
            log(f"    [{prev[:20]}] {l[:35]}")
    except Exception as e:
        log(f"  fail: {str(e)[:45]}")
    browser.close()
with open("cardekho_html.txt","w",encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n\nHO GAYA. cardekho_html.txt + cardekho.html UPLOAD kar do.")