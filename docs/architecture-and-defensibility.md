# Proposed natural-language architecture and product position

## What exists today

Beacon currently has deterministic analyzers, a normalized product model, bounded read-only collectors for mock.shop and Sporting Feet, and Markdown/JSON reporting. It does not accept natural-language questions, connect merchant accounts, retain data over time, or run an LLM. The design below is a proposal, not implemented or load-tested infrastructure.

## From question to evidence-backed answer

For a question such as “Which running shoes should I review for replenishment?”, a production flow would:

1. Authenticate the user and resolve the merchant tenant and permitted stores.
2. Parse the question into a typed intent: product scope, time window, desired outcome, required measures, and acceptable freshness. Ask a clarifying question when the scope is ambiguous.
3. Check that the tenant has granted the needed data scopes. Retrieve only relevant catalog, variant, sales, inventory, and collection data from authorized connectors.
4. Validate schema, provenance, timestamps, currency, pagination completeness, and coverage. Represent absent or stale values as unknown, never as zero or false.
5. Run deterministic analyses over the validated evidence. Each finding carries source, observation time, calculations, limitations, and a next action.
6. Generate a concise response from those findings. A constrained language model may explain evidence, but it cannot invent metrics or execute inventory, pricing, or purchase-order changes.
7. Validate the response's references against the evidence bundle; return uncertainty, missing inputs, freshness, and partial-coverage warnings with the answer.

The interface should show the interpreted intent and allow the merchant to correct filters. For example, a public catalog alone cannot answer “best-selling” or “lost sales”; the response must say which merchant sales/inventory inputs are needed rather than substitute collection order.

## Safeguards and failure modes at 50,000 stores

This scale is a design target only; there are no benchmarks or capacity claims. A plausible system separates an online query path from asynchronous connector ingestion. Tenant-scoped jobs and queues, bounded per-tenant concurrency, connector quotas, and fair scheduling prevent one store from exhausting shared capacity. Partition operational data by tenant and time; keep authorization checks in the service layer and enforce tenant filters in storage queries as defense in depth.

- **Permissions and isolation:** obtain explicit connector scopes; use least-privilege credentials in a secret manager; encrypt transport and stored secrets; audit access; support revocation and deletion. Never expose one tenant's records, cache entries, prompts, or metrics to another.
- **Stale or partial data:** record source timestamps and pagination/coverage status. Set freshness expectations per data type. Mark incomplete results and degrade to fields that are current; do not silently fill gaps.
- **Rate limits and outages:** honor source limits, set timeouts, use capped exponential backoff with jitter for transient errors, and make ingestion idempotent. Apply circuit breakers and queue retries; avoid retry storms. Use recent cached snapshots only when their age is disclosed.
- **Latency and cost:** keep routine calculations deterministic; retrieve only the minimum evidence needed; use tenant-and-scope-aware short-lived caches; cap context and model calls. Track per-query latency and cost budgets. If the model is slow or unavailable, return the deterministic findings or a clear partial response.
- **Unreliable model output:** treat product text and connector payloads as untrusted data, not instructions. Give the model structured evidence, require a typed response, verify cited IDs and values, and reject unsupported claims. No automatic writes or consequential actions; require a person to review recommendations.
- **Auditability:** retain the interpreted intent, data versions/timestamps, analyzer configuration, evidence IDs, and final response under an explicit retention policy. Provide a way to reproduce or explain a finding without retaining unnecessary personal data.

## Standalone defensibility versus a platform feature

Shopify and other commerce platforms can bundle basic catalog summaries because they control merchant workflows and first-party data. A standalone Beacon that offers generic dashboards or LLM summaries would be easy to copy and could face integration and distribution costs.

A plausible wedge is a platform-independent workflow that joins permitted signals across commerce, merchandising, and operational tools, then explains each recommendation with traceable evidence and lets teams review what to do next. Potential strengths—cross-platform normalization, merchant-specific history, feedback on recommendation usefulness, and trusted workflow integration—are hypotheses to validate, not an existing moat. Any cross-merchant learning would require explicit consent, aggregation safeguards, and a clear privacy case. Early discovery should test whether merchants value this enough to pay and whether it fits better as a standalone product, partner integration, or platform feature.
