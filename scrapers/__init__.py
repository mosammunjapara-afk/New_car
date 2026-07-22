"""
scrapers/__init__.py — Central scraper registry
=================================================

Har brand ka apna scraper file hai (scrapers/brands/). Yahan unhe register
karte hain. ACTIVE_SCRAPERS me jo brand hai, wahi sync ke time chalega.

Naya brand add karne ke liye:
  1. scrapers/brands/yourbrand.py banao (maruti.py copy karke)
  2. Neeche import karo aur ACTIVE_SCRAPERS me add karo
  3. Test karo, phir hi live karo
"""

from scrapers.brands.maruti import scrape_maruti
from scrapers.brands.nexa import scrape_nexa
from scrapers.brands.tata import scrape_tata
from scrapers.brands.hyundai import scrape_hyundai
from scrapers.brands.kia import scrape_kia
from scrapers.brands.mahindra import scrape_mahindra
from scrapers.brands.toyota import scrape_toyota
from scrapers.brands.honda import scrape_honda
from scrapers.brands.volkswagen import scrape_volkswagen
from scrapers.brands.mg import scrape_mg
from scrapers.brands.renault import scrape_renault
from scrapers.brands.citroen import scrape_citroen
from scrapers.brands.jeep import scrape_jeep
from scrapers.brands.mercedes import scrape_mercedes
from scrapers.brands.bmw import scrape_bmw
from scrapers.brands.lexus import scrape_lexus
from scrapers.brands.landrover import scrape_landrover
from scrapers.brands.jaguar import scrape_jaguar
from scrapers.brands.cardekho_source import scrape_from_cardekho


def scrape_maruti_full():
    """Maruti ka poora data = Arena + Nexa dono. Dono ek 'Maruti Suzuki' brand ke neeche."""
    results = []
    results.extend(scrape_maruti())   # Arena: Swift, WagonR, Dzire...
    results.extend(scrape_nexa())     # Nexa: Baleno, Fronx, Grand Vitara...
    return results


# Sirf ye brands sync ke time chalenge:
def scrape_mahindra_full():
    """Mahindra: official XUV700 (auto configurator) + naye models CarDekho se."""
    rows = []
    try:
        rows.extend(scrape_mahindra())  # XUV700 official
    except Exception as e:
        print(f"  [Mahindra] official fail: {str(e)[:40]}")
    try:
        rows.extend(scrape_from_cardekho("Mahindra"))  # Thar/Scorpio/XUV3XO/etc
    except Exception as e:
        print(f"  [Mahindra] cardekho fail: {str(e)[:40]}")
    # dedup (model, variant, fuel) lowest price
    best = {}
    for r in rows:
        k = (r["model"], r["variant"], r["fuel_type"])
        if k not in best or r["ex_showroom_price"] < best[k]["ex_showroom_price"]:
            best[k] = r
    return list(best.values())


def scrape_audi():
    return scrape_from_cardekho("Audi")


def scrape_volvo():
    return scrape_from_cardekho("Volvo")


def scrape_skoda():
    return scrape_from_cardekho("Skoda")


ACTIVE_SCRAPERS = {
    "Maruti Suzuki": scrape_maruti_full,   # Arena + Nexa dono
    "Tata Motors": scrape_tata,            # Nexon, Punch, Harrier, Safari...
    "Hyundai": scrape_hyundai,             # Creta, Venue, i20, Verna, Exter...
    "Kia": scrape_kia,                     # Seltos, Sonet, Carens, Syros...
    "Mahindra": scrape_mahindra_full,      # XUV700 official + Thar/Scorpio/XUV3XO (CarDekho)
    "Toyota": scrape_toyota,               # Glanza, Fortuner, Innova, Hyryder...
    "Honda": scrape_honda,                 # City, Amaze, Elevate, ZR-V, Amaze 2G
    "Volkswagen": scrape_volkswagen,       # Taigun, Virtus, Tiguan, Golf GTI
    "MG": scrape_mg,                       # Hector, Astor, ZS EV, Comet EV, Gloster...
    "Renault": scrape_renault,             # Kwid, Kiger, Triber, Duster
    "Citroen": scrape_citroen,             # C3, C3 Aircross, Basalt, e-C3, C5 Aircross
    "Jeep": scrape_jeep,                    # Compass, Meridian, Wrangler, Grand Cherokee
    "Mercedes-Benz": scrape_mercedes,       # C/E/S-Class, GLA/GLC/GLE, EQ, Maybach, AMG (starting prices)
    "BMW": scrape_bmw,                      # 2/3/5/7 Series, X1/X3/X5/X7, i-series (starting prices)
    "Lexus": scrape_lexus,                  # ES, NX, RX, LX, LM (variant-wise)
    "Land Rover": scrape_landrover,         # Range Rover, Sport, Velar, Evoque, Defender, Discovery (PDF)
    "Jaguar": scrape_jaguar,                # F-PACE (PDF)
    "Audi": scrape_audi,                    # A4/A6/Q3/Q5/Q7/Q8/e-tron (CarDekho, auto)
    "Volvo": scrape_volvo,                  # XC40/XC60/XC90/S90/C40 (CarDekho, auto)
    "Skoda": scrape_skoda,                  # Kushaq/Slavia/Kodiaq/Kylaq (CarDekho, auto)
}