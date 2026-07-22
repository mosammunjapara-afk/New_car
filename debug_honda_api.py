"""
debug_honda_api.py — Honda ke asli /api/ endpoints seedha GET karke JSON dekho
==============================================================================
Network dump se pata chala Honda ke 3 asli API hain (koi form-fill nahi chahiye,
Hyundai jaisa clean GET):

  1. /api/getDynamicPageOptions?pageName=priceCheck  -> saari cars + variants (?)
  2. /api/getAllStates                                -> states list
  3. /api/getAllCities?stateId=<id>                   -> cities
  4. /api/getStateCheck?cityName=<name>               -> city ka price-region (?)

Ye script har ek ko kholega aur response honda_api_responses.txt me save karega.
Isse mujhe variant + price ka exact structure mil jayega, phir scraper ban jayega.

CHALAO:
    python debug_honda_api.py

Phir honda_api_responses.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import json

BASE = "https://www.hondacarindia.com"

# Jo endpoints try karne hain (order matters — pehle states, phir city)
ENDPOINTS = [
    "/api/getDynamicPageOptions?pageName=priceCheck",
    "/api/getOfferCars",
    "/api/getAllStates",
    "/api/getAllCities?stateId=1",
    "/api/getStateCheck?cityName=Mumbai",
    "/api/getAllDealerViaTypes?cityId=15&radius=100",
]

out_lines = []


def log(s=""):
    print(s)
    out_lines.append(str(s))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Pehle asli page kholo taaki cookies/session mil jaye (Incapsula ke liye)
    log("Warming up: check-price page khol rahe hain (session ke liye)...")
    try:
        page.goto(f"{BASE}/check-price", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
    except Exception as e:
        log(f"  warmup warn: {str(e)[:60]}")

    for ep in ENDPOINTS:
        url = BASE + ep
        log("\n" + "=" * 70)
        log(f"GET {ep}")
        log("=" * 70)
        try:
            # fetch() browser context ke andar (same cookies/headers)
            result = page.evaluate(
                """async (u) => {
                    try {
                        const r = await fetch(u, {
                            method: 'GET',
                            headers: {'Content-Type': 'application/json'}
                        });
                        const t = await r.text();
                        return {status: r.status, body: t};
                    } catch (e) {
                        return {status: -1, body: String(e)};
                    }
                }""",
                url,
            )
            status = result.get("status")
            body = result.get("body", "")
            log(f"STATUS: {status}")
            # pretty-print agar JSON ho
            try:
                parsed = json.loads(body)
                pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
                log("BODY (JSON, pehle 4000 chars):")
                log(pretty[:4000])
            except Exception:
                log("BODY (raw, pehle 2000 chars):")
                log(body[:2000])
        except Exception as e:
            log(f"  FAILED: {str(e)[:80]}")

        page.wait_for_timeout(1000)

    browser.close()

with open("honda_api_responses.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print("\n\n" + "=" * 60)
print("HO GAYA. honda_api_responses.txt UPLOAD kar do.")
print("=" * 60)