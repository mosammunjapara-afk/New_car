"""
debug_lexus3.py — Lexus NX/LX ka rendered text dump (parser kyun 0 de raha)
============================================================================
TOTAL 0 aaya — parser filter strict. Ye script NX aur LX page ka poora rendered
text (INR wali lines + around) dump karta hai, taaki dekhein variant+fuel+price
kis structure me hain (ek line ya alag lines).

CHALAO:
    python debug_lexus3.py
Phir lexus3.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.lexusindia.co.in"
PAGES = [("NX", f"{BASE}/models/nx/"), ("LX", f"{BASE}/models/lx/")]

out = []
def log(s=""):
    print(s); out.append(str(s))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page.set_default_timeout(30000)
    for model, url in PAGES:
        log("\n"+"="*60); log(f"{model}: {url}"); log("="*60)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            for _ in range(8):
                page.mouse.wheel(0, 1000); page.wait_for_timeout(600)
            page.wait_for_timeout(2000)
            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            # INR wali line + 3 upar 1 neeche
            for i, l in enumerate(lines):
                if re.search(r"(INR|₹|Rs)\s*[\d,]+", l):
                    lo = max(0, i-3); hi = min(len(lines), i+2)
                    log(f"  --- around line {i} ---")
                    for j in range(lo, hi):
                        mark = ">>" if j == i else "  "
                        log(f"  {mark} [{j}] {lines[j][:60]}")
        except Exception as e:
            log(f"  fail: {str(e)[:40]}")
    browser.close()

with open("lexus3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\nHO GAYA. lexus3.txt UPLOAD karo.")