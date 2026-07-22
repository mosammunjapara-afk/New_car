"""
debug_skoda7.py — Skoda ke variant + price RENDERED DOM se padho
================================================================
Bada clue: page pe trims DIKHTE hain (Classic, Signature, Active, Sportline,
Prestige). Prices JS-state me hain (network me nahi), par SCREEN pe render hoti
hain. Toh hum rendered DOM ka poora text + har price-jaisa element uske aas-paas
ke variant naam ke saath nikaalte hain.

Ye script kushaq (aur slavia) page pe:
  1. Poora scroll karke sab lazy content render karata hai
  2. Har element jisme "₹" hai, uska text + aas-paas (parent) ka text nikaalta hai
     — taaki variant naam + price ek saath mile
  3. Sab kuch skoda_debug7.txt me daalta hai

CHALAO:
    python debug_skoda7.py
Browser khulega. Agar variant/price section dikhe to us tak scroll ho jaane do
(script khud karega). ~40 sec me ho jayega. Phir skoda_debug7.txt UPLOAD karo.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.skoda-auto.co.in"
PAGES = [
    ("Kushaq", f"{BASE}/models/kushaq/kushaq"),
    ("Slavia", f"{BASE}/models/slavia/slavia"),
    ("Kylaq",  f"{BASE}/models/kylaq/kylaq"),
    ("Kodiaq", f"{BASE}/models/kodiaq/kodiaq"),
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

    for name, url in PAGES:
        log("\n" + "=" * 70)
        log(f"MODEL: {name}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=50000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(5000)

            # poora scroll — sab lazy sections render ho jayein
            for _ in range(10):
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(600)
            page.wait_for_timeout(2000)

            # koi "Variants" / "Price" / "All variants" tab ho to click
            for label in ["Variants", "All Variants", "View all variants",
                          "Price", "Prices", "Compare Variants", "Explore Variants"]:
                try:
                    el = page.locator(f"text={label}").first
                    if el.count() > 0:
                        el.click(timeout=2500)
                        page.wait_for_timeout(3000)
                        for _ in range(4):
                            page.mouse.wheel(0, 1200)
                            page.wait_for_timeout(500)
                except Exception:
                    pass

            # ---- har element jisme ₹ hai, uska + parent ka text nikaalo ----
            pairs = page.evaluate(r"""() => {
                const out = [];
                const all = Array.from(document.querySelectorAll('body *'));
                for (const el of all) {
                    // sirf wo elements jinke apne (direct) text me ₹ ho
                    const own = Array.from(el.childNodes)
                        .filter(n => n.nodeType === 3)
                        .map(n => n.textContent).join(' ').trim();
                    if (own.includes('₹') && /\d/.test(own)) {
                        // parent/ancestor ka text (variant naam ke liye)
                        let ctx = '';
                        let p = el;
                        for (let i=0; i<3 && p; i++) { p = p.parentElement; if (p) ctx = p.innerText; }
                        out.push({ price: own.slice(0,40), context: (ctx||'').slice(0,160).replace(/\s+/g,' ') });
                    }
                }
                return out;
            }""")

            log(f"  ₹-elements mile: {len(pairs)}")
            seen = set()
            for pr in pairs[:40]:
                key = pr["price"] + pr["context"][:40]
                if key in seen:
                    continue
                seen.add(key)
                log(f"    PRICE: {pr['price']}")
                log(f"      ctx: {pr['context']}")

            # trims list bhi (Skoda ke known trims)
            body_txt = page.inner_text("body")
            trims = [t for t in ["Classic","Signature","Active","Ambition","Style",
                                 "Sportline","Prestige","Onyx","Selection","Lounge",
                                 "L&K","Laurin","Monte Carlo"] if t in body_txt]
            log(f"  trims dikhe: {trims}")
        except Exception as e:
            log(f"  fail: {str(e)[:70]}")

    browser.close()

with open("skoda_debug7.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. skoda_debug7.txt UPLOAD kar do.")
print("=" * 60)