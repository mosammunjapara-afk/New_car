"""
debug_cardekho5.py — CarDekho: model ka APNA variant-table (exact price)
=========================================================================
0 API calls the — matlab data server-side render hota hai (HTML me). Ab hum:
  1. Page ke saare embedded JSON (script tags) me se wo dhoondte hain jisme
     variant list ho — "variantName" ke saath NON-empty price
  2. DOM me us section ko target karte hain jisme model ka apna variant table hai
     (heading "Kushaq Price List" / "Swift Variants" ke neeche wali table)

Ye sidebar (doosre models) ko chhod ke sirf is model ke variants deta hai.

CHALAO:
    python debug_cardekho5.py
Phir cardekho_debug5.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.cardekho.com"
MODELS = [
    ("Skoda Kushaq", "skoda", "kushaq", "Kushaq"),
    ("Maruti Swift", "maruti-suzuki", "swift", "Swift"),
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

    for name, make, model, mname in MODELS:
        url = f"{BASE}/{make}/{model}/price"
        log("\n" + "=" * 70)
        log(f"MODEL: {name}  →  {url}")
        log("=" * 70)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            for _ in range(8):
                page.mouse.wheel(0, 1300)
                page.wait_for_timeout(500)
            page.wait_for_timeout(2000)

            # ---- 1. embedded JSON me variant list (NON-empty price) ----
            scripts = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('script'))
                    .map(s => s.textContent).filter(t => t && t.length > 300);
            }""")
            log(f"\n  script blocks: {len(scripts)}")
            found_json = False
            for s in scripts:
                # variantName ke saath actual price value?
                if '"variantName"' in s or '"variantPriceValue"' in s or '"variantList"' in s:
                    # non-empty variantName nikaalo
                    pairs = re.findall(
                        r'"variantName"\s*:\s*"([^"]{2,45})"[^}]*?"(?:variantPriceValue|priceValue|price)"\s*:\s*"?(\d{5,8})',
                        s)
                    if pairs:
                        found_json = True
                        log(f"  ✓✓ embedded variant list mila ({len(pairs)}):")
                        for vn, pr in pairs[:30]:
                            log(f"      {vn}  —  ₹{pr}")
                        break
                    # ya reverse order (price pehle, naam baad me)
                    pairs2 = re.findall(
                        r'"(?:variantPriceValue|priceValue)"\s*:\s*"?(\d{5,8})"?[^}]*?"variantName"\s*:\s*"([^"]{2,45})"',
                        s)
                    if pairs2:
                        found_json = True
                        log(f"  ✓✓ embedded variant list (rev) ({len(pairs2)}):")
                        for pr, vn in pairs2[:30]:
                            log(f"      {vn}  —  ₹{pr}")
                        break

            if not found_json:
                # koi bhi script jisme mname + price-jaisa ho, uska ek chunk dikhao
                for s in scripts:
                    if mname.lower() in s.lower() and re.search(r'\d{6,7}', s):
                        i = s.lower().find(mname.lower())
                        log(f"  (variant-json nahi mila; {mname} ka context:)")
                        log(f"    {s[max(0,i-40):i+400]}")
                        break

            # ---- 2. DOM: model ke naam wale heading ke neeche variant rows ----
            dom_rows = page.evaluate(f"""() => {{
                const out = [];
                // headings jisme "{mname}" + "Variant"/"Price" ho
                const heads = Array.from(document.querySelectorAll('h1,h2,h3,h4'));
                for (const h of heads) {{
                    const ht = (h.innerText||'').toLowerCase();
                    if (ht.includes('{mname.lower()}') && (ht.includes('variant') || ht.includes('price'))) {{
                        // us heading ke baad wala table/list
                        let sib = h.parentElement;
                        for (let i=0; i<4 && sib; i++) {{
                            const rows = sib.querySelectorAll('tr,li');
                            for (const r of rows) {{
                                const t = (r.innerText||'').trim().replace(/\\s+/g,' ');
                                if (t.length<80 && /(₹|Rs)\\s?[\\d,.]+/.test(t) && /[A-Za-z]{{2}}/.test(t))
                                    out.push(t);
                            }}
                            if (out.length>0) break;
                            sib = sib.parentElement;
                        }}
                    }}
                }}
                return out;
            }}""")
            seen = set(); uniq = []
            for r in dom_rows:
                if r[:45] not in seen:
                    seen.add(r[:45]); uniq.append(r)
            if uniq:
                log(f"\n  DOM variant rows ({len(uniq)}):")
                for r in uniq[:30]:
                    log(f"    {r[:70]}")
        except Exception as e:
            log(f"  fail: {str(e)[:60]}")

    browser.close()

with open("cardekho_debug5.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. cardekho_debug5.txt UPLOAD kar do.")
print("=" * 60)