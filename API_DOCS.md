# CarYanams Price API — Documentation

Real-time, variant-wise **ex-showroom car prices** for India. 21 brands, 1170+ variants, updated automatically from official manufacturer sources.

---

## Base URL

```
https://api.caryanams.com
```
(local testing: `http://localhost:8000`)

## Authentication

Har request me API key `X-API-Key` header me bhejein:

```
X-API-Key: your_api_key_here
```

Key ke bina ya galat key pe `401 Unauthorized` aayega. Monthly limit cross hone pe `429`.

---

## Endpoints

### 1. Get car price — `GET /api/v1/new-car-price`

Ek specific variant ka ex-showroom (aur optional on-road) price.

**Query params:**

| param | required | description |
|-------|----------|-------------|
| `brand` | yes | e.g. `Maruti Suzuki` |
| `model` | yes | e.g. `Swift` |
| `variant` | yes | e.g. `VXi` |
| `fuel_type` | no | `Petrol` / `Diesel` / `CNG` / `Electric` / `Hybrid` |
| `state` | no | on-road price ke liye, e.g. `Maharashtra` |

**Example:**
```bash
curl -H "X-API-Key: your_key" \
  "https://api.caryanams.com/api/v1/new-car-price?brand=Maruti%20Suzuki&model=Swift&variant=VXi"
```

**Response:**
```json
{
  "brand": "Maruti Suzuki",
  "model": "Swift",
  "variant": "VXi",
  "fuel_type": "Petrol",
  "ex_showroom_price": 699000,
  "last_updated": "2026-07-21T09:15:00"
}
```

---

### 2. List brands — `GET /api/v1/brands`

Saare available brands + car count.

```json
{ "brands": [{"brand": "Audi", "count": 13}, ...], "total_brands": 21 }
```

### 3. List models — `GET /api/v1/models?brand=Hyundai`

Ek brand ke saare models + variant count.

```json
{ "brand": "Hyundai", "models": [{"model": "Creta", "variants": 20}, ...] }
```

### 4. List variants — `GET /api/v1/variants?brand=Kia&model=Seltos`

Ek model ke saare variants + prices (ek call me poori list).

```json
{
  "brand": "Kia", "model": "Seltos",
  "variants": [
    {"variant": "HTE", "fuel_type": "Petrol", "ex_showroom_price": 1090000, "last_checked_at": "..."},
    ...
  ]
}
```

### 5. Price history — `GET /api/v1/price-history?brand=..&model=..&variant=..`

Us variant ke price changes ka log (kab kitna badla).

```json
{ "brand": "...", "model": "...", "variant": "...",
  "history": [{"old_price": 690000, "new_price": 699000, "changed_at": "..."}] }
```

### 6. Usage — `GET /api/v1/usage`

Aapke API key ka usage (calls used / limit).

---

## Covered Brands (21)

**Mass-market:** Maruti Suzuki, Nexa, Hyundai, Tata, Kia, Toyota, Honda, Mahindra, Volkswagen, MG, Renault, Citroen, Jeep, Skoda

**Luxury:** Mercedes-Benz, BMW, Audi, Volvo, Lexus, Land Rover, Jaguar

Data har roz automatically refresh hota hai — jab manufacturer price change kare, API me auto-update.

---

## Error Codes

| code | meaning |
|------|---------|
| `200` | Success |
| `401` | Missing/invalid API key |
| `404` | Car/brand/model not found |
| `429` | Monthly call limit reached |

---

## Pricing Tiers

| Tier | Calls/month | Price | Best for |
|------|-------------|-------|----------|
| **Free** | 500 | ₹0 | Testing, hobby |
| **Starter** | 10,000 | ₹2,999/mo | Small dealers, apps |
| **Business** | 100,000 | ₹9,999/mo | Portals, aggregators |
| **Enterprise** | Unlimited + SLA | Custom | Large platforms |

All tiers: all 21 brands, all endpoints, auto-updated data. Contact: sales@caryanams.com

---

## Quick Start

1. Sign up → get API key
2. Test: `GET /api/v1/brands` with your key
3. Fetch prices: `GET /api/v1/new-car-price?brand=..&model=..&variant=..`
4. Interactive docs: visit `/docs` (Swagger UI)