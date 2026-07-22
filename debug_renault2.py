"""
debug_renault2.py — Renault variant-wise prices (price.html + rplug API)
=========================================================================
Renault API: /agg/v1/vn/slice120?uri=...rplug.renault.com/product/...
(starting price). Variant-wise prices -price.html page pe hain.

Ye script har model ke -price.html page pe jaake variant + price capture karta
hai (rplug API + page ₹ prices dono).

CHALAO:
    python debug_renault2.py
Phir renault2.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

MODELS = {
    "Kwid": "https://www.renault.co.in/cars/renault-kwid/kwid-price.html",
    "Kiger": "https://www.renault.co.in/cars/renault-kiger/kiger-price.html",
    "Triber": "https://www.renault.co.in/cars/renault-triber/triber-price.html",
}

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def real_prices(body):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,7})\b', body) if 300000 <= int(n) <= 3000000))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    apis = []
    def on_response(resp):
        u = resp.url
        if "rplug" in u or "slice" in u or ("renault" in u and "agg" in u):
            try:
                b = resp.text()
            except Exception:
                b = ""
            if real_prices(b):
                apis.append((u, b))
    page.on("response", on_response)

    for model, url in MODELS.items():
        apis.clear()
        log("\n" + "=" * 70)
        log(f"MODEL: {model}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=50000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(7000)
            for _ in range(8):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(600)
            page.wait_for_timeout(3000)

            # rplug API
            log(f"  rplug/agg API calls: {len(apis)}")
            seen = set()
            for u, b in apis:
                base = u.split("?")[0]
                if base in seen: continue
                seen.add(base)
                log(f"    {u[:120]}")
                log(f"      prices: {real_prices(b)[:15]}")
                # variant naam
                names = re.findall(r'"(?:name|label|title|version|grade)"\s*:\s*"([^"]{2,40})"', b)
                if names:
                    log(f"      names: {names[:12]}")
                log(f"      sample: {b[:200].replace(chr(10),' ')}")

            # page pe variant + ₹ (RXE/RXL/RXT/RXZ Renault trims)
            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            log("  --- page: ₹ lines + upar (variant?) ---")
            shown = 0
            for i, l in enumerate(lines):
                if "₹" in l and re.search(r"\d", l):
                    prev = lines[i-1] if i > 0 else ""
                    log(f"    [{prev[:22]}] -> {l[:35]}")
                    shown += 1
                    if shown > 20:
                        break
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("renault2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. renault2.txt UPLOAD kar do.")
print("=" * 60)