"""
scrapers/brands/tata.py — Tata Motors scraper (POST API, saare fuel types)
===========================================================================

Tata ka price page POST API se data laata hai:
  POST .../price.getpricefilteredresult.json
  BODY: browser jo bhejta hai wahi, bas fuel_type ki value badal ke.

Trick: page kholo (session + base body milti hai), phir page ke andar se
har fuel code (Petrol/Diesel/CNG) ke liye POST karo. Poora data automatic.

Ye logic debug_tata11.py me test hua tha (Nexon: 19+15+10 = 44 variants).
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

BASE = "https://cars.tatamotors.com"

MODELS = {
    "nexon": "Nexon",
    "punch": "Punch",
    "tiago": "Tiago",
    "tigor": "Tigor",
    "altroz": "Altroz",
    "harrier": "Harrier",
    "safari": "Safari",
    "curvv": "Curvv",
}

FUEL_CODES = {
    "Petrol": "5-29KIJOIL",
    "Diesel": "1-ID-1738",
    "CNG": "1-ID-268",
}


def _detect_fuel(label: str) -> str:
    l = label.lower()
    if "cng" in l:
        return "CNG"
    if "diesel" in l:
        return "Diesel"
    if "electric" in l or "ev" in l:
        return "Electric"
    return "Petrol"


def _parse_api(data, slug):
    out = []
    variants = data.get("results", {}).get("variantPriceFeatures", [])
    for v in variants:
        label = v.get("variantLabel", "")
        pd = v.get("priceDetails", {})
        price_str = pd.get("originalPrice") or pd.get("price") or ""
        price = int(re.sub(r"[^\d]", "", price_str)) if price_str else None
        if price and 100000 < price < 8000000:
            variant_name = re.sub(r",\s*(Petrol|Diesel|CNG|Electric).*$", "", label, flags=re.I).strip()
            out.append({
                "model": slug,
                "variant": variant_name,
                "fuel_type": _detect_fuel(label),
                "ex_showroom_price": price,
            })
    return out


def _scrape_one_model(page, slug):
    url = f"{BASE}/{slug}/ice/price.html"
    api_url = f"{BASE}/{slug}/ice/price.getpricefilteredresult.json"

    captured = {"body": None}

    def on_request(req):
        if "getpricefilteredresult" in req.url and req.method == "POST" and req.post_data:
            captured["body"] = req.post_data

    page.on("request", on_request)
    # NOTE: "networkidle" NAHI use karte — Tata page pe New Relic/analytics
    # (bam.nr-data.net) continuously chalte rehte hain, isliye networkidle kabhi
    # aata hi nahi aur 60s timeout ho jaata hai (POST capture se pehle). Isse
    # saare Tata models 0 aate the. "domcontentloaded" turant aata hai.
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    for _ in range(5):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(700)
    page.wait_for_timeout(3000)
    page.remove_listener("request", on_request)

    if not captured["body"]:
        return []

    try:
        base = _json.loads(captured["body"])
    except Exception:
        return []

    collected = {}
    # har fuel ke liye: browser ki POORI body copy karo, sirf fuel_type value badlo
    # (price/edition filters rehne do — API ko chahiye; transmission empty karo)
    for fuel_name, code in FUEL_CODES.items():
        body = _json.loads(_json.dumps(base))
        for f in body.get("filtersSelected", []):
            if f.get("filterType") == "fuel_type":
                f["values"] = [code]
            if f.get("filterType") == "transmission_type":
                f["values"] = []
        body["filtersSelected"] = [
            f for f in body.get("filtersSelected", [])
            if f.get("values") or f.get("filterType") != "transmission_type"
        ]

        try:
            result = page.evaluate("""
                async (args) => {
                    const [url, body] = args;
                    try {
                        const r = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'content-type': 'application/json',
                                'x-requested-with': 'XMLHttpRequest',
                                'accept': '*/*'
                            },
                            body: JSON.stringify(body)
                        });
                        if (!r.ok) return {err: r.status};
                        return await r.json();
                    } catch(e) { return {err: String(e)}; }
                }
            """, [api_url, body])

            if isinstance(result, dict) and result.get("results"):
                for row in _parse_api(result, slug):
                    collected[(row["variant"], row["fuel_type"])] = row
        except Exception:
            pass

    return list(collected.values())


def scrape_tata():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        for slug in MODELS:
            try:
                res = _scrape_one_model(page, slug)
                fuels = {}
                for r in res:
                    fuels[r["fuel_type"]] = fuels.get(r["fuel_type"], 0) + 1
                breakdown = ", ".join(f"{k}:{v}" for k, v in fuels.items())
                print(f"  [Tata] {slug}: {len(res)} variant(s)  [{breakdown}]")
                all_results.extend(res)
            except Exception as e:
                print(f"  [Tata] {slug} failed: {str(e)[:60]}")
        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_tata()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)