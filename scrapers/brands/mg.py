"""
scrapers/brands/mg.py — MG Motor India scraper (DIRECT official API)
====================================================================

MG ka official variant API (AWS API Gateway — saare models ek call me):
  https://eeysubngbk.execute-api.ap-south-1.amazonaws.com/prod/api/variants

Response: list of models, har model me variants[], har variant me:
  model_line     -> MG_COMET_EV / ASTOR / HECTOR ...
  model_text1    -> variant naam (COMET EV EXCLUSIVE FC)
  modelseries    -> trim (EXCLUSIVE FC)
  fuel_type      -> code (01/02/05)
  pricing[0].cities[0].price -> exact ex-showroom price (city-wise, base same)

Ye API browser session ke through fetch karte hain (ek MG page khol ke).
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

VARIANTS_API = "https://eeysubngbk.execute-api.ap-south-1.amazonaws.com/prod/api/variants"
WARMUP_URL = "https://www.mgmotor.co.in/service/astor-my-mg-shield"

# model_line -> clean display naam
MODEL_NAMES = {
    "MG_COMET_EV": "Comet EV",
    "ASTOR": "Astor",
    "WINDSOR_EV": "Windsor EV",
    "WINDSOR_PRO": "Windsor EV Pro",
    "HECTOR": "Hector",
    "MG_ZS_EV": "ZS EV",
    "HECTOR_PLUS_7_SEATER": "Hector Plus 7-Seater",
    "HECTOR_PLUS_6_SEATER": "Hector Plus 6-Seater",
    "MAJESTOR": "Majestor",
    "GLOSTER": "Gloster",
    "MG_CYBERSTER": "Cyberster",
    "MG_M9": "M9",
}

# MG fuel codes
FUEL_CODES = {
    "01": "Diesel",   # Gloster, Majestor
    "02": "Petrol",   # Astor, Hector
    "05": "Electric", # Comet/Windsor/ZS EV
    "03": "Petrol",
    "04": "CNG",
}


def _detect_fuel(fuel_cd, model_line, variant_desc):
    f = FUEL_CODES.get(str(fuel_cd), "")
    if f:
        return f
    # fallback naam se
    d = (model_line + " " + variant_desc).upper()
    if " EV" in d or "ELECTRIC" in d:
        return "Electric"
    if "DIESEL" in d:
        return "Diesel"
    return "Petrol"


def _clean_variant(desc, model_name):
    """'COMET EV EXCLUSIVE FC' -> 'Exclusive FC' (model naam hata ke, title-case)."""
    d = (desc or "").strip()
    # model ke words start se hata do
    mwords = model_name.upper().replace("-", " ").replace("EV", "").split()
    # bhi common prefixes hata do (COMET EV, ZS EV, HECTOR, ASTOR, HECTORPLUS7...)
    d = re.sub(r"(?i)^(MG\s+)?", "", d)
    dwords = d.split()
    # jo words model naam me hain, unhe start se hata (EV, COMET, HECTOR...)
    skip = set(w.upper() for w in model_name.replace("-", " ").split())
    skip |= {"EV", "COMET", "HECTOR", "ASTOR", "ZS", "WINDSOR", "GLOSTER",
             "MAJESTOR", "HECTORPLUS7", "HECTORPLUS6", "PLUS"}
    out_words = []
    started = False
    for w in dwords:
        if not started and w.upper() in skip:
            continue
        started = True
        out_words.append(w)
    result = " ".join(out_words).strip()
    if not result:
        result = d
    # title case (par MT/CVT/AT/EV/FC bade rakho)
    words = []
    for w in result.split():
        if w.upper() in ("MT", "CVT", "AT", "EV", "FC", "MT6", "6MT", "4X2", "4X4",
                         "7STR", "6STR", "7S", "6S", "VTI-TECH", "PRO"):
            words.append(w.upper())
        else:
            words.append(w.capitalize())
    return " ".join(words).strip()


def _parse_variants(data):
    results = []
    seen = set()
    if not isinstance(data, list):
        # kabhi {"data": [...]} ho
        data = data.get("data", []) if isinstance(data, dict) else []
    for m in data:
        model_line = m.get("model_line", "")
        model_name = MODEL_NAMES.get(model_line, model_line.replace("_", " ").title())
        for v in m.get("variants", []):
            desc = v.get("model_text1", "") or v.get("modelseries", "")
            # price: pricing[0].cities[0].price
            price = None
            pricing = v.get("pricing", [])
            if pricing and pricing[0].get("cities"):
                praw = pricing[0]["cities"][0].get("price", "")
                # "1006800.00 " -> decimal se pehle ka hissa (warna .00 jud ke galat)
                praw = str(praw).strip().split(".")[0]
                praw = re.sub(r"[^\d]", "", praw)
                if praw:
                    try:
                        price = int(praw)
                    except Exception:
                        price = None
            if not price or not (100000 < price < 30000000):
                continue
            variant = _clean_variant(desc, model_name)
            fuel = _detect_fuel(v.get("fuel_type"), model_line, desc)
            key = (model_name, variant, fuel)
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "model": model_name,
                "variant": variant,
                "fuel_type": fuel,
                "ex_showroom_price": price,
            })
    return results


def scrape_mg():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        try:
            page.goto(WARMUP_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            data = None
            for attempt in range(3):
                try:
                    result = page.evaluate(
                        """async (url) => {
                            const r = await fetch(url, {headers: {'Content-Type':'application/json'}});
                            return await r.text();
                        }""",
                        VARIANTS_API,
                    )
                    data = _json.loads(result)
                    if data:
                        break
                except Exception:
                    page.wait_for_timeout(2000)

            if data:
                all_results = _parse_variants(data)
                by_model = {}
                for r in all_results:
                    by_model.setdefault(r["model"], []).append(r)
                for mn, rows in by_model.items():
                    print(f"  [MG] {mn}: {len(rows)} variant(s)")
            else:
                print("  [MG] variants API nahi mila")
        except Exception as e:
            print(f"  [MG] failed: {str(e)[:60]}")
        finally:
            browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_mg()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)