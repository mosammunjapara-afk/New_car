"""
scrapers/brands/honda.py — Honda scraper (car page __NEXT_DATA__ se)
=====================================================================

Honda Next.js site hai. Har car ke price page ke __NEXT_DATA__ me poora
variant × fuel × transmission × price mapping hota hai — ek hi jagah, clean.

Structure (har car ke andar "priceCheck"/carModelData me):
  [
    {
      "resourceFuelType": "Petrol",
      "grade": [
        {"transType":"MT (Manual)","variants":["SV","V","ZX","ZX+"],
         "price":["1199900","1329900","1525900","1614900"]},
        {"transType":"CVT (Automatic)","variants":["V","ZX","ZX+"],
         "price":["1429900","1625900","1714900",null]}
      ]
    },
    {"resourceFuelType":"e:HEV", "grade":[...]}
  ]

Isliye getCarPrice POST karne ki zaroorat nahi — sab __NEXT_DATA__ me hai.
Hum har car page kholte hain, __NEXT_DATA__ nikaalte hain, aur "grade" blocks
parse karte hain.

Data: model, variant (grade + transmission), fuel_type, ex_showroom_price
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

# Honda ke car pages. check-price/<slug> page pe __NEXT_DATA__ me price data hota hai.
# (slug offer-cars + tech-specs se confirmed)
CAR_PAGES = {
    "City": "https://www.hondacarindia.com/check-price/honda-city",
    "Amaze": "https://www.hondacarindia.com/check-price/honda-amaze",
    "Amaze 2nd Gen": "https://www.hondacarindia.com/check-price/honda-amaze-2g",
    "Elevate": "https://www.hondacarindia.com/check-price/honda-elevate",
    "ZR-V": "https://www.hondacarindia.com/check-price/honda-zrv",
}


def _detect_fuel(fuel_raw):
    f = (fuel_raw or "").lower()
    if "diesel" in f:
        return "Diesel"
    if "cng" in f:
        return "CNG"
    if "electric" in f and "hybrid" not in f:
        return "Electric"
    # Honda: "e:HEV", "Electric Hybrid" -> Hybrid; baaki Petrol
    if "hev" in f or "hybrid" in f:
        return "Hybrid"
    return "Petrol"


def _extract_fuel_blocks(next_data_text):
    """
    __NEXT_DATA__ text me se saare 'resourceFuelType' wale blocks nikaalo.
    Har block ka 'grade' array balanced-brace se pakadte hain (nested-safe).
    """
    blocks = []
    for m in re.finditer(r'"resourceFuelType"\s*:\s*"([^"]+)"', next_data_text):
        fuel = m.group(1)
        # is block ke aage 'grade' array dhoondo
        gidx = next_data_text.find('"grade"', m.end())
        if gidx == -1:
            continue
        # '[' se shuru, balanced ']' tak
        start = next_data_text.find('[', gidx)
        if start == -1:
            continue
        depth = 0
        end = -1
        for i in range(start, min(len(next_data_text), start + 20000)):
            c = next_data_text[i]
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end == -1:
            continue
        grade_json = next_data_text[start:end]
        try:
            grades = _json.loads(grade_json)
        except Exception:
            continue
        blocks.append({"resourceFuelType": fuel, "grade": grades})
    return blocks


def _parse_blocks(fuel_blocks, model_name):
    out = []
    seen = set()
    for blk in fuel_blocks:
        fuel = _detect_fuel(blk.get("resourceFuelType", ""))
        for g in blk.get("grade", []):
            if not isinstance(g, dict):
                continue
            trans = (g.get("transType") or "").strip()
            variants = g.get("variants") or []
            prices = g.get("price") or []
            for i, vn in enumerate(variants):
                if not vn:
                    continue
                price = prices[i] if i < len(prices) else None
                if not price:
                    continue
                try:
                    price = int(re.sub(r"[^\d]", "", str(price)))
                except Exception:
                    continue
                if not (100000 < price < 30000000):
                    continue
                # variant label = grade + transmission (dedupe ke liye)
                label = vn.strip()
                if trans and trans.split()[0].lower() not in label.lower():
                    label = f"{label} {trans}"
                key = (model_name, label, fuel, price)
                if key in seen:
                    continue
                seen.add(key)
                out.append({
                    "model": model_name,
                    "variant": label,
                    "fuel_type": fuel,
                    "ex_showroom_price": price,
                })
    return out


def scrape_honda():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for model_name, url in CAR_PAGES.items():
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(5000)
                nd = page.evaluate(
                    "() => { const s=document.getElementById('__NEXT_DATA__');"
                    " return s ? s.textContent : ''; }"
                )
                if not nd:
                    print(f"  [Honda] {model_name}: __NEXT_DATA__ nahi mila")
                    continue

                blocks = _extract_fuel_blocks(nd)
                res = _parse_blocks(blocks, model_name)

                fuels = {}
                for r in res:
                    fuels[r["fuel_type"]] = fuels.get(r["fuel_type"], 0) + 1
                bd = ", ".join(f"{k}:{v}" for k, v in fuels.items())
                print(f"  [Honda] {model_name}: {len(res)} variant(s)  [{bd}]")
                all_results.extend(res)
            except Exception as e:
                print(f"  [Honda] {model_name} failed: {str(e)[:60]}")

        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_honda()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)