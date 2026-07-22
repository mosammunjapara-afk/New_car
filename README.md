# CarYanams Price API — Python Version (Hinglish Guide)

Ye aapki apni New Car Price API hai — **poori Python me** (FastAPI se banayi).
Bilkul Surepass/UBV/DRAM jaisi: customer ko sirf ek API key deni hoti hai,
aur wo apni key se price le sakta hai.

3 kaam karti hai:
1. **Scraper** — manufacturer website se new car prices leta hai
2. **Auto price-change** — price badle to khud detect karke DB update + history save
3. **API key system** — customers ko bechne ke liye (key banao, quota lago)

---

## Kya chahiye

- **Python 3.9+** — https://python.org se install karo
- Bas. Database SQLite hai (ek file), alag se kuch install nahi karna.

---

## Setup (pehli baar — 3 min)

Terminal kholo, is folder me jao:

```bash
cd caryanams-py
pip install -r requirements.txt
```

`.env` (ya environment variable) me apna admin secret set karo. Windows PowerShell:

```powershell
$env:ADMIN_SECRET = "koi_lamba_random_secret_12345"
```

Mac/Linux:

```bash
export ADMIN_SECRET="koi_lamba_random_secret_12345"
```

---

## Server chalu karo

```bash
uvicorn main:app --port 4000
```

Dikhega: `Uvicorn running on http://127.0.0.1:4000`

**Bonus:** browser me `http://localhost:4000/docs` kholo — FastAPI khud ek
interactive API documentation deta hai jahan aap har endpoint click karke test
kar sakte ho. (Ye Surepass ke docs jaisa hi hai — customers ko dene layak.)

---

## Prices update karo (doosra terminal)

```bash
curl -X POST "http://localhost:4000/admin/trigger-sync" -H "X-Admin-Secret: AAPKA_SECRET"
```

Saari cars dekho:
```bash
curl "http://localhost:4000/admin/cars" -H "X-Admin-Secret: AAPKA_SECRET"
```

---

## API KEY banana — customer ko bechne ke liye

```bash
curl -X POST "http://localhost:4000/admin/create-key" \
  -H "X-Admin-Secret: AAPKA_SECRET" \
  -H "Content-Type: application/json" \
  -d "{\"customer_name\":\"ABC Motors\",\"plan_calls_per_month\":5000}"
```

Response me `api_key` milega (`cyk_...`) — wo customer ko do. Bas.

Key band karni ho:
```bash
curl -X POST "http://localhost:4000/admin/revoke-key" \
  -H "X-Admin-Secret: AAPKA_SECRET" \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"cyk_xxxx\"}"
```

---

## Customer kaise use karega (sirf key se)

```bash
curl "http://localhost:4000/api/v1/new-car-price?brand=Maruti Suzuki&model=swift&variant=ZXi MT&state=Gujarat" \
  -H "X-API-Key: cyk_xxxx"
```

Response:
```json
{
  "brand": "Maruti Suzuki",
  "model": "swift",
  "variant": "ZXi MT",
  "ex_showroom_price": 799000,
  "on_road_price": 926840,
  "last_updated": "2026-07-14 11:27:58"
}
```

Baaki: `/api/v1/price-history` (price kab-kab badla), `/api/v1/usage` (quota).

---

## Test karo (Python)

Server chalu rakhte hue, doosre terminal me:
```bash
python test_client.py
```
Ye poora flow test karega: sync -> key banao -> price lo -> quota -> galat key.

---

## File structure

```
caryanams-py/
  main.py              <- API server (yahi chalate ho)
  database.py          <- tables + connection
  api_keys.py          <- key generate/verify/quota
  price_sync.py        <- auto price-change detection
  scrapers/
    __init__.py        <- kaunse brand active hain (registry)
    brands/
      maruti.py         <- Maruti scraper (abhi DEMO mode me)
  test_client.py       <- Python test
  requirements.txt
```

---

## Naya brand add karna

1. `scrapers/brands/maruti.py` copy karke naya file banao (jaise `toyota.py`)
2. Us brand ki website ke hisaab se URL/selector badlo
3. `scrapers/__init__.py` me import karke `ACTIVE_SCRAPERS` me add karo
4. `trigger-sync` chala ke test karo

Ek time pe ek brand. Verify hone ke baad hi live karo.

---

## Zaroori baatein

- **Abhi Maruti DEMO mode me hai** — `scrapers/brands/maruti.py` me `USE_DEMO = True`.
  Isse sample data aata hai (taaki system test ho sake). Live jaane ke liye
  `USE_DEMO = False` karo aur website structure verify karo.
- **On-road RTO rates** approximate hain (`database.py` me `state_tax`) — apne
  hisaab se exact daalo.
- **Sirf manufacturer ki official site** se scrape karo (CarDekho/CarWale se nahi).
- **Sell karne se pehle** 1-2 mahina prices ki accuracy khud check karo.
