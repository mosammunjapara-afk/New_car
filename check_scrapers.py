"""
check_scrapers.py — dekho kaunse brands register hain
======================================================
Jeep sync me nahi aa raha. Ye check karta hai ki ACTIVE_SCRAPERS me kaunse
brands hain (aapki current __init__.py ke hisaab se).

CHALAO:
    python check_scrapers.py
"""

try:
    from scrapers import ACTIVE_SCRAPERS
    print("=" * 50)
    print("ACTIVE_SCRAPERS me ye brands hain:")
    print("=" * 50)
    for i, name in enumerate(ACTIVE_SCRAPERS.keys(), 1):
        print(f"  {i}. {name}")
    print()
    print(f"TOTAL: {len(ACTIVE_SCRAPERS)} brands")
    if "Jeep" in ACTIVE_SCRAPERS:
        print("\n✓ Jeep REGISTER hai")
    else:
        print("\n✗ Jeep NAHI hai — __init__.py purani hai, nayi replace karo!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()