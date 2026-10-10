# Beacon merchant intelligence report

> Source: Sporting Feet public catalog (UCP MCP read-only search_catalog).
> Requested URL: https://www.sporting-feet.com/
> API endpoint: https://sporting-feet.myshopify.com/api/ucp/mcp
> Search query: trainers (result order is not sales rank or collection position).
> Scope: storefront product sample; collected 5 product(s), maximum 5.
> Observed at: 2026-10-10T05:47:40.201899+00:00

## Collection warnings
- Real, public Sporting Feet catalog data; read-only UCP search. No cart or checkout operation was used.
- Search result order is not sales rank or collection position; those values remain unknown.
- UCP catalog search defaults to sale-ready products and may omit wholly unavailable products.
- Review count, inventory history/age, and exact product image count are not exposed by this search response.
- Variant availability is the source's sale-ready boolean, not units on hand or guaranteed fulfillment.
- The search response does not expose variant pagination completeness; counts and size runs cover returned variants only.
- A single observed discount is a review prompt and does not establish overstock.
- More matching products exist; only the first bounded page of 5 was collected.
- Brooks Divide 6 GTX, Women's media are previews; exact product image count remains unknown.
- Brooks Adrenaline GTS 25, Women's media are previews; exact product image count remains unknown.
- Brooks Cascadia 19, Women's media are previews; exact product image count remains unknown.
- FitFlop RTG Leather/Suede Sneakers E4R media are previews; exact product image count remains unknown.
- adidas Tensaur Cross Trainer, Junior media are previews; exact product image count remains unknown.

## Analyzer findings
## Brooks Adrenaline GTS 25, Women's — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Valid current and original prices were not both observed; discount level cannot be assessed.
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.
- Recommended action: Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.

## Brooks Cascadia 19, Women's — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Observed price reduction: 14.8% (below the configured 40.0% heavy-discount threshold).
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: The observed price does not cross the heavy-discount threshold, and overstock cannot be assessed without verified inventory history.
- Recommended action: Obtain inventory age/history before assessing overstock; do not treat price alone as evidence of excess stock.

## Brooks Divide 6 GTX, Women's — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Valid current and original prices were not both observed; discount level cannot be assessed.
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.
- Recommended action: Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.

## FitFlop RTG Leather/Suede Sneakers E4R — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Valid current and original prices were not both observed; discount level cannot be assessed.
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.
- Recommended action: Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.

## adidas Tensaur Cross Trainer, Junior — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Valid current and original prices were not both observed; discount level cannot be assessed.
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.
- Recommended action: Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.

## Brooks Adrenaline GTS 25, Women's — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
  - Observed unavailable variants: 9.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.

## Brooks Cascadia 19, Women's — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
  - Observed unavailable variants: 4.5, 6, 6.5, 7, 7.5, 8, 8.5, 9.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.

## Brooks Divide 6 GTX, Women's — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
  - Observed unavailable variants: 4.5, 5, 7.5, 8.5, 9.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.

## FitFlop RTG Leather/Suede Sneakers E4R — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
  - Observed unavailable variants: 4.5, 5.5, 7.5, 8, 8.5, 9.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.

## adidas Tensaur Cross Trainer, Junior — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
  - Observed unavailable variants: 11, 1, 2.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.
