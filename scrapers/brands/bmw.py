"""
scrapers/brands/bmw.py — BMW India scraper
===========================================

BMW all-models page pe har model ka naam + fuel + starting price hai:
  "SUV New iX1 LWB Models Electric From ₹5,240,000"
  "SUV X1 Models Petrol From ₹5,090,000"

Ye page ke rendered blocks se model + fuel + price nikaalta hai.
NOTE: Model-level starting price (variant-wise nahi — BMW variant configurator
me hai). Luxury ke liye official starting-price acceptable.
"""

import re
from playwright.sync_api import sync_playwright

URL = "https://www.bmw.in/en/all-models.html"

# body-type prefixes jo model naam se hata dena hai
BODY_PREFIX = ["SUV", "SAV", "Sedan", "Cabrio", "Coupe", "Coupé", "Touring",
               "Gran Coupe", "Gran Coupé", "New", "SAC"]


def _clean_model(raw):
    """
    'SUV New iX1 LWB Models Electric From ...' -> 'iX1 LWB'
    Block se model naam nikaalo: body-prefix + 'Models/Model/Electric/...' hata ke.
    """
    s = raw
    # "From ₹..." ke pehle ka hissa
    s = re.split(r"(Models?|Model)\s+(Electric|Petrol|Hybrid|Diesel)", s)[0]
    # body prefixes hata
    words = s.split()
    out = []
    for w in words:
        if w in BODY_PREFIX:
            continue
        out.append(w)
    name = " ".join(out).strip()
    # "New" bacha ho to hata
    name = re.sub(r"^\s*New\s+", "", name).strip()
    return name


def scrape_bmw():
    all_results = []
    best = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page.set_default_timeout(40000)
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(6000)
            for _ in range(12):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(500)
            page.wait_for_timeout(3000)

            # body-lines approach: model | ... | fuel | From ₹price
            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            for i, l in enumerate(lines):
                m = re.search(r"From\s*₹\s*([\d,]+)", l)
                if not m:
                    continue
                price = int(re.sub(r"[^\d]", "", m.group(1)))
                if not (2000000 < price < 100000000):
                    continue
                # fuel: isi ya upar wali line
                fuel = "Petrol"
                ctx = " ".join(lines[max(0, i-3):i+1])
                if "Electric" in ctx:
                    fuel = "Electric"
                elif "Hybrid" in ctx:
                    fuel = "Hybrid"
                elif "Diesel" in ctx:
                    fuel = "Diesel"
                # model naam: upar wali lines me (fuel/Models/From nahi)
                model = None
                body_only = {"SUV", "SAV", "Sedan", "Cabrio", "Coupe", "Coupé",
                             "Touring", "New", "Gran", "SAC", "Models", "Model"}
                for j in range(i, max(-1, i-6), -1):
                    cand = lines[j].strip()
                    if not cand:
                        continue
                    if re.search(r"(From|₹|Models?|Electric|Petrol|Hybrid|Diesel)", cand):
                        continue
                    # body-type-only naam skip karo (asli model naam dhoondo)
                    if cand in body_only:
                        continue
                    model = cand
                    break
                if not model:
                    continue
                # clean
                model = re.sub(r"^(SUV|SAV|Sedan|Cabrio|Coupe|Coupé|Touring|New)\s+", "", model).strip()
                if len(model) < 1 or len(model) > 30:
                    continue
                key = (model, fuel)
                # same model+fuel ke multiple price — sabse kam (starting) rakho
                if key in best and price >= best[key]["ex_showroom_price"]:
                    continue
                best[key] = {
                    "model": model,
                    "variant": "Base",
                    "fuel_type": fuel,
                    "ex_showroom_price": price,
                }
            all_results = list(best.values())
            print(f"  [BMW] {len(all_results)} models (starting prices)")
        except Exception as e:
            print(f"  [BMW] failed: {str(e)[:60]}")
        finally:
            browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_bmw()
    print(f"\nTOTAL: {len(cars)}")
    for c in cars:
        print(c)