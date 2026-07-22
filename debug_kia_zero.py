"""
debug_kia_zero.py — Kia Carnival + EV9 (0 kyun?) ka trim+price dekho
=====================================================================
Carnival aur EV9 0 dete hain. Kia scraper text se trim parse karta hai
(HTE/HTK/HTX/GTX...). In 2 models ke trim naam shayad alag hain (Carnival:
Limousine/Prestige; EV9: GT Line) jo list me nahi. Ya price format alag.

Ye script inke page pe jaake SAARE ₹-price wale lines + aas paas ka text
dikhata hai — taaki asli trim naam pata chale.

CHALAO:
    python debug_kia_zero.py
Phir kia_zero.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.kia.com/in/our-vehicles"
TESTS = {
    "Carnival": f"{BASE}/carnival.html",
    "EV9": f"{BASE}/ev9.html",
    "Seltos (works)": f"{BASE}/seltos.html",  # compare ke liye
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
            page.wait_for_timeout(5000)
            for _ in range(10):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(600)
            page.wait_for_timeout(3000)

            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]

            # saare ₹ price lines + 2 line upar (trim naam)
            log("  --- ₹ price lines + upar wali line (trim?) ---")
            shown = 0
            for i, l in enumerate(lines):
                if "₹" in l and re.search(r"\d", l):
                    prev = lines[i-1] if i > 0 else ""
                    prev2 = lines[i-2] if i > 1 else ""
                    log(f"    [{prev2[:20]}] [{prev[:20]}] -> {l[:40]}")
                    shown += 1
                    if shown > 20:
                        break
            if shown == 0:
                log("    (koi ₹ price nahi — page structure alag ya price nahi)")
                # MSRP / Price / starting words dhoondo
                for kw in ["MSRP", "Starting", "Price", "starting at", "Ex-showroom"]:
                    cnt = txt.count(kw)
                    if cnt:
                        log(f"    '{kw}': {cnt}x page me hai")
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("kia_zero.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. kia_zero.txt UPLOAD kar do.")
print("=" * 60)