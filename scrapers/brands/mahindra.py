"""
scrapers/brands/mahindra.py — Mahindra scraper (3D config data + price API)
============================================================================

Mahindra ek 3D configurator (Eccentric Engine) use karta hai. Data 2 jagah:
  1. modal-data.json — har model ke variants + unique_codes
     URL: .../Visualize360/{MODEL}/assets/one3d/assets/{MODEL}/modal-data.json
  2. Product-ShowQuickView?pid={unique_code} — us variant ka price
     price.list.value me asli ex-showroom price

Ye Mahindra ka sabse mushkil (3D + obfuscated) tha, par crack ho gaya.
Har model ka base-folder version-number alag ho sakta hai — isliye pehle
model page se base URL nikaalte hain.
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

# Model slug -> (page URL, 3D model code jo folder me hota hai)
# page se base folder nikaalenge, isliye sirf page URL + model code chahiye
MODELS = {
    # Ye model 3D "modal-data.json" system use karta hai — automatic kaam karta hai:
    "XUV700": {"page": "https://auto.mahindra.com/XUV700.html", "code": "XUV700", "name": "XUV700"},

    # Neeche wale naye models "server-side rendered" hain — inka content Playwright
    # ko nahi milta (13 tarike test kiye). Inke liye alag system (change-alert) banega.
    # Jab koi reliable tarika milega, uncomment kar denge:
    # "X3XO":  {"page": "https://auto.mahindra.com/suv/xuv3xo/X3XO.html", "code": "X3XO", "name": "XUV 3XO"},
    # "THRN":  {"page": "https://auto.mahindra.com/suv/thar/THRN.html", "code": "THRN", "name": "Thar"},
    # "TH5D":  {"page": "https://auto.mahindra.com/suv/thar-roxx/TH5D.html", "code": "TH5D", "name": "Thar Roxx"},
    # "SCN":   {"page": "https://auto.mahindra.com/suv/scorpio-n/SCN.html", "code": "SCN", "name": "Scorpio N"},
    # "SCRC":  {"page": "https://auto.mahindra.com/suv/scorpio-classic/SCRC.html", "code": "SCRC", "name": "Scorpio Classic"},
    # "BOL":   {"page": "https://auto.mahindra.com/suv/bolero/BOL.html", "code": "BOL", "name": "Bolero"},
    # "NEO":   {"page": "https://auto.mahindra.com/suv/bolero-neo/NEO.html", "code": "NEO", "name": "Bolero Neo"},
}

QUICKVIEW = ("https://auto.mahindra.com/on/demandware.store/"
             "Sites-amc-Site/en_IN/Product-ShowQuickView?pid=")


def _detect_fuel(v):
    f = (v.get("fuel_type") or "").lower()
    if "diesel" in f:
        return "Diesel"
    if "cng" in f:
        return "CNG"
    if "electric" in f or "ev" in f:
        return "Electric"
    return "Petrol"


def _find_modaldata_url(page, model_code):
    """Model page ke network se modal-data.json ka exact URL pakdo."""
    found = {"url": None}

    def on_response(resp):
        if "modal-data.json" in resp.url:
            found["url"] = resp.url

    page.on("response", on_response)
    try:
        page.goto(MODELS[model_code]["page"], timeout=90000)
    except Exception:
        pass
    # loading animation + data load hone do
    for _ in range(20):
        page.wait_for_timeout(2000)
        if found["url"]:
            break
    page.remove_listener("response", on_response)
    return found["url"]


def _get_price(page, unique_code):
    """Ek unique_code ka ex-showroom price (price.list.value)."""
    try:
        page.goto(QUICKVIEW + unique_code, timeout=25000)
        body = page.inner_text("body")
        data = _json.loads(body)
        pl = data.get("product", {}).get("price", {}).get("list", {})
        val = pl.get("value")
        if val:
            return int(re.sub(r"[^\d]", "", str(val)))
    except Exception:
        pass
    return None


def _scrape_one_model(page, model_code):
    info = MODELS[model_code]
    # 1. modal-data.json ka URL pakdo
    md_url = _find_modaldata_url(page, model_code)
    if not md_url:
        return []
    # 2. modal-data.json padho
    try:
        page.goto(md_url, timeout=30000)
        data = _json.loads(page.inner_text("body"))
    except Exception:
        return []

    variants = data.get("variants", [])
    results = []
    seen_labels = set()
    seen_names = set()
    for v in variants:
        uc = v.get("unique_codes", {})
        code = uc.get("1") or (list(uc.values())[0] if uc else None)
        if not code:
            continue
        # DEDUP asli identity pe: variant_label_code (MM931/MM963...) har
        # sub-variant ka unique hai. Isse same config ke alag packs alag rehte
        # hain aur ek doosre ko overwrite nahi karte (pehle 25 me se sirf 7
        # bachte the — naam collide ho jaate the).
        label = v.get("variant_label_code") or code
        if label in seen_labels:
            continue
        seen_labels.add(label)

        # variant naam banao — poora unique banane ke liye wheeldrive + pack bhi
        wd = (v.get("wheeldrive_type") or "").strip()      # FWD / AWD
        pack = (v.get("pack_type") or "").strip()          # luxury / ''
        parts = [v.get("variant_name", ""), v.get("fuel_type", ""),
                 v.get("transmission_type", ""), v.get("seat_type", "")]
        # AWD dikhao (FWD default hai, chhod dete hain taaki naam saaf rahe)
        if wd and wd.upper() != "FWD":
            parts.append(wd)
        if pack:
            parts.append(pack.title())  # "Luxury"
        variant_name = " ".join(str(p) for p in parts if p).strip()

        # agar phir bhi naam repeat ho (rare), to label-code laga do
        if variant_name in seen_names:
            variant_name = f"{variant_name} ({label})"
        seen_names.add(variant_name)

        # price
        price = _get_price(page, code)
        if price and 100000 < price < 10000000:
            results.append({
                "model": info["name"],
                "variant": variant_name,
                "fuel_type": _detect_fuel(v),
                "ex_showroom_price": price,
            })
    return results


def scrape_mahindra():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        for code in MODELS:
            try:
                res = _scrape_one_model(page, code)
                fuels = {}
                for r in res:
                    fuels[r["fuel_type"]] = fuels.get(r["fuel_type"], 0) + 1
                bd = ", ".join(f"{k}:{v}" for k, v in fuels.items())
                print(f"  [Mahindra] {MODELS[code]['name']}: {len(res)} variant(s)  [{bd}]")
                all_results.extend(res)
            except Exception as e:
                print(f"  [Mahindra] {MODELS[code]['name']} failed: {str(e)[:50]}")
        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_mahindra()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars[:40]:
        print(car)