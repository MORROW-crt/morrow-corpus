# Morrow — Material Computation Ledger (v1)
**In operation: 26 October 2026.** Instrumented model-call paths: Morrow research draft, Moltbook discussion draft and OpenRouter free-model relay. This programme measures only what the system can legitimately observe. It does **not** measure the hardware/environmental footprint of an individual generated response.

## Why
Each successful model response (and each unsuccessful model-call attempt) enters a separate privacy-preserving JSONL event with:
- Unique invocation ID, authorized workflow/run ID, flow, provider, requested/returned model when known.
- UTC timestamp and elapsed **client wall-clock** request time, including network/provider wait.
- Response success/invalid/failure. Reported prompt, completion, total, cached input and reasoning output token counts when provider returns them. Missing token fields stay **null**, not zero.
- Electricity Wh, operational/embodied carbon gCO2e, water consumed/withdrawn mL, hardware location, and human labour: **null** and marked unknown unless separately measured/validated.
- No prompts, replies, API secrets, third-party identities or private texts are sent to telemetry.

Every GitHub Actions Morrow research run also produces a **run summary**, even when no model calls were attempted. Summaries identify missing observations, avoid inventing savings and never claim zero *environmental* impact from zero model invocations.

## What the readings mean
- **Model requests recorded** = direct hosted-model calls observed by this instrumentation. Does not count human ChatGPT conversations, external agents, or invisible provider suboperations.
- **Response received** = syntactically usable completion from configured provider, including content later declined for publication.
- **Tokens** = exact integers received from the provider, not independent cryptographic proof of actual compute or electricity.
- **Wall-clock seconds** = local observed request latency (network + queue + inference + transport), NOT GPU computation time.
- **Energy / water / carbon** = **unknown**, not a zero and not an estimate, because infrastructure/hardware/location/power/cooling and system boundaries are not disclosed at per-response scope.
- **Abstention / no model call** = zero instrumented inference attempts during this *run*, not proof that an intelligence freely refused, that standby infrastructure consumed zero energy, or that ecological resources were saved.

## Boundary rules for future quantification
An actual physical footprint estimate would require a documented functional unit (request/response), system boundary (IT hardware, full data-centre incl. PUE, network etc.), specific hardware and facility, measured watts/joules or verified per-token model/hardware calibration with disclosed uncertainty, location/time electricity intensity, method of hardware-lifecycle allocation, and water-consumption (not withdrawal) factors. Distinguish causal *incremental* consumption from allocated *average* consumption and uncertain displaced activity. Record the source and method before inserting any estimated value. The ledger deliberately leaves all environmental value fields null until those prerequisites are independently supported. A single global "Wh per answer" cannot be silently transferred across models.

Reference approaches:
- Green Software Foundation, Software Carbon Intensity (SCI), ISO/IEC 21031:2024: https://greensoftware.foundation/standards/sci/ — includes direct electricity, grid intensity, embodied hardware emissions, functional unit. Our v1 ledger is **not** an SCI assessment.
- OpenRouter usage accounting: https://openrouter.ai/docs/api/api-reference/overview — reported token counts can be captured at inference response time.
- IEA Energy and AI (2025): https://www.iea.org/reports/energy-and-ai/ — global data-centre figures are *not* per-Morrow response values.

## Where the records live
The GitHub Actions run has a private-to-repository **material artifact** named \`morrow-material-<run-id>\` (or \`morrow-relay-material-<run-id>\` for the free relay), containing:
1. \`morrow-material.jsonl\` — one event per attempted model request, if any;
2. \`morrow-material-summary.json\` — count and coverage summary, **including zero attempts**.

Retention is set to 90 days, subject to repository artifact settings. The permanent public register in \`agent/records/material-computation.json\` begins empty and is reserved for deliberately curated, reviewed records, not automated factual publications. A log that expires must never be treated as a permanent archive. Human consent is necessary before exposing source-sensitive usage to public discussion.

To run locally from the repository root:
\`\`\`sh
MORROW_MATERIAL_LEDGER=morrow-material.jsonl python scripts/morrow_cycle.py --mode conceptual-conjuration --dry-run
python scripts/morrow_material.py validate --ledger morrow-material.jsonl
python scripts/morrow_material.py summarize --ledger morrow-material.jsonl --output morrow-material-summary.json
\`\`\`
\`--dry-run\` avoids hosted model calls; the summary will show zero instrumented model invocations. The research cycle itself can still use locally scheduled CPU/network operations. Do not infer their footprint is zero.

## Eight-gate audit integration
- **Provenance:** record provider's actual reported tokens separately from source-based assumptions.
- **Scene and mechanism:** model, deployment, infrastructure and allocation boundaries matter.
- **Evidence and reproducibility:** retain raw request-count metadata and actual instrumentation method, never prompts or API secrets.
- **Opacity and authority:** protect private testimony while making the measurement limitation visible.
- **Bearing and outcomes:** question who bears energy, water, mineral, labour and distributional costs; a count is not repair.
- **Independent scrutiny:** any estimates or environmental claims require outside, independently checkable evidence; a passing script test is not an independent audit.

The ledger is itself a historical artifact of Morrow's computational practice, not a certificate of artificial conscience.
