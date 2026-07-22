"""
debug_toyota_models.py — Toyota ke SAARE model IDs nikaalo (direct API ke liye)
================================================================================
Pata chala: Toyota variants API = webapi.tfsin.toyotabharat.com/1.0/api/cities/
null/models/{ID}/variants  (Fortuner ID=8).

Camry/Land Cruiser ke page pe API auto-fire nahi hota, par agar ID pata ho to
SEEDHA API call kar sakte hain (page kholne ki zaroorat nahi) — ye zyada reliable.

Ye script Toyota ki models-list API dhoondta hai (jisme har model ka id+naam ho),
aur har model ka /variants direct call karke variant-count dikhata hai.

CHALAO:
    python debug_toyota_models.py
Phir toyota_models.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

out = []
def log(s=""):
    print(s)
    out.append(str(s))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    models_data = {"list": None}
    def on_response(resp):
        u = resp.url
        if "toyotabharat" in u and "/models" in u and "/variants" not in u:
            try:
                models_data["list"] = resp.json()
                models_data["url"] = u
            except Exception:
                pass
    page.on("response", on_response)

    # homepage kholo (models list API load hota hai)
    log("Homepage khol rahe hain (models list API ke liye)...")
    try:
        page.goto("https://www.toyotabharat.com/", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(6000)
        for _ in range(6):
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(600)
        page.wait_for_timeout(3000)
    except Exception as e:
        log(f"  homepage fail: {str(e)[:50]}")

    # ek model page bhi kholo taaki models API pakka fire ho
    if not models_data["list"]:
        try:
            page.goto("https://www.toyotabharat.com/showroom/fortuner/index-fortuner.html",
                      wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(6000)
        except Exception:
            pass

    if models_data.get("list"):
        log(f"\n✓ models list API: {models_data.get('url','')[:90]}")
        data = models_data["list"]
        # structure samajho
        items = data if isinstance(data, list) else data.get("models", data.get("data", []))
        log(f"  total models: {len(items) if hasattr(items,'__len__') else '?'}")
        id_map = {}
        if isinstance(items, list):
            for m in items:
                if isinstance(m, dict):
                    mid = m.get("id") or m.get("modelId") or m.get("Id")
                    nm = m.get("name") or m.get("modelName") or m.get("Name") or ""
                    if mid:
                        id_map[nm] = mid
                        log(f"    id={mid}  {nm}")
        models_data["id_map"] = id_map
    else:
        log("\n  models list API nahi mila. Direct IDs try karenge (0-30).")

    # ---- har model ID ka /variants direct call ----
    log("\n=== Direct /variants call (browser context) ===")
    ids_to_try = list(models_data.get("id_map", {}).values()) or list(range(1, 31))
    base = "https://webapi.tfsin.toyotabharat.com/1.0/api/cities/null/models"
    id_to_name = {v: k for k, v in models_data.get("id_map", {}).items()}
    for mid in ids_to_try:
        try:
            r = page.evaluate("""async (url) => {
                try { const x = await fetch(url); const t = await x.text();
                    return {status:x.status, body:t.slice(0,1500)}; }
                catch(e){ return {status:-1, body:String(e)}; }
            }""", f"{base}/{mid}/variants")
            body = r.get("body", "")
            names = re.findall(r'"name"\s*:\s*"([^"]{2,40})"', body)
            prices = re.findall(r'"price"\s*:\s*(\d{6,8})', body)
            nm = id_to_name.get(mid, "")
            if names:
                log(f"  id={mid} {nm}: {len(names)} variants -> {names[:6]}")
        except Exception as e:
            log(f"  id={mid} err: {str(e)[:30]}")

    browser.close()

with open("toyota_models.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. toyota_models.txt UPLOAD kar do.")
print("=" * 60)