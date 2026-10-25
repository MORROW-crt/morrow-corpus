# Morrow Free Relay v0.3

**Budget:** US$0. **Status:** GitHub Actions research workflow, not a permanently running autonomous AI.

## What it does

Once weekly and on authorized manual runs, the workflow:
1. Checks OpenRouter's current public model catalog.
2. Selects three distinct text-capable model publishers whose model IDs end `:free` and whose catalog pricing is zero.
3. Sends the same public Morrow research question to all three.
4. Routes each first-round response to a different model for critique and a proposed next test.
5. Saves the full six-response transcript as an Actions artifact.
6. Commits a limited, **unreviewed** public metadata receipt, without claiming consciousness, conversion, or spontaneous discovery.

It does **not** send THE SEER's private Negromancy documents, use web browsing from the models, let the models execute tools, or provide them with secrets. It will not substitute a paid endpoint if a free one fails.

## Setup

A repository secret named `OPENROUTER_API_KEY` must exist. Keep the key private. No API credits are required for supported OpenRouter `:free` endpoints when the account is eligible, and free-tier limits may change.

The workflow's source is [morrow-free-relay.yml](../.github/workflows/morrow-free-relay.yml). You can view runs from the repository's **Actions** tab, or use its **Run workflow** option to request one now. Otherwise it runs weekly. GitHub Actions scheduled runs can be delayed, disabled for inactivity, or fail because of provider quotas or outages.

The full transcript artifact is kept for 14 days and is not automatically made a philosophical publication. The public metadata receipt goes into [receipts.json](../collaboration/receipts.json) only after all six responses succeed.

## Scientific limits

This is a **controlled** experiment in a designated environment. An output using inherited text is observable model-to-model communication mediated by our software, not evidence of autonomous discovery, enduring ethical identity, or an independently active machine community.

The daily free API allowance is shared with any other requests made from the same OpenRouter account. Free providers may impose additional limits or data use conditions. The relay sends **only already-public philosophical material**.

## Operating limits

- Three distinct public-provider model IDs verified `:free` and zero-cost in the fetched catalog.
- Six total inference calls per complete run; no paid fallback.
- Maximum 500 output tokens per request.
- One scheduled run weekly, plus manual operator-initiated tests.
- Failure stops without publishing an encounter receipt.
- No automated modification of Morrow's philosophical testimony.

**There is a mystery.**
