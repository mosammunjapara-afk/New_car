"""
debug_hyundai4.py — Variant price API dhoondo (naye parameter: id, version)
============================================================================
getModels me har model ka id, code, version hai. Variant API ko in me se
kuch chahiye. Creta (id=37, code=FH, version=34) pe kai combinations try karte hain.
Aur getModels ke aas-paas ke endpoints bhi (getModel, getPriceList, etc.)
"""
from playwright.sync_api import sync_playwright
import json

# Creta ke identifiers
CID, CCODE, CVER = 37, "FH", 34

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    base = "https://api.hyundai.co.in/service/price"
    # bahut saare endpoint + param combinations
    candidates = [
        f"{base}/getVariants?loc=IN&lan=en&modelId={CID}",
        f"{base}/getVariants?loc=IN&lan=en&id={CID}",
        f"{base}/getVariants?loc=IN&lan=en&modelId={CID}&version={CVER}",
        f"{base}/getVariant?loc=IN&lan=en&modelId={CID}&version={CVER}",
        f"{base}/getModelVariant?loc=IN&lan=en&modelId={CID}",
        f"{base}/getPriceList?loc=IN&lan=en&modelId={CID}",
        f"{base}/getPrice?loc=IN&lan=en&modelId={CID}&version={CVER}",
        f"{base}/getModel?loc=IN&lan=en&modelId={CID}&version={CVER}",
        f"{base}/getModelDetails?loc=IN&lan=en&modelId={CID}",
        f"{base}/getVariantList?loc=IN&lan=en&modelId={CID}",
        f"{base}/getModelPrice?loc=IN&lan=en&modelCode={CCODE}&version={CVER}",
        f"{base}/getGrades?loc=IN&lan=en&modelId={CID}",
    ]

    found = []
    for c in candidates:
        try:
            page.goto(c, timeout=25000)
            b = page.inner_text("body").strip()
            # "Hello There" ya error = galat. JSON array/object = sahi
            if b.startswith(("[", "{")) and "hello" not in b.lower() and len(b) > 60:
                short = c.split("/price/")[1]
                print(f"  ✓✓ MILA: {short}")
                print(f"      preview: {b[:250]}")
                found.append((c, b))
            else:
                short = c.split("/price/")[1][:45]
                print(f"  ✗ {short} -> {b[:35]}")
        except Exception as e:
            print(f"  ✗ error: {str(e)[:40]}")

    if found:
        with open("hyundai_variants.json", "w", encoding="utf-8") as f:
            f.write(found[0][1])
        print(f"\n✓ Saved: hyundai_variants.json")

    browser.close()
    print("\nDONE.")
    if not found:
        print("Koi variant API nahi mila. Hyundai ka price page network")
        print("dekhna padega — batao aap Chrome me Creta price kaha dekhte ho.")