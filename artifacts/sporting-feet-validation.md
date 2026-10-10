# Sporting Feet real-catalog validation

## Selection, access, and feasibility

- **Retailer:** [Sporting Feet](https://www.sporting-feet.com/), an independent footwear storefront.
- **Access method:** Its published [UCP discovery document](https://www.sporting-feet.com/.well-known/ucp) advertises `search_catalog` and product lookup. The selected source is the public MCP endpoint `https://sporting-feet.myshopify.com/api/ucp/mcp`. The API returned HTTP 200 without credentials during validation. The adapter uses `search_catalog` only; cart, checkout, payment, and buyer-data tools are not called.
- **Permission basis:** The retailer's [robots.txt](https://www.sporting-feet.com/robots.txt) says public storefront pages are crawlable and directs agents to UCP/MCP for catalog interactions. Its [agent instructions](https://www.sporting-feet.com/agents.md) say read-only browsing needs no authentication and document catalog access. The [terms of service](https://www.sporting-feet.com/policies/terms-of-service) contain no stated restriction on catalog browsing or automated access; their commercial-use clause concerns products bought from the store. This is a narrow permission assessment based on the retailer's published instructions and observed API access, not legal advice or permission to transact.
- **Fields returned:** Product ID, title, URL, description HTML, GBP price range, size option labels, variant prices and sale availability, and product/variant media previews.
- **Gaps:** Search results are not collection listings and are not sales ranks. The endpoint defaults to sale-ready products, which may omit fully unavailable products. Variant pagination completeness is not stated, so variant counts and size runs describe returned variants only. Collection position, sales rank, review count, inventory history/age, and exact gallery image count are not available from this response. A sale-availability boolean does not report stock quantity.
- **Feasibility:** Sufficient to evaluate variant-level size patterns and observed prices/descriptions on returned items, but not to validate sales- or inventory-based claims.

## Collection result

On 2026-10-10, the CLI queried `trainers` for the UK/GBP context and collected five products in one bounded search page. Dataset timestamp: `2026-10-10T05:47:40.201899+00:00`. The API reported more matching results, so this is an incomplete sample. The JSON records each product's observed timestamp, product page URL, and source endpoint.

| Product | Price observed (GBP) | Original price | Returned variants available / unavailable | Size option |
|---|---:|---:|---:|---|
| Brooks Divide 6 GTX, Women's | 120.00 | Unknown | 5 / 5 | Size |
| Brooks Adrenaline GTS 25, Women's | 145.00 | Unknown | 9 / 1 | Size |
| Brooks Cascadia 19, Women's | 115.00 | 135.00 | 2 / 8 | Size |
| FitFlop RTG Leather/Suede Sneakers E4R | 90.00 | Unknown | 4 / 6 | Size |
| adidas Tensaur Cross Trainer, Junior | 35.00 | Unknown | 2 / 3 | Size |

Unknown original prices were not converted from a source zero or missing value. For Cascadia, current price was 115 GBP and original/list price 135 GBP: a 14.8% observed reduction. No sample crosses the configured 40% heavy-discount threshold.

## Analyzer evaluation

All five existing analyzers were run on all five normalized products using the existing default configuration. No analyzer thresholds or domain models were changed.

| Analyzer | Result on this sample | Interpretation |
|---|---|---|
| Best-selling product with unavailable variants | 5 insufficient-evidence findings; 0 positive findings | Variant availability is observed, but sales rank and its source are unknown for every product. Unavailable variants are supporting stock evidence only; no best-seller or lost-sales claim is made. |
| Broken size run | 0 findings | Each product has an explicit `Size` option and numeric labels among returned variants. None matched the existing sparse-at-endpoints heuristic. Variant pagination completeness is not stated, and the expected assortment is not known, so the result cannot establish complete size runs. |
| Prominent unavailable product | 0 findings | Search order is not collection order. Collection position is unknown for every product, so prominence cannot be evaluated. |
| Thin product page | 0 findings | Descriptions were observed as present for all five products. Exact image counts and review counts are unknown; unknowns were not treated as zero or as defects. |
| Heavy discount / possible overstock | 5 findings, all insufficient evidence; 0 positive findings | Four products have no observed original price. Cascadia's 14.8% reduction is below the configured 40% threshold. Inventory age/history is absent for all five, so no overstock claim is supported. |

All displayed scores are ordinal heuristic priorities, not probabilities. Findings cannot establish actual demand, conversion, shopper intent, lost sales, inventory age, or overstock.

## Manual page comparison

Independently fetched the five product pages over HTTPS (HTTP 200) and compared their visible page titles and embedded product price with the UCP records. All five titles matched the product identity and all five page prices matched the UCP current price:

| Product | Product page title observed | Page price | UCP price | Match |
|---|---|---:|---:|---|
| Brooks Divide 6 GTX, Women's | Brooks Divide 6 GTX, Women's | £120.00 | £120.00 | Yes |
| Brooks Adrenaline GTS 25, Women's | Brooks Adrenaline GTS 25, Women's | £145.00 | £145.00 | Yes |
| Brooks Cascadia 19, Women's | Brooks Cascadia 19, Women's | £115.00 | £115.00 | Yes |
| FitFlop RTG Leather/Suede Sneakers E4R | FitFlop RTG Leather/Suede Sneakers E4R | £90.00 | £90.00 | Yes |
| adidas Tensaur Cross Trainer, Junior | adidas Tensaur Cross Trainer, Junior | £35.00 | £35.00 | Yes |

The page check validates title and current price only. It does not validate sales rank, collection ordering, review count, stock quantity, image completeness, or historical pricing. Variant status was taken from the retailer's documented catalog response and not reconstructed from page behavior; variant list completeness is not established.

## Commands and test result

Reproduce the real collection (network required):

```bash
beacon-collect-sporting-feet 'https://www.sporting-feet.com/' --query trainers --max-products 5 \
  --json-out artifacts/sporting-feet-trainers.json \
  --report-out artifacts/sporting-feet-trainers.md
```

Run the offline test suite:

```bash
pytest -q
```

Actual validation result: **85 passed in 0.08s** on Python 3.12.14. The test suite uses saved fixture responses and does not require network access. The existing synthetic demo was not modified or used to fabricate this real-store sample.

## Remaining blockers

- No merchant sales/rank feed: the best-seller analyzer remains evidence-limited.
- No collection-order request through this selected UCP search: the prominent-position analyzer cannot be evaluated.
- No verified inventory history: heavy discounting cannot establish overstock.
- Review count and exact image count are unavailable, limiting thin-page coverage.
- Search may omit products that are entirely unavailable and returned only the first five of more matching products.
