"""
debug_tata11.py — POST body ke saath test + error dikhao
=========================================================
Browser ki exact body copy karke, sirf fuel_type badal ke, POST karte hain.
Agar fail ho to error code dikhata hai.
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://cars.tatamotors.com/nexon/ice/price.html"
API = "https://cars.tatamotors.com/nexon/ice/price.getpricefilteredresult.json"
FUELS = {"Petrol": "5-29KIJOIL", "Diesel": "1-ID-1738", "CNG": "1-ID-268"}

captured = {"body": None}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    def on_request(req):
        if "getpricefilteredresult" in req.url and req.method == "POST" and req.post_data:
            captured["body"] = req.post_data
    page.on("request", on_request)

    print("Kholte hain...")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(4000)
    for _ in range(4):
        page.mouse.wheel(0, 1000); page.wait_for_timeout(500)
    page.wait_for_timeout(2000)
    page.remove_listener("request", on_request)

    if not captured["body"]:
        print("✗ base body capture nahi hua")
        browser.close(); exit()

    print("✓ Base body mil gayi:")
    print("  ", captured["body"][:200])
    base = json.loads(captured["body"])

    for fname, code in FUELS.items():
        body = json.loads(json.dumps(base))
        for f in body.get("filtersSelected", []):
            if f.get("filterType") == "fuel_type":
                f["values"] = [code]
            if f.get("filterType") == "transmission_type":
                f["values"] = []
        body["filtersSelected"] = [f for f in body["filtersSelected"]
                                    if f.get("values") or f.get("filterType") != "transmission_type"]

        result = page.evaluate("""
            async (args) => {
                const [url, body] = args;
                try {
                    const r = await fetch(url, {
                        method:'POST',
                        headers:{'content-type':'application/json','x-requested-with':'XMLHttpRequest','accept':'*/*'},
                        body: JSON.stringify(body)
                    });
                    return {status: r.status, text: (await r.text()).slice(0,200)};
                } catch(e){ return {err:String(e)}; }
            }
        """, [API, body])

        print(f"\n=== {fname} (code {code}) ===")
        if isinstance(result, dict) and "status" in result:
            print(f"  HTTP {result['status']}")
            if result["status"] == 200:
                try:
                    data = json.loads(result["text"]) if result["text"].startswith("{") else None
                except: data = None
                # poora response chahiye - dobara proper fetch
                full = page.evaluate("""
                    async (args) => {
                        const [url, body] = args;
                        const r = await fetch(url, {method:'POST',headers:{'content-type':'application/json','x-requested-with':'XMLHttpRequest','accept':'*/*'},body:JSON.stringify(body)});
                        return await r.json();
                    }
                """, [API, body])
                variants = full.get("results",{}).get("variantPriceFeatures",[])
                print(f"  ✓ {len(variants)} variants:")
                for v in variants[:15]:
                    print(f"     {v.get('variantLabel','?'):35s} {v.get('priceDetails',{}).get('originalPrice','?')}")
            else:
                print(f"  body: {result['text'][:150]}")
        else:
            print(f"  {result}")

    browser.close()
    print("\nDONE.")