"""
debug_cardekho10.py — CarDekho GraphQL (apis.cardekho.com/f8) variant query pakdo
==================================================================================
BADA UNLOCK: CarDekho ka data GraphQL API se aata hai:
    POST https://apis.cardekho.com/f8
    body: {"operationName":"...","query":"...","variables":{...}}
Aur humare paas __token hai. 784 models __CD_DATA__ me.

getUserV2 to user ka tha. Variant-price ek ALAG query se aata hai jo variant
section scroll pe fire hoti hai. Ye script HAR /f8 POST ki POORI body + response
capture karta hai — usme variant-price query + response structure mil jayega.

CHALAO:
    python debug_cardekho10.py
Phir cardekho_debug10.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.cardekho.com"
URL = f"{BASE}/maruti-suzuki/swift/variants"

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

    # har /f8 (graphql) request-response pair
    gql = []  # (op_name, req_body, resp_body)

    def on_response(resp):
        u = resp.url
        if "apis.cardekho.com" not in u and "/f8" not in u:
            return
        try:
            req_body = resp.request.post_data or ""
        except Exception:
            req_body = ""
        try:
            resp_body = resp.text()
        except Exception:
            resp_body = ""
        op = ""
        try:
            j = json.loads(req_body)
            op = j.get("operationName", "") if isinstance(j, dict) else ""
        except Exception:
            m = re.search(r'"operationName"\s*:\s*"([^"]+)"', req_body)
            op = m.group(1) if m else "?"
        gql.append((op, req_body, resp_body))
    page.on("response", on_response)

    log(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=50000)
    page.wait_for_timeout(4000)

    # variant section tak dhire dhire scroll (har lazy query fire ho)
    for _ in range(18):
        page.mouse.wheel(0, 800)
        page.wait_for_timeout(500)
    page.wait_for_timeout(3000)

    # variant tab / "view all" bhi try
    for label in ["View all variants", "All Variants", "Variants", "Compare"]:
        try:
            el = page.locator(f"text={label}").first
            if el.count() > 0:
                el.click(timeout=2500)
                page.wait_for_timeout(3000)
        except Exception:
            pass
    page.wait_for_timeout(3000)

    log(f"\n=== GraphQL /f8 calls: {len(gql)} ===")
    for i, (op, rb, resp) in enumerate(gql):
        log("\n" + "-" * 60)
        log(f"[{i}] operationName: {op}")
        # request query text (short)
        qm = re.search(r'"query"\s*:\s*"([^"]{0,400})', rb)
        if qm:
            log(f"  query: {qm.group(1)[:300]}")
        # variables
        vm = re.search(r'"variables"\s*:\s*(\{[^}]{0,200}\})', rb)
        if vm:
            log(f"  variables: {vm.group(1)}")
        # response: exact prices + variant names?
        names = re.findall(r'"variant\w*[Nn]ame"\s*:\s*"([^"]{2,45})"', resp)
        prices = sorted(set(int(x) for x in re.findall(r'\b(\d{6,7})\b', resp) if 200000 <= int(x) <= 9999999))
        if names or prices:
            log(f"  RESP variant names: {names[:15]}")
            log(f"  RESP exact prices: {prices[:15]}")
        log(f"  resp sample: {resp[:300].replace(chr(10),' ')}")

    # token bhi save (baad me API call ke liye)
    try:
        token = page.evaluate("() => window.__token || ''")
        log(f"\n__token (full): {token}")
    except Exception:
        pass

    browser.close()

with open("cardekho_debug10.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. cardekho_debug10.txt UPLOAD kar do.")
print("=" * 60)