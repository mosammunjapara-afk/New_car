"""
debug_carwale_variants.py — CarWale ka EXACT per-variant price API dhoondo
===========================================================================
Pichhla test: CarWale pe real prices hain (Kushaq 10.69L official se match).
Par wo "Rs. X Lakh" text tha + variant groups. Ab EXACT per-variant price
(rupee me, fuel/transmission ke saath) chahiye.

CarWale ke har model ki ek 'price in city' ya 'variants' page/API hoti hai jahan
har variant ka exact ₹ price hota hai. Ye script:
  1. Kushaq model page se andar ke 'price'/'variants' links nikaalta hai
  2. Us variants page pe jaake exact per-variant price API capture karta hai
  3. JSON API jisme "variant" + exact 6-7 digit price ho, use dikhata hai

CHALAO:
    python debug_carwale_variants.py
Phir carwale_variants.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.carwale.com"

SKIP = ["google","gtm","facebook","gstatic","fonts.","youtube","doubleclick",
        "analytics","clarity","adobe","demdex","omtrdc","onetrust","hotjar","bing",
        "segment","taboola","criteo","crazyegg","globalmediacampaign","moengage",
        "clevertap","amazon-adsystem","bhrigu","scorecardresearch","branch"]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def exact_prices(body):
    nums = re.findall(r'\b(\d{6,8})\b', body)
    return sorted(set(int(n) for n in nums if 100000 <= int(n) <= 9999999))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    calls = []
    def on_response(resp):
        u = resp.url
        if any(s in u for s in SKIP):
            return
        ct = resp.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            b = resp.text()
        except Exception:
            return
        if exact_prices(b) and any(k in b.lower() for k in
                ["variant","price","fuel","transmission","exshowroom","ex_showroom","model"]):
            calls.append((u, resp.request.method, b))
    page.on("response", on_response)

    # 1. model page kholo, andar ke variant/price links nikaalo
    start = f"{BASE}/skoda-cars/kushaq/"
    log(f"Kholte hain: {start}")
    page.goto(start, wait_until="domcontentloaded", timeout=50000)
    page.wait_for_timeout(5000)
    for _ in range(5):
        page.mouse.wheel(0, 1400)
        page.wait_for_timeout(600)

    hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
    # variant/price wale links
    vlinks = sorted(set(h for h in hrefs if "kushaq" in h.lower()
                        and any(k in h.lower() for k in ["variant","price","specs"])))
    log(f"\nvariant/price links ({len(vlinks)}):")
    for h in vlinks[:15]:
        log(f"  {h}")

    # 2. har link pe jaake exact-price API dhoondo
    targets = vlinks[:4] if vlinks else []
    # fallback: common CarWale patterns
    if not targets:
        targets = [
            f"{BASE}/skoda-cars/kushaq/price-in-new-delhi/",
            f"{BASE}/skoda-cars/kushaq/variants/",
        ]

    for link in targets:
        calls.clear()
        log("\n" + "=" * 70)
        log(f"VISIT: {link}")
        log("=" * 70)
        try:
            resp = page.goto(link, wait_until="domcontentloaded", timeout=45000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(5000)
            for _ in range(5):
                page.mouse.wheel(0, 1400)
                page.wait_for_timeout(600)
            page.wait_for_timeout(2000)

            # exact-price JSON APIs
            hits = [(u, m, b, exact_prices(b)) for (u, m, b) in calls]
            hits.sort(key=lambda x: -len(x[3]))
            log(f"  exact-price JSON APIs: {len(hits)}")
            seen = set()
            for u, m, b, gp in hits[:5]:
                base = u.split("?")[0]
                if base in seen:
                    continue
                seen.add(base)
                log(f"\n  [{m}] {u[:130]}")
                log(f"  {len(gp)} exact prices: {gp[:20]}")
                log(f"  body: {b[:600].replace(chr(10),' ')}")

            # __NEXT_DATA__ / embedded json me variant+price
            try:
                nd = page.evaluate(
                    "() => { const s=document.getElementById('__NEXT_DATA__'); return s?s.textContent:''; }")
                if nd:
                    gp = exact_prices(nd)
                    if len(gp) >= 3:
                        log(f"\n  __NEXT_DATA__ me {len(gp)} exact prices: {gp[:20]}")
                        # variant naam ke around
                        i = nd.lower().find('"variant')
                        if i != -1:
                            log(f"  near variant: {nd[i:i+400]}")
            except Exception:
                pass

            # page pe variant + exact price table
            txt = page.inner_text("body")
            vlines = [l.strip() for l in txt.split("\n")
                      if re.search(r"(Classic|Signature|Active|Ambition|Style|Sportline|Prestige|Monte)", l)
                      and ("₹" in l or "Rs" in l or "Lakh" in l)]
            if vlines:
                log(f"\n  variant+price lines ({len(vlines)}):")
                for l in vlines[:20]:
                    log(f"    {l[:70]}")
        except Exception as e:
            log(f"  fail: {str(e)[:60]}")

    browser.close()

with open("carwale_variants.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. carwale_variants.txt UPLOAD kar do.")
print("=" * 60)