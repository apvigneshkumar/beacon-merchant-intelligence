# Beacon Merchant Intelligence

A deterministic Python prototype for the Beacon Product Builder assignment. The core analyzers run on synthetic records, Shopify's fictional `mock.shop` demo catalog, or a bounded read-only catalog sample from Sporting Feet. The retailer sample validates the pipeline against a real public storefront; it is not evidence of sales, demand, or inventory history.

The five independent analyzers identify: sales-ranked products with unavailable variants, sparse observed numeric size runs, prominent collection items with unavailable variants, product-page completeness signals, and heavy discounting as a prompt to investigate possible overstock. Every finding contains evidence and rationale. Scores are configurable heuristic priorities, not probabilities.

## Collector scope and limitations

- Only `mock.shop` and its subdomains are supported. This does not claim compatibility with arbitrary storefronts.
- mock.shop is a public, token-free Storefront API designed for storefront development and testing. Its catalogs are fictional, so analyzer results do not represent real merchant activity.
- mock.shop is an API source, not a hosted product-page demo. Its sample products can return `onlineStoreUrl: null`; in that case `Product.url` remains unknown. A product URL is recorded only if Shopify reports a same-host HTTPS URL.
- The collector sends one bounded GraphQL request per run and enforces at least one second between requests in a process. It accepts at most 10 products, requests up to 50 variants and 20 images per product, uses a 15-second timeout and 2 MB response cap, requires HTTPS, allowlists mock.shop hosts, and refuses redirects. It does not paginate or retry.
- Collection ordering is only a visibility proxy. The source does not supply sales rank, inventory history/age, shopper intent, lost sales, or review count; these fields remain unknown.
- Variant `availableForSale` means purchasable according to the source, not units on hand or guaranteed fulfillment. `Size` is identified only if Shopify reports an option with that name; numeric product options are not guessed to be sizes.
- The existing `Product` model has no currency field, so observed currency codes are preserved alongside each normalized product in the JSON output.
- Product samples can be incomplete. Truncated records and unavailable source fields are surfaced in warnings.
- Allbirds was evaluated as an initial candidate, but its current Terms of Use prohibit automated scripts and web crawlers. It is not used as a data source.
- This milestone has no LLM, autonomous agent, web UI, database, or deployment setup.

## Real retailer validation: Sporting Feet

Sporting Feet was selected for a small real-data validation. Its [robots.txt](https://www.sporting-feet.com/robots.txt) says public storefront pages are crawlable and directs agents to UCP/MCP for catalog interactions. Its [agent instructions](https://www.sporting-feet.com/agents.md) document read-only catalog access without authentication. Its [UCP discovery document](https://www.sporting-feet.com/.well-known/ucp) publishes the catalog tools. The [terms of service](https://www.sporting-feet.com/policies/terms-of-service) did not state a restriction on catalog browsing or automated access; the relevant commercial-use clause concerns purchased products. This adapter uses only `search_catalog`; it never invokes cart, checkout, or payment tools.

The source can provide product IDs, public product URLs, titles, descriptions, GBP price ranges, size options, and variant sale availability. Search ordering is not collection position or sales rank. UCP catalog search defaults to sale-ready products, so fully unavailable products may be absent. The response does not state whether variant enumeration is complete; variant counts and size runs therefore describe returned variants only. Review count, inventory age/history, and exact product image count are unknown. `Product` and analyzers remain unchanged; a source-specific adapter preserves those gaps as `None`.

```bash
beacon-collect-sporting-feet 'https://www.sporting-feet.com/' --query trainers --max-products 5 \
  --json-out artifacts/sporting-feet-trainers.json \
  --report-out artifacts/sporting-feet-trainers.md
```

The validated sample, analyzer report, and manual comparison are in `artifacts/sporting-feet-trainers.json`, `artifacts/sporting-feet-trainers.md`, and `artifacts/sporting-feet-validation.md`. This adapter supports only Sporting Feet's HTTPS storefront root, is capped at 10 results, uses the retailer's published UCP MCP endpoint, has a 15-second timeout, 2 MB response cap, one-second request pacing, and refuses redirects. It is retailer-specific, not a general Shopify or multi-retailer connector.

The size-run analyzer recognizes numeric labels only, compares the product's observed options, and cannot establish the expected range. The price and page signals are heuristic and need validation against merchant data before operational use.

## Assignment submission documents

- [Proposed natural-language query architecture, scale safeguards, and defensibility](docs/architecture-and-defensibility.md). It distinguishes the implemented prototype from the proposed 50,000-store architecture; no scale testing is claimed.
- [Product discovery and prioritization framework](docs/product-thinking.md). It is a proposed framework and does not claim completed merchant research.
- [AI-assisted workflow and reflection](docs/ai-workflow.md). Prompt themes are paraphrased; this is not a verbatim transcript or a public transcript link.
- [Real Sporting Feet sample dataset](artifacts/sporting-feet-trainers.json), [analyzer report](artifacts/sporting-feet-trainers.md), and [access, validation, and limitations report](artifacts/sporting-feet-validation.md).
- [Synthetic mock.shop dataset](artifacts/mock-shop-men.json) and [synthetic analyzer report](artifacts/mock-shop-men.md). These records are fictional demo data.

The real sample is a bounded observation, manually checked for product title and current price against five public product pages. It is not a benchmark or proof of sales, demand, lost sales, inventory history, or analyzer accuracy.

## Setup

Requires Python 3.10 or newer (Python 3.12 is supported).

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
```

## Synthetic demo

```bash
beacon-demo
# or: python -m beacon_merchant_intelligence.demo
```

The demo emits a Markdown report for synthetic examples and labels it as such.

## Collect a mock.shop sample

```bash
beacon-collect 'https://mock.shop/collections/men' --max-products 5 \
  --json-out artifacts/mock-shop-men.json \
  --report-out artifacts/mock-shop-men.md
```

The command accepts a storefront root such as `https://mock.shop/`, a store subdomain such as `https://coffee.mock.shop/`, or one collection URL such as `https://mock.shop/collections/men`. It rejects other hosts, non-HTTPS URLs, query strings, fragments, ports, unsupported paths, and sample limits above 10 products. The default output paths are `artifacts/collection.json` and `artifacts/report.md`.

The JSON dataset contains normalized `Product` fields, source URLs, observation timestamps, observed currency codes, and collection warnings. The Markdown report runs the existing five analyzers. Scores are described as heuristic priority scores, not probabilities. Fixture-based tests make no network requests.

## Tests

```bash
pytest
```

## Package layout

```text
src/beacon_merchant_intelligence/
  models.py                 # normalized domain types and findings
  config.py                 # analyzer thresholds and heuristic scores
  analyzers/                # five independent analyzers
  prioritization.py         # deterministic score ordering
  reporting.py              # synthetic and collected Markdown reports
  collector.py              # bounded mock.shop GraphQL collection and extraction
  normalization.py          # Shopify record to Product mapping
  sporting_feet.py          # bounded Sporting Feet read-only UCP client
  sporting_feet_normalization.py # UCP product record to Product mapping
  sporting_feet_cli.py      # Sporting Feet validation command
  cli.py                    # beacon-collect command and JSON serialization
  demo.py                   # synthetic-data demonstration
tests/
  data/                     # saved mock.shop and Sporting Feet UCP responses
  test_*.py                 # analyzer, collector, and reporting tests
```
