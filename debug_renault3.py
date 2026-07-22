"""
debug_renault3.py — Renault variant+price main model page se + rplug slice API
===============================================================================
-price.html khaali/404. Par main model page (renault-kiger.html) pe prices dikhe
the (5.81L, 8.45L...). rplug slice120 API bhi wahin fire hoti hai.

Ye script main model page pe jaake:
  1. rplug slice120 API ki POORI response capture karta hai (variant+price)
  2. page pe variant naam (RXE/RXT/RXZ) + ₹ price
  3. configurator me jaake bhi try

CHALAO:
    python debug_renault3.py
Phir renault3.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

MODELS = {
    "Kiger": "https://www.renault.co.in/cars/renault-kiger.html",
    "Kwid": "https://www.renault.co.in/cars/renault-kwid.html",
    "Triber": "https://www.renault.co.in/cars/renault-triber.html",
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

    slice_calls = []
    def on_response(resp):
        u = resp.url
        if "slice" in u or "rplug" in u or ("/agg/" in u):
            try:
                b = resp.text()
            except Exception:
                b = ""
            slice_calls.append((u, b))
    page.on("response", on_response)

    for model, url in MODELS.items():
        slice_calls.clear()
        log("\n" + "=" * 70)
        log(f"MODEL: {model}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=50000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(6000)
            for _ in range(8):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(600)
            page.wait_for_timeout(3000)

            # slice/rplug API
            log(f"  slice/agg/rplug calls: {len(slice_calls)}")
            seen = set()
            for u, b in slice_calls:
                base = u.split("?")[0]
                if base in seen: continue
                seen.add(base)
                prices = real_prices(b)
                log(f"    {u[:130]}")
                log(f"      {len(prices)} prices: {prices[:15]}")
                # variant naam
                names = re.findall(r'"(?:name|label|title|version|grade|nameVersion)"\s*:\s*"([^"]{2,45})"', b)
                if names:
                    log(f"      names: {names[:12]}")
                if prices or names:
                    log(f"      sample: {b[:300].replace(chr(10),' ')}")

            # page pe variant + ₹
            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            log("  --- page ₹ lines + upar (variant?) ---")
            shown = 0
            for i, l in enumerate(lines):
                if "₹" in l and re.search(r"\d", l):
                    prev = lines[i-1] if i > 0 else ""
                    prev2 = lines[i-2] if i > 1 else ""
                    log(f"    [{prev2[:18]}][{prev[:18]}] -> {l[:32]}")
                    shown += 1
                    if shown > 20:
                        break
            # Renault trims dhoondo
            for trim in ["RXE","RXL","RXT","RXZ","Authentic","Evolution","Techno","Emotion"]:
                if trim in txt:
                    log(f"    (trim dikha: {trim})")
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("renault3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. renault3.txt UPLOAD kar do.")
print("=" * 60)