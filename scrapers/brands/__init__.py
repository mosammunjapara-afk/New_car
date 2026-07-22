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


def scrape_maruti_full():
    """Maruti ka poora data = Arena + Nexa dono. Dono ek 'Maruti Suzuki' brand ke neeche."""
    results = []
    results.extend(scrape_maruti())   # Arena: Swift, WagonR, Dzire...
    results.extend(scrape_nexa())     # Nexa: Baleno, Fronx, Grand Vitara...
    return results


# Sirf ye brands sync ke time chalenge:
ACTIVE_SCRAPERS = {
    "Maruti Suzuki": scrape_maruti_full,   # Arena + Nexa dono
    "Tata Motors": scrape_tata,            # Nexon, Punch, Harrier, Safari...
    "Hyundai": scrape_hyundai,             # Creta, Venue, i20, Verna, Exter...
    "Kia": scrape_kia,                     # Seltos, Sonet, Carens, Syros...
    "Mahindra": scrape_mahindra,           # XUV700 (auto). Naye models alag system se.
    "Toyota": scrape_toyota,               # Glanza, Fortuner, Innova, Hyryder...
    "Honda": scrape_honda,                 # City, Amaze, Elevate, ZR-V, Amaze 2G
    "Volkswagen": scrape_volkswagen,       # Taigun, Virtus, Tiguan, Golf GTI
    "MG": scrape_mg,                       # Hector, Astor, ZS EV, Comet EV, Gloster...
    "Renault": scrape_renault,             # Kwid, Kiger, Triber, Duster
    "Citroen": scrape_citroen,             # C3, C3 Aircross, Basalt, e-C3, C5 Aircross
    "Jeep": scrape_jeep,                    # Compass, Meridian, Wrangler, Grand Cherokee
}