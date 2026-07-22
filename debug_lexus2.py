"""
debug_lexus2.py — Lexus saare models ka variant + price
========================================================
Lexus khula aur variant-wise deta hai! (LX 500d Urban Diesel INR 2.81cr...)
Ye script saare model pages (es/nx/rx/lx/lm) khol ke variant + price nikaalta.

CHALAO:
    python debug_lexus2.py
Phir lexus2.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.lexusindia.co.in"
MODEL_PAGES = [
    ("ES", f"{BASE}/models/es-350h/"),
    ("ES", f"{BASE}/models/es-500e/"),
    ("NX", f"{BASE}/models/nx/"),
    ("RX", f"{BASE}/models/rx/"),
    ("LX", f"{BASE}/models/lx/"),
    ("LM", f"{BASE}/models/lm/"),
    ("LS", f"{BASE}/models/ls/"),
    ("LC", f"{BASE}/models/lc/"),
]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page.set_default_timeout(40000)

    for model, url in MODEL_PAGES:
        log("\n" + "=" * 70)
        log(f"MODEL: {model}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=40000)
            st = resp.status if resp else "?"
            log(f"  status: {st}")
            if st != 200:
                continue
            page.wait_for_timeout(5000)
            for _ in range(8):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(500)
            page.wait_for_timeout(2000)

            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            # variant + INR/₹ price lines
            found = []
            for i, l in enumerate(lines):
                if re.search(r"(INR|₹|Rs)\s*[\d,]+", l):
                    # variant naam: isi line me (LX 500d Urban | Diesel | INR ...) ya upar
                    m = re.search(r"(INR|₹|Rs)\s*([\d,]+)", l)
                    price = int(re.sub(r"[^\d]", "", m.group(2)))
                    if 2000000 < price < 100000000:
                        ctx = [lines[j] for j in range(max(0,i-2), i+1)]
                        found.append((price, " | ".join(x[:30] for x in ctx)))
            seen=set()
            for pr, c in found:
                if c[:40] in seen: continue
                seen.add(c[:40])
                log(f"    Rs {pr}  <- {c[:80]}")
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("lexus2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. lexus2.txt UPLOAD kar do.")
print("=" * 60)