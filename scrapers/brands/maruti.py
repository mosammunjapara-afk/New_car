"""
scrapers/brands/maruti.py — Maruti Arena scraper (DIRECT official pricing API)
==============================================================================

Maruti ka official pricing API (page-scraping se bahut behtar — exact prices):

  POST/GET: /pricing/v2/common/pricing/ex-showroom-detail
            ?forCode=08&modelCodes=AT,VZ,CL,DE,VR,ER,SP,SI,EC,WA,CA
            &channel=NRM,NRC&variantInfoRequired=true

Response: har model ke saare variants, exact price, naam, fuel — ek call me.
  {"data":{"models":[
    {"modelCd":"VZ","modelDesc":"NEW BREZZA","exShowroomDetailResponseDTOList":[
      {"variantCd":"VZR4EL1","variantDesc":"MARUTI BREZZA LXI 1.5L 5MT",
       "exShowroomPrice":811400,"fuelTypeCd":"PET","colorType":"M"}, ...]}]}}

Note: har variant colorType M (metallic) + NM (non-metallic) ke liye 2 baar
aata hai, same price — dedup karte hain.

Ye API browser session ke bina bhi chal sakta hai, par safe rehne ke liye ek
page khol ke usi context me fetch karte hain (Incapsula/session ke liye).
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

# forCode = 08 (Delhi region — ex-showroom same base). channel NRM+NRC.
PRICING_API = (
    "https://www.marutisuzuki.com/pricing/v2/common/pricing/ex-showroom-detail"
    "?forCode=08&modelCodes=AT,VZ,CL,DE,VR,ER,SP,SI,EC,WA,CA"
    "&channel=NRM,NRC&variantInfoRequired=true"
)

# ek Arena page (session/cookies ke liye kholte hain, phir usi context me API fetch)
WARMUP_URL = "https://www.marutisuzuki.com/arena/brezza/price"

# model code -> display naam (Arena cars). Commercial (Super Carry) chhod dete hain.
MODEL_NAMES = {
    "AT": "Alto K10",
    "VZ": "Brezza",
    "CL": "Celerio",
    "DE": "Dzire",
    "VR": "Eeco",
    "ER": "Ertiga",
    "SP": "S-Presso",
    "SI": "Swift",
    "EC": "Victoris",
    "WA": "Wagon R",
    # "CA": Super Carry — commercial vehicle, chhod diya
}


def _detect_fuel(fuel_cd, variant_desc):
    f = (fuel_cd or "").upper()
    d = (variant_desc or "").upper()
    if "CNG" in f or "CNG" in d:
        return "CNG"
    if "DSL" in f or "DIESEL" in d:
        return "Diesel"
    if "ELE" in f or "ELECTRIC" in d or " EV" in d:
        return "Electric"
    # Maruti ke pricing me PET = Petrol; hybrid alag se aata
    if "HYB" in f or "HYBRID" in d:
        return "Hybrid"
    return "Petrol"


def _clean_variant(desc, model_name):
    """
    'MARUTI BREZZA LXI 1.5L 5MT' -> 'LXi 1.5L 5MT' (brand+model hata ke).
    """
    d = desc.strip()
    # "MARUTI" aur model naam (BREZZA/SWIFT etc) hata do
    d = re.sub(r"(?i)^MARUTI\s+SUZUKI\s+", "", d)
    d = re.sub(r"(?i)^MARUTI\s+", "", d)
    # model ke pehle shabd(on) ko hata (BREZZA, ALTO K10, WAGON R, S-PRESSO)
    mwords = model_name.upper().split()
    dwords = d.split()
    # jitne model-words start me match karein, hata do
    idx = 0
    for mw in mwords:
        if idx < len(dwords) and dwords[idx].upper().replace("-", "") == mw.replace("-", ""):
            idx += 1
    if idx > 0:
        d = " ".join(dwords[idx:])
    return d.strip() or desc.strip()


def _parse_pricing(data):
    """pricing API JSON se variant list nikaalo.
    Ek hi (model, variant, fuel) ke kai price-versions aate hain (M/NM color,
    ya alag city-base). Har unique variant ka SABSE KAM price rakhte hain
    (= asli base ex-showroom), taaki har variant ek hi baar aaye."""
    best = {}  # (model, variant, fuel) -> row (lowest price)
    models = data.get("data", {}).get("models", []) if isinstance(data, dict) else []
    for m in models:
        code = m.get("modelCd")
        model_name = MODEL_NAMES.get(code)
        if not model_name:
            continue  # jo model humari list me nahi (Super Carry etc.)
        for d in m.get("exShowroomDetailResponseDTOList", []):
            price = d.get("exShowroomPrice")
            desc = d.get("variantDesc", "")
            if not price or not desc:
                continue
            try:
                price = int(price)
            except Exception:
                continue
            if not (100000 < price < 30000000):
                continue
            variant = _clean_variant(desc, model_name)
            fuel = _detect_fuel(d.get("fuelTypeCd"), desc)
            key = (model_name, variant, fuel)
            if key not in best or price < best[key]["ex_showroom_price"]:
                best[key] = {
                    "model": model_name,
                    "variant": variant,
                    "fuel_type": fuel,
                    "ex_showroom_price": price,
                }
    return list(best.values())


def scrape_maruti():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        try:
            # 1. warmup page (session/cookies)
            page.goto(WARMUP_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            # 2. usi context me pricing API fetch (retry)
            data = None
            for attempt in range(3):
                try:
                    result = page.evaluate(
                        """async (url) => {
                            const r = await fetch(url, {headers: {'Content-Type':'application/json'}});
                            return await r.text();
                        }""",
                        PRICING_API,
                    )
                    data = _json.loads(result)
                    if data.get("data", {}).get("models"):
                        break
                except Exception:
                    page.wait_for_timeout(2000)

            if data:
                all_results = _parse_pricing(data)
                # per-model count print
                by_model = {}
                for r in all_results:
                    by_model.setdefault(r["model"], []).append(r)
                for mn, rows in by_model.items():
                    fuels = {}
                    for r in rows:
                        fuels[r["fuel_type"]] = fuels.get(r["fuel_type"], 0) + 1
                    bd = ", ".join(f"{k}:{v}" for k, v in fuels.items())
                    print(f"  [Maruti] {mn}: {len(rows)} variant(s)  [{bd}]")
            else:
                print("  [Maruti] pricing API nahi mila")
        except Exception as e:
            print(f"  [Maruti] failed: {str(e)[:60]}")
        finally:
            browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_maruti()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)