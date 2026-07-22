"""
debug_bmw2.py — BMW all-models: model naam + price + fuel
==========================================================
all-models page pe har model ka [fuel] + "From ₹X" hai. Model naam price ke
aas-paas hoga. Ye script har ₹ line ke around ka poora text (2-3 line upar)
nikaalta hai taaki model naam + fuel + price connect ho.

CHALAO:
    python debug_bmw2.py
Phir bmw2.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

URL = "https://www.bmw.in/en/all-models.html"

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

    log(f"Kholte hain: {URL}")
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(6000)
        for _ in range(12):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(600)
        page.wait_for_timeout(3000)
    except Exception as e:
        log(f"  fail: {str(e)[:50]}")

    # DOM se: har "From ₹" element ka + around ka structure
    # BMW cards me model naam alag element me hota hai
    data = page.evaluate(r"""() => {
        const out = [];
        const all = Array.from(document.querySelectorAll('body *'));
        for (const el of all) {
            const t = (el.innerText||'').trim();
            // chhota block jisme "From ₹" ho
            if (/From\s*₹[\d,]+/.test(t) && t.length < 200) {
                out.push(t.replace(/\s+/g,' ').slice(0,180));
            }
        }
        return out;
    }""")
    # dedup
    seen=set(); uniq=[]
    for t in data:
        k=t[:60]
        if k not in seen:
            seen.add(k); uniq.append(t)
    log(f"\n'From ₹' blocks: {len(uniq)}")
    for t in uniq[:40]:
        log(f"  {t[:120]}")

    # aur — poora body text ki lines (model naam price ke upar hota hai)
    txt = page.inner_text("body")
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    log("\n\n=== body lines: ₹ ke around 3 upar ===")
    for i, l in enumerate(lines):
        if "From ₹" in l or ("₹" in l and re.search(r"\d", l)):
            ctx = [lines[j] for j in range(max(0,i-3), i+1)]
            log(f"  {' | '.join(x[:22] for x in ctx)}")

    browser.close()

with open("bmw2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. bmw2.txt UPLOAD kar do.")
print("=" * 60)