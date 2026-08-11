# How to Compare Product Prices (e.g. iPhone)

This guide walks you through comparing prices across multiple websites using **Price Compare** mode in Web Scraper Pro.

---

## What Price Compare does

1. You paste product page URLs (one store listing per line).
2. You tell the tool which CSS selector holds the price on those pages.
3. It fetches each page politely, reads the price, and shows a comparison table sorted by price.

**MVP limit:** up to **50 URLs per run**. For hundreds or thousands of sites, run multiple batches and combine exports in Excel or Google Sheets.

---

## Step-by-step: compare iPhone prices

### 1. Open the dashboard

Start the app (`.\start.ps1` on Windows) and open **http://127.0.0.1:8000**.

### 2. Choose **Price Compare**

It is the first option under **What do you want to do?**

### 3. Paste product page URLs

One URL per line — each should be a **product detail page**, not a search results page.

Example:

```
https://store-a.example.com/iphone-16-pro-256gb
https://store-b.example.com/products/iphone-16-pro
https://store-c.example.com/phones/apple-iphone-16-pro
```

**Tip:** Click **Load example** first to try the built-in demo (books.toscrape.com practice site).

### 4. Set the price CSS selector

On any product page:

1. **Right-click** the price → **Inspect**
2. Find the HTML element that wraps the price (often a `<span>` with a class like `price` or `product-price`)
3. Copy the class as a CSS selector, e.g. `.price` or `[itemprop="price"]`

Paste that into **Step 2 — CSS selector for the price**.

Leave it blank to let the tool try common selectors (`.price`, `[itemprop="price"]`, `.a-price`, etc.).

### 5. Click **Compare Prices**

Results appear in a table:

| Website | Price | Status | Link |
|---------|-------|--------|------|
| store-a.example.com | $999.00 | OK | Open |
| store-b.example.com | $1,049.00 | OK | Open |

Rows with a parseable number are sorted **lowest first**.

### 6. Export for larger comparisons

- Click **CSV** or **Excel** to download results.
- Run another batch of up to 50 URLs.
- Paste all CSV files into one spreadsheet to compare 1000+ listings over time.

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| **Blocked by robots.txt** | Some retailers disallow scraping. Open **Settings** and uncheck robots check only if you are allowed to scrape that site. |
| **No price found** | Wrong CSS selector — inspect the page again. Try a simpler selector like `.price`. |
| **HTTP 403** | The site blocks automated requests. Try another retailer or use their official API. |
| **Need 1000+ sites** | Run 20 batches of 50 URLs, export each run, merge in Excel. |

---

## Responsible use

- Check each site's **Terms of Service** and **robots.txt** before scraping.
- Use reasonable delays (default: 1 second between requests).
- Do not scrape login-only or paywalled prices without permission.

---

## API (optional)

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

Poll `GET /api/jobs/{job_id}` until `status` is `completed`, then fetch `GET /api/jobs/{job_id}/results`.
