"""
debug_brezza2.py — Brezza ka sahi price-page dhoondo
=====================================================
Brezza /arena/brezza/price pe koi ₹ nahi aayi (Swift pe aati hai). Do wajah:
alag URL, ya price alag jagah/slow. Ye script Brezza ke alag URLs try karta hai
aur zyada wait deta hai. Homepage se asli Brezza link bhi nikaalta hai.

CHALAO:
    python debug_brezza2.py
Phir brezza2.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

out = []
def log(s=""):
    print(s)
    out.append(str(s))


CANDIDATES = [
    "https://www.marutisuzuki.com/arena/brezza/price",
    "https://www.marutisuzuki.com/arena/brezza",
    "https://www.nexaexperience.com/brezza/price",  # galti se nexa me to nahi
]


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 1. Maruti Arena homepage se Brezza ka asli link
    log("Arena homepage se Brezza link dhoondte hain...")
    try:
        page.goto("https://www.marutisuzuki.com/arena", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)
        hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
        blinks = sorted(set(h for h in hrefs if "brezza" in h.lower()))
        log("  Brezza links homepage pe:")
        for h in blinks:
            log(f"    {h}")
            if h not in CANDIDATES:
                CANDIDATES.append(h)
    except Exception as e:
        log(f"  homepage fail: {str(e)[:50]}")

    # 2. har candidate try karo, zyada wait
    for url in CANDIDATES:
        log("\n" + "=" * 70)
        log(f"TRY: {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            log(f"  status: {resp.status if resp else '?'}")
            if not resp or resp.status != 200:
                continue
            # zyada wait — 30s tak ₹ ka intezaar
            got = False
            try:
                page.wait_for_function("() => document.body.innerText.includes('₹')", timeout=30000)
                got = True
            except Exception:
                pass
            page.wait_for_timeout(3000)
            for _ in range(8):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(500)
            page.wait_for_timeout(2000)

            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            plines = [(i, l) for i, l in enumerate(lines) if "₹" in l and re.search(r"\d", l)]
            log(f"  ₹ dikha (30s): {got}, price lines: {len(plines)}")
            for i, l in plines[:20]:
                prev = lines[i-1] if i > 0 else ""
                log(f"    [{prev[:22]}] -> {l[:35]}")
            if plines:
                log("  ✓✓ YE URL KAAM KARTA HAI")
                break
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("brezza2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. brezza2.txt UPLOAD kar do.")
print("=" * 60)