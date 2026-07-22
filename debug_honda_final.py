"""
debug_honda_final.py — Honda ka asli variant-price API pakdo (100% tarika)
===========================================================================
Ye script:
  1. Browser KHOL ke dikhayega (headed) — aap khud dekh paoge
  2. check-price page kholega
  3. Aap KHUD haath se: State chuno -> City chuno -> "Check Price" dabao
  4. Ye background me chalne wale HAR network call ko record karega
     (jaha bhi variant + price aayega — wahi humara API hai)
  5. Sab kuch honda_network_dump.txt me save karega

CHALANE SE PEHLE (ek baar):
    pip install playwright
    python -m playwright install chromium

CHALAO:
    python debug_honda_final.py

Phir browser khulega. Usme:
  - "Select State" pe click -> Maharashtra chuno
  - "Select City"  pe click -> Mumbai (ya koi bhi) chuno
  - "Check Price"  button dabao
  - Prices dikhne ke baad ~5 sec ruko
  - Phir terminal me ENTER dabao (script band ho jayegi + file save)

RESULT: honda_network_dump.txt upload kar dena. Usme asli API URL + response hoga.
"""

from playwright.sync_api import sync_playwright
import re

URL = "https://www.hondacarindia.com/check-price"

# Jo domains humein nahi chahiye (ads/analytics) — skip
SKIP = ["chat360", "google", "doubleclick", "gtm", "facebook", "gstatic",
        "fonts", "youtube", "analytics", "clarity", "recaptcha", "hotjar",
        "segment", "adservice", "linkedin", "bing"]

records = []          # (url, method, status, content_type, body)
price_hits = []       # sirf wo calls jinme variant + price dikhe


def interesting(body: str) -> bool:
    """Kya is response me variant-price data hai?"""
    if not body:
        return False
    has_number = re.search(r"\d{5,8}", body)  # price jaisa bada number
    has_kw = any(k in body.lower() for k in
                 ["variant", "grade", "price", "exshowroom", "ex_showroom",
                  "trim", "model", "petrol", "diesel"])
    return bool(has_number and has_kw)


with sync_playwright() as p:
    # headed = aap browser dekh paoge
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        if any(s in u for s in SKIP):
            return
        ct = resp.headers.get("content-type", "")
        # JSON ya XHR/fetch dono capture karo (Honda ka API kisi bhi form me ho)
        if not any(t in ct for t in ["json", "javascript", "text"]):
            # phir bhi agar URL me price/variant clue ho to capture
            if not any(k in u.lower() for k in ["price", "variant", "grade", "model"]):
                return
        try:
            body = resp.text()
        except Exception:
            body = ""
        rec = (u, resp.request.method, resp.status, ct, body)
        records.append(rec)
        if interesting(body):
            price_hits.append(rec)

    page.on("response", on_response)

    print("\n" + "=" * 60)
    print("Browser khul raha hai... check-price page load ho raha hai")
    print("=" * 60)
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    print("""
+----------------------------------------------------------+
|  AB AAP KHUD YE KARO (browser window me):                |
|                                                          |
|   1. 'Select State' pe click -> Maharashtra chuno        |
|   2. 'Select City'  pe click -> Mumbai (ya koi) chuno    |
|   3. 'Check Price'  button dabao                         |
|   4. Prices dikhne ke baad 5 second ruko                 |
|                                                          |
|  Ho gaya? To yahan terminal me ENTER dabao ↓             |
+----------------------------------------------------------+
""")
    input(">>> Jab prices dikh jayein, ENTER dabao... ")

    # form submit ke baad thoda aur ruko
    page.wait_for_timeout(2000)

    # page pe dikh rahe ₹ prices bhi grab karo (backup)
    try:
        page_text = page.inner_text("body")
    except Exception:
        page_text = ""

    browser.close()

# ---------------------------------------------------------------------------
# Result file likho
# ---------------------------------------------------------------------------
with open("honda_network_dump.txt", "w", encoding="utf-8") as f:
    f.write("=" * 70 + "\n")
    f.write("HONDA NETWORK DUMP\n")
    f.write("=" * 70 + "\n\n")

    f.write(f"### PRICE-JAISE API HITS ({len(price_hits)}) ###\n")
    f.write("(Ye sabse important — inme variant + price hone chahiye)\n\n")
    seen = set()
    for u, m, st, ct, body in price_hits:
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        f.write("-" * 70 + "\n")
        f.write(f"URL    : {u}\n")
        f.write(f"METHOD : {m}   STATUS: {st}   TYPE: {ct}\n")
        f.write(f"BODY (pehle 1500 chars):\n{body[:1500]}\n\n")

    f.write("\n\n" + "=" * 70 + "\n")
    f.write(f"### SAARE JSON/XHR CALLS ({len(records)}) — sirf URL list ###\n\n")
    seen2 = set()
    for u, m, st, ct, body in records:
        base = u.split("?")[0]
        if base in seen2:
            continue
        seen2.add(base)
        flag = "  <== PRICE?" if interesting(body) else ""
        f.write(f"[{m} {st}] {u[:120]}{flag}\n")

    f.write("\n\n" + "=" * 70 + "\n")
    f.write("### PAGE PE DIKHNE WALE ₹ PRICES (backup) ###\n\n")
    for line in page_text.split("\n"):
        if "₹" in line and re.search(r"\d", line):
            f.write("  " + line.strip()[:80] + "\n")

# ---------------------------------------------------------------------------
# Terminal summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print(f"HO GAYA! {len(price_hits)} price-jaisi API mili, {len(records)} total calls.")
print("=" * 60)
if price_hits:
    print("\nSabse pehli price API (preview):")
    u, m, st, ct, body = price_hits[0]
    print(f"  {m} {u[:100]}")
    print(f"  {body[:250]}")
else:
    print("\nKoi obvious price API nahi mili — koi baat nahi,")
    print("honda_network_dump.txt me saari calls hain, main dekh lunga.")

print("\n>>> honda_network_dump.txt file UPLOAD kar do. <<<")