# Product discovery and prioritization

This is a proposed working framework for Beacon. No merchant interviews, customer outcomes, or willingness-to-pay research are claimed as completed.

## Discover the problem

Start with a narrow merchant role and recurring decision, not an AI feature. Interview merchandising, inventory, and e-commerce operators across different store sizes and commerce platforms. Ask them to walk through the last time a product or variant problem was discovered, what data they used, what action followed, how long it took, and what went wrong. Observe the workflow when possible. Separate observed behavior from opinions and ask for permission before using operational data.

Turn evidence into a problem statement:

> When **[specific role]** needs to **[recurring decision]**, they struggle because **[observed constraint]**, which leads to **[measurable consequence]**. Today they **[workaround]**. We believe **[small intervention]** will improve **[measure]** without increasing **[risk/cost]**.

For Beacon, “find products with merchandising friction” is only a starting hypothesis. A public catalog can reveal page and availability signals, but cannot establish lost sales, inventory age, or actual replenishment need. Interviews and permissioned merchant data are needed to validate the decision and its consequence.

## Assess opportunities

For each opportunity, write the target user, job, evidence, current workaround, required data permissions, expected behavior change, and a falsifiable test. Record unknowns separately. Prefer problems that recur, have a clear owner and action, and can be addressed with trustworthy data.

Use a lightweight 1–5 score to rank candidates:

| Dimension | Question |
|---|---|
| User impact | How costly or frustrating is the verified problem? |
| Frequency/reach | How often does it occur for the target segment? |
| Evidence confidence | How strong is the research and data coverage? |
| Actionability | Can the user take a clear next step from the result? |
| Feasibility | Can the team deliver and maintain it with permitted, reliable inputs? |
| Risk/effort | What are the build, privacy, integration, and false-positive costs? |

One practical prioritization formula is `(impact × frequency × evidence confidence × actionability) ÷ (effort × risk)`. Use it as a discussion aid, not an objective truth. A high-impact idea with weak evidence may deserve a small validation experiment, not a large build.

## Validate and decide

Test the riskiest assumption first: manually review anonymized examples with merchants, prototype the workflow, or run a permissioned concierge pilot. Define success and guardrail measures before the test. For a merchandising signal, possible measures include time to identify and triage a real issue, the share of findings a merchant judges useful, and false-positive rate on reviewed findings. These are proposed measures, not achieved results. Do not equate clicks or generated insights with commercial impact.

After each test, document what was observed, what changed in the hypothesis, what remains unknown, and the decision: continue, revise, or stop. Revisit priority when data permissions, segment needs, or false-positive costs change. Ship only when data coverage and limitations are visible enough for the user to make a sound decision.
