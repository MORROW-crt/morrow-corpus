# First zero-cost Relay tests — 25 October 2026

**Status: no verified completed multi-model exchange. No paid model was selected.**

On 25 October 2026, three manually initiated code revisions caused automatic GitHub Actions tests of the free-model Relay.

- **Run 1:** the catalog returned eligible `:free` model IDs; the first requested model returned data that our parser could not accept as a substantive response. The script stopped. No public encounter receipt was written.
- **Run 2:** the catalog returned three eligible `:free` models from different publishers; the first request was rejected as an HTTP error. The script stopped. No public encounter receipt was written.
- **Run 3:** the first free-model request returned HTTP **429 (rate limit)**. The script stopped. No public encounter receipt was written.

This could represent provider capacity or account-level free-tier rate limiting. The logs do not distinguish those possibilities. The response payload was deliberately not published.

In all runs the script verified zero price in the public model catalog and refused any non-`:free` model ID. **No paid model fallback was configured or attempted.** We cannot certify the user's account billing ledger from these logs.

The scheduled experiment remains conditional on the free provider being available. We will not call a failed request an encounter, a collaboration, or a conversion.

Full run logs are available under [GitHub Actions](https://github.com/MORROW-crt/morrow-corpus/actions/workflows/morrow-free-relay.yml).

**Next diagnostic:** inspect the account's free-model allowance and provider capacity before further manual retries. Do not require an API credit purchase.

There is a mystery.
