"""
debug_brezza.py — Maruti Brezza 0 kyun? page structure dekho
=============================================================
Maruti scraper variant line ko MODEL NAAM se pehchaanta hai (line "Brezza..."
se shuru honi chahiye). Brezza 0 de raha hai — matlab uske page pe variant
lines ka format alag hai, ya price alag jagah.

Ye script Brezza (+ Swift compare) ke page pe saare ₹-price lines + upar/neeche
ka text dikhata hai — taaki asli structure pata chale.

CHALAO:
    python debug_brezza.py
Phir brezza.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.marutisuzuki.com/arena"
TESTS = {
    "Brezza": f"{BASE}/brezza/price",
    "Swift (works)": f"{BASE}/swift/price",
}

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

    for model, url in TESTS.items():
        log("\n" + "=" * 70)
        log(f"MODEL: {model}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            log(f"  status: {resp.status if resp else '?'}")
            try:
                page.wait_for_function("() => document.body.innerText.includes('₹')", timeout=20000)
            except Exception:
                log("  (₹ 20s me nahi dikha)")
            page.wait_for_timeout(3000)
            for _ in range(6):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(500)
            page.wait_for_timeout(2000)

            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]

            # saare ₹ lines + upar wali 2 line
            log("  --- ₹ price lines + upar (variant naam?) ---")
            shown = 0
            for i, l in enumerate(lines):
                if "₹" in l and re.search(r"\d", l):
                    prev = lines[i-1] if i > 0 else ""
                    prev2 = lines[i-2] if i > 1 else ""
                    log(f"    [{prev2[:22]}] [{prev[:22]}] -> {l[:35]}")
                    shown += 1
                    if shown > 25:
                        break
            if shown == 0:
                log("    (koi ₹ line nahi)")
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("brezza.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. brezza.txt UPLOAD kar do.")
print("=" * 60)