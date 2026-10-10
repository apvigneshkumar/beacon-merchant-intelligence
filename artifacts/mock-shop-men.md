# Beacon merchant intelligence report

> Source: Shopify mock.shop public demo Storefront API. Products are fictional demo data, not real merchant observations.
> Requested URL: https://mock.shop/collections/men
> API endpoint: https://mock.shop/api
> Collection: Men; collected 5 product(s), maximum 5.
> Observed at: 2026-10-10T05:25:16.586898+00:00

## Collection warnings
- mock.shop records are fictional demo data, not observations from a real merchant.
- Sales rank, inventory history, and review count are not exposed by this collector; those analyzer inputs remain unknown.
- Variant availability means available for sale, not units on hand or guaranteed fulfillment.
- One page is collected per run; collection/API ordering is only a visibility proxy and is not demand rank.
- The source has more products than this bounded sample (maximum 5); later products were not fetched.
- Hoodie has no verified public product-page URL in the source response.
- Men's T-shirt has no verified public product-page URL in the source response.
- Men's Crewneck has no verified public product-page URL in the source response.
- Sweatpants has no verified public product-page URL in the source response.
- Shorts has no verified public product-page URL in the source response.

## Analyzer findings
## Hoodie — prominent_collection_item_unavailable
- Assessment: `signal`
- Evidence sufficiency: `limited`
- Heuristic priority score: 70/100 (not a probability)
- Evidence:
  - Observed collection position: 1 (visibility proxy only).
  - Unavailable variants: Medium / Olive, Medium / Purple.
- Rationale: A high-visibility collection position co-occurs with unavailable variants; position does not establish demand.
- Recommended action: Check whether the collection ordering and availability are current, and consider surfacing available alternatives.

## Hoodie — broken_size_run
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Size option 'Size' was identified, but only 0 distinct numeric sizes were parsed; at least 5 are required.
  - The expected size range and category-specific size standards were not provided.
- Rationale: The size-run heuristic needs enough explicitly identified numeric size options to compare observed availability.
- Recommended action: Confirm the size option and expected assortment before evaluating a size-run gap.

## Men's Crewneck — broken_size_run
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Size option 'Size' was identified, but only 0 distinct numeric sizes were parsed; at least 5 are required.
  - The expected size range and category-specific size standards were not provided.
- Rationale: The size-run heuristic needs enough explicitly identified numeric size options to compare observed availability.
- Recommended action: Confirm the size option and expected assortment before evaluating a size-run gap.

## Men's T-shirt — broken_size_run
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Size option 'Size' was identified, but only 0 distinct numeric sizes were parsed; at least 5 are required.
  - The expected size range and category-specific size standards were not provided.
- Rationale: The size-run heuristic needs enough explicitly identified numeric size options to compare observed availability.
- Recommended action: Confirm the size option and expected assortment before evaluating a size-run gap.

## Shorts — broken_size_run
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Size option 'Size' was identified, but only 0 distinct numeric sizes were parsed; at least 5 are required.
  - The expected size range and category-specific size standards were not provided.
- Rationale: The size-run heuristic needs enough explicitly identified numeric size options to compare observed availability.
- Recommended action: Confirm the size option and expected assortment before evaluating a size-run gap.

## Sweatpants — broken_size_run
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Size option 'Size' was identified, but only 0 distinct numeric sizes were parsed; at least 5 are required.
  - The expected size range and category-specific size standards were not provided.
- Rationale: The size-run heuristic needs enough explicitly identified numeric size options to compare observed availability.
- Recommended action: Confirm the size option and expected assortment before evaluating a size-run gap.

## Hoodie — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Valid current and original prices were not both observed; discount level cannot be assessed.
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.
- Recommended action: Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.

## Men's Crewneck — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Valid current and original prices were not both observed; discount level cannot be assessed.
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.
- Recommended action: Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.

## Men's T-shirt — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Valid current and original prices were not both observed; discount level cannot be assessed.
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.
- Recommended action: Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.

## Shorts — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Valid current and original prices were not both observed; discount level cannot be assessed.
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.
- Recommended action: Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.

## Sweatpants — heavy_discount_possible_overstock
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Valid current and original prices were not both observed; discount level cannot be assessed.
  - Inventory age/history was not provided; discount alone does not establish overstock.
- Rationale: A discount requires a non-negative current price and a positive original price at least as high as current price; overstock also requires verified inventory context.
- Recommended action: Verify price data before evaluating discounting; obtain inventory age/history before making an overstock claim.

## Hoodie — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
  - Observed unavailable variants: Medium / Olive, Medium / Purple.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.

## Men's Crewneck — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.

## Men's T-shirt — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.

## Shorts — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.

## Sweatpants — sales_ranked_unavailable_variants
- Assessment: `insufficient_evidence`
- Evidence sufficiency: `insufficient`
- Heuristic priority score: 0/100 (not a probability)
- Evidence:
  - Sales rank was not provided; best-selling status cannot be established.
- Rationale: The best-selling status cannot be assessed without an observed, sourced sales ranking.
- Recommended action: Connect a verified sales ranking or merchant sales feed before prioritizing restock.
