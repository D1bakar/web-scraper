# How to Compare Prices

**Extract the web. Instantly.** — This guide walks through Web Scraper Pro's **Price Compare** mode: compare product prices across up to 50 websites in a single job.

---

## What You Get

- A **sorted comparison table** (lowest price first when numeric)
- **CSV import** for bulk URL lists
- **Smart selector hints** — heuristic CSS suggestions, no API key needed
- **Animated bar chart** in the dashboard
- **Export** as JSON, CSV, or Excel

---

## Step 1 — Launch the Dashboard

```powershell
cd web-scraper
.\start.bat
```

Open **http://127.0.0.1:8000** → select **💰 Price Compare** from the mode grid.

---

## Step 2 — Add Product URLs

Paste one product page URL per line:

```
https://store-a.com/product/iphone-16
https://store-b.com/iphone-16-pro
https://store-c.com/apple-iphone-16
```

**Tips:**
- Use the **Try example** button for a safe demo on books.toscrape.com
- **Import CSV** — first column should contain URLs (header row optional)
- Maximum **50 URLs** per job

---

## Step 3 — Set the Price Selector

Enter the CSS selector that targets the price element on each page.

| Example selector | When to use |
|------------------|-------------|
| `.price_color` | books.toscrape.com demo |
| `.price` | Common class name |
| `[itemprop="price"]` | schema.org markup |
| `#product-price` | ID-based pricing |

**Smart hints:** Click **✨ Smart hints** after entering a URL — the engine analyzes the page and suggests selectors with confidence scores.

**How to find a selector manually:**
1. Right-click the price on the product page
2. Choose **Inspect**
3. Copy the class or attribute (e.g. `.product-price`)

---

## Step 4 — Run the Comparison

Click **Compare Prices** (or press `Ctrl+Enter`).

Watch the **Live Status** panel for progress. When complete:
- Results table sorted by price
- **Bar chart** showing relative prices
- **Share** or **Copy** buttons for your findings

---

## Step 5 — Export Results

Use the export buttons above the results table:

| Format | Best for |
|--------|----------|
| **JSON** | Pipelines and APIs |
| **CSV** | Spreadsheets |
| **Excel** | Reports and sharing |

Or call the API directly:

```bash
curl "http://localhost:8000/api/jobs/{job_id}/export?format=csv"
```

---

## API Example

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "price_compare",
    "urls": [
      "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
      "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"
    ],
    "price_selector": ".price_color",
    "product_label": "Demo books"
  }'
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty prices | Verify CSS selector — use Smart hints |
| `ROBOTS_BLOCKED` | Disable robots check in Settings, or use demo URLs |
| Some sites fail | Normal for protected sites — check `status` and `error` columns |
| Rate limited (429) | Increase delay in Settings |

---

## Ethics

Always check **robots.txt** and Terms of Service. Use polite delays. Web Scraper Pro enforces robots.txt by default — that's a feature, not a bug.

---

**Next:** [WHY_DIFFERENT.md](WHY_DIFFERENT.md) · [DEPLOYMENT.md](DEPLOYMENT.md) · [README](../README.md)
