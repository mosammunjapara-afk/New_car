"""
debug_brezza3.py — Brezza ke ₹ elements ka structure (element-wise)
====================================================================
₹ symbol page pe HAI par line me ₹+number ek saath nahi (alag elements me).
Isliye line-parse fail. Ye script har ₹ wale element ka + uske parent ka text
nikaalta hai (element-wise) — taaki variant naam + price ek saath mile.

Swift (works) se compare bhi.

CHALAO:
    python debug_brezza3.py
Phir brezza3.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

TESTS = {
    "Brezza": "https://www.marutisuzuki.com/arena/brezza/price",
    "Swift": "https://www.marutisuzuki.com/arena/swift/price",
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
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            try:
                page.wait_for_function("() => document.body.innerText.includes('₹')", timeout=30000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            for _ in range(8):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(500)
            page.wait_for_timeout(2000)

            # har element jisme ₹ ho — uska text + parent ka text
            data = page.evaluate(r"""() => {
                const out = [];
                const all = Array.from(document.querySelectorAll('body *'));
                for (const el of all) {
                    const own = Array.from(el.childNodes)
                        .filter(n => n.nodeType === 3)
                        .map(n => n.textContent).join(' ').trim();
                    if (own.includes('₹')) {
                        let ctx = '';
                        let pp = el.parentElement;
                        if (pp) ctx = (pp.innerText || '').slice(0, 120).replace(/\s+/g,' ');
                        out.push({ own: own.slice(0,40), ctx: ctx });
                    }
                }
                return out;
            }""")
            log(f"  ₹-elements: {len(data)}")
            seen = set()
            shown = 0
            for d in data:
                k = d["own"] + d["ctx"][:30]
                if k in seen:
                    continue
                seen.add(k)
                shown += 1
                if shown > 20:
                    break
                log(f"    ₹text: {repr(d['own'])}")
                log(f"      ctx: {d['ctx'][:90]}")

            # aur — koi variant-price API JSON to nahi
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("brezza3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. brezza3.txt UPLOAD kar do.")
print("=" * 60)