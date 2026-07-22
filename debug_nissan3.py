"""
debug_nissan3.py — Nissan Magnite: element-wise price + configurator API
=========================================================================
Prices page pe trims dikhe (Visia/Acenta/Tekna/Kuro) par ₹ line nahi (JS-render,
ya ₹ alag element me). Ye script:
  1. prices.html pe har ₹-element + parent text (Brezza jaisa)
  2. configurator (magniteconfigurator.nissan.in) ka API bhi capture

CHALAO:
    python debug_nissan3.py
Phir nissan3.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def real_prices(body):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,7})\b', body) if 300000 <= int(n) <= 2000000))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    cfg_apis = []
    def on_response(resp):
        u = resp.url
        low = u.lower()
        if any(s in low for s in ["google","gtm","facebook","demdex","font",".css",".png",".jpg","clarity","adobe"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            if real_prices(b):
                cfg_apis.append((u, b))
    page.on("response", on_response)

    # 1. prices.html element-wise
    url = "https://www.nissan.in/vehicles/new/magnite/prices.html"
    log("=" * 70)
    log(f"PRICES PAGE: {url}")
    log("=" * 70)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=50000)
        page.wait_for_timeout(6000)
        for _ in range(8):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(600)
        page.wait_for_timeout(3000)

        # har element jisme ₹ ya "Rs" + digits
        data = page.evaluate(r"""() => {
            const out = [];
            const all = Array.from(document.querySelectorAll('body *'));
            for (const el of all) {
                const own = Array.from(el.childNodes).filter(n=>n.nodeType===3)
                    .map(n=>n.textContent).join(' ').trim();
                if ((own.includes('₹')||/Rs\.?\s*\d/.test(own)) && /\d{5,}/.test(own)) {
                    let ctx=''; let pp=el.parentElement;
                    if (pp) ctx=(pp.innerText||'').slice(0,100).replace(/\s+/g,' ');
                    out.push({own: own.slice(0,35), ctx});
                }
            }
            return out;
        }""")
        log(f"  ₹-elements: {len(data)}")
        seen=set()
        for d in data[:30]:
            k=d['own']+d['ctx'][:25]
            if k in seen: continue
            seen.add(k)
            log(f"    ₹: {repr(d['own'])}  ctx: {d['ctx'][:60]}")

        # embedded json me price?
        html = page.content()
        prices_in_html = real_prices(html)
        log(f"  HTML me price-range numbers: {prices_in_html[:15]}")
        # variant naam ke saath price (JSON pattern)
        pairs = re.findall(r'"(?:variantName|grade|version|name)"\s*:\s*"([^"]{2,30})"[^}]{0,80}?(\d{6,7})', html)
        if pairs:
            log(f"  variant+price pairs in HTML: {pairs[:15]}")
    except Exception as e:
        log(f"  fail: {str(e)[:50]}")

    # 2. configurator API
    log("\n" + "=" * 70)
    log("CONFIGURATOR: magniteconfigurator.nissan.in")
    log("=" * 70)
    cfg_apis.clear()
    try:
        page.goto("https://magniteconfigurator.nissan.in/#/presentation",
                  wait_until="domcontentloaded", timeout=50000)
        page.wait_for_timeout(8000)
        for _ in range(6):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(600)
        page.wait_for_timeout(4000)
        log(f"  price JSON APIs: {len(cfg_apis)}")
        seen=set()
        for u,b in cfg_apis:
            base=u.split('?')[0]
            if base in seen: continue
            seen.add(base)
            log(f"    {u[:110]}")
            log(f"      prices: {real_prices(b)[:15]}")
            names=re.findall(r'"(?:name|grade|version|variant|title)"\s*:\s*"([^"]{2,35})"',b)
            if names: log(f"      names: {names[:12]}")
            log(f"      sample: {b[:200].replace(chr(10),' ')}")
    except Exception as e:
        log(f"  cfg fail: {str(e)[:50]}")

    browser.close()

with open("nissan3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. nissan3.txt UPLOAD kar do.")
print("=" * 60)